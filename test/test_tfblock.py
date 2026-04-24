#!/usr/bin/env python3
"""Unit tests for TFBlock comment parsing.

Tests cover:
- normalize_comment: all comment styles, empty marker lines, block comment delimiters
- preceding_comments: using real .tf fixtures in test/terraform/
"""

import pathlib
from unittest.mock import patch

import pytest

from sphinx_terraform_ch.tfblock import TFBlock

TERRAFORM_DIR = pathlib.Path(__file__).parent / "terraform"
PROJECT_A = TERRAFORM_DIR / "projectA"
PROJECT_B = TERRAFORM_DIR / "projectB"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_block(block_type: str, labels: list, file_path: pathlib.Path) -> TFBlock:
    """Instantiate a TFBlock with sphinx logging silenced."""
    with patch("sphinx_terraform_ch.tfblock.logging"):
        return TFBlock(
            file=file_path.name,
            fullpath=file_path,
            module="test",
            block_type=block_type,
            labels=labels,
            data={},
        )


# ---------------------------------------------------------------------------
# normalize_comment — pure function tests (no file I/O)
# ---------------------------------------------------------------------------

@pytest.fixture
def block():
    """A TFBlock instance used only to call normalize_comment."""
    return make_block("variable", ["dummy"], PROJECT_B / "variables.tf")


class TestNormalizeCommentHash:
    def test_single_line(self, block):
        assert block.normalize_comment("# A comment") == "A comment"

    def test_strips_leading_space(self, block):
        assert block.normalize_comment("#   spaced") == "spaced"

    def test_multiline(self, block):
        raw = "# First line\n# Second line"
        assert block.normalize_comment(raw) == "First line\nSecond line"

    def test_empty_marker_line_becomes_blank(self, block):
        """A bare '#' with no text should produce an empty line, not '#'."""
        raw = "# Line one\n#\n# Line two"
        assert block.normalize_comment(raw) == "Line one\n\nLine two"


class TestNormalizeCommentDoubleSlash:
    def test_single_line(self, block):
        assert block.normalize_comment("// A comment") == "A comment"

    def test_strips_leading_space(self, block):
        assert block.normalize_comment("//   spaced") == "spaced"

    def test_multiline(self, block):
        raw = "// First line\n// Second line"
        assert block.normalize_comment(raw) == "First line\nSecond line"

    def test_empty_marker_line_becomes_blank(self, block):
        """A bare '//' with no text should produce an empty line, not '//'."""
        raw = "// Line one\n//\n// Line two"
        assert block.normalize_comment(raw) == "Line one\n\nLine two"


class TestNormalizeCommentBlockStyle:
    def test_single_line_block(self, block):
        assert block.normalize_comment("/* A comment */") == "A comment"

    def test_opening_delimiter_only_produces_no_output(self, block):
        """'/**' or '/*' alone should not appear in cleaned output."""
        raw = "/**\n  Content here\n */"
        result = block.normalize_comment(raw)
        assert "/**" not in result
        assert "*/" not in result
        assert "Content here" in result

    def test_closing_delimiter_not_in_output(self, block):
        """Closing ' */' line should not appear in cleaned output."""
        raw = "/* A comment\n */"
        result = block.normalize_comment(raw)
        assert "*/" not in result
        assert result == "A comment"

    def test_multiline_block_interior_content(self, block):
        """Interior lines of a block comment are returned as-is (stripped)."""
        raw = "/**\n  Line one.\n\n  Line two.\n */"
        result = block.normalize_comment(raw)
        assert "Line one." in result
        assert "Line two." in result
        assert "/**" not in result
        assert "*/" not in result

    def test_interior_star_lines(self, block):
        """Lines like ' * text' inside a block comment strip the leading '*'."""
        raw = "/*\n * First\n * Second\n */"
        result = block.normalize_comment(raw)
        assert "First" in result
        assert "Second" in result


# ---------------------------------------------------------------------------
# preceding_comments — integration tests against real .tf files
# ---------------------------------------------------------------------------

class TestPrecedingCommentsHash:
    def test_single_hash_comment(self):
        """resource with a single '#' comment directly above it."""
        block = make_block("resource", ["aws_s3_bucket", "main"], PROJECT_A / "s3.tf")
        assert block.preceding_comments == "Primary storage bucket for project assets."

    def test_single_hash_comment_public_access(self):
        """resource with a '#' comment; blank line above comment stops collection."""
        block = make_block(
            "resource", ["aws_s3_bucket_public_access_block", "main"], PROJECT_A / "s3.tf"
        )
        assert block.preceding_comments == "Block all public access by default."

    def test_hash_comment_on_variable_with_hyphen(self):
        """Variable with a hyphen in the label name."""
        block = make_block("variable", ["some-variable"], PROJECT_B / "variables.tf")
        assert block.preceding_comments == "A very nice input variable"

    def test_hash_comment_submodule_hyphen_label(self):
        """Variable with hyphen label in a sub-directory."""
        block = make_block(
            "variable", ["submodule-input"], PROJECT_B / "sub" / "variables.tf"
        )
        assert block.preceding_comments == "A very nice input variable in submodule"

    def test_multiline_hash_comment_with_blank_marker_line(self):
        """Multi-line '#' comment where empty '#' lines should become blank lines."""
        block = make_block("data", ["foo_data", "qux"], PROJECT_B / "main.tf")
        result = block.preceding_comments
        assert result is not None
        assert "Documentation for this data." in result
        assert "Might be somewhat related to" in result
        # Empty '#' line between the two sentences must NOT appear as a literal '#'
        assert "\n#\n" not in result


class TestPrecedingCommentsDoubleSlash:
    def test_multiline_double_slash(self):
        """Terraform block preceded by multi-line '//' comment."""
        block = make_block("terraform", [], PROJECT_B / "main.tf")
        result = block.preceding_comments
        assert result is not None
        assert "Documentation for terraform/main.tf" in result
        assert "list item 1" in result
        assert "list item 2" in result

    def test_empty_slash_line_becomes_blank(self):
        """Empty '//' lines inside the comment must not produce a bare '//' line."""
        block = make_block("terraform", [], PROJECT_B / "main.tf")
        result = block.preceding_comments
        assert result is not None
        # A bare '//' marker line should become an empty line, not the literal '//'
        assert "\n//\n" not in result
        assert not result.startswith("//")


class TestPrecedingCommentsBlockStyle:
    def test_compact_multiline_block(self):
        """'/* ... \\n */' block comment — closing line must not appear in output."""
        block = make_block(
            "resource", ["aws_s3_bucket_versioning", "main"], PROJECT_A / "s3.tf"
        )
        result = block.preceding_comments
        assert result is not None
        assert "Another Pre Comment" in result
        assert "*/" not in result

    def test_multiline_block_rst_content(self):
        """Multi-line '/** ... */' comment with RST content."""
        block = make_block("resource", ["foo_resource", "baz"], PROJECT_B / "main.tf")
        result = block.preceding_comments
        assert result is not None
        assert "Here is a" in result
        assert "/**" not in result
        assert "*/" not in result

    def test_multiline_block_markdown_content(self):
        """Multi-line '/** ... */' comment with Markdown content."""
        block = make_block("resource", ["foo_resource", "markdown"], PROJECT_B / "main.tf")
        result = block.preceding_comments
        assert result is not None
        assert "Markdown" in result
        assert "/**" not in result
        assert "*/" not in result


class TestPrecedingCommentsNone:
    def test_no_comment_returns_none(self):
        """Block with no comment above it returns None."""
        block = make_block("output", ["some-output"], PROJECT_B / "outputs.tf")
        assert block.preceding_comments is None

    def test_blank_line_gap_stops_collection(self):
        """Blank line between a comment and the block means no comment captured."""
        # resource "aws_s3_bucket_server_side_encryption_configuration" has no
        # adjacent comment — it's separated from the previous block by blank lines.
        block = make_block(
            "resource",
            ["aws_s3_bucket_server_side_encryption_configuration", "main"],
            PROJECT_A / "s3.tf",
        )
        assert block.preceding_comments is None

    def test_module_without_adjacent_comment_returns_none(self):
        """Module block separated from prior content by a blank line."""
        block = make_block("module", ["foobar"], PROJECT_B / "main.tf")
        assert block.preceding_comments is None
