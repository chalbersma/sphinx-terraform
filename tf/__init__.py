#!/usr/bin/env python3

from .tfmodule import TFBlock, TFModule, TFParse

from sphinx.application import Sphinx

def setup(app: Sphinx):

    """
    Extension Setup, Called By Sphinx
    """

    app.add_directive("tfmodule", TFParse)


