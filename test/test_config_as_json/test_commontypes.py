#! /usr/local/bin/python3
"""Test common types."""

# Copyright (c) 2024-2026 Tom Björkholm
# MIT License

# pylint: disable=duplicate-code

from copy import deepcopy
import pytest
from config_as_json.commontypes import num_row_to_str_list, \
    str_list_to_num_row


@pytest.mark.parametrize('ind, outd',
                         [(['a', 'x', 'some text'],
                           ['a', 'x', 'some text']),
                          (['a', 4, 3.14],
                           ['a', '4', '3.14'])])
def test_num_row_to_str_lst_ok(capsys, ind, outd):
    """Test num_row_to_str_list for OK cases."""
    ret = num_row_to_str_list(ind)
    out, err = capsys.readouterr()
    assert outd == ret
    assert '' == out
    assert '' == err


def test_num_row_to_str_lst_nok(capsys):
    """Test num_row_to_str_list for not OK case."""
    ind = ['a', 2, None, 'x']
    with pytest.raises(TypeError) as exc:
        _ = num_row_to_str_list(ind)
    out, err = capsys.readouterr()
    assert 'Found None when expecting str' in str(exc)
    assert '' == out
    assert '' == err


def test_str_list_to_num_row(capsys):
    """Test str_list_to_num_row."""
    data = ['a', 'x', 'some text']
    res = deepcopy(data)
    ret = str_list_to_num_row(data)
    out, err = capsys.readouterr()
    assert res == ret
    assert '' == out
    assert '' == err
