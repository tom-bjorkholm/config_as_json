#! /usr/local/bin/python3
"""Test DictKeyValueTypesValidator."""

# Copyright (c) 2026 Tom Björkholm
# MIT License

import sys
from collections.abc import Hashable
from enum import Enum
from typing import Any, TypeVar, cast
import pytest
from pytest import CaptureFixture
from config_as_json import DictKeyValueTypesValidator as public_validator
from config_as_json.dict_validators import DictForEachValidator, \
    DictKeyValueTypesValidator
from config_as_json.list_validators import ListOrderingValidator, \
    ListValueValidator
from config_as_json.validator import InvalidConfiguration
from .validator_test_helpers import EmptyValidationConfig, \
    SingleMemberValidationConfig, assert_validate_member_failure

KT = TypeVar('KT', bound=Hashable)
VT = TypeVar('VT')


class RuleKey(Enum):
    """Non-string keys used by key/value type tests."""

    ALPHA = 'alpha'
    BETA = 'beta'


def _assert_same_dict(capsys: CaptureFixture[str],
                      validator: DictKeyValueTypesValidator,
                      member_value: dict[KT, VT]) -> None:
    """Assert that validation returns the original dict without output."""
    cfg = EmptyValidationConfig()
    returned = validator.validate_member(cfg, 'value', member_value,
                                         sys.stderr)
    captured_out, captured_err = capsys.readouterr()
    assert returned is member_value
    assert captured_out == ''
    assert captured_err == ''


def test_kv_types_exported() -> None:
    """The compact dict type validator is available from the package."""
    assert public_validator is DictKeyValueTypesValidator


@pytest.mark.parametrize(
    'key_type, value_type, value_validator, exc_type, message',
    [('str', int, None, TypeError, 'key_type must be a type'),
     (list, int, None, TypeError, 'key_type must be a hashable type'),
     (str, 'int', None, TypeError, 'value_type must be a type'),
     (str, int, object(), TypeError,
      'value_validator must be a MemberValidator or None')])
def test_kv_init_bad_args(
        key_type: object, value_type: object, value_validator: object,
        exc_type: type[Exception], message: str) -> None:
    """Constructor arguments must be valid runtime types and validators."""
    with pytest.raises(exc_type) as exc:
        DictKeyValueTypesValidator(
            key_type=cast(Any, key_type), value_type=cast(Any, value_type),
            value_validator=cast(Any, value_validator))
    assert message in str(exc.value)


def test_kv_init_simple() -> None:
    """The simple constructor form stores key and value runtime types."""
    validator = DictKeyValueTypesValidator(str, int)
    assert validator.key_type is str
    assert validator.value_type is int
    assert validator.value_validator is None


def test_kv_init_wraps_value() -> None:
    """An inner value validator is wrapped in a DictForEachValidator."""
    inner = ListValueValidator(0, 10, None)
    validator = DictKeyValueTypesValidator(str, list, inner)
    assert validator.key_type is str
    assert validator.value_type is list
    assert isinstance(validator.value_validator, DictForEachValidator)


@pytest.mark.parametrize(
    'key_type, value_type, member_value',
    [(str, int, {'a': 1, 'b': 2}), (int, str, {
        1: 'one',
        2: 'two'
    }), (RuleKey, list, {
        RuleKey.ALPHA: [1],
        RuleKey.BETA: []
    }), (str, int, {})])
def test_kv_ok(capsys: CaptureFixture[str], key_type: type[Hashable],
               value_type: type[object],
               member_value: dict[Hashable, object]) -> None:
    """Well-formed uniform dicts pass and are returned unchanged."""
    validator = DictKeyValueTypesValidator(key_type, value_type)
    _assert_same_dict(capsys, validator, member_value)


def test_kv_accepts_bool_int(capsys: CaptureFixture[str]) -> None:
    """The type checks use normal isinstance semantics."""
    validator = DictKeyValueTypesValidator(str, int)
    member_value = {'enabled': True}
    _assert_same_dict(capsys, validator, member_value)


@pytest.mark.parametrize(
    'member_value, message',
    [([1, 2], 'Value for value is not a dict'),
     ({
         'a': 1,
         2: 2
     }, 'Key 2 in value is not of type str'),
     ({
         'a': 1,
         'b': 'bad'
     }, 'Value bad for value[b] is not of type int')])
def test_kv_rejects_bad_values(
        capsys: CaptureFixture[str], member_value: object,
        message: str) -> None:
    """Invalid outer values, keys and values must be reported clearly."""
    validator = DictKeyValueTypesValidator(str, int)
    assert_validate_member_failure(capsys, validator, member_value,
                                   InvalidConfiguration, message)


def test_kv_type_before_inner(capsys: CaptureFixture[str]) -> None:
    """The configured value type is checked before the inner validator."""
    validator = DictKeyValueTypesValidator(str, list,
                                           ListValueValidator(0, 10, None))
    assert_validate_member_failure(
        capsys, validator, {'ports': 'not-a-list'}, InvalidConfiguration,
        'Value not-a-list for value[ports] is not of type list')


def test_kv_inner_list_ok(capsys: CaptureFixture[str]) -> None:
    """Nested list contents can be validated through value_validator."""
    validator = DictKeyValueTypesValidator(str, list,
                                           ListValueValidator(0, 10, None))
    cfg = EmptyValidationConfig()
    member_value = {'ports': [1, 2], 'fallback': []}
    result = validator.validate_member(cfg, 'value', member_value, sys.stderr)
    out, err = capsys.readouterr()
    assert result == {'ports': [1, 2], 'fallback': []}
    assert result is not member_value
    assert out == ''
    assert err == ''


def test_kv_inner_normalizes(capsys: CaptureFixture[str]) -> None:
    """Value normalizations are returned without mutating the input dict."""
    validator = DictKeyValueTypesValidator(str, list,
                                           ListOrderingValidator(int))
    cfg = EmptyValidationConfig()
    member_value = {'first': [3, 1, 2], 'second': [2, 1]}
    result = validator.validate_member(cfg, 'value', member_value, sys.stderr)
    out, err = capsys.readouterr()
    assert result == {'first': [1, 2, 3], 'second': [1, 2]}
    assert member_value == {'first': [3, 1, 2], 'second': [2, 1]}
    assert out == ''
    assert err == ''


def test_kv_inner_failure(capsys: CaptureFixture[str]) -> None:
    """Errors from the optional value validator carry the dict key path."""
    validator = DictKeyValueTypesValidator(str, list,
                                           ListValueValidator(0, 10, None))
    assert_validate_member_failure(
        capsys, validator, {'ports': [1, 20]}, InvalidConfiguration,
        'Value 20 for value[ports] at index 1 is greater than maximum 10')


def test_kv_parsed_json(capsys: CaptureFixture[str]) -> None:
    """Test DictKeyValueTypesValidator through the Config validation plan."""
    cfg = SingleMemberValidationConfig(
        'value', {'a': 0}, DictKeyValueTypesValidator(str, int),
        from_json_data_text='{"value": {"a": 7}}')
    out, err = capsys.readouterr()
    assert getattr(cfg, 'value') == {'a': 7}
    assert out == ''
    assert err == ''
