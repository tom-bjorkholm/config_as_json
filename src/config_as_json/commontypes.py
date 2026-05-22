#! /usr/local/bin/python3
"""Collect shared type aliases and typing helpers for the package.

The aliases in this module describe JSON-compatible values and path-like
input.
"""

# Copyright (c) 2024-2026 Tom Björkholm
# MIT License

from pathlib import Path
from types import NoneType


type PathOrStr = Path | str
"""Path or string representing a file name."""

type JsonType = None | int | float | str | bool | list[JsonType] | \
    dict[str, JsonType]
"""Recursive JSON value accepted by the configuration helpers.

JSON numbers can be either Python ``int`` or ``float``. Both are accepted as
valid leaves of the recursive type. ``bool`` is included because Python's
``bool`` is a subclass of ``int`` and ``json.dumps`` writes it as a literal
``true`` or ``false``.
"""

json_types = (NoneType, int, float, str, bool, list, dict)
"""Tuple of all JSON-compatible types for use in isinstance checks."""


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
A path ends with ``'['`` when a rule intentionally targets the list elements
themselves instead of a dictionary key inside those elements.

Paths must be non-empty and must start with a dictionary key. Any path element
that starts with ``'['`` but is not exactly ``'['`` is reserved for future list
syntax and is illegal in declarative path rules.
"""
