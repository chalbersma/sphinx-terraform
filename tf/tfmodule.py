#!/usr/bin/env python3

import logging
import os


from docutils import nodes
from docutils.utils import new_document
from docutils.frontend import get_default_settings
from docutils.parsers.rst import Directive

from myst_parser.parsers.docutils_ import Parser

class TFBlock:

    def __init__(self, file, module):

        self.logger = logging.getLogger("sphinx_terraform.tfmodule")

        self.file = file
        self.module = module

class TFModule:

    def __init__(self, path):

        self.logger = logging.getLogger("sphinx_terraform.tfmodule")

        self.path = path


class TFParse(Directive):

    logger = logging.getLogger("sphinx_terraform.tfparse")

    def run(self):

        settings = get_default_settings()
        document = new_document("report", settings)

        debug_string = '''**Debugging**'''

        this_parser = Parser()

        this_parser.parse(debug_string, document)

        return document.children



