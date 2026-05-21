#! /usr/local/bin/python3
"""Sketch the public write-side JSON conversion hook API.

This module records the proposed public names, type signatures and docstrings
for write-side conversion hooks. It intentionally contains no conversion
logic yet. The implementation can move these declarations or extend them
after the API sketch has been reviewed.
"""

# Copyright (c) 2026 Tom Björkholm
# MIT License

from typing import Callable, NamedTuple, Optional, Protocol, Sequence, TextIO
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

Applications must not return both a recursive key selector and a path selector
that ends with the same dictionary key. For example, returning both
``'format'`` and ``('outputs', '[', 'format')`` is a selector conflict even if
the current configuration data does not contain that path. The implementation
should detect such conflicts when it checks ``serialize_converters()`` and
raise ``SerializeSelectorError``. A path ending in ``'['`` targets list
elements, not a dictionary key, so it does not conflict with a recursive key
selector.

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

    If ``value_type`` is not ``None``, every matched non-``None`` value must
    be an instance of that type before ``func`` is called. If the value has
    another type, serialization should raise a path-aware
    ``JsonWriteHookError``. This rule applies to both absolute path selectors
    and recursive key-name selectors.

    If ``value_type`` is ``None``, no pre-conversion type check is performed
    and the conversion function is responsible for accepting the matched
    value.

    The conversion function is called with the value, the current path text,
    the current ``stderr_file``, and the keyword arguments from ``args``. The
    path text is a string intended for diagnostics, in the same style as
    member names passed to member validators. Converter functions should not
    parse the path text as a selector.

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


class SerializeSelectorError(ValueError):
    """Raised when write-side conversion selectors are not valid together.

    This exception reports programming errors in ``serialize_converters()``
    declarations, such as invalid selector types, invalid ``ConfigPath``
    syntax, or a recursive key selector that conflicts with a path selector
    ending in the same dictionary key. It also reports selectors that would
    cross child-owned nested ``Config`` ownership boundaries.
    """


type SerializeConverters = dict[SerializeSelector, SerializeConverter]
"""Write-side conversion rules for rich Python values before JSON write."""


# pylint: disable-next=too-few-public-methods
class JsonWriteHookProvider(Protocol):
    """Describe the write-side hook that ``Config`` classes may provide."""

    def serialize_converters(self) -> SerializeConverters:
        """Return conversion rules for rich Python values before JSON write.

        The returned dictionary maps selectors to converters. A selector may
        be either a recursive key-name string or an absolute ``ConfigPath``.
        Path selectors use the same rules as ROCF paths.

        The returned selectors are checked before conversion starts. Returning
        both a recursive key selector and a path selector ending with the same
        dictionary key is a declaration error, even if that path is absent
        from the current configuration data. Such conflicts should raise
        ``SerializeSelectorError``.

        Converters apply only to data owned by this object. If a member is a
        declared nested ``Config`` object, that object serializes itself and
        applies its own converters.

        For ``DICT_VALUE_BY_KEY`` nested declarations, declared nested values
        remain child-owned and use only their own converters. Undeclared plain
        values inside the same dictionary remain parent-owned and may use this
        object's converters.

        A parent converter must not target child-owned data. When the current
        object has declared nested ``Config`` values, the write path supplies
        those owned subtrees to ``apply_serialize_converters()`` as
        ``child_owned_paths``. Selectors that would convert those child-owned
        subtrees, their descendants, or an ancestor container containing them
        should raise ``SerializeSelectorError``.

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


def apply_serialize_converters(data: dict[str, object],
                               converters: SerializeConverters,
                               stderr_file: TextIO,
                               child_owned_paths: Sequence[ConfigPath] = ()) \
                                   -> dict[str, JsonType]:
    """Return JSON-compatible data after write-side conversions.

    ``Config.as_json_string()`` should call this function after validation and
    after nested ``Config`` members have been converted to their own JSON data,
    but before calling ``json.dumps()``. The function owns selector checking,
    converter dispatch, built-in fallback conversions such as enum-name
    serialization, and recursive JSON-compatibility checks.

    ``child_owned_paths`` describes nested ``Config`` subtrees that are present
    in ``data`` only because the child object already serialized itself. This
    function must not traverse or convert those subtrees while applying the
    current object's converters.

    Args:
        data: Root data dictionary owned by the current ``Config`` object.
        converters: Explicit converters returned by
            ``Config.serialize_converters()``.
        stderr_file: Stream passed through to converter functions.
        child_owned_paths: Paths to nested ``Config`` subtrees owned by child
            objects. Selectors that would convert those subtrees, their
            descendants, or an ancestor container containing them are invalid.

    Returns:
        A JSON-compatible dictionary ready to pass to ``json.dumps()``.

    Raises:
        SerializeSelectorError: The selector declarations are invalid or
            ambiguous, or a selector crosses a child-owned path boundary.
        JsonWriteHookError: A matched value has the wrong type, a converter
            raises an error that should be wrapped with path context, or a
            conversion result is not JSON-compatible.
    """
    raise NotImplementedError('Sketch only.')
