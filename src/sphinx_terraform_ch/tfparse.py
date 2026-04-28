#!/usr/bin/env python3

import os
import re
import json
import pathlib

import jsonschema
import yaml

from sphinx.util import logging
from docutils.utils import new_document
from docutils.parsers.rst import Directive, directives
from myst_parser.parsers.sphinx_ import MystParser

from .tfmodule import TFModule
from .fnmap_gen import FnMapGen, fn_recurse_dirs

class TFParse(Directive):
    logger = logging.getLogger("TFParse")

    option_spec = {
        "path": directives.path,
        "file": directives.path,
        "submodules_depth": directives.nonnegative_int,
        "ignore": directives.unchanged,
        "hide_nocomment": directives.flag,
    }

    def yield_module_dirs(self):
        """Return a list of module dir dicts from the :path: directive option."""
        paths = [
            {
                "root": os.path.realpath(os.path.expanduser(self.options["path"])),
                "depth": self.options.get("submodules_depth", 0),
                "ignore": json.loads(self.options.get("ignore", "[]")),
            }
        ]
        results = []
        for p in paths:
            self.logger.info(f"Debugging Ignore Entries for {p['root']}, {p['ignore']}")
            results.extend(fn_recurse_dirs(p["root"], p["depth"], p["ignore"]))
        return results

    def run(self):

        md_text = list()

        path = self.options.get("path", None)
        file = self.options.get("file", None)

        if path and file:
            raise self.error("':path:' and ':file:' are mutually exclusive")

        if path is not None:
            path = os.path.realpath(os.path.expanduser(path))
            if not os.path.isdir(path):
                raise self.error(f":path: {path!r} is not a directory")

        if file is not None:
            file = os.path.realpath(os.path.expanduser(file))
            if not os.path.isfile(file):
                raise self.error(f":file: {file!r} is not a file")

            schema_path = pathlib.Path(__file__).parent / "module_map.schema.json"
            schema = json.loads(schema_path.read_text())

            try:
                file_data = yaml.safe_load(pathlib.Path(file).read_text())
            except yaml.YAMLError as exc:
                raise self.error(f":file: {file!r} could not be parsed: {exc}")

            try:
                jsonschema.validate(file_data, schema)
            except jsonschema.ValidationError as exc:
                raise self.error(f":file: {file!r} failed schema validation: {exc.message}")

            paths = FnMapGen(file, file_data).paths

            module_paths = []
            for p in paths:
                module_paths.extend(fn_recurse_dirs(p["root"], p["depth"], p["ignore"]))

        elif path is not None:
            module_paths = self.yield_module_dirs()

        else:
            module_paths = []

        hide_nocomment = "hide_nocomment" in self.options

        for this_modules_path in module_paths:
            this_module = TFModule(name=this_modules_path["relative"],
                                   path=this_modules_path["full"],
                                   hide_nocomment=hide_nocomment)
            md_text.extend(this_module.get_markdown())

        transient_doc = new_document("<tfmodule>", self.state.document.settings)

        MystParser().parse("\n".join(md_text), transient_doc)

        return transient_doc.children
