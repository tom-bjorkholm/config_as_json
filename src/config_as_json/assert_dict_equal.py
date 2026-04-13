#! /usr/local/bin/python3
"""Check and assert that dicts are equal ignoring some keys."""

# Copyright (c) 2024-2026 Tom Björkholm
# MIT License

from typing import Mapping, Any
from copy import deepcopy
import sys


def _print_dict_differs(msg: str, lhs: Mapping[str, Any],
                        rhs: Mapping[str, Any]) -> None:
    """Print message and dicts."""
    print(f'{msg}\n' +
          f'Number of keys in left dict: {len(lhs)}\n' +
          f'Number of keys in right dict: {len(rhs)}\n' +
          f' left dict: {str(lhs)}\nright dict: {str(rhs)}',
          file=sys.stderr)


def assert_dict_equal(lhs: Mapping[str, Any], rhs: Mapping[str, Any],
                      ignorekeys: list[str]) -> None:
    """Check and assert that dicts are equal ignoring some keys.

    Try to print differences to stderr.
    @param lhs  Left hand side dict.
    @param rhs  Right hand side dict.
    @param ignorekeys  Keys to ignore when comparing.
    """
    lhs_val = deepcopy(lhs)
    rhs_val = deepcopy(rhs)
    assert isinstance(lhs_val, dict)
    assert isinstance(rhs_val, dict)
    for key in ignorekeys:
        if key in lhs_val:
            del lhs_val[key]
        if key in rhs_val:
            del rhs_val[key]
    if len(lhs_val) != len(rhs_val):
        _print_dict_differs('Different number of keys in dicts',
                            lhs_val, rhs_val)
    assert len(lhs_val) == len(rhs_val)
    for key in lhs_val.keys():
        if key not in rhs:
            _print_dict_differs(f'Key "{key}" exist only in left dict.',
                                lhs_val, rhs_val)
            assert key in rhs
        if lhs_val[key] != rhs_val[key]:
            txt = f'Key "{key}" has different values in left and right\n'
            txt += f' left[{key}] = {lhs_val[key]}\n'
            txt += f'right[{key}] = {rhs_val[key]}\n'
            _print_dict_differs(txt, lhs_val, rhs_val)
        assert lhs_val[key] == rhs_val[key]
    if lhs_val != rhs_val:  # pragma: no cover
        _print_dict_differs('Dicts differs', lhs_val, rhs_val)
    assert lhs_val == rhs_val
