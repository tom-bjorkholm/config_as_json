#! /usr/local/bin/python3
"""Sketch the public write-side JSON conversion hook API.

This module records the proposed public names, type signatures and docstrings
for write-side conversion hooks. It intentionally contains no conversion
logic yet. The implementation can move these declarations or extend them
after the API sketch has been reviewed.
"""

# Copyright (c) 2026 Tom Björkholm
# MIT License

from typing import Callable, NamedTuple, Optional, Protocol
from config_as_json.commontypes import ConfigPath, JsonType
from config_as_json.validator import InvalidConfiguration


type SerializeSelector = str | ConfigPath
"""Select values that should use one write-side converter.

A plain string is a recursive dictionary key selector. For example,
``'format'`` applies to every dictionary member named ``format`` in data owned
by the current ``Config`` object.

A ``ConfigPath`` is an absolute path selector. For example,
``('outputs', '[', 'format')`` applies only to that path. The one-element path
``('format',)`` means the root key ``format``; it is not the same as the plain
string selector ``'format'``.

Declared nested ``Config`` objects form ownership boundaries. Parent
converters do not apply inside nested objects; each nested object uses only
its own write-side converters.
"""


class SerializeConverter(NamedTuple):
    """Describe one write-side conversion from Python data to JSON data.

    A converter is selected by a ``SerializeSelector`` returned from
    ``serialize_converters()``. Explicit converters override built-in
    conversions such as enum-name serialization.

    ``None`` values pass through unchanged. This lets validation and
    omit-when-None handling decide whether ``None`` is allowed or omitted.

    If ``value_type`` is not ``None``, a matched non-``None`` value must be an
    instance of that type before ``func`` is called. If the value has another
    type, serialization should raise a path-aware ``JsonWriteHookError``.

    If ``value_type`` is ``None``, no pre-conversion type check is performed
    and the conversion function is responsible for accepting the matched
    value.

    The conversion result must be recursively JSON-compatible. Valid output is
    ``None``, ``int``, ``str``, ``bool``, a list of valid values, or a
    dictionary with string keys and valid values. Invalid output should raise
    a path-aware ``JsonWriteHookError`` before ``json.dumps()`` is called.

    Attributes:
        value_type: Optional expected Python type before conversion.
        func: Callable that converts a Python value to JSON-compatible data.
        args: Keyword arguments passed to ``func``.
    """

    value_type: Optional[type[object]]
    func: Callable[..., JsonType]
    args: dict[str, object]


class JsonWriteHookError(InvalidConfiguration):
    """Raised when write-side JSON conversion cannot produce valid JSON."""


# pylint: disable-next=too-few-public-methods
class JsonWriteHookProvider(Protocol):
    """Describe the write-side hook that ``Config`` classes may provide."""

    def serialize_converters(self) -> dict[SerializeSelector,
                                           SerializeConverter]:
        """Return conversion rules for rich Python values before JSON write.

        The returned dictionary maps selectors to converters. A selector may
        be either a recursive key-name string or an absolute ``ConfigPath``.
        Path selectors use the same rules as ROCF paths.

        Converters apply only to data owned by this object. If a member is a
        declared nested ``Config`` object, that object serializes itself and
        applies its own converters.

        Explicit converters override built-in fallback conversions. If more
        than one selector matches a value, the most specific path selector
        should win over a recursive key-name selector.

        Derived ``Config`` classes should override this method with
        ``@override`` when they need explicit write-side converters. The base
        ``Config`` implementation should return an empty dictionary.

        Returns:
            Write-side conversion rules. Return an empty dictionary when no
            explicit conversions are needed.
        """
        raise NotImplementedError('Sketch only.')
