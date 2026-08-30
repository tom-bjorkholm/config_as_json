#! /usr/local/bin/python3
"""Test that parsing and writing name a nested value by its whole path."""

# Copyright (c) 2026 Tom Björkholm
# MIT License

import json
from io import StringIO
from pathlib import Path
from typing import Optional
import pytest
from pytest import CaptureFixture
from config_as_json.validator import InvalidConfigurationValue
from .check_capsys import check_capsys
from .member_path_test_configs import Leaf, Top

JsonDict = dict[str, object]


def _leaf_data(kind: str = 'csv', limits: Optional[JsonDict] = None,
               extra_key: Optional[str] = None,
               dropped_key: Optional[str] = None,
               old_kind: bool = False) -> JsonDict:
    """Return JSON data for one Leaf, optionally shaped like a bad file."""
    kind_key = 'old_kind' if old_kind else 'kind'
    data: JsonDict = {kind_key: kind, 'tags': ['plain'],
                      'limits': {'cpu': 1} if limits is None else limits}
    if extra_key is not None:
        data[extra_key] = 1
    if dropped_key is not None:
        del data[dropped_key]
    return data


def _top_text(leaf: object = None, leaves: Optional[list[object]] = None) \
        -> str:
    """Return JSON text for one Top holding the given nested leaf data."""
    section: JsonDict = {
        'leaf': _leaf_data() if leaf is None else leaf,
        'leaves': [_leaf_data()] if leaves is None else leaves,
        'by_name': {'main': _leaf_data()},
        'mixed': {'picked': _leaf_data(), 'plain_value': 3}}
    return json.dumps({'section': section})


@pytest.mark.parametrize('leaf_data, error_type, expected', [
    (_leaf_data(kind='nope'), InvalidConfigurationValue,
     'Value nope for section.leaf.kind is not one of'),
    (_leaf_data(extra_key='zzz'), KeyError,
     'Unexpected parameter section.leaf.zzz in JSON data'),
    (_leaf_data(dropped_key='tags'), KeyError,
     'No value for section.leaf.tags in JSON data'),
    (_leaf_data(limits={'cpu': 1, 'gpu': 2}), KeyError,
     'Unexpected parameter section.leaf.limits[gpu] in JSON data'),
    (_leaf_data(limits={}), KeyError,
     'No value for section.leaf.limits[cpu] in JSON data'),
    ('not an object', KeyError,
     'Nested Config member section.leaf must be a JSON object')
])
def test_parse_json_paths(leaf_data: object, error_type: type[Exception],
                          expected: str, capsys: CaptureFixture[str]) -> None:
    """Test that a failure two levels down while parsing names the path."""
    stderr_file = StringIO()
    with pytest.raises(error_type) as exc:
        Top(from_json_data_text=_top_text(leaf=leaf_data),
            stderr_file=stderr_file)
    assert expected in str(exc.value)
    assert expected in stderr_file.getvalue()
    check_capsys(capsys)


def test_parse_list_element_path(capsys: CaptureFixture[str]) -> None:
    """Test that a rejected value in a nested list names its index."""
    stderr_file = StringIO()
    leaves: list[object] = [_leaf_data(), _leaf_data(kind='nope')]
    with pytest.raises(InvalidConfigurationValue) as exc:
        Top(from_json_data_text=_top_text(leaves=leaves),
            stderr_file=stderr_file)
    assert exc.value.member_name == 'section.leaves[1].kind'
    check_capsys(capsys)


def test_read_path(tmp_path: Path, capsys: CaptureFixture[str]) -> None:
    """Test that reading a file names a rejected value by its whole path."""
    json_file = tmp_path / 'config.json'
    json_file.write_text(_top_text(leaf=_leaf_data(kind='nope')),
                         encoding='utf-8')
    stderr_file = StringIO()
    with pytest.raises(InvalidConfigurationValue) as exc:
        Top(from_json_filename=json_file, stderr_file=stderr_file)
    assert exc.value.member_name == 'section.leaf.kind'
    check_capsys(capsys)


def test_as_json_string_path(capsys: CaptureFixture[str]) -> None:
    """Test that serializing names a rejected value by its whole path."""
    top = Top()
    top.section.leaf.kind = 'nope'
    stderr_file = StringIO()
    with pytest.raises(InvalidConfigurationValue) as exc:
        top.as_json_string(stderr_file=stderr_file, member_name=None)
    assert exc.value.member_name == 'section.leaf.kind'
    check_capsys(capsys)


def test_write_path(tmp_path: Path, capsys: CaptureFixture[str]) -> None:
    """Test that writing a file names a rejected value by its whole path."""
    top = Top()
    top.section.by_name['main'].kind = 'nope'
    stderr_file = StringIO()
    with pytest.raises(InvalidConfigurationValue) as exc:
        top.write(to_json_filename=tmp_path / 'out.json',
                  stderr_file=stderr_file)
    assert exc.value.member_name == 'section.by_name[main].kind'
    check_capsys(capsys)


def test_write_wrong_type_path(capsys: CaptureFixture[str]) -> None:
    """Test that a nested member of the wrong type is named while writing."""
    top = Top()
    top.section.leaves = ['not a Leaf']  # type: ignore[list-item]
    stderr_file = StringIO()
    with pytest.raises(TypeError) as exc:
        top.as_json_string(stderr_file=stderr_file, member_name=None)
    assert 'Nested Config member section.leaves[0] must be Leaf' in \
        str(exc.value)
    check_capsys(capsys)


def test_rocf_own_notation(capsys: CaptureFixture[str]) -> None:
    """Test that automatic-change paths stay in their own notation.

    The paths that ``ConfigAutoChangeHook`` records address JSON data, where
    an object with attributes looks like a dictionary. They are composed one
    nesting level at a time and are deliberately not the dotted paths that
    diagnostics report.
    """
    stderr_file = StringIO()
    top = Top(from_json_data_text=_top_text(leaf=_leaf_data(old_kind=True)),
              stderr_file=stderr_file)
    changes = top.auto_change_hook().changes
    assert len(changes) == 1
    assert changes[0].old_path == 'section[leaf][old_kind]'
    assert changes[0].new_path == 'section[leaf][kind]'
    assert stderr_file.getvalue() == ''
    check_capsys(capsys)


def test_parse_plain_names(capsys: CaptureFixture[str]) -> None:
    """Test that a top level parse still reports plain member names."""
    stderr_file = StringIO()
    with pytest.raises(InvalidConfigurationValue) as exc:
        Leaf(from_json_data_text=json.dumps(_leaf_data(kind='nope')),
             stderr_file=stderr_file)
    assert exc.value.member_name == 'kind'
    with pytest.raises(KeyError) as key_exc:
        Leaf(from_json_data_text=json.dumps(_leaf_data(extra_key='zzz')),
             stderr_file=stderr_file)
    assert 'Unexpected parameter zzz in JSON data' in str(key_exc.value)
    check_capsys(capsys)
