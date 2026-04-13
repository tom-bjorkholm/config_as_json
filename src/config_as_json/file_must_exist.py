#! /usr/local/bin/python3
"""Check that a required input file exists before continuing."""

# Copyright (c) 2024-2025 Tom Björkholm
# MIT License


from pathlib import Path
from typing import TextIO, Optional
import sys
from config_as_json.commontypes import PathOrStr


def file_must_exist(filename: PathOrStr,
                    with_content_txt: Optional[str] = None,
                    stderr_file: TextIO = sys.stderr) -> None:
    """Terminate with a helpful message when an expected file is missing.

    Args:
        filename: Path to the file that must exist.
        with_content_txt: Optional human-readable description of the expected
                          file contents.
        stderr_file: Stream used for user-facing diagnostics. Defaults to
                     ``sys.stderr``.

    Raises:
        SystemExit: The file does not exist.
    """
    if not isinstance(filename, Path):
        filename = Path(filename)
    if not filename.exists():
        msg = f'File {str(filename)} '
        if with_content_txt is not None:
            msg += 'with ' + with_content_txt + ' '
        msg += 'does not exist. Cannot proceed.'
        print(msg, file=stderr_file)
        sys.exit(1)
