#! /usr/local/bin/python3
# mypy: disable-error-code="no-untyped-def,no-untyped-call"
"""Test Config initialization edge cases in a small separate module."""

# Copyright (c) 2024-2026 Tom Björkholm
# MIT License

import sys
import pytest
from .test_config import ConfigSomething


def test_config_something_init_rejects_both_json_sources(capsys):
    """Test ConfigSomething init when both JSON sources are supplied."""
    with pytest.raises(ValueError) as exc:
        _ = ConfigSomething(from_json_text='{}',
                            from_json_filename='unused.cfg',
                            stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert 'Either JSON text or JSON file can be provided' in str(exc.value)
    assert out == ''
    assert err == ''
