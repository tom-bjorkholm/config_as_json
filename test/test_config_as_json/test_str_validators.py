#! /usr/local/bin/python3
"""Test string validators."""

# Copyright (c) 2026 Tom Björkholm
# MIT License

import sys
from typing import Optional, Sequence, TextIO
import pytest
from pytest import CaptureFixture
import config_as_json.validator as validator_module
from config_as_json import Config, InvalidConfiguration, \
    InvalidConfigurationValue, MemberValidationStep, MemberValidator, \
    StrCaseChangeValidator, StrCaseSpec, StrCaseValidator, StrLenValidator, \
    StrPositionSpec, StrValidator, ValidationPlan
from .validator_test_helpers import EmptyValidationConfig, \
    SingleMemberValidationConfig, assert_validate_member_failure, \
    assert_validate_member_ok


FIRST_STRING = StrPositionSpec.FIRST_IN_STRING
FIRST_WORD = StrPositionSpec.FIRST_IN_WORD
FIRST_SENTENCE = StrPositionSpec.FIRST_IN_SENTENCE
EVERY = StrPositionSpec.EVERY_CHARACTER
LOWER = StrCaseSpec.LOWER
UPPER = StrCaseSpec.UPPER
ORIGINAL = StrCaseSpec.ORIGINAL


class PaletteConfig(Config):
    """Config class used for StrValidator integration tests."""

    def __init__(self, from_json_data_text: Optional[str] = None,
                 stderr_file: TextIO = sys.stderr) -> None:
        """Construct test config object."""
        self.shade = 'GREEN'
        self.accent = 'blu'
        super().__init__(from_json_data_text=from_json_data_text,
                         from_json_filename=None, stderr_file=stderr_file)

    def accent_names(self) -> Sequence[str]:
        """Return the allowed accent names."""
        return ['blue', 'black']

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Get validation plan for use when validating the Config object."""
        _ = stderr_file
        return [
            MemberValidationStep(member_names=['shade'],
                                 validator=StrValidator(['red', 'green'],
                                                        ignore_case=True,
                                                        normalize=True)),
            MemberValidationStep(member_names=['accent'],
                                 validator=StrValidator(self.accent_names,
                                                        ignore_case=False,
                                                        best_match=True))
        ]


class TextConfig(Config):
    """Config class used for string validator integration tests."""

    def __init__(self, from_json_data_text: Optional[str] = None,
                 stderr_file: TextIO = sys.stderr) -> None:
        """Construct test config object."""
        self.code = 'abc'
        self.title = 'hello WORLD. again? YES!'
        super().__init__(from_json_data_text=from_json_data_text,
                         from_json_filename=None, stderr_file=stderr_file)

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Get validation plan for use when validating the Config object."""
        _ = stderr_file
        return [
            MemberValidationStep(member_names=['code'],
                                 validator=StrLenValidator(2, 6)),
            MemberValidationStep(
                member_names=['title'],
                validator=StrCaseChangeValidator(FIRST_SENTENCE, UPPER, LOWER))
        ]


def _assert_programmer_error(capsys: CaptureFixture[str],
                             validator: MemberValidator,
                             exc_type: type[Exception], message: str) -> None:
    """Assert validation-time programmer errors are not printed."""
    cfg = EmptyValidationConfig()
    with pytest.raises(exc_type) as exc:
        validator.validate_member(cfg, 'value', 'alpha', sys.stderr)
    out, err = capsys.readouterr()
    assert message in str(exc.value)
    assert out == ''
    assert err == ''


def _bad_len_bound() -> Optional[int]:
    """Return an invalid dynamic length bound for error handling tests."""
    return 'x'  # type: ignore[return-value]


def test_str_not_in_validator_module() -> None:
    """Test that validator.py does not re-export StrValidator."""
    assert not hasattr(validator_module, 'StrValidator')


@pytest.mark.parametrize(
    'validator, member_value, expected',
    [(StrValidator(['red', 'green'], ignore_case=False), 'red', 'red'),
     (StrValidator(['red', 'green'], ignore_case=True), 'GREEN', 'GREEN'),
     (StrValidator(['red', 'green'], ignore_case=True,
                   normalize=True), 'GREEN', 'green'),
     (StrValidator(['Alpha'], ignore_case=False,
                   best_match=True), 'alpha', 'Alpha'),
     (StrValidator(lambda: ['blue', 'black'], ignore_case=False,
                   best_match=True), 'blu', 'blue')])
def test_str_validator_ok(capsys: CaptureFixture[str],
                          validator: MemberValidator, member_value: object,
                          expected: object) -> None:
    """Test OK cases of StrValidator."""
    assert_validate_member_ok(capsys, validator, member_value, expected)


def test_str_rejects_bad_type(capsys: CaptureFixture[str]) -> None:
    """Test that StrValidator rejects non-string values."""
    validator = StrValidator(['red', 'green'], ignore_case=False)
    assert_validate_member_failure(capsys, validator, 42, InvalidConfiguration,
                                   'Value for value is not a string.')


def test_str_rejects_disallowed(capsys: CaptureFixture[str]) -> None:
    """Test that StrValidator rejects unknown values."""
    validator = StrValidator(['red', 'green'], ignore_case=False)
    assert_validate_member_failure(capsys, validator, 'blue',
                                   InvalidConfigurationValue,
                                   'Value blue for value')


def test_str_rejects_ambiguous(capsys: CaptureFixture[str]) -> None:
    """Test that best-match validation rejects ambiguous prefixes."""
    validator = StrValidator(['blue', 'black'], ignore_case=False,
                             best_match=True)
    assert_validate_member_failure(capsys, validator, 'bl',
                                   InvalidConfigurationValue,
                                   'Value bl for value')


def test_palette_default_values(capsys: CaptureFixture[str]) -> None:
    """Test StrValidator integration in a derived config class."""
    cfg = PaletteConfig()
    out, err = capsys.readouterr()
    assert cfg.shade == 'green'
    assert cfg.accent == 'blue'
    assert out == ''
    assert err == ''


def test_palette_parsed_json(capsys: CaptureFixture[str]) -> None:
    """Test StrValidator integration when values come from parsed JSON."""
    cfg = PaletteConfig(
        from_json_data_text='{"shade": "Red", "accent": "black"}')
    out, err = capsys.readouterr()
    assert cfg.shade == 'red'
    assert cfg.accent == 'black'
    assert out == ''
    assert err == ''


@pytest.mark.parametrize(
    'min_length, max_length, exc_type, message',
    [(None, None, ValueError, 'At least one of min_length or max_length'),
     (-1, 5, ValueError, 'min_length must be non-negative'),
     (1, -1, ValueError, 'max_length must be non-negative'),
     (True, 5, TypeError, 'min_length must be an int'),
     (1, False, TypeError, 'max_length must be an int'),
     (5, 3, ValueError,
      'min_length must be less than or equal to max_length')])
def test_str_len_init_bad_args(min_length: object, max_length: object,
                               exc_type: type[Exception],
                               message: str) -> None:
    """Test StrLenValidator constructor validation."""
    with pytest.raises(exc_type) as exc:
        StrLenValidator(min_length, max_length)  # type: ignore[arg-type]
    assert message in str(exc.value)


@pytest.mark.parametrize(
    'validator, member_value, expected',
    [(StrLenValidator(0, 0), '', ''),
     (StrLenValidator(1, None), 'a', 'a'),
     (StrLenValidator(None, 3), 'abc', 'abc'),
     (StrLenValidator(lambda: None, lambda: None), 'anything', 'anything'),
     (StrLenValidator(lambda: 2, lambda: None), 'ab', 'ab')])
def test_str_len_validator_ok(capsys: CaptureFixture[str],
                              validator: MemberValidator, member_value: object,
                              expected: object) -> None:
    """Test OK cases of StrLenValidator."""
    assert_validate_member_ok(capsys, validator, member_value, expected)


@pytest.mark.parametrize('validator, value, message', [
    (StrLenValidator(0, 3), 42, 'Value for value is not a string'),
    (StrLenValidator(3, 5), 'ab', 'length 2 which is less than minimum 3'),
    (StrLenValidator(0, 2), 'abc', 'length 3 which is greater than maximum 2')
])
def test_str_len_rejects_values(capsys: CaptureFixture[str],
                                validator: MemberValidator, value: object,
                                message: str) -> None:
    """Test StrLenValidator failures."""
    assert_validate_member_failure(capsys, validator, value,
                                   InvalidConfiguration, message)


@pytest.mark.parametrize(
    'validator, exc_type, message',
    [(StrLenValidator(_bad_len_bound, None), TypeError,
      'min_length must be an int or None'),
     (StrLenValidator(lambda: -1, None), ValueError,
      'min_length must be non-negative'),
     (StrLenValidator(lambda: 5, lambda: 3), ValueError,
      'min_length must be less than or equal to max_length')])
def test_str_len_dynamic_bad_args(capsys: CaptureFixture[str],
                                  validator: MemberValidator,
                                  exc_type: type[Exception],
                                  message: str) -> None:
    """Test StrLenValidator dynamic bound validation."""
    _assert_programmer_error(capsys, validator, exc_type, message)


def test_str_len_dynamic_values(capsys: CaptureFixture[str]) -> None:
    """Test that StrLenValidator uses current callable bounds."""
    max_length = 3

    def current_max_length() -> Optional[int]:
        """Return the current maximum string length."""
        return max_length

    validator = StrLenValidator(1, current_max_length)
    assert_validate_member_ok(capsys, validator, 'abc', 'abc')
    max_length = 2
    assert_validate_member_failure(
        capsys, validator, 'abc', InvalidConfiguration,
        'length 3 which is greater than maximum 2')


@pytest.mark.parametrize(
    'validator, value, expected',
    [(StrCaseValidator(EVERY, LOWER, ORIGINAL), 'abc-123', 'abc-123'),
     (StrCaseValidator(EVERY, UPPER, ORIGINAL), 'ABC-123', 'ABC-123'),
     (StrCaseValidator(FIRST_STRING, UPPER, LOWER), 'Hello', 'Hello'),
     (StrCaseValidator(FIRST_WORD, UPPER, LOWER),
      '  Hello  World', '  Hello  World'),
     (StrCaseValidator(FIRST_SENTENCE, UPPER, LOWER),
      '  Hello world.  Again? Yes!', '  Hello world.  Again? Yes!'),
     (StrCaseValidator(EVERY, ORIGINAL, ORIGINAL), 'mIXed', 'mIXed')])
def test_str_case_validator_ok(capsys: CaptureFixture[str],
                               validator: MemberValidator, value: object,
                               expected: object) -> None:
    """Test OK cases of StrCaseValidator."""
    assert_validate_member_ok(capsys, validator, value, expected)


@pytest.mark.parametrize(
    'position, special_case, other_case, message',
    [(object(), UPPER, LOWER,
      'special_position must be a StrPositionSpec'),
     (FIRST_STRING, object(), LOWER,
      'special_position_case must be a StrCaseSpec'),
     (FIRST_STRING, UPPER, object(),
      'other_position_case must be a StrCaseSpec')])
def test_str_case_init_bad_args(position: object, special_case: object,
                                other_case: object, message: str) -> None:
    """Test string case validator constructor validation."""
    with pytest.raises(TypeError) as exc:
        StrCaseValidator(position, special_case,  # type: ignore[arg-type]
                         other_case)  # type: ignore[arg-type]
    assert message in str(exc.value)
    with pytest.raises(TypeError) as exc:
        StrCaseChangeValidator(position,  # type: ignore[arg-type]
                               special_case,  # type: ignore[arg-type]
                               other_case)  # type: ignore[arg-type]
    assert message in str(exc.value)


@pytest.mark.parametrize('validator, value, message', [
    (StrCaseValidator(EVERY, LOWER, ORIGINAL), 'abC',
     "at index 2 is not lowercase"),
    (StrCaseValidator(FIRST_STRING, UPPER, LOWER), 'hello',
     "at index 0 is not uppercase"),
    (StrCaseValidator(FIRST_WORD, UPPER, LOWER), 'Hello world',
     "at index 6 is not uppercase"),
    (StrCaseValidator(FIRST_SENTENCE, UPPER, LOWER), 'Hello. again',
     "at index 7 is not uppercase"),
    (StrCaseValidator(EVERY, UPPER, ORIGINAL), 42,
     'Value for value is not a string')
])
def test_str_case_rejects_values(capsys: CaptureFixture[str],
                                 validator: MemberValidator, value: object,
                                 message: str) -> None:
    """Test StrCaseValidator failures."""
    assert_validate_member_failure(capsys, validator, value,
                                   InvalidConfiguration, message)


@pytest.mark.parametrize(
    'validator, member_value, expected',
    [(StrCaseChangeValidator(EVERY, LOWER, ORIGINAL), 'AbC-123',
      'abc-123'),
     (StrCaseChangeValidator(FIRST_STRING, UPPER, ORIGINAL), 'alpha BETA',
      'Alpha BETA'),
     (StrCaseChangeValidator(FIRST_WORD, UPPER, LOWER),
      ' hello WORLD\tAGAIN', ' Hello World\tAgain'),
     (StrCaseChangeValidator(FIRST_SENTENCE, UPPER, LOWER),
      ' hello WORLD. again? YES!', ' Hello world. Again? Yes!'),
     (StrCaseChangeValidator(EVERY, ORIGINAL, ORIGINAL), 'mIXed', 'mIXed')])
def test_case_change_validator_ok(capsys: CaptureFixture[str],
                                  validator: MemberValidator,
                                  member_value: object,
                                  expected: object) -> None:
    """Test OK cases of StrCaseChangeValidator."""
    assert_validate_member_ok(capsys, validator, member_value, expected)


def test_case_change_rejects_type(capsys: CaptureFixture[str]) -> None:
    """Test that StrCaseChangeValidator rejects non-string values."""
    validator = StrCaseChangeValidator(EVERY, LOWER, ORIGINAL)
    assert_validate_member_failure(capsys, validator, 42, InvalidConfiguration,
                                   'Value for value is not a string')


def test_string_validators_integrate(capsys: CaptureFixture[str]) -> None:
    """Test string length and case changing through Config.validate()."""
    cfg = TextConfig()
    out, err = capsys.readouterr()
    assert cfg.code == 'abc'
    assert cfg.title == 'Hello world. Again? Yes!'
    assert out == ''
    assert err == ''


def test_string_validators_parse(capsys: CaptureFixture[str]) -> None:
    """Test string validators when values come from parsed JSON."""
    cfg = TextConfig(from_json_data_text='{"code": "abcd", '
                     '"title": "good MORNING! good NIGHT."}')
    out, err = capsys.readouterr()
    assert cfg.code == 'abcd'
    assert cfg.title == 'Good morning! Good night.'
    assert out == ''
    assert err == ''


def test_string_validators_reject(capsys: CaptureFixture[str]) -> None:
    """Test string validators reject invalid parsed JSON values."""
    with pytest.raises(InvalidConfiguration) as exc:
        _ = TextConfig(from_json_data_text='{"code": "abcdefg", '
                       '"title": "Hello"}', stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert 'length 7 which is greater than maximum 6' in str(exc.value)
    assert out == ''
    assert 'length 7 which is greater than maximum 6' in err


def test_str_len_integrates(capsys: CaptureFixture[str]) -> None:
    """Test StrLenValidator through the generic one-member helper."""
    cfg = SingleMemberValidationConfig('value', 'abc', StrLenValidator(1, 3),
                                       from_json_data_text='{"value": "ab"}')
    out, err = capsys.readouterr()
    assert getattr(cfg, 'value') == 'ab'
    assert out == ''
    assert err == ''
