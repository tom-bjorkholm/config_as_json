#! /usr/local/bin/python3
"""Function for checking that file exists."""

# Copyright (c) 2024-2025 Tom Björkholm
# MIT License


from pathlib import Path
from typing import TextIO
import sys
from typing import Optional
from config_as_json.commontypes import PathOrStr


def file_must_exist(filename: PathOrStr,
                    with_content_txt: Optional[str] = None,
                    stderr_file: TextIO = sys.stderr) -> None:
    """Check that input file exists. Exit if not."""
    if not isinstance(filename, Path):
        filename = Path(filename)
    if not filename.exists():
        msg = f'File {str(filename)} '
        if with_content_txt is not None:
            msg += 'with ' + with_content_txt + ' '
        msg += 'does not exist. Cannot proceed.'
        print(msg, file=stderr_file)
        sys.exit(1)
