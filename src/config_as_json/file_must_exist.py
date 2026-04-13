#! /usr/local/bin/python3
"""Function for checking that file exists."""

# Copyright (c) 2024-2025 Tom Björkholm
# MIT License


from os import path
import sys
from typing import Optional


def file_must_exist(filename: str,
                    with_content_txt: Optional[str] = None) -> None:
    """Check that input file exists. Exit if not."""
    if not path.exists(filename):
        msg = f'File {filename} '
        if with_content_txt is not None:
            msg += 'with ' + with_content_txt + ' '
        msg += 'does not exist. Cannot proceed.'
        print(msg, file=sys.stderr)
        sys.exit(1)
