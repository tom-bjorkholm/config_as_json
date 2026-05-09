#! /usr/local/bin/python3
"""Test Config initialization edge cases in a small separate module."""

# Copyright (c) 2024-2026 Tom Björkholm
# MIT License

import sys
import pytest
from .test_config import ConfigSomething


def test_init_rejects_json_pair(capsys: pytest.CaptureFixture[str]) -> None:
    """Test ConfigSomething init when both JSON sources are supplied."""
    with pytest.raises(ValueError) as exc:
        _ = ConfigSomething(from_json_text='{}',
                            from_json_filename='unused.cfg',
                            stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert 'Either JSON text or JSON file can be provided' in str(exc.value)
    assert out == ''
    assert err == ''
