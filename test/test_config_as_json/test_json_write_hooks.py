#! /usr/local/bin/python3
"""Test write-side JSON conversion hooks.

These tests exercise the public helper :func:`apply_serialize_converters`
directly. Integration with :class:`Config` is exercised in
``test_config_serialize_converters.py``.
"""

# Copyright (c) 2026 Tom Björkholm
# MIT License

import sys
from copy import deepcopy
from enum import Enum
from io import StringIO
from pathlib import Path
from typing import TextIO, cast
import pytest
from config_as_json.commontypes import ConfigPath, JsonType
from config_as_json.json_write_hooks import (
    JsonWriteHookError, SerializeConverter, SerializeConverters,
    SerializeSelectorError, apply_serialize_converters)
from .write_hook_test_helpers import Priority, Severity, to_enum_value


# ----------------------------------------------------------------------
# Test helpers
# ----------------------------------------------------------------------


def to_iso(value: object, *, path_text: str, stderr_file: TextIO,
           **_extra: object) -> JsonType:
    """Test converter that turns a ``Path`` into its POSIX string form."""
    _ = path_text, stderr_file
    assert isinstance(value, Path)
    return value.as_posix()


def add_prefix(value: object, *, path_text: str, stderr_file: TextIO,
               prefix: str) -> JsonType:
    """Prefix a string value to test that ``args`` is forwarded."""
    _ = path_text, stderr_file
    assert isinstance(value, str)
    return f'{prefix}{value}'


def explode(value: object, *, path_text: str, stderr_file: TextIO,
            **_extra: object) -> JsonType:
    """Raise a non-hook exception to test conversion error wrapping."""
    _ = value, path_text, stderr_file
    raise RuntimeError('boom')


def explode_hook(value: object, *, path_text: str, stderr_file: TextIO,
                 **_extra: object) -> JsonType:
    """Raise a path-aware ``JsonWriteHookError`` directly."""
    _ = value, stderr_file
    raise JsonWriteHookError(f'custom failure at {path_text}')


def return_path(value: object, *, path_text: str, stderr_file: TextIO,
                **_extra: object) -> JsonType:
    """Return the converter's ``path_text`` for diagnostic inspection."""
    _ = value, stderr_file
    return path_text


# Container for the result of running ``apply_serialize_converters`` in tests.
ERR = StringIO()


def run(data: dict[str, object], converters: object,
        child_owned: tuple[ConfigPath, ...] = ()) -> dict[str, JsonType]:
    """Wrap :func:`apply_serialize_converters` with a fresh error stream.

    The ``converters`` parameter is intentionally typed as ``object`` so
    every test can pass dict literals with concrete key types (``str``,
    a specific ``tuple`` shape, or even an invalid shape used to test
    error handling) without fighting Python's invariant dict generic.
    The wrapper casts the value to :class:`SerializeConverters`; the
    real shape is validated at runtime by
    :func:`apply_serialize_converters`.
    """
    return apply_serialize_converters(
        data=data, converters=cast(SerializeConverters, converters),
        stderr_file=ERR, child_owned_paths=child_owned)


# ----------------------------------------------------------------------
# Built-in fallback behavior
# ----------------------------------------------------------------------


def test_no_converters_passthrough() -> None:
    """Plain JSON data with no converters is returned unchanged."""
    data: dict[str, object] = {
        'name': 'alpha', 'count': 3, 'rate': 1.5,
        'flag': True, 'maybe': None, 'tags': ['a', 'b'],
        'nested': {'k': 'v'}}
    out = run(data, {})
    assert out == data


def test_input_not_mutated() -> None:
    """``apply_serialize_converters`` never mutates the input tree."""
    data: dict[str, object] = {'items': [{'level': Severity.HIGH}]}
    snapshot = deepcopy(data)
    _ = run(data, {})
    assert data == snapshot


@pytest.mark.parametrize(
    'enum_value, expected',
    [(Severity.LOW, 'LOW'), (Severity.HIGH, 'HIGH'),
     (Priority.LOW, 'LOW'), (Priority.MEDIUM, 'MEDIUM')])
def test_enum_fallback_name(enum_value: Enum, expected: str) -> None:
    """Built-in fallback turns Enum/IntEnum members into their .name."""
    out = run({'level': enum_value}, {})
    assert out == {'level': expected}


def test_enum_in_containers() -> None:
    """Built-in fallback recurses into nested containers."""
    data: dict[str, object] = {
        'levels': [Severity.LOW, Priority.HIGH],
        'pairs': {'a': Severity.HIGH, 'b': Priority.LOW}}
    out = run(data, {})
    assert out == {
        'levels': ['LOW', 'HIGH'],
        'pairs': {'a': 'HIGH', 'b': 'LOW'}}


def test_none_passes_through() -> None:
    """``None`` is never sent to a converter; it passes through unchanged."""
    converters = {'value': SerializeConverter(
        value_type=Path, func=to_iso, args={})}
    out = run({'value': None}, converters)
    assert out == {'value': None}


# ----------------------------------------------------------------------
# Recursive-key selectors
# ----------------------------------------------------------------------


def test_rec_key_at_any_depth() -> None:
    """A plain string selector matches every dict member with that name."""
    converters = {'level': SerializeConverter(
        value_type=Enum, func=to_enum_value, args={})}
    data: dict[str, object] = {
        'level': Severity.LOW,
        'group': {'level': Severity.HIGH, 'other': 1},
        'items': [{'level': Priority.MEDIUM}, {'level': None}]}
    out = run(data, converters)
    assert out == {
        'level': 'low',
        'group': {'level': 'high', 'other': 1},
        'items': [{'level': 2}, {'level': None}]}


def test_rec_key_overrides_fallback() -> None:
    """An explicit converter for a key wins over the Enum fallback."""
    converters = {'level': SerializeConverter(
        value_type=Enum, func=to_enum_value, args={})}
    out = run({'level': Severity.LOW, 'other': Severity.HIGH}, converters)
    assert out == {'level': 'low', 'other': 'HIGH'}


# ----------------------------------------------------------------------
# Path selectors
# ----------------------------------------------------------------------


def test_path_exact_position() -> None:
    """A ConfigPath selector only matches its exact path."""
    converters = {('outputs', '[', 'format'): SerializeConverter(
        value_type=Enum, func=to_enum_value, args={})}
    data: dict[str, object] = {
        'outputs': [{'format': Severity.HIGH, 'note': Severity.LOW}],
        'format': Severity.HIGH}
    out = run(data, converters)
    assert out == {
        'outputs': [{'format': 'high', 'note': 'LOW'}],
        'format': 'HIGH'}


def test_path_list_iteration() -> None:
    """A path ending in ``'['`` applies the converter to each list element."""
    converters = {('matrix', '['): SerializeConverter(
        value_type=str, func=add_prefix, args={'prefix': 'X-'})}
    out = run({'matrix': ['a', 'b', 'c']}, converters)
    assert out == {'matrix': ['X-a', 'X-b', 'X-c']}


def test_path_misses_key() -> None:
    """A path selector that cannot reach the key is a no-op."""
    converters = {('outputs', '[', 'format'): SerializeConverter(
        value_type=Enum, func=to_enum_value, args={})}
    out = run({'outputs': [{}, {}]}, converters)
    assert out == {'outputs': [{}, {}]}


def test_path_text_brackets() -> None:
    """Diagnostics use bracket notation for list indexes and dict keys."""
    converters = {('outputs', '[', 'format'): SerializeConverter(
        value_type=Enum, func=return_path, args={})}
    out = run({'outputs': [{'format': Severity.LOW},
                           {'format': Severity.HIGH}]}, converters)
    assert out == {'outputs': [{'format': 'outputs[0][format]'},
                               {'format': 'outputs[1][format]'}]}


# ----------------------------------------------------------------------
# value_type pre-check, converter errors, JSON-compatibility check
# ----------------------------------------------------------------------


def test_value_type_mismatch() -> None:
    """``value_type`` is checked before the converter is invoked."""
    converters = {'level': SerializeConverter(
        value_type=Enum, func=to_enum_value, args={})}
    with pytest.raises(JsonWriteHookError, match='expected Enum'):
        _ = run({'level': 'not-an-enum'}, converters)


def test_value_type_none_skips() -> None:
    """When ``value_type`` is ``None`` the converter accepts any value."""
    def echo(value: object, *, path_text: str, stderr_file: TextIO,
             **_extra: object) -> JsonType:
        _ = path_text, stderr_file
        if isinstance(value, str):
            return f'str:{value}'
        if isinstance(value, int):
            return f'int:{value}'
        return None
    converters = {'pick': SerializeConverter(
        value_type=None, func=echo, args={})}
    assert run({'pick': 'x'}, converters) == {'pick': 'str:x'}
    assert run({'pick': 7}, converters) == {'pick': 'int:7'}


def test_runtime_error_wrapped() -> None:
    """Non-hook converter exceptions are wrapped with path/selector info."""
    converters = {'level': SerializeConverter(
        value_type=Enum, func=explode, args={})}
    with pytest.raises(JsonWriteHookError,
                       match="Converter for 'level' at .*RuntimeError"):
        _ = run({'level': Severity.LOW}, converters)


def test_hook_error_propagates() -> None:
    """``JsonWriteHookError`` raised inside a converter propagates as-is."""
    converters = {'level': SerializeConverter(
        value_type=Enum, func=explode_hook, args={})}
    with pytest.raises(JsonWriteHookError, match='custom failure at level'):
        _ = run({'level': Severity.LOW}, converters)


def test_non_json_output() -> None:
    """A converter output that is not JSON-compatible is rejected."""
    def returns_path(value: object, *, path_text: str, stderr_file: TextIO,
                     **_extra: object) -> JsonType:
        _ = value, path_text, stderr_file
        return Path('/tmp/x')  # type: ignore[return-value]
    converters = {'file': SerializeConverter(
        value_type=str, func=returns_path, args={})}
    with pytest.raises(JsonWriteHookError, match='non-JSON type'):
        _ = run({'file': 'x'}, converters)


def test_non_json_no_converter() -> None:
    """A non-JSON value with no converter is rejected with a clear error."""
    with pytest.raises(JsonWriteHookError, match='non-JSON type'):
        _ = run({'file': Path('/tmp/x')}, {})


# ----------------------------------------------------------------------
# Selector validation
# ----------------------------------------------------------------------


@pytest.mark.parametrize('selector', ['', '[', ('value', '[bad'), (), (5,), 7])
def test_invalid_selector_shape(selector: object) -> None:
    """Bad selector shapes are reported before any conversion runs."""
    converters = {selector: SerializeConverter(
        value_type=str, func=add_prefix, args={'prefix': '-'})}
    with pytest.raises(SerializeSelectorError):
        _ = run({'value': 'x'}, converters)


def test_value_must_be_converter() -> None:
    """A non-:class:`SerializeConverter` mapping value is rejected."""
    bad = {'value': object()}
    with pytest.raises(SerializeSelectorError, match='SerializeConverter'):
        _ = run({'value': 'x'}, bad)


def test_rec_vs_path_end_conflict() -> None:
    """A rec-key and a path ending in the same key is a declaration error."""
    converters = {
        'format': SerializeConverter(value_type=str, func=add_prefix,
                                     args={'prefix': '-'}),
        ('outputs', '[', 'format'): SerializeConverter(
            value_type=str, func=add_prefix, args={'prefix': '-'})}
    with pytest.raises(SerializeSelectorError, match='ends in key'):
        _ = run({'outputs': [{'format': 'csv'}]}, converters)


def test_rec_vs_path_through() -> None:
    """A rec-key and a path passing through that key also conflict."""
    converters = {
        'outputs': SerializeConverter(value_type=list, func=lambda v, **_kw: v,
                                      args={}),
        ('outputs', '[', 'name'): SerializeConverter(
            value_type=str, func=add_prefix, args={'prefix': '-'})}
    with pytest.raises(SerializeSelectorError, match='passes through key'):
        _ = run({'outputs': [{'name': 'a'}]}, converters)


def test_path_wrong_list_vs_dict() -> None:
    """A path expecting a list but finding a dict in data raises."""
    converters = {('items', '[', 'name'): SerializeConverter(
        value_type=str, func=add_prefix, args={'prefix': '-'})}
    data: dict[str, object] = {'items': {'name': 'wrong'}}
    with pytest.raises(SerializeSelectorError, match='expects a list'):
        _ = run(data, converters)


def test_path_wrong_dict_vs_list() -> None:
    """A path expecting a dict key but finding a list in data raises."""
    converters = {('items', 'name'): SerializeConverter(
        value_type=str, func=add_prefix, args={'prefix': '-'})}
    data: dict[str, object] = {'items': [{'name': 'a'}]}
    with pytest.raises(SerializeSelectorError, match='expects a dict'):
        _ = run(data, converters)


def test_path_wrong_scalar() -> None:
    """A path that expects a container but finds a scalar raises."""
    converters = {('items', 'name'): SerializeConverter(
        value_type=str, func=add_prefix, args={'prefix': '-'})}
    data: dict[str, object] = {'items': 'scalar'}
    with pytest.raises(SerializeSelectorError, match='expects a container'):
        _ = run(data, converters)


# ----------------------------------------------------------------------
# Child-owned subtree boundaries
# ----------------------------------------------------------------------


def test_path_into_child_rejected() -> None:
    """A converter declared into a child-owned subtree is rejected."""
    converters = {('child', 'inner'): SerializeConverter(
        value_type=str, func=add_prefix, args={'prefix': '-'})}
    with pytest.raises(SerializeSelectorError, match='child-owned'):
        _ = run({'child': {'inner': 'x'}}, converters,
                child_owned=(('child',),))


def test_path_ancestor_rejected() -> None:
    """A path that contains a child-owned subtree is rejected."""
    converters = {('parent',): SerializeConverter(
        value_type=dict, func=lambda v, **_kw: v, args={})}
    with pytest.raises(SerializeSelectorError, match='ancestor'):
        _ = run({'parent': {'child': {'inner': 'x'}}}, converters,
                child_owned=(('parent', 'child'),))


def test_rec_key_skips_child() -> None:
    """Recursive key walk does not descend into child-owned subtrees."""
    converters = {'level': SerializeConverter(
        value_type=Enum, func=to_enum_value, args={})}
    data: dict[str, object] = {
        'level': Severity.LOW,
        'child': {'level': 'already-converted-by-child'}}
    out = run(data, converters, child_owned=(('child',),))
    assert out == {'level': 'low',
                   'child': {'level': 'already-converted-by-child'}}


def test_child_list_wildcard() -> None:
    """``'['`` in child_owned_paths matches each list element."""
    converters = {'level': SerializeConverter(
        value_type=Enum, func=to_enum_value, args={})}
    data: dict[str, object] = {
        'level': Severity.LOW,
        'items': [{'level': 'already-1'}, {'level': 'already-2'}]}
    out = run(data, converters, child_owned=(('items', '['),))
    assert out == {'level': 'low',
                   'items': [{'level': 'already-1'},
                             {'level': 'already-2'}]}


def test_child_dict_wildcard() -> None:
    """``'['`` in child_owned_paths also matches each dict value (DICT_VALUE).

    The conversion walk first encounters a dict (the ``children`` member),
    iterates its values, and the literal ``'['`` in the child-owned path
    matches each of those dict values without descending into them.
    """
    converters = {'level': SerializeConverter(
        value_type=Enum, func=to_enum_value, args={})}
    data: dict[str, object] = {
        'level': Severity.LOW,
        'children': {'a': {'level': 'already-a'},
                     'b': {'level': 'already-b'}}}
    out = run(data, converters, child_owned=(('children', '['),))
    assert out == {'level': 'low',
                   'children': {'a': {'level': 'already-a'},
                                'b': {'level': 'already-b'}}}


# ----------------------------------------------------------------------
# Dict key restrictions
# ----------------------------------------------------------------------


def test_dict_key_bracket_start() -> None:
    """Dict keys starting with ``'['`` are not allowed in JSON data."""
    data: dict[str, object] = {'[weird': 1}
    with pytest.raises(JsonWriteHookError, match="must not start with '\\['"):
        _ = run(data, {})


def test_dict_key_literal_bracket() -> None:
    """A literal ``'['`` dict key is not allowed in JSON data."""
    data: dict[str, object] = {'[': 1}
    with pytest.raises(JsonWriteHookError, match="must not start with '\\['"):
        _ = run(data, {})


# ----------------------------------------------------------------------
# args passing and signature contract
# ----------------------------------------------------------------------


def test_args_forwarded() -> None:
    """``args`` is forwarded to the converter as keyword arguments."""
    converters = {'name': SerializeConverter(
        value_type=str, func=add_prefix, args={'prefix': 'U-'})}
    assert run({'name': 'alice'}, converters) == {'name': 'U-alice'}


def test_root_must_be_dict() -> None:
    """The top-level ``data`` argument must be a dict."""
    with pytest.raises(JsonWriteHookError, match='Root data must be a dict'):
        _ = apply_serialize_converters(data=[],  # type: ignore[arg-type]
                                       converters={}, stderr_file=sys.stderr)


def test_converters_must_be_dict() -> None:
    """The ``converters`` argument must be a dict."""
    with pytest.raises(SerializeSelectorError, match='must return a dict'):
        _ = apply_serialize_converters(
            data={}, converters=[],  # type: ignore[arg-type]
            stderr_file=sys.stderr)
