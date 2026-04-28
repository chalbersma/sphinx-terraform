#!/usr/bin/env python3

import argparse
import os
import sys
import logging

from sphinx_terraform_ch.tfmodule import TFModule


def get_parser(color=False):
    parser = argparse.ArgumentParser(
        prog="tfreport",
        description="Generate a Terraform documentation report for a module path.",
        color=color
    )
    parser.add_argument(
        "path",
        help="Path to the Terraform module directory.",
    )
    parser.add_argument(
        "--level",
        type=int,
        default=1,
        help="Heading level for the generated report (default: 1).",
    )

    parser.add_argument("-v", "--verbose", action="append_const", help="Verbosity Controls",
                        const=1, default=[])

    return parser


def main():
    parser = get_parser(color=True)
    args = parser.parse_args()

    VERBOSE = len(args.verbose)
    EXTRA_MODULES = ["boto3", "urllib3", "botocore", "botocore.hooks", "botocore.retryhandler"]

    if VERBOSE == 0:
        logging.basicConfig(level=logging.ERROR)
        extra_level = logging.ERROR
    elif VERBOSE == 1:
        logging.basicConfig(level=logging.WARNING)
        extra_level = logging.ERROR
    elif VERBOSE == 2:
        logging.basicConfig(level=logging.INFO)
        extra_level = logging.WARNING
    elif VERBOSE == 3:
        logging.basicConfig(level=logging.DEBUG)
        extra_level = logging.INFO
    else:
        logging.basicConfig(level=logging.DEBUG)
        extra_level = logging.DEBUG

    for mod in EXTRA_MODULES:
        logging.getLogger(mod).setLevel(extra_level)

    logger = logging.getLogger(__name__)


    path = os.path.realpath(os.path.expanduser(args.path))
    if not os.path.isdir(path):
        logger.error(f"path {path!r} is not a directory")
        raise NotADirectoryError()

    name = os.path.basename(path)
    module = TFModule(path=path, name=name, level=args.level)

    print("\n".join(module.get_markdown()))

if __name__ == "__main__":
    sys.exit(main())
