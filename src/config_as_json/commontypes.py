#! /usr/local/bin/python3
"""Collect shared type aliases and typing helpers for the package.

The aliases in this module describe JSON-compatible values and path-like
input.
"""

# Copyright (c) 2024-2026 Tom Björkholm
# MIT License

from pathlib import Path
# imports needed by mypy, but not by python:
from typing import Union, List, Dict  # pylint: disable=unused-import,ungrouped-imports # noqa: E501


type PathOrStr = Path | str
"""Path or string representing a file name."""

type JsonType = \
    'Union[None, int, str, bool, List[JsonType], Dict[str, JsonType]]'
"""Recursive JSON value accepted by the configuration helpers."""
