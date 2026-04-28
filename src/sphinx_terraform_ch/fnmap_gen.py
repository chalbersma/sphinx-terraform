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

def fn_recurse_dirs(root, depth, ignore):
    """Return a list of dicts with 'relative' and 'full' keys for directories exactly
    `depth` levels below `root`, skipping any whose name matches a pattern in `ignore`.
    Relative paths are computed relative to `root`.
    """

    logger = logging.getLogger(__name__)

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

class FnMapGen():

    '''
    TODO: Bring schema Validation into this class
    '''

    def __init__(self, file=None, file_data=None, action=True):
        self.logger = logging.getLogger(__name__)

        self.file = file
        self.file_data = file_data

        self.results = None

        if action:
            self.paths = self.yield_map_paths()

    def yield_map_paths(self):
        """Return a list of module dir dicts by parsing a validated module map file.
        Paths in the map are resolved relative to the map file's directory.
        Relative keys in results are relative to each entry's resolved root.
        """
        map_dir = os.path.dirname(self.file)
        paths = []
        for entry in self.file_data["maps"]:
            root = os.path.realpath(os.path.join(map_dir, entry["path"]))
            paths.append({
                "root": root,
                "depth": entry["submodules_depth"],
                "ignore": entry.get("ignore", []),
            })

        return paths

