#! /usr/local/bin/python3
"""Check tested code output to stdour and stderr."""

# Copyright (c) 2024 - 2025 Tom Björkholm
# MIT License

from typing import Optional
import pytest


def _check_out_stream(out_err: str, in_it: Optional[str | list[str]],
                      name: str) -> None:
    """Check that output has expected content."""
    if in_it is None:
        assert '' == out_err, \
            f'Expected {name} to be empty string, not: {out_err}'
    elif isinstance(in_it, list):
        assert len(in_it) > 0, \
            'Expected given list of strings in output, but list empty'
        for item in in_it:
            assert isinstance(item, str), \
                'Expected output list is not list of str'
            assert len(item) > 0, \
                'Expected item in output, but item empty'
            assert item in out_err, \
                f'Expected {item} in {name}, but it is {out_err}'
    else:
        assert isinstance(in_it, str), \
            f'Expecting something that is {type(in_it).__name__} ' + \
            'not str in output.'
        assert in_it in out_err, \
            f'Expected {in_it} in {name}, but it is {out_err}'


def check_capsys(capsys: pytest.CaptureFixture[str],
                 in_out: Optional[str | list[str]] = None,
                 in_err: Optional[str | list[str]] = None) -> None:
    """Check tested code output to on stdour and stderr."""
    out, err = capsys.readouterr()
    _check_out_stream(out_err=out, in_it=in_out, name='stdout')
    _check_out_stream(out_err=err, in_it=in_err, name='stderr')
