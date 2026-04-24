#!/usr/bin/env python3

import os
import pathlib

import pygohcl
from sphinx.util import logging

from .tfblock import TFBlock


class TFModule:

    block_depths = {
        "resource": {"labels": 2},
        "variable": {"labels": 1},
        "locals": {"labels": 0},
        "data": {"labels": 2},
        "terraform": {"labels": 0},
        "module": {"labels": 1},
        "provider": {"labels": 1},
        "check": {"labels": 1},
        "import": {"labels": 0},
        "removed": {"labels": 0},
    }

    def __init__(self, path, name=None, level=3):
        self.logger = logging.getLogger("TFModule")

        self.path = path
        self.name = name or os.path.basename(path)
        self.level = level

        self.module_blocks = [block for block in self.iterate_all_tf_files()]

    def get_markdown(self):

        markdown = ["", "#"*self.level+ f" Module: {self.name}", "",
                    f"```{{tf:project}} {self.name}","```"]

        self.logger.debug(f"Generating Markdown for {self.name}")

        for block in self.module_blocks:

            markdown.extend(block.generate_markdown())

        return markdown


    def iterate_all_tf_files(self):
        """Yield a TFBlock for every block found in all *.tf files under self.path."""
        root = pathlib.Path(self.path)

        for tf_file in sorted(root.rglob("*.tf")):
            try:
                parsed = pygohcl.loads(tf_file.read_text())
            except pygohcl.HCLParseError as e:
                self.logger.warning(f"Failed to parse {tf_file}: {e}")
                continue

            rel_path = tf_file.relative_to(root)

            for block_type, config in self.block_depths.items():
                if block_type not in parsed:
                    continue

                num_labels = config["labels"]
                block_data = parsed[block_type]

                if num_labels == 0:
                    blocks = block_data if isinstance(block_data, list) else [block_data]
                    for block_dict in blocks:
                        yield TFBlock(
                            file=str(rel_path),
                            fullpath=str(tf_file),
                            module=self.name,
                            block_type=block_type,
                            labels=[],
                            data=block_dict,
                        )
                elif num_labels == 1:
                    for label1 in block_data:
                        yield TFBlock(
                            file=str(rel_path),
                            fullpath=str(tf_file),
                            module=self.name,
                            block_type=block_type,
                            labels=[label1],
                            data=block_data[label1],
                        )
                elif num_labels == 2:
                    for label1, inner in block_data.items():
                        for label2 in inner:
                            yield TFBlock(
                                file=str(rel_path),
                                fullpath=str(tf_file),
                                module=self.name,
                                block_type=block_type,
                                labels=[label1, label2],
                                data=inner[label2],
                            )
