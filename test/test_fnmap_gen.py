#!/usr/bin/env python3
"""Unit tests for FnMapGen module map generation.

Tests cover:
- Default config does not include paths from test/terraform
- Default config includes projects in example_map and example_map2
- ignore_cat filters entries by their per-entry category field
"""

import pathlib
import yaml
from unittest.mock import patch

import pytest

from sphinx_terraform_ch.fnmap_gen import FnMapGen

TEST_DIR = pathlib.Path(__file__).parent
MODULE_MAP = TEST_DIR / "module_map.yaml"


@pytest.fixture
def map_file_data():
    with open(MODULE_MAP) as f:
        return yaml.safe_load(f)


def make_fnmapgen(file_data, ignore_cat=None):
    """Instantiate FnMapGen with sphinx logging silenced."""
    with patch("sphinx_terraform_ch.fnmap_gen.logging"):
        return FnMapGen(
            file=str(MODULE_MAP),
            file_data=file_data,
            ignore_cat=ignore_cat,
        )


# ---------------------------------------------------------------------------
# Default config
# ---------------------------------------------------------------------------

class TestFnMapGenDefault:
    def test_ignores_terraform_dir(self, map_file_data):
        """Default config must not include any paths under test/terraform."""
        gen = make_fnmapgen(map_file_data)
        terraform_dir = str(TEST_DIR / "terraform")
        roots = [p["root"] for p in gen.paths]
        assert not any(r.startswith(terraform_dir) for r in roots)

    def test_includes_example_map(self, map_file_data):
        """Default config must include at least one path from example_map."""
        gen = make_fnmapgen(map_file_data)
        example_map_dir = str(TEST_DIR / "example_map")
        roots = [p["root"] for p in gen.paths]
        assert any(r.startswith(example_map_dir) for r in roots)

    def test_includes_example_map2(self, map_file_data):
        """Default config must include at least one path from example_map2."""
        gen = make_fnmapgen(map_file_data)
        example_map2_dir = str(TEST_DIR / "example_map2")
        roots = [p["root"] for p in gen.paths]
        assert any(r.startswith(example_map2_dir) for r in roots)


# ---------------------------------------------------------------------------
# ignore_cat filtering
# ---------------------------------------------------------------------------

class TestFnMapGenIgnoreCat:
    def test_ignore_cat_two_excludes_example_map2(self, map_file_data):
        """ignore_cat='Two' must exclude category Two entries (example_map2)."""
        gen = make_fnmapgen(map_file_data, ignore_cat="Two")
        example_map2_dir = str(TEST_DIR / "example_map2")
        roots = [p["root"] for p in gen.paths]
        assert not any(r.startswith(example_map2_dir) for r in roots)

    def test_ignore_cat_two_keeps_category_one(self, map_file_data):
        """ignore_cat='Two' must still include category One entries (example_map)."""
        gen = make_fnmapgen(map_file_data, ignore_cat="Two")
        example_map_dir = str(TEST_DIR / "example_map")
        roots = [p["root"] for p in gen.paths]
        assert any(r.startswith(example_map_dir) for r in roots)
