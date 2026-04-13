#! /usr/local/bin/python3
"""Compare mapping objects while ignoring selected keys.

This primarily exists as a tool for developers of applications that use
configuration classes derived from ``Config``.
It is also useful in test code that wants a readable failure message
before asserting equality of configuration objects in applications that
use the library.
"""

# Copyright (c) 2024-2026 Tom Björkholm
# MIT License

from typing import Mapping, TextIO
import sys


def _print_dict_differs(msg: str, lhs: Mapping[str, object],
                        rhs: Mapping[str, object],
                        stderr_file: TextIO = sys.stderr) -> None:
    """Print a detailed mismatch report to standard error.

    Args:
        msg: Summary of the mismatch that was detected.
        lhs: Left-hand mapping after any ignored keys were removed.
        rhs: Right-hand mapping after any ignored keys were removed.
        stderr_file: Stream used for diagnostics. Defaults to ``sys.stderr``.
    """
    print(f'{msg}\n' +
          f'Number of keys in left dict: {len(lhs)}\n' +
          f'Number of keys in right dict: {len(rhs)}\n' +
          f' left dict: {str(lhs)}\nright dict: {str(rhs)}',
          file=stderr_file)


def assert_dict_equal(lhs: Mapping[str, object], rhs: Mapping[str, object],
                      ignorekeys: list[str],
                      stderr_file: TextIO = sys.stderr) -> None:
    """Assert that two mappings are equal after ignoring selected keys.

    The function makes defensive copies, removes any keys listed in
    ``ignorekeys`` from both sides, prints a readable difference report when
    a mismatch is detected, and finally raises ``AssertionError`` through the
    normal ``assert`` statements.

    Args:
        lhs: Left-hand mapping to compare.
        rhs: Right-hand mapping to compare.
        ignorekeys: Keys to drop from both mappings before comparison.
        stderr_file: Stream used for diagnostics. Defaults to ``sys.stderr``.

    Raises:
        AssertionError: The mappings do not match after ignored keys have been
                        removed.
    """
    lhs_val = dict(lhs)
    rhs_val = dict(rhs)
    assert isinstance(lhs_val, dict)
    assert isinstance(rhs_val, dict)
    for key in ignorekeys:
        if key in lhs_val:
            del lhs_val[key]
        if key in rhs_val:
            del rhs_val[key]
    if len(lhs_val) != len(rhs_val):
        _print_dict_differs('Different number of keys in dicts',
                            lhs_val, rhs_val, stderr_file)
    assert len(lhs_val) == len(rhs_val)
    for key, value in lhs_val.items():
        if key not in rhs_val:
            _print_dict_differs(f'Key "{key}" exist only in left dict.',
                                lhs_val, rhs_val, stderr_file)
            assert key in rhs_val
        if value != rhs_val[key]:
            txt = f'Key "{key}" has different values in left and right\n'
            txt += f' left[{key}] = {value}\n'
            txt += f'right[{key}] = {rhs_val[key]}\n'
            _print_dict_differs(txt, lhs_val, rhs_val, stderr_file)
        assert value == rhs_val[key]
    if lhs_val != rhs_val:  # pragma: no cover
        _print_dict_differs('Dicts differs', lhs_val, rhs_val, stderr_file)
    assert lhs_val == rhs_val
