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


class TFParse(Directive):
    logger = logging.getLogger("TFParse")

    option_spec = {
        "path": directives.path,
        "file": directives.path,
        "submodules_depth": directives.nonnegative_int,
        "ignore": directives.unchanged,
        "hide_nocomment": directives.flag,
    }

    @staticmethod
    def _recurse_dirs(root, depth, ignore, logger):
        """Return a list of dicts with 'relative' and 'full' keys for directories exactly
        `depth` levels below `root`, skipping any whose name matches a pattern in `ignore`.
        Relative paths are computed relative to `root`.
        """
        results = []

        def _recurse(current, remaining):
            if remaining == 0:
                results.append({"relative": os.path.relpath(current, root), "full": current})
                return
            for entry in sorted(os.scandir(current), key=lambda e: e.name):
                entry_pass = True
                for pattern in ignore:
                    if re.search(pattern, entry.name):
                        entry_pass = False
                        logger.info(f"Ignoring {entry.name} because it matches {pattern}")
                        break
                if entry.is_dir() and entry_pass:
                    _recurse(entry.path, remaining - 1)

        _recurse(root, depth)
        return results

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
            results.extend(self._recurse_dirs(p["root"], p["depth"], p["ignore"], self.logger))
        return results

    def yield_map_paths(self, file, file_data):
        """Return a list of module dir dicts by parsing a validated module map file.
        Paths in the map are resolved relative to the map file's directory.
        Relative keys in results are relative to each entry's resolved root.
        """
        map_dir = os.path.dirname(file)
        paths = []
        for entry in file_data["maps"]:
            root = os.path.realpath(os.path.join(map_dir, entry["path"]))
            paths.append({
                "root": root,
                "depth": entry["submodules_depth"],
                "ignore": entry.get("ignore", []),
            })
        results = []
        for p in paths:
            self.logger.info(f"Debugging Ignore Entries for {p['root']}, {p['ignore']}")
            results.extend(self._recurse_dirs(p["root"], p["depth"], p["ignore"], self.logger))
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

            module_paths = self.yield_map_paths(file, file_data)

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
