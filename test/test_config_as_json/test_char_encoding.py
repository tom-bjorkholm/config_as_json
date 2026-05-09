#! /usr/local/bin/python3
# mypy: disable-error-code="no-untyped-def,no-untyped-call"
"""Test character encoding helpers and validators."""

# Copyright (c) 2026 Tom Björkholm
# MIT License

import sys
from typing import cast
import pytest
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
def test_valid_char_encoding_returns_lookup_result(capsys, enc, is_ok):
    """Test direct character encoding lookup results."""
    ret = valid_char_encoding(enc)
    out, err = capsys.readouterr()
    assert ret == is_ok
    assert out == ''
    assert err == ''


@pytest.mark.parametrize('enc', [8, True])
def test_valid_char_encoding_rejects_non_string_values(capsys, enc):
    """Test direct character encoding lookup with wrong value types."""
    with pytest.raises(TypeError) as exc_info:
        _ = valid_char_encoding(enc)
    out, err = capsys.readouterr()
    assert out == ''
    assert err == ''
    assert 'must be str' in str(exc_info.value)


@pytest.mark.parametrize('enc', ['utf-8', 'iso8859-1'])
def test_check_char_encoding_accepts_known_encodings(capsys, enc):
    """Test check_char_encoding accepts recognized encodings."""
    check_char_encoding(enc, stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert out == ''
    assert err == ''


@pytest.mark.parametrize('enc', ['utf-88', 'abc123'])
def test_check_char_encoding_exits_for_unknown_encodings(capsys, enc):
    """Test direct check_char_encoding failure behavior."""
    with pytest.raises(SystemExit):
        check_char_encoding(enc, stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert out == ''
    assert f'{enc} is not a recognized encoding' in err


@pytest.mark.parametrize('enc', ['utf-8', 'iso8859-1'])
def test_char_encoding_validator_accepts_known_encodings(capsys, enc):
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
def test_char_encoding_validator_rejects_invalid_members(
        capsys, member_value, error_text):
    """Test CharEncodingValidator raises InvalidConfiguration."""
    with pytest.raises(InvalidConfiguration) as exc_info:
        _ = _validate_char_encoding(member_value)
    assert error_text in str(exc_info.value)
    out, err = capsys.readouterr()
    assert out == ''
    assert 'Invalid configuration: ' + error_text in err
