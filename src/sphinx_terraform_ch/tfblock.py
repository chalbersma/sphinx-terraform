#!/usr/bin/env python3

import re
import pathlib

from sphinx.util import logging


class TFBlock:

    def __init__(self, file: str|pathlib.Path, fullpath: str|pathlib.Path, module: str, block_type: str, labels: list[str], data: dict):
        self.logger = logging.getLogger("TFBlock")

        self.file = file
        self.fullpath = fullpath
        self.module = module
        self.block_type = block_type
        self.labels = labels
        self.data = data

        self.logger.debug(f"Parsing Module {self.module} {self.file} {self.block_type} {" ".join(self.labels)}")
        self.logger.debug(f"{self.line_number}")
        self.logger.debug(f"{self.preceding_comments}")
        self.logger.debug(f"{self.source_code}")

    def _find_block_span(self, content: str):
        """Find (start, end) of this block using header regex + brace counting.

        Regex locates the block header and opening brace; brace counting finds
        the matching close brace, handling arbitrary nesting depth.
        """
        header_parts = [re.escape(self.block_type)]
        for label in self.labels:
            header_parts.append(rf'"{re.escape(label)}"')
        header_pattern = re.compile(r'\s+'.join(header_parts) + r'\s*\{')

        m = header_pattern.search(content)
        if not m:
            return None

        start = m.start()
        depth = 0
        for i in range(m.end() - 1, len(content)):
            if content[i] == '{':
                depth += 1
            elif content[i] == '}':
                depth -= 1
                if depth == 0:
                    return (start, i + 1)

        return None  # unclosed block

    def _match_in_file(self):
        """Return (content, span) cached — reads the file at most once per instance.

        span is a (start, end) tuple of character offsets, or None if not found.
        """
        if not hasattr(self, '_cached_file_data'):
            try:
                content = pathlib.Path(self.fullpath).read_text()
            except OSError:
                self._cached_file_data = (None, None)
            else:
                self._cached_file_data = (content, self._find_block_span(content))
        return self._cached_file_data

    @property
    def source_code(self) -> str | None:
        """Find and return the source text of this block from its file."""
        content, span = self._match_in_file()
        return content[span[0]:span[1]] if span else None

    @property
    def line_number(self) -> int | None:
        """Return the 1-based line number where this block starts in its file."""
        content, span = self._match_in_file()
        if not span:
            return None
        return content[:span[0]].count('\n') + 1

    @property
    def preceding_comments(self) -> str | None:
        """Return any comments that directly precede this block (no blank lines between).

        Handles #, //, and /* */ comment styles, including multi-line block comments.
        """
        content, span = self._match_in_file()
        if not span:
            return None

        lines = content[:span[0]].splitlines()
        collected = []
        in_block_comment = False  # True while scanning backwards inside a /* */ block

        for line in reversed(lines):
            stripped = line.strip()

            if in_block_comment:
                # Still inside a block comment (scanning backwards); keep going until /*
                collected.append(line)
                if stripped.startswith('/*'):
                    in_block_comment = False
            elif not stripped:
                # Blank line — stop, comments must be contiguous with the block
                break
            elif stripped.startswith('/*') and stripped.endswith('*/'):
                # Single-line block comment: /* ... */
                collected.append(line)
            elif stripped.endswith('*/'):
                # End of a multi-line block comment (we're scanning backwards into it)
                collected.append(line)
                in_block_comment = True
            elif stripped.startswith('#') or stripped.startswith('//'):
                collected.append(line)
            else:
                break

        if not collected:
            return None

        return self.normalize_comment('\n'.join(reversed(collected)))

    def normalize_comment(self, comment: str) -> str:
        """Strip comment markers from extracted HCL comment text.

        Handles #, //, /* */, and interior * lines from block comments.
        Preserves markdown list items (e.g. '* item' with a leading space-star).
        """
        lines = comment.splitlines()
        cleaned = []
        for line in lines:
            s = line.strip()
            if s.startswith('/*') or s.startswith('*/'):
                s = s.lstrip('/*').rstrip('*/').strip()
            elif s.startswith('//'):
                s = s[2:].strip()
            elif s.startswith('#'):
                s = s[1:].strip()
            elif s.startswith('*'):
                s = s.lstrip('*').strip()
            if not s:
                cleaned.append("")
            else:
                cleaned.append(s)
        return '\n'.join(cleaned).strip()


    def generate_markdown(self):


        if len(self.labels) > 0:
            label_text = " ".join(self.labels)
        else:
            label_text = f"{self.module}:{self.block_type}"

        self.logger.debug(f"Generate Markdown for {self.module}'s {self.block_type} {label_text}")

        snippet = ["", f"```{{tf:{self.block_type}}} {label_text}",
                   "",
                   f"{self.preceding_comments or ''}", "```"]


        # Future Logic to Toggle Comments
        code_snippet = ["", "```{code-block} tf",
                        ":linenos:",
                        f":lineno-start: {self.line_number}",
                        f":caption: Definition of {self.block_type} {label_text} from file `{self.file}`",
                        "",
                        self.source_code or '',
                        "```"
                        ]

        # For Future togglability
        snippet.extend(code_snippet)

        self.logger.debug("\n".join(snippet))

        return snippet