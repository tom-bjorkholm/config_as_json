#! /usr/local/bin/python3
"""Test runtime type validators."""

# Copyright (c) 2024-2026 Tom Björkholm
# MIT License

from typing import Callable, Protocol, runtime_checkable, cast
import pytest
from pytest import CaptureFixture
from config_as_json import InvalidConfigurationType as RootTypeError
from config_as_json import ValueAsTypeValidator as RootAsTypeValidator
from config_as_json import ValueTypeValidator as RootTypeValidator
from config_as_json.type_validators import InvalidConfigurationType, \
    ValueAsTypeValidator, ValueTypeValidator
from config_as_json.validator import InvalidConfiguration, MemberValidator
from .validator_test_helpers import SingleMemberValidationConfig, \
    assert_validate_member_failure, assert_validate_member_ok


# pylint: disable-next=too-few-public-methods
class BaseValue:
    """Base class for conversion specificity tests."""

    def __str__(self) -> str:
        """Return text used by direct string conversion."""
        return 'direct'


# pylint: disable-next=too-few-public-methods
class MiddleValue(BaseValue):
    """More specific value type in the conversion hierarchy."""


# pylint: disable-next=too-few-public-methods
class LeafValue(MiddleValue):
    """Most specific value type in the conversion hierarchy."""


@runtime_checkable
class TextSourceProtocol(Protocol):  # pylint: disable=too-few-public-methods
    """Structural source type used for virtual type matching."""

    def text_value(self) -> str:
        """Return text for conversion."""
        raise NotImplementedError


# pylint: disable-next=too-few-public-methods
class TextSource:
    """Concrete value matching ``TextSourceProtocol`` structurally."""

    def __str__(self) -> str:
        """Return text used by direct string conversion."""
        return 'direct-text'

    def text_value(self) -> str:
        """Return text used by protocol-based conversion."""
        return 'protocol-text'


def convert_middle(value: object) -> str:
    """Convert ``MiddleValue`` instances through a custom function."""
    assert isinstance(value, MiddleValue)
    return 'callable'


def convert_base(value: object) -> str:
    """Convert ``BaseValue`` instances through a custom function."""
    assert isinstance(value, BaseValue)
    return 'base-callable'


def convert_yes_no(value: object) -> bool:
    """Convert yes/no strings to boolean values."""
    if value == 'yes':
        return True
    if value == 'no':
        return False
    raise ValueError('Expected yes or no.')


def convert_text_to_int(value: object) -> int:
    """Convert string input to an integer."""
    assert isinstance(value, str)
    return int(value)


def convert_float_to_int(value: object) -> int:
    """Convert float input to a clearly distinguishable integer."""
    assert isinstance(value, float)
    return int(value) + 10


def convert_text_source(value: object) -> str:
    """Convert ``TextSource`` instances through a custom function."""
    assert isinstance(value, TextSource)
    return 'concrete-text'


def convert_text_like(value: object) -> str:
    """Convert structural text sources through a custom function."""
    assert isinstance(value, TextSourceProtocol)
    return value.text_value()


def bad_int_conversion(value: object) -> int:
    """Return a deliberately wrong type for conversion error tests."""
    _ = value
    return cast(int, 'bad')


def test_package_exports_types() -> None:
    """Test that package-root imports expose the type validators."""
    assert RootTypeValidator is ValueTypeValidator
    assert RootAsTypeValidator is ValueAsTypeValidator
    assert RootTypeError is InvalidConfigurationType


@pytest.mark.parametrize('bad_value_type', [None, 'str', (str,)])
def test_value_type_init_bad_type(bad_value_type: object) -> None:
    """Test ValueTypeValidator rejects bad allowed type specs."""
    with pytest.raises(TypeError) as exc:
        ValueTypeValidator(bad_value_type)  # type: ignore[arg-type]
    assert 'value_type must be a type or a list of types' in str(exc.value)


def test_value_type_rejects_empty() -> None:
    """Test ValueTypeValidator rejects an empty allowed-type list."""
    with pytest.raises(ValueError) as exc:
        ValueTypeValidator([])
    assert 'value_type must be non-empty' in str(exc.value)


def test_value_type_bad_list_member() -> None:
    """Test ValueTypeValidator checks each type in a list."""
    with pytest.raises(TypeError) as exc:
        ValueTypeValidator([str, 3])  # type: ignore[list-item]
    assert 'value_type[1] must be a type' in str(exc.value)


def test_value_type_bad_denied() -> None:
    """Test ValueTypeValidator rejects invalid denied type specs."""
    bad_denied = cast(type[object], 'int')
    with pytest.raises(TypeError) as exc:
        ValueTypeValidator(str, not_allowed_type=bad_denied)
    assert 'not_allowed_type must be a type or a list of types' in \
        str(exc.value)


def test_value_type_bad_denied_list() -> None:
    """Test ValueTypeValidator checks each denied type in a list."""
    bad_denied = cast(list[type[object]], [int, 'bool'])
    with pytest.raises(TypeError) as exc:
        ValueTypeValidator(str, not_allowed_type=bad_denied)
    assert 'not_allowed_type[1] must be a type' in str(exc.value)


def test_value_type_bad_strict() -> None:
    """Test ValueTypeValidator rejects non-boolean strict flags."""
    with pytest.raises(TypeError) as exc:
        ValueTypeValidator(str, strict='yes')  # type: ignore[arg-type]
    assert 'strict must be a bool' in str(exc.value)


@pytest.mark.parametrize('value_type, denied_type, strict',
                         [(bool, int, False), (int, int, True)])
def test_value_type_contradiction(value_type: type[object],
                                  denied_type: type[object],
                                  strict: bool) -> None:
    """Test ValueTypeValidator rejects impossible type rules."""
    with pytest.raises(ValueError) as exc:
        ValueTypeValidator(value_type, not_allowed_type=denied_type,
                           strict=strict)
    assert 'is denied by not_allowed_type' in str(exc.value)


def test_value_type_empty_denied(capsys: CaptureFixture[str]) -> None:
    """Test an empty denied-type list means no denied runtime types."""
    validator = ValueTypeValidator([int, str], not_allowed_type=[])
    assert validator.value_type == [int, str]
    assert validator.not_allowed_type == []
    assert_validate_member_ok(capsys, validator, 7, 7)


def test_value_type_copies_specs(capsys: CaptureFixture[str]) -> None:
    """Test constructor lists are copied into the validator."""
    allowed_types: list[type[object]] = [int, str]
    denied_types: list[type[object]] = [bool]
    validator = ValueTypeValidator(allowed_types,
                                   not_allowed_type=denied_types)
    allowed_types.append(float)
    denied_types.clear()
    assert validator.value_type == [int, str]
    assert validator.not_allowed_type is bool
    assert_validate_member_failure(capsys, validator, True,
                                   InvalidConfigurationType,
                                   'Value for value must not be of type bool')


@pytest.mark.parametrize(
    'validator, member_value, expected',
    [(ValueTypeValidator(str), 'alpha', 'alpha'),
     (ValueTypeValidator(int), 3, 3),
     (ValueTypeValidator(int), True, True),
     (ValueTypeValidator(list), [1, 2], [1, 2]),
     (ValueTypeValidator([str, int]), 'alpha', 'alpha'),
     (ValueTypeValidator([str, int]), 5, 5),
     (ValueTypeValidator(int, not_allowed_type=bool), 5, 5),
     (ValueTypeValidator(bool, not_allowed_type=int, strict=True),
      True, True)])
def test_value_type_validator_ok(capsys: CaptureFixture[str],
                                 validator: MemberValidator,
                                 member_value: object,
                                 expected: object) -> None:
    """Test OK cases of ValueTypeValidator."""
    assert_validate_member_ok(capsys, validator, member_value, expected)


@pytest.mark.parametrize(
    'validator, member_value, message',
    [(ValueTypeValidator(str), 42, 'Value for value is not of type str'),
     (ValueTypeValidator(bool), 1, 'Value for value is not of type bool'),
     (ValueTypeValidator(list), (1, 2),
      'Value for value is not of type list'),
     (ValueTypeValidator([str, int]), 3.5,
      'Value for value is not of type str or int'),
     (ValueTypeValidator(int, not_allowed_type=bool), True,
      'Value for value must not be of type bool'),
     (ValueTypeValidator(int, strict=True), True,
      'Value for value is not of type int')])
def test_value_type_rejects_values(capsys: CaptureFixture[str],
                                   validator: MemberValidator,
                                   member_value: object, message: str) -> None:
    """Test ValueTypeValidator failures."""
    assert_validate_member_failure(capsys, validator, member_value,
                                   InvalidConfigurationType, message)


def test_value_type_exception_base(capsys: CaptureFixture[str]) -> None:
    """Test type errors still inherit from InvalidConfiguration."""
    assert_validate_member_failure(capsys, ValueTypeValidator(str), 42,
                                   InvalidConfiguration,
                                   'Value for value is not of type str')


def test_value_type_parsed_json(capsys: CaptureFixture[str]) -> None:
    """Test ValueTypeValidator integration through Config.validate()."""
    cfg = SingleMemberValidationConfig('value', 'alpha',
                                       ValueTypeValidator(str),
                                       from_json_data_text='{"value": "beta"}')
    out, err = capsys.readouterr()
    assert getattr(cfg, 'value') == 'beta'
    assert out == ''
    assert err == ''


def test_value_as_type_bad_target() -> None:
    """Test ValueAsTypeValidator requires one target runtime type."""
    with pytest.raises(TypeError) as exc:
        ValueAsTypeValidator([int])  # type: ignore[arg-type]
    assert 'value_type must be a type' in str(exc.value)


def test_value_as_type_bad_direct() -> None:
    """Test ValueAsTypeValidator rejects invalid direct type specs."""
    with pytest.raises(TypeError) as exc:
        ValueAsTypeValidator(int, direct_types='str')  # type: ignore[arg-type]
    assert 'direct_types must be a type or a list of types' in str(exc.value)


def test_value_as_type_bad_dir_list() -> None:
    """Test ValueAsTypeValidator checks direct type list members."""
    bad_types = cast(list[type[object]], [str, 3])
    with pytest.raises(TypeError) as exc:
        ValueAsTypeValidator(int, direct_types=bad_types)
    assert 'direct_types[1] must be a type' in str(exc.value)


def test_value_as_type_bad_map() -> None:
    """Test ValueAsTypeValidator requires a dict of conversion functions."""
    bad_map = cast(dict[type[object], Callable[[object], int]], [])
    with pytest.raises(TypeError) as exc:
        ValueAsTypeValidator(int, convertable_types=bad_map)
    assert 'convertable_types must be a dict' in str(exc.value)


def test_value_as_type_bad_map_key() -> None:
    """Test ValueAsTypeValidator checks conversion map keys."""
    raw_map: dict[object, Callable[[object], int]] = {
        'str': convert_text_to_int}
    bad_map = cast(dict[type[object], Callable[[object], int]], raw_map)
    with pytest.raises(TypeError) as exc:
        ValueAsTypeValidator(int, convertable_types=bad_map)
    assert 'convertable_types key must be a type' in str(exc.value)


def test_value_as_type_bad_map_value() -> None:
    """Test ValueAsTypeValidator checks conversion map values."""
    raw_map: dict[type[object], object] = {str: 'bad'}
    bad_map = cast(dict[type[object], Callable[[object], int]], raw_map)
    with pytest.raises(TypeError) as exc:
        ValueAsTypeValidator(int, convertable_types=bad_map)
    assert 'convertable_types[str] must be callable' in str(exc.value)


def test_value_as_type_overlap() -> None:
    """Test ValueAsTypeValidator rejects exact direct/callable overlap."""
    with pytest.raises(ValueError) as exc:
        ValueAsTypeValidator(int, direct_types=str,
                             convertable_types={str: convert_text_to_int})
    assert 'is both a direct type and a convertable type' in str(exc.value)


@pytest.mark.parametrize(
    'validator, member_value, expected',
    [(ValueAsTypeValidator(int, direct_types=str), 7, 7),
     (ValueAsTypeValidator(int, direct_types=str), '5', 5),
     (ValueAsTypeValidator(int, direct_types=[str, float]), 4.8, 4),
     (ValueAsTypeValidator(bool, convertable_types={str: convert_yes_no}),
      'yes', True)])
def test_value_as_type_validator_ok(capsys: CaptureFixture[str],
                                    validator: MemberValidator,
                                    member_value: object,
                                    expected: object) -> None:
    """Test OK cases of ValueAsTypeValidator."""
    assert_validate_member_ok(capsys, validator, member_value, expected)


def test_value_as_type_specific_func(capsys: CaptureFixture[str]) -> None:
    """Test callable conversion wins when its base class is more specific."""
    validator = ValueAsTypeValidator(
        str, direct_types=BaseValue,
        convertable_types={MiddleValue: convert_middle})
    assert_validate_member_ok(capsys, validator, LeafValue(), 'callable')


def test_value_as_type_specific_dir(capsys: CaptureFixture[str]) -> None:
    """Test direct conversion wins when its base class is more specific."""
    validator = ValueAsTypeValidator(
        str, direct_types=MiddleValue,
        convertable_types={BaseValue: convert_base})
    assert_validate_member_ok(capsys, validator, LeafValue(), 'direct')


def test_value_as_type_virtual_dir(capsys: CaptureFixture[str]) -> None:
    """Test direct conversion can match a structural runtime type."""
    text_type = cast(type[object], TextSourceProtocol)
    validator = ValueAsTypeValidator(str, direct_types=text_type)
    assert_validate_member_ok(capsys, validator, TextSource(), 'direct-text')


def test_value_as_type_concrete_func(capsys: CaptureFixture[str]) -> None:
    """Test concrete callable conversion beats virtual direct conversion."""
    text_type = cast(type[object], TextSourceProtocol)
    validator = ValueAsTypeValidator(
        str, direct_types=text_type,
        convertable_types={TextSource: convert_text_source})
    assert_validate_member_ok(capsys, validator, TextSource(), 'concrete-text')


def test_value_as_type_direct_wins(capsys: CaptureFixture[str]) -> None:
    """Test concrete direct conversion beats virtual callable conversion."""
    text_type = cast(type[object], TextSourceProtocol)
    conv_map: dict[type[object], Callable[[object], str]] = {
        text_type: convert_text_like}
    validator = ValueAsTypeValidator(str, direct_types=TextSource,
                                     convertable_types=conv_map)
    assert_validate_member_ok(capsys, validator, TextSource(), 'direct-text')


def test_value_as_type_copies_specs(capsys: CaptureFixture[str]) -> None:
    """Test constructor lists and maps are copied into the validator."""
    direct_types: list[type[object]] = [str]
    conv_map: dict[type[object], Callable[[object], int]] = {
        float: convert_float_to_int}
    validator = ValueAsTypeValidator(int, direct_types=direct_types,
                                     convertable_types=conv_map)
    direct_types.clear()
    conv_map.clear()
    assert validator.direct_types == str
    assert list(validator.convertable_types) == [float]
    assert_validate_member_ok(capsys, validator, '5', 5)
    assert_validate_member_ok(capsys, validator, 2.9, 12)


@pytest.mark.parametrize(
    'validator, member_value, message',
    [(ValueAsTypeValidator(int, direct_types=str), [],
      'Value for value is not of type int or str'),
     (ValueAsTypeValidator(int, direct_types=str), 'abc',
      'Value for value could not be converted to int'),
     (ValueAsTypeValidator(int, convertable_types={str: bad_int_conversion}),
      '5', 'Conversion for value returned str instead of int'),
     (ValueAsTypeValidator(bool, convertable_types={str: convert_yes_no}),
      'maybe', 'Value for value could not be converted to bool')])
def test_value_as_type_rejects_val(capsys: CaptureFixture[str],
                                   validator: MemberValidator,
                                   member_value: object, message: str) -> None:
    """Test ValueAsTypeValidator failures."""
    assert_validate_member_failure(capsys, validator, member_value,
                                   InvalidConfigurationType, message)


def test_value_as_type_json(capsys: CaptureFixture[str]) -> None:
    """Test ValueAsTypeValidator integration through Config.validate()."""
    cfg = SingleMemberValidationConfig(
        'value', 1, ValueAsTypeValidator(int, direct_types=str),
        from_json_data_text='{"value": "5"}')
    out, err = capsys.readouterr()
    assert getattr(cfg, 'value') == 5
    assert out == ''
    assert err == ''
