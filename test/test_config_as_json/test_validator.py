#! /usr/local/bin/python3
"""Test the validation framework."""

# Copyright (c) 2024-2026 Tom Björkholm
# MIT License

from abc import ABCMeta
import sys
from io import StringIO
from pathlib import Path
from typing import Callable, Optional, Sequence, TextIO
import pytest
from pytest import CaptureFixture
from config_as_json.config import Config
from config_as_json.commontypes import PathOrStr
from config_as_json.validator import IntFloatValidator, \
    InvalidConfiguration, InvalidConfigurationValue, ValidationPlan, \
    ValidationStep, MemberValidationStep, \
    WholeConfigValidationStep, MemberValidator, WholeConfigValidator, \
    MemberValidatorSequence, not_one_of_allowed_values, string_best_match
from config_as_json.type_validators import ValueTypeValidator
from .validator_test_helpers import \
    EmptyValidationConfig, SingleMemberValidationConfig, \
    assert_validate_member_failure, assert_validate_member_ok


class ConfigMissingValidationPlan(Config):
    """Config class used to test missing get_validation_plan()."""

    def __init__(self, from_json_data_text: Optional[str] = None,
                 stderr_file: TextIO = sys.stderr) -> None:
        """Construct test config object."""
        self.value = 'alpha'
        super().__init__(from_json_data_text=from_json_data_text,
                         from_json_filename=None, stderr_file=stderr_file)


# pylint: disable-next=too-few-public-methods
class UppercaseValidator(MemberValidator):
    """Normalize one string member to upper case."""

    def validate_member(self, config: Config, member_name: str,
                        member_value: object,
                        stderr_file: TextIO = sys.stderr) \
            -> Optional[object]:
        """Validate one member and return the upper-case value."""
        _ = config
        _ = member_name
        _ = stderr_file
        assert isinstance(member_value, str)
        return member_value.upper()


# pylint: disable-next=too-few-public-methods
class PrefixFromNameValidator(MemberValidator):
    """Prefix one member with the normalized name from the config."""

    def validate_member(self, config: Config, member_name: str,
                        member_value: object,
                        stderr_file: TextIO = sys.stderr) \
            -> Optional[object]:
        """Validate one member and return the prefixed value."""
        assert isinstance(config, ValidationOrderConfig)
        _ = member_name
        _ = stderr_file
        assert isinstance(member_value, str)
        return f'{config.name}:{member_value}'


# pylint: disable-next=too-few-public-methods
class WholeConfigSuffixValidator(WholeConfigValidator):
    """Append one suffix to the alias field during whole-config validation."""

    def __init__(self, suffix: str) -> None:
        """Store the suffix to append."""
        self._suffix = suffix

    def validate(self, config: Config,
                 stderr_file: TextIO = sys.stderr) -> None:
        """Validate the whole config by mutating one member."""
        assert isinstance(config, ValidationOrderConfig)
        _ = stderr_file
        config.alias = config.alias + self._suffix


# pylint: disable-next=too-few-public-methods
class IdentityValidator(MemberValidator):
    """Return the validated member unchanged."""

    def validate_member(self, config: Config, member_name: str,
                        member_value: object,
                        stderr_file: TextIO = sys.stderr) \
            -> Optional[object]:
        """Validate one member and return it unchanged."""
        _ = config
        _ = member_name
        _ = stderr_file
        return member_value


# pylint: disable-next=too-few-public-methods
class ReplaceWithNoneValidator(MemberValidator):
    """Replace the validated member with None."""

    def validate_member(self, config: Config, member_name: str,
                        member_value: object,
                        stderr_file: TextIO = sys.stderr) \
            -> Optional[object]:
        """Validate one member and replace it with None."""
        _ = config
        _ = member_name
        _ = member_value
        _ = stderr_file
        replacement: Optional[object] = None
        return replacement


class ValidationOrderConfig(Config):
    """Config class used to test validation order and write-back."""

    def __init__(self, from_json_data_text: Optional[str] = None,
                 stderr_file: TextIO = sys.stderr) -> None:
        """Construct test config object."""
        self.name = 'alpha'
        self.alias = 'beta'
        super().__init__(from_json_data_text=from_json_data_text,
                         from_json_filename=None, stderr_file=stderr_file)

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Get validation plan for use when validating the Config object."""
        return [
            MemberValidationStep(member_names=['name'],
                                 validator=UppercaseValidator()),
            MemberValidationStep(member_names=['alias'],
                                 validator=PrefixFromNameValidator()),
            WholeConfigValidationStep(
                validator=WholeConfigSuffixValidator('!'))
        ]


class MissingMemberConfig(Config):
    """Config class used to test validation of a missing member."""

    def __init__(self, stderr_file: TextIO) -> None:
        """Construct test config object."""
        self.value = 'alpha'
        super().__init__(from_json_data_text=None, from_json_filename=None,
                         stderr_file=stderr_file)

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Get validation plan for use when validating the Config object."""
        return [
            MemberValidationStep(member_names=['missing'],
                                 validator=IdentityValidator())
        ]


class NoneWriteBackConfig(Config):
    """Config class used to test member write-back of None."""

    def __init__(self, stderr_file: TextIO) -> None:
        """Construct test config object."""
        self.value = 'alpha'
        super().__init__(from_json_data_text=None, from_json_filename=None,
                         stderr_file=stderr_file)

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Get validation plan for use when validating the Config object."""
        return [
            MemberValidationStep(member_names=['value'],
                                 validator=ReplaceWithNoneValidator())
        ]


# pylint: disable-next=too-few-public-methods
class CountValidation(WholeConfigValidator):
    """Whole-config validator that records completed validation."""

    def validate(self, config: Config,
                 stderr_file: TextIO = sys.stderr) -> None:
        """Record one validation pass on ``LoadValidationConfig``."""
        _ = stderr_file
        assert isinstance(config, LoadValidationConfig)
        config.mark_validated()


class LoadValidationConfig(Config):
    """Config class used to test validation during JSON loading."""

    def __init__(self, from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 stderr_file: TextIO = sys.stderr) -> None:
        """Construct test config object."""
        self.value = 'alpha'
        self._validation_count = 0
        super().__init__(from_json_data_text=from_json_data_text,
                         from_json_filename=from_json_filename,
                         stderr_file=stderr_file)

    def mark_validated(self) -> None:
        """Record that validation reached the counting step."""
        self._validation_count += 1

    def validation_count(self) -> int:
        """Return how many validation passes reached the counter."""
        return self._validation_count

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Get validation plan for use when validating the Config object."""
        _ = stderr_file
        return [
            MemberValidationStep(
                member_names=['value'],
                validator=MemberValidatorSequence(
                    [ValueTypeValidator(str), UppercaseValidator()])),
            WholeConfigValidationStep(validator=CountValidation())
        ]


# pylint: disable-next=too-few-public-methods
class AppendTextValidator(MemberValidator):
    """Append text to a string member."""

    def __init__(self, text: str) -> None:
        """Store the text to append."""
        self.text = text

    def validate_member(self, config: Config, member_name: str,
                        member_value: object,
                        stderr_file: TextIO = sys.stderr) \
            -> Optional[object]:
        """Validate one string member and append configured text."""
        _ = config
        _ = member_name
        _ = stderr_file
        assert isinstance(member_value, str)
        return member_value + self.text


def write_json_file(config_file: Path, json_text: str) -> None:
    """Write JSON text used by load-validation tests."""
    config_file.write_text(json_text, encoding='UTF-8')


def test_missing_plan_raises(capsys: CaptureFixture[str]) -> None:
    """Test that direct Config subclasses must implement a plan."""
    with pytest.raises(NotImplementedError) as exc:
        _ = ConfigMissingValidationPlan(stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert 'Config.get_validation_plan() must be implemented' in \
        str(exc.value)
    assert out == ''
    assert 'Config.get_validation_plan() must be implemented' in err


def test_validate_order(capsys: CaptureFixture[str]) -> None:
    """Test that validation order and write-back work as documented."""
    cfg = ValidationOrderConfig(stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert cfg.name == 'ALPHA'
    assert cfg.alias == 'ALPHA:beta!'
    assert out == ''
    assert err == ''


def test_validate_missing_member(capsys: CaptureFixture[str]) -> None:
    """Test validation failure when a listed member does not exist."""
    with pytest.raises(AttributeError) as exc:
        _ = MissingMemberConfig(stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert 'Member missing not found in Config object' in str(exc.value)
    assert out == ''
    assert 'Member missing not found in Config object' in err


def test_validate_missing_stderr(capsys: CaptureFixture[str]) -> None:
    """Test validation failure routing to an explicitly supplied stream."""
    stderr_file = StringIO()
    with pytest.raises(AttributeError) as exc:
        _ = MissingMemberConfig(stderr_file=stderr_file)
    out, err = capsys.readouterr()
    assert 'Member missing not found in Config object' in str(exc.value)
    assert out == ''
    assert err == ''
    assert 'Member missing not found in Config object' in \
        stderr_file.getvalue()


def test_member_writes_none(capsys: CaptureFixture[str]) -> None:
    """Test that a member validator can replace a member with None."""
    cfg = NoneWriteBackConfig(stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert cfg.value is None
    assert out == ''
    assert err == ''


def test_allowed_values_no_print(capsys: CaptureFixture[str]) -> None:
    """Test explicit suppression of printing in helper message builder."""
    ret = not_one_of_allowed_values('color', 'orange', ['red', 'green'], None)
    out, err = capsys.readouterr()
    assert 'Invalid configuration:' in ret
    assert 'orange' in ret
    assert out == ''
    assert err == ''


def test_best_match_bad_type(capsys: CaptureFixture[str]) -> None:
    """Test that string_best_match rejects non-string values."""
    with pytest.raises(InvalidConfiguration) as exc:
        string_best_match(42, ['red', 'green'],  # type: ignore[arg-type]
                          'value', sys.stderr)
    out, err = capsys.readouterr()
    assert 'Value for value is not a string.' in str(exc.value)
    assert out == ''
    assert 'Value for value is not a string.' in err


def test_validation_bases_abstract() -> None:
    """Test that validation role base classes cannot be instantiated."""
    with pytest.raises(TypeError):
        ABCMeta.__call__(WholeConfigValidator)
    with pytest.raises(TypeError):
        ABCMeta.__call__(MemberValidator)
    with pytest.raises(TypeError):
        ABCMeta.__call__(ValidationStep)


@pytest.mark.parametrize('call, message', [
    (lambda cfg: WholeConfigValidator.validate(WholeConfigSuffixValidator('!'),
                                               cfg, sys.stderr),
     'WholeConfigValidator.validate() must be implemented'),
    (lambda cfg: MemberValidator.validate_member(IdentityValidator(), cfg,
                                                 'value', 'raw', sys.stderr),
     'MemberValidator.validate_member() must be implemented'),
    (lambda cfg: ValidationStep.apply(
        MemberValidationStep(['value'], IdentityValidator()), cfg, sys.stderr),
     'ValidationStep.apply() must be implemented')])
def test_validation_base_not_impl(capsys: CaptureFixture[str],
                                  call: Callable[[Config], object],
                                  message: str) -> None:
    """Test base validation methods when called directly."""
    cfg = EmptyValidationConfig()
    with pytest.raises(NotImplementedError) as exc:
        call(cfg)
    out, err = capsys.readouterr()
    assert message in str(exc.value)
    assert out == ''
    assert message in err


def test_read_validates_file(capsys: CaptureFixture[str],
                             tmp_path: Path) -> None:
    """Test that read() validates and normalizes loaded JSON."""
    cfg = LoadValidationConfig(stderr_file=sys.stderr)
    config_file = tmp_path / 'config.json'
    write_json_file(config_file, '{"value": "Beta"}')
    cfg.read(config_file, stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert cfg.value == 'BETA'
    assert cfg.validation_count() == 2
    assert out == ''
    assert err == ''


def test_read_rejects_invalid(capsys: CaptureFixture[str],
                              tmp_path: Path) -> None:
    """Test that read() raises when loaded JSON fails validation."""
    cfg = LoadValidationConfig(stderr_file=sys.stderr)
    config_file = tmp_path / 'config.json'
    write_json_file(config_file, '{"value": 7}')
    with pytest.raises(InvalidConfiguration) as exc:
        cfg.read(config_file, stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert 'Value for value is not of type str' in str(exc.value)
    assert out == ''
    assert 'Value for value is not of type str' in err


def test_parse_json_validates(capsys: CaptureFixture[str]) -> None:
    """Test that explicit parse_json() validates parsed JSON."""
    cfg = LoadValidationConfig(stderr_file=sys.stderr)
    cfg.parse_json('{"value": "Beta"}', stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert cfg.value == 'BETA'
    assert cfg.validation_count() == 2
    assert out == ''
    assert err == ''


def test_init_file_validates_once(capsys: CaptureFixture[str],
                                  tmp_path: Path) -> None:
    """Test that from_json_filename validates without a duplicate pass."""
    config_file = tmp_path / 'config.json'
    write_json_file(config_file, '{"value": "Beta"}')
    cfg = LoadValidationConfig(from_json_filename=config_file,
                               stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert cfg.value == 'BETA'
    assert cfg.validation_count() == 1
    assert out == ''
    assert err == ''


def test_init_text_validates_once(capsys: CaptureFixture[str]) -> None:
    """Test that from_json_data_text validates without a duplicate pass."""
    cfg = LoadValidationConfig(from_json_data_text='{"value": "Beta"}',
                               stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert cfg.value == 'BETA'
    assert cfg.validation_count() == 1
    assert out == ''
    assert err == ''


def test_read_defaults_validate(capsys: CaptureFixture[str],
                                tmp_path: Path) -> None:
    """Test that read() validates when defaults fill omitted values."""
    cfg = LoadValidationConfig(stderr_file=sys.stderr)
    config_file = tmp_path / 'config.json'
    write_json_file(config_file, '{}')
    cfg.read(config_file, ok_to_use_defaults=True, stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert cfg.value == 'ALPHA'
    assert cfg.validation_count() == 2
    assert out == ''
    assert err == ''


@pytest.mark.parametrize(
    'validators, exc_type, message',
    [(None, TypeError, 'validators must be a sequence'),
     ([], ValueError, 'validators must be non-empty'),
     ([object()], TypeError, 'validators[0] must be a MemberValidator')])
def test_member_seq_init_bad_args(validators: object,
                                  exc_type: type[Exception],
                                  message: str) -> None:
    """Test constructor validation for MemberValidatorSequence."""
    with pytest.raises(exc_type) as exc:
        MemberValidatorSequence(validators)  # type: ignore[arg-type]
    assert message in str(exc.value)


def test_member_seq_copies() -> None:
    """Test that MemberValidatorSequence detaches the validator list."""
    validators: list[MemberValidator] = [IdentityValidator()]
    validator = MemberValidatorSequence(validators)
    validators.append(AppendTextValidator('!'))
    assert validator.validators == validators[:1]


def test_member_seq_applies_order(capsys: CaptureFixture[str]) -> None:
    """Test direct use of MemberValidatorSequence."""
    validator = MemberValidatorSequence(
        [UppercaseValidator(), AppendTextValidator('!')])
    assert_validate_member_ok(capsys, validator, 'alpha', 'ALPHA!')


def test_member_seq_integrates(capsys: CaptureFixture[str]) -> None:
    """Test MemberValidatorSequence through Config.validate()."""
    validator = MemberValidatorSequence(
        [UppercaseValidator(), AppendTextValidator('!')])
    cfg = SingleMemberValidationConfig('value', 'alpha', validator)
    out, err = capsys.readouterr()
    assert getattr(cfg, 'value') == 'ALPHA!'
    assert out == ''
    assert err == ''


@pytest.mark.parametrize(
    'min_value, max_value, allowed_values, exc_type, message',
    [(None, None, None, ValueError,
      'At least one of min_value, max_value, or allowed_values'),
     (None, None, 7, TypeError, 'allowed_values must be a sequence'),
     (None, None, [], ValueError, 'allowed_values must be a non-empty'),
     (3, 2, None, ValueError,
      'min_value must be less than or equal to max_value'),
     (True, None, None, TypeError,
      'IntFloatValidator only supports exact int or float values'),
     (1, 2.0, None, TypeError, 'max_value must be of type int'),
     (1, 5, 7, TypeError, 'allowed_values must be a sequence of int'),
     (None, 2.0, [1.0, 2
                  ], TypeError, 'allowed_values must be a sequence of float'),
     (None, None, lambda: [], ValueError,
      'allowed_values must be a non-empty'),
     (None, None, lambda: [1, 2.0], TypeError,
      'allowed_values must be a sequence of int'),
     (None, None, lambda: ['x'], TypeError,
      'IntFloatValidator only supports exact int or float values')])
def test_int_float_init_bad_limits(min_value: object, max_value: object,
                                   allowed_values: object,
                                   exc_type: type[Exception],
                                   message: str) -> None:
    """Test IntFloatValidator constructor validation."""
    allowed = allowed_values
    with pytest.raises(exc_type) as exc:
        IntFloatValidator(min_value=min_value,  # type: ignore[type-var]
                          max_value=max_value,
                          allowed_values=allowed)  # type: ignore[arg-type]
    assert message in str(exc.value)


@pytest.mark.parametrize(
    'validator, member_value, expected',
    [(IntFloatValidator(1, 5, None), 1, 1),
     (IntFloatValidator(0, 1, None), True, True),
     (IntFloatValidator(1, 5, [2, 3, 5]), 3, 3),
     (IntFloatValidator(None, 1.5, [0.5, 1.5]), 0.5, 0.5),
     (IntFloatValidator(None, None, [2.0]), 2.0, 2.0),
     (IntFloatValidator(None, None, lambda: [2, 4]), 4, 4),
     (IntFloatValidator(None, None, lambda: [2.0, 4.0]), 4.0, 4.0)])
def test_int_float_validator_ok(capsys: CaptureFixture[str],
                                validator: MemberValidator,
                                member_value: object,
                                expected: object) -> None:
    """Test OK cases of IntFloatValidator."""
    assert_validate_member_ok(capsys, validator, member_value, expected)


@pytest.mark.parametrize(
    'validator, member_value, exc_type, message',
    [(IntFloatValidator(1, 5, None), 1.0, InvalidConfiguration,
      'Value for value is not of type int'),
     (IntFloatValidator(1.0, 5.0, None), 1, InvalidConfiguration,
      'Value for value is not of type float'),
     (IntFloatValidator(2, None, None), 1, InvalidConfiguration,
      'Value 1 for value is less than minimum 2'),
     (IntFloatValidator(None, 3, None), 4, InvalidConfiguration,
      'Value 4 for value is greater than maximum 3'),
     (IntFloatValidator(1, 5, [2, 3]), 4, InvalidConfigurationValue,
      'Value 4 for value is not one of the allowed values')])
def test_int_float_rejects_values(capsys: CaptureFixture[str],
                                  validator: MemberValidator,
                                  member_value: object,
                                  exc_type: type[Exception],
                                  message: str) -> None:
    """Test IntFloatValidator failures for value type and constraints."""
    assert_validate_member_failure(capsys, validator, member_value, exc_type,
                                   message)


def test_int_float_allowed_range(capsys: CaptureFixture[str]) -> None:
    """Test that allowed values do not bypass range validation."""
    validator = IntFloatValidator(1, 5, [6])
    cfg = EmptyValidationConfig()
    with pytest.raises(InvalidConfiguration) as exc:
        validator.validate_member(cfg, 'value', 6, sys.stderr)
    out, err = capsys.readouterr()
    assert 'Value 6 for value is greater than maximum 5' in str(exc.value)
    assert out == ''
    assert 'Value 6 for value is greater than maximum 5' in err


def test_int_float_callable_infers(capsys: CaptureFixture[str]) -> None:
    """A callable supplies the numeric type when bounds do not."""
    calls: list[int] = []

    def current_allowed_values() -> Sequence[int]:
        """Return allowed values and record the call."""
        calls.append(len(calls))
        return [2, 3]

    validator = IntFloatValidator(None, None, current_allowed_values)
    assert calls == [0]
    assert_validate_member_ok(capsys, validator, 2, 2)
    assert calls == [0, 1]


def test_int_float_bounds_first(capsys: CaptureFixture[str]) -> None:
    """Bounds provide the numeric type without calling allowed_values."""
    calls: list[str] = []

    def current_allowed_values() -> Sequence[int]:
        """Return allowed values and record the call."""
        calls.append('validate')
        return [2, 3]

    validator = IntFloatValidator(1, 5, current_allowed_values)
    assert not calls
    assert_validate_member_ok(capsys, validator, 2, 2)
    assert calls == ['validate']


def test_int_float_dynamic_values(capsys: CaptureFixture[str]) -> None:
    """Every validation uses the callable's current allowed values."""
    allowed_values = [2, 3]

    def current_allowed_values() -> Sequence[int]:
        """Return the current allowed-values list."""
        return allowed_values

    validator = IntFloatValidator(None, None, current_allowed_values)
    assert_validate_member_ok(capsys, validator, 2, 2)
    allowed_values = [4, 5]
    assert_validate_member_failure(
        capsys, validator, 2, InvalidConfigurationValue,
        'Value 2 for value is not one of the allowed values')
    assert_validate_member_ok(capsys, validator, 4, 4)


@pytest.mark.parametrize(
    'allowed_values, exc_type, message',
    [([], ValueError, 'allowed_values must be a non-empty'),
     ([1.0], TypeError, 'allowed_values must be a sequence of int')])
def test_int_float_later_values(capsys: CaptureFixture[str],
                                allowed_values: Sequence[object],
                                exc_type: type[Exception],
                                message: str) -> None:
    """Dynamic allowed values must stay non-empty and type-compatible."""

    def current_allowed_values() -> Sequence[object]:
        """Return the parameterized allowed-values sequence."""
        return allowed_values

    allowed = current_allowed_values
    validator = IntFloatValidator(1, 5, allowed)  # type: ignore[arg-type]
    cfg = EmptyValidationConfig()
    with pytest.raises(exc_type) as exc:
        validator.validate_member(cfg, 'value', 2, sys.stderr)
    out, err = capsys.readouterr()
    assert message in str(exc.value)
    assert out == ''
    assert err == ''


def test_int_float_parsed_json(capsys: CaptureFixture[str]) -> None:
    """Test IntFloatValidator integration through Config.validate()."""
    cfg = SingleMemberValidationConfig('value', 2,
                                       IntFloatValidator(1, 5, [2, 3]),
                                       from_json_data_text='{"value": 3}')
    out, err = capsys.readouterr()
    assert getattr(cfg, 'value') == 3
    assert out == ''
    assert err == ''
