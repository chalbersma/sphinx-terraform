#!/usr/bin/env python3

import os
import re
import json

from sphinx.util import logging
from docutils.utils import new_document
from docutils.parsers.rst import Directive, directives
from myst_parser.parsers.sphinx_ import MystParser

from .tfmodule import TFModule


class TFParse(Directive):
    logger = logging.getLogger("TFParse")

    option_spec = {
        "path": directives.path,
        "submodules_depth": directives.nonnegative_int,
        "ignore": directives.unchanged,
        "hide_nocomment": directives.flag,
    }

    def _dirs_at_depth(self):
        """Yield dicts with 'relative' and 'full' keys for directories exactly
        `submodules_depth` levels below `path`, skipping any whose name matches
        a pattern in `ignore`.
        """
        root = os.path.realpath(os.path.expanduser(self.options["path"]))
        depth = self.options.get("submodules_depth", 0)
        ignore = json.loads(self.options.get("ignore", "[]"))

        def _recurse(current, remaining):
            if remaining == 0:
                yield {"relative": os.path.relpath(current, root), "full": current}
                return
            for entry in sorted(os.scandir(current), key=lambda e: e.name):
                self.logger.warning(f"Debugging Entry {entry.name}, {ignore}")
                entry_pass = True
                for pattern in ignore:
                    if re.search(pattern, entry.name):
                        entry_pass = False
                        self.logger.info(f"Ignoring {entry.name} because it matches {pattern}")
                        break
                if entry.is_dir() and entry_pass:
                    yield from _recurse(entry.path, remaining - 1)

        yield from _recurse(root, depth)

    def run(self):

        md_text = list()

        path = self.options.get("path", None)

        if path is not None:
            path = os.path.realpath(os.path.expanduser(path))
            if not os.path.isdir(path):
                raise self.error(f":path: {path!r} is not a directory")

        module_paths = list(self._dirs_at_depth()) if path is not None else []

        hide_nocomment = "hide_nocomment" in self.options

        for this_modules_path in module_paths:
            this_module = TFModule(name=this_modules_path["relative"],
                                   path=this_modules_path["full"],
                                   hide_nocomment=hide_nocomment)
            md_text.extend(this_module.get_markdown())

        transient_doc = new_document("<tfmodule>", self.state.document.settings)

        MystParser().parse("\n".join(md_text), transient_doc)

        return transient_doc.children
