#!/usr/bin/env python3

from .tfblock import TFBlock
from .tfmodule import TFModule
from .tfparse import TFParse

from .tfdomain import TerraformDomain

from .fnmap_gen import FnMapGen, fn_recurse_dirs

from sphinx.application import Sphinx

def setup(app: Sphinx):

    """
    Extension Setup, Called By Sphinx
    """

    app.add_directive("tfmodule", TFParse)
    app.add_domain(TerraformDomain)


