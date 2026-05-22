#! /usr/local/bin/python3
"""Shared fixtures used by the write-side conversion hook tests.

Extracted to keep ``test_json_write_hooks.py`` and
``test_config_serialize_converters.py`` from triggering pylint's
``duplicate-code`` rule on the same small sample enum/converter pair.
"""

# Copyright (c) 2026 Tom Björkholm
# MIT License

from enum import Enum, IntEnum
from typing import TextIO
from config_as_json.commontypes import JsonType


class Severity(Enum):
    """Plain Enum used to confirm the built-in enum fallback."""

    LOW = 'low'
    HIGH = 'high'


class Priority(IntEnum):
    """IntEnum that motivates the write-side hook.

    ``json.dumps`` writes :class:`enum.IntEnum` members as integers
    because ``IntEnum`` is a subclass of :class:`int`, so a custom
    encoder never sees them. The write-side hook handles this case by
    running before ``json.dumps``.
    """

    LOW = 1
    MEDIUM = 2
    HIGH = 3


def to_enum_name(value: object, *, path_text: str, stderr_file: TextIO,
                 **_extra: object) -> JsonType:
    """Convert an :class:`enum.Enum` member to its symbolic ``.name``."""
    _ = path_text, stderr_file
    assert isinstance(value, Enum)
    return value.name


def to_enum_value(value: object, *, path_text: str, stderr_file: TextIO,
                  **_extra: object) -> JsonType:
    """Convert an :class:`enum.Enum` member to its associated ``.value``."""
    _ = path_text, stderr_file
    assert isinstance(value, Enum)
    result = value.value
    assert isinstance(result, (str, int, float, bool)) or result is None
    return result
