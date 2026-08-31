#! /usr/local/bin/python3
"""Test the reported path of every node and every leaf of a deep tree.

The tree in :mod:`member_path_deep_tree` holds every nesting kind inside
every other nesting kind, and records the path handed to every Config object
and to every plain member. Each traversal is compared with the whole list of
paths that the tree must report, so a path that is wrong, missing, or
reported where none was expected is caught even though nothing fails
validation.
"""

# Copyright (c) 2026 Tom Björkholm
# MIT License

from collections.abc import Sequence
from io import StringIO
from pathlib import Path
from typing import Optional
import pytest
from pytest import CaptureFixture
from .check_capsys import check_capsys
from .member_path_deep_tree import CONFIG_PATHS, MEMBER_PATHS, RECORDER, \
    RecTop, tree_text

TOP_TEXT = '<top level>'
"""Text standing for the path of the object a traversal was started on."""

PREFIXES: list[Optional[str]] = [None, 'root[2]']
"""The paths that a traversal is started on in the tests below."""


def _below(paths: Sequence[Optional[str]], prefix: Optional[str]) \
        -> list[str]:
    """Return the expected paths as text, below the given start path."""
    if prefix is None:
        return [TOP_TEXT if path is None else path for path in paths]
    return [prefix if path is None else f'{prefix}.{path}' for path in paths]


def _recorded_configs() -> list[str]:
    """Return the recorded Config object paths as text."""
    return [TOP_TEXT if path is None else path for path in RECORDER.configs]


def _assert_all_paths(prefix: Optional[str]) -> None:
    """Assert that every path was recorded exactly once."""
    assert sorted(_recorded_configs()) == sorted(_below(CONFIG_PATHS, prefix))
    assert sorted(RECORDER.members) == sorted(_below(MEMBER_PATHS, prefix))


def _assert_path_set(prefix: Optional[str]) -> None:
    """Assert that exactly the expected paths were recorded.

    A traversal that builds or serializes nested objects validates each of
    them as it goes, and validates them again when the object holding them
    is validated. The paths are therefore recorded more than once, and only
    the set of them is the interesting result.
    """
    assert set(_recorded_configs()) == set(_below(CONFIG_PATHS, prefix))
    assert set(RECORDER.members) == set(_below(MEMBER_PATHS, prefix))


@pytest.mark.parametrize('prefix', PREFIXES)
def test_validate_sweep(prefix: Optional[str],
                        capsys: CaptureFixture[str]) -> None:
    """Test that validating names every node and leaf exactly once."""
    top = RecTop()
    stderr_file = StringIO()
    RECORDER.clear()
    top.validate(stderr_file=stderr_file, member_name=prefix)
    _assert_all_paths(prefix)
    assert stderr_file.getvalue() == ''
    check_capsys(capsys)


@pytest.mark.parametrize('prefix', PREFIXES)
def test_parse_sweep(prefix: Optional[str],
                     capsys: CaptureFixture[str]) -> None:
    """Test that parsing names every node and leaf of the parsed tree."""
    stderr_file = StringIO()
    RECORDER.clear()
    _ = RecTop(from_json_data_text=tree_text(), stderr_file=stderr_file,
               member_name=prefix)
    _assert_path_set(prefix)
    assert stderr_file.getvalue() == ''
    check_capsys(capsys)


@pytest.mark.parametrize('prefix', PREFIXES)
def test_read_sweep(prefix: Optional[str], tmp_path: Path,
                    capsys: CaptureFixture[str]) -> None:
    """Test that reading a file names every node and leaf that was read."""
    json_file = tmp_path / 'tree.json'
    json_file.write_text(tree_text(), encoding='utf-8')
    stderr_file = StringIO()
    RECORDER.clear()
    _ = RecTop(from_json_filename=json_file, stderr_file=stderr_file,
               member_name=prefix)
    _assert_path_set(prefix)
    assert stderr_file.getvalue() == ''
    check_capsys(capsys)


@pytest.mark.parametrize('prefix', PREFIXES)
def test_json_string_sweep(prefix: Optional[str],
                           capsys: CaptureFixture[str]) -> None:
    """Test that serializing names every node and leaf it serializes."""
    top = RecTop()
    stderr_file = StringIO()
    RECORDER.clear()
    _ = top.as_json_string(stderr_file=stderr_file, member_name=prefix)
    _assert_path_set(prefix)
    assert stderr_file.getvalue() == ''
    check_capsys(capsys)


def test_write_sweep(tmp_path: Path, capsys: CaptureFixture[str]) -> None:
    """Test that writing a file names every node and leaf it writes.

    A file is always written for a whole configuration, so the paths of a
    write start at the object that is written.
    """
    top = RecTop()
    stderr_file = StringIO()
    RECORDER.clear()
    top.write(to_json_filename=tmp_path / 'out.json', stderr_file=stderr_file)
    _assert_path_set(None)
    assert stderr_file.getvalue() == ''
    check_capsys(capsys)


def test_absent_optional(capsys: CaptureFixture[str]) -> None:
    """Test that an absent optional member contributes no path at all."""
    top = RecTop()
    top.spare = None
    stderr_file = StringIO()
    RECORDER.clear()
    top.validate(stderr_file=stderr_file, member_name=None)
    absent = [path for path in _recorded_configs()
              if path.startswith('spare')]
    assert absent == []
    assert 'leaf' in _recorded_configs()
    assert stderr_file.getvalue() == ''
    check_capsys(capsys)
