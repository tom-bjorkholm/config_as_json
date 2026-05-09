#! /usr/local/bin/python3
"""Test character encoding helpers and validators."""

# Copyright (c) 2026 Tom Björkholm
# MIT License

import sys
from typing import Any, cast
import pytest
from pytest import CaptureFixture
from config_as_json.char_encoding import CharEncodingValidator, \
    check_char_encoding, valid_char_encoding
from config_as_json.config import Config
from config_as_json.validator import InvalidConfiguration


def _validate_char_encoding(member_value: object) -> object:
    """Validate ``member_value`` with ``CharEncodingValidator``."""
    return CharEncodingValidator().validate_member(config=cast(Config,
                                                               object()),
                                                   member_name='encoding',
                                                   member_value=member_value,
                                                   stderr_file=sys.stderr)


@pytest.mark.parametrize('enc, is_ok', [('utf-8', True), ('iso8859-1', True),
                                        ('abc123', False)])
def test_valid_encoding_lookup(capsys: CaptureFixture[str], enc: str,
                               is_ok: bool) -> None:
    """Test direct character encoding lookup results."""
    ret = valid_char_encoding(enc)
    out, err = capsys.readouterr()
    assert ret == is_ok
    assert out == ''
    assert err == ''


@pytest.mark.parametrize('enc', [8, True])
def test_valid_encoding_bad_type(capsys: CaptureFixture[str],
                                 enc: object) -> None:
    """Test direct character encoding lookup with wrong value types."""
    with pytest.raises(TypeError) as exc_info:
        _ = valid_char_encoding(cast(Any, enc))
    out, err = capsys.readouterr()
    assert out == ''
    assert err == ''
    assert 'must be str' in str(exc_info.value)


@pytest.mark.parametrize('enc', ['utf-8', 'iso8859-1'])
def test_check_encoding_known(capsys: CaptureFixture[str], enc: str) -> None:
    """Test check_char_encoding accepts recognized encodings."""
    check_char_encoding(enc, stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert out == ''
    assert err == ''


@pytest.mark.parametrize('enc', ['utf-88', 'abc123'])
def test_check_encoding_unknown(capsys: CaptureFixture[str], enc: str) -> None:
    """Test direct check_char_encoding failure behavior."""
    with pytest.raises(SystemExit):
        check_char_encoding(enc, stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert out == ''
    assert f'{enc} is not a recognized encoding' in err


@pytest.mark.parametrize('enc', ['utf-8', 'iso8859-1'])
def test_validator_accepts_encoding(capsys: CaptureFixture[str],
                                    enc: str) -> None:
    """Test CharEncodingValidator accepts recognized encodings."""
    ret = _validate_char_encoding(enc)
    assert ret == enc
    out, err = capsys.readouterr()
    assert out == ''
    assert err == ''


@pytest.mark.parametrize(
    'member_value, error_text',
    [(8, 'Value for encoding is not a string.'),
     (True, 'Value for encoding is not a string.'),
     ('abc123', 'abc123 is not a recognized character encoding for')])
def test_validator_rejects_encoding(capsys: CaptureFixture[str],
                                    member_value: object,
                                    error_text: str) -> None:
    """Test CharEncodingValidator raises InvalidConfiguration."""
    with pytest.raises(InvalidConfiguration) as exc_info:
        _ = _validate_char_encoding(member_value)
    assert error_text in str(exc_info.value)
    out, err = capsys.readouterr()
    assert out == ''
    assert 'Invalid configuration: ' + error_text in err
