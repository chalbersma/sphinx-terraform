#!/usr/bin/env python3

import argparse
import os
import sys
import logging
import json

import yaml

from sphinx_terraform_ch import FnMapGen, fn_recurse_dirs

def get_parser(color=False):
    parser = argparse.ArgumentParser(
        prog="tfreport",
        description="Expand the Terraform Map",
        color=color
    )
    parser.add_argument(
        "map",
        help="Map of Terraform Modules yaml file",
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


    map = os.path.realpath(os.path.expanduser(args.map))
    if not os.path.isfile(map):
        logger.error(f"map {map} is not a file")
        raise FileNotFoundError()

    try:
        with open (map, "r") as map_fobj:
            map_data = yaml.safe_load(map_fobj)
    except yaml.YAMLError as exc:
        logger.error(f"Error parsing map file: {map}")
        logger.debug(f"Error: {exc}")
        raise exc

    paths = FnMapGen(map, map_data).paths

    module_paths = []

    for p in paths:
        module_paths.extend(fn_recurse_dirs(p["root"], p["depth"], p["ignore"]))

    print(json.dumps(module_paths, indent=2, default=True, sort_keys=True))


if __name__ == "__main__":
    main()
