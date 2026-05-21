#! /usr/local/bin/python3
"""Collect shared type aliases and typing helpers for the package.

The aliases in this module describe JSON-compatible values and path-like
input.
"""

# Copyright (c) 2024-2026 Tom Björkholm
# MIT License

from pathlib import Path
# imports needed by mypy, but not by python:
# pylint: disable-next=unused-import,ungrouped-imports
from typing import Union, List, Dict


type PathOrStr = Path | str
"""Path or string representing a file name."""

type JsonType = \
    'Union[None, int, str, bool, List[JsonType], Dict[str, JsonType]]'
"""Recursive JSON value accepted by the configuration helpers."""

type ConfigPath = tuple[str, ...]
"""Path through decoded configuration JSON data.

The path rules are shared by features that need to point at values inside a
configuration-shaped JSON data tree, including read old configuration file
(ROCF) rules and write-side JSON conversion hooks.

A path is interpreted relative to a root data object chosen by the caller. For
ROCF rules, that root is the parsed root JSON object being normalized. For
write-side conversion hooks, that root is the data owned by the current
``Config`` object. Declared nested ``Config`` objects define ownership
boundaries and use their own paths.

Ordinary path elements are dictionary keys. The special path element ``'['``
means "each list element". For example, ``('outputs', '[', 'format')``
addresses the ``format`` key in every object inside the root ``outputs`` list.

Paths must be non-empty and must start with a dictionary key. Any path element
that starts with ``'['`` but is not exactly ``'['`` is reserved for future list
syntax and is illegal in declarative path rules.
"""
