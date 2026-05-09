#! /usr/local/bin/python3
"""Test assert_dict_equal."""

# Copyright (c) 2024-2026 Tom Björkholm
# MIT License

import sys
from typing import Mapping
import pytest
from pytest import CaptureFixture
from config_as_json.assert_dict_equal import _print_dict_differs, \
    assert_dict_equal


def test_print_dict_differs(capsys: CaptureFixture[str]) -> None:
    """Test simple case of _print_dict_differs."""
    lhs = {'a': 'b', 'c': 2}
    rhs = {'d': 'e', 'f': 4, 'g': 5}
    msg = 'A small test message'
    # pylint: disable-next=protected-access
    _print_dict_differs(msg=msg, lhs=lhs, rhs=rhs, stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert '' == out
    assert msg in err
    assert 'Number of keys in left dict: 2' in err
    assert 'Number of keys in right dict: 3' in err
    assert " left dict: {'a': 'b', 'c': 2}" in err
    assert "right dict: {'d': 'e', 'f': 4, 'g': 5}" in err


@pytest.mark.parametrize('lhs,rhs,ign',
                         [({'a': 2, 'b': 'c'}, {'a': 2, 'b': 'c'}, []),
                          ({'a': 2, 'b': 'c'}, {'a': 2, 'b': 'c'},
                           ['d', 'e']),
                          ({'a': 2, 'b': 'c', 'd': 4, 'e': 'bad'},
                           {'a': 2, 'b': 'c', 'd': 7, 'e': 'good'},
                           ['d', 'e']),
                          ({'a': 2, 'b': 'c'}, {'a': 2, 'b': 'e'},
                           ['d', 'b'])])
def test_assert_dict_equal_ok1(capsys: CaptureFixture[str],
                               lhs: Mapping[str, object],
                               rhs: Mapping[str, object],
                               ign: list[str]) -> None:
    """Test OK cases for assert_dict_equal."""
    assert_dict_equal(lhs, rhs, ign, stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert '' == out
    assert '' == err


@pytest.mark.parametrize('lhs,rhs,ign,msgs',
                         [({'a': 'b', 'c': 'd'},
                           {'a': 'g'}, ['k', 'l'],
                           ['Different number of keys in dicts',
                            'in left dict: 2',
                            'in right dict: 1']),
                          ({'a': 'b', 'c': 'd'},
                           {'a': 'b', 'e': 'k'}, ['y', 'z'],
                           ['Key "c" exist only in left dict']),
                          ({'a': 'b', 'c': 'd'},
                           {'a': 'x', 'c': 'k'}, ['y', 'z'],
                           ['Key "a" has different values in left and right',
                            ' left[a] = b', 'right[a] = x'])])
def test_assert_dict_equal_nok1(capsys: CaptureFixture[str],
                                lhs: Mapping[str, object],
                                rhs: Mapping[str, object], ign: list[str],
                                msgs: list[str]) -> None:
    """Test not OK cases for assert_dict_equal."""
    with pytest.raises(AssertionError):
        assert_dict_equal(lhs, rhs, ign, stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert '' == out
    for msg in msgs:
        assert msg in err
