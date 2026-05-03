#! /usr/local/bin/python3
# mypy: disable-error-code="no-untyped-def,no-untyped-call"
"""Test the validation framework."""

# Copyright (c) 2024-2026 Tom Björkholm
# MIT License

from abc import ABCMeta
import sys
from io import StringIO
from typing import Any, Optional, Sequence, TextIO, cast
import pytest
from config_as_json.config import Config
from config_as_json.validator import IntFloatValidator, \
    InvalidConfiguration, InvalidConfigurationValue, StrValidator, \
    ValidationPlan, ValidationStep, MemberValidationStep, \
    WholeConfigValidationStep, MemberValidator, WholeConfigValidator, \
    ValueTypeValidator, CallingMemberValidator, \
    CallingWholeConfigValidator, MemberValidatorSequence, \
    not_one_of_allowed_values, string_best_match
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
                        stderr_file=sys.stderr) -> Optional[object]:
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
                        stderr_file=sys.stderr) -> Optional[object]:
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

    def validate(self, config: Config, stderr_file=sys.stderr) -> None:
        """Validate the whole config by mutating one member."""
        assert isinstance(config, ValidationOrderConfig)
        _ = stderr_file
        config.alias = config.alias + self._suffix


# pylint: disable-next=too-few-public-methods
class IdentityValidator(MemberValidator):
    """Return the validated member unchanged."""

    def validate_member(self, config: Config, member_name: str,
                        member_value: object,
                        stderr_file=sys.stderr) -> Optional[object]:
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
                        stderr_file=sys.stderr) -> Optional[object]:
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
                validator=WholeConfigSuffixValidator('!'))]


class MissingMemberConfig(Config):
    """Config class used to test validation of a missing member."""

    def __init__(self, stderr_file: TextIO) -> None:
        """Construct test config object."""
        self.value = 'alpha'
        super().__init__(from_json_data_text=None, from_json_filename=None,
                         stderr_file=stderr_file)

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Get validation plan for use when validating the Config object."""
        return [MemberValidationStep(member_names=['missing'],
                                     validator=IdentityValidator())]


class NoneWriteBackConfig(Config):
    """Config class used to test member write-back of None."""

    def __init__(self, stderr_file: TextIO) -> None:
        """Construct test config object."""
        self.value = 'alpha'
        super().__init__(from_json_data_text=None, from_json_filename=None,
                         stderr_file=stderr_file)

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Get validation plan for use when validating the Config object."""
        return [MemberValidationStep(member_names=['value'],
                                     validator=ReplaceWithNoneValidator())]


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
        return [
            MemberValidationStep(
                member_names=['shade'],
                validator=StrValidator(
                    ['red', 'green'], ignore_case=True,
                    normalize=True)),
            MemberValidationStep(
                member_names=['accent'],
                validator=StrValidator(
                    self.accent_names, ignore_case=False,
                    best_match=True))]


class MethodCallConfig(EmptyValidationConfig):
    """Config class with callable methods used by method-call validators."""

    def __init__(self, member_result: object = None,
                 whole_result: object = None) -> None:
        """Construct the config object and store configured method results."""
        self._member_result = member_result
        self._whole_result = whole_result
        self._member_calls: list[dict[str, object]] = []
        self._whole_calls: list[dict[str, object]] = []
        self.non_callable = 'not callable'
        super().__init__()

    def member_calls(self) -> list[dict[str, object]]:
        """Return recorded member-method calls."""
        return self._member_calls

    def whole_calls(self) -> list[dict[str, object]]:
        """Return recorded whole-config method calls."""
        return self._whole_calls

    def check_member(self, **kwargs: object) -> object:
        """Record a member validation call and return the configured result."""
        self._member_calls.append(kwargs)
        return self._member_result

    def normalize_member(self, value: object) -> object:
        """Return a normalized member value."""
        self._member_calls.append({'value': value})
        if value is None:
            return None
        return f'{value}-normalized'

    def check_whole_config(self, **kwargs: object) -> object:
        """Record a whole-config validation call."""
        self._whole_calls.append(kwargs)
        return self._whole_result

    def mutate_whole_config(self, suffix: str) -> object:
        """Mutate the config object and return the configured result."""
        self.value = self.value + suffix
        return self._whole_result


class MethodCallValidationConfig(Config):
    """Config class that uses method-call validators in its plan."""

    def __init__(self, from_json_data_text: Optional[str] = None,
                 stderr_file: TextIO = sys.stderr) -> None:
        """Construct a config object with method-call validation."""
        self.name = ' alpha '
        self.count = 2
        super().__init__(from_json_data_text=from_json_data_text,
                         from_json_filename=None, stderr_file=stderr_file)

    def normalize_name(self, value: object) -> object:
        """Normalize a name string."""
        if not isinstance(value, str):
            msg = 'Invalid configuration: name must be a string.'
            raise InvalidConfiguration(msg)
        return value.strip().upper()

    def check_count(self, value: object) -> Optional[bool]:
        """Check that the count is a positive integer."""
        if isinstance(value, int) and value > 0:
            return True
        return False

    def add_name_suffix(self, suffix: str) -> None:
        """Add a suffix to the normalized name."""
        self.name = self.name + suffix

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Get validation plan for use when validating the Config object."""
        _ = stderr_file
        name_validator = CallingMemberValidator(
            method_name='normalize_name', arg_name_value='value',
            normalizing=True)
        count_validator = CallingMemberValidator(
            method_name='check_count', arg_name_value='value')
        whole_config_validator = CallingWholeConfigValidator(
            method_name='add_name_suffix', other_args={'suffix': '!'})
        return [
            MemberValidationStep(member_names=['name'],
                                 validator=name_validator),
            MemberValidationStep(member_names=['count'],
                                 validator=count_validator),
            WholeConfigValidationStep(validator=whole_config_validator)]


# pylint: disable-next=too-few-public-methods
class AppendTextValidator(MemberValidator):
    """Append text to a string member."""

    def __init__(self, text: str) -> None:
        """Store the text to append."""
        self.text = text

    def validate_member(self, config: Config, member_name: str,
                        member_value: object,
                        stderr_file=sys.stderr) -> Optional[object]:
        """Validate one string member and append configured text."""
        _ = config
        _ = member_name
        _ = stderr_file
        assert isinstance(member_value, str)
        return member_value + self.text


@pytest.mark.parametrize('validator, member_value, expected',
                         [(StrValidator(['red', 'green'],
                                        ignore_case=False),
                           'red', 'red'),
                          (StrValidator(['red', 'green'],
                                        ignore_case=True),
                           'GREEN', 'GREEN'),
                          (StrValidator(['red', 'green'],
                                        ignore_case=True,
                                        normalize=True),
                           'GREEN', 'green'),
                          (StrValidator(['Alpha'],
                                        ignore_case=False,
                                        best_match=True),
                           'alpha', 'Alpha'),
                          (StrValidator(lambda: ['blue', 'black'],
                                        ignore_case=False,
                                        best_match=True),
                           'blu', 'blue')])
def test_str_validator_ok(capsys, validator, member_value, expected):
    """Test OK cases of StrValidator."""
    assert_validate_member_ok(capsys, validator, member_value, expected)


@pytest.mark.parametrize(
    'bad_value_type',
    [None, 'str', [str]])
def test_value_type_validator_init_rejects_non_type(bad_value_type):
    """Test ValueTypeValidator constructor validation."""
    with pytest.raises(TypeError) as exc:
        ValueTypeValidator(bad_value_type)
    assert 'value_type must be a type' in str(exc.value)


@pytest.mark.parametrize(
    'validator, member_value, expected',
    [(ValueTypeValidator(str), 'alpha', 'alpha'),
     (ValueTypeValidator(int), 3, 3),
     (ValueTypeValidator(int), True, True),
     (ValueTypeValidator(list), [1, 2], [1, 2])])
def test_value_type_validator_ok(capsys, validator, member_value, expected):
    """Test OK cases of ValueTypeValidator."""
    assert_validate_member_ok(capsys, validator, member_value, expected)


@pytest.mark.parametrize(
    'validator, member_value, message',
    [(ValueTypeValidator(str), 42, 'Value for value is not of type str'),
     (ValueTypeValidator(bool), 1, 'Value for value is not of type bool'),
     (ValueTypeValidator(list), (1, 2),
      'Value for value is not of type list')])
def test_value_type_validator_rejects_invalid_member_values(
        capsys, validator, member_value, message):
    """Test ValueTypeValidator failures."""
    assert_validate_member_failure(
        capsys, validator, member_value, InvalidConfiguration, message)


def test_value_type_validator_integration_uses_parsed_json(capsys):
    """Test ValueTypeValidator integration through Config.validate()."""
    cfg = SingleMemberValidationConfig(
        'value', 'alpha', ValueTypeValidator(str),
        from_json_data_text='{"value": "beta"}')
    out, err = capsys.readouterr()
    assert getattr(cfg, 'value') == 'beta'
    assert out == ''
    assert err == ''


def test_missing_get_validation_plan_raises(capsys):
    """Test that direct Config subclasses must implement a plan."""
    with pytest.raises(NotImplementedError) as exc:
        _ = ConfigMissingValidationPlan(stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert 'Config.get_validation_plan() must be implemented' in \
        str(exc.value)
    assert out == ''
    assert 'Config.get_validation_plan() must be implemented' in err


def test_validate_applies_member_and_whole_config_in_order(capsys):
    """Test that validation order and write-back work as documented."""
    cfg = ValidationOrderConfig(stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert cfg.name == 'ALPHA'
    assert cfg.alias == 'ALPHA:beta!'
    assert out == ''
    assert err == ''


def test_validate_missing_member_raises_attribute_error(capsys):
    """Test validation failure when a listed member does not exist."""
    with pytest.raises(AttributeError) as exc:
        _ = MissingMemberConfig(stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert 'Member missing not found in Config object' in str(exc.value)
    assert out == ''
    assert 'Member missing not found in Config object' in err


def test_validate_missing_member_uses_supplied_stderr_file(capsys):
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


def test_validate_member_can_write_back_none(capsys):
    """Test that a member validator can replace a member with None."""
    cfg = NoneWriteBackConfig(stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert cfg.value is None
    assert out == ''
    assert err == ''


def test_not_one_of_allowed_values_can_suppress_printing(capsys):
    """Test explicit suppression of printing in helper message builder."""
    ret = not_one_of_allowed_values('color', 'orange',
                                    ['red', 'green'], None)
    out, err = capsys.readouterr()
    assert 'Invalid configuration:' in ret
    assert 'orange' in ret
    assert out == ''
    assert err == ''


def test_string_best_match_rejects_invalid_value_type(capsys):
    """Test that string_best_match rejects non-string values."""
    with pytest.raises(InvalidConfiguration) as exc:
        string_best_match(cast(Any, 42), ['red', 'green'],
                          'value', sys.stderr)
    out, err = capsys.readouterr()
    assert 'Value for value is not a string.' in str(exc.value)
    assert out == ''
    assert 'Value for value is not a string.' in err


def test_validation_roles_and_step_base_class_are_abstract():
    """Test that validation role base classes cannot be instantiated."""
    whole_config_validator_class = cast(Any, WholeConfigValidator)
    member_validator_class = cast(Any, MemberValidator)
    validation_step_class = cast(Any, ValidationStep)
    with pytest.raises(TypeError):
        ABCMeta.__call__(whole_config_validator_class)
    with pytest.raises(TypeError):
        ABCMeta.__call__(member_validator_class)
    with pytest.raises(TypeError):
        ABCMeta.__call__(validation_step_class)


@pytest.mark.parametrize(
    'call, message',
    [(lambda cfg: WholeConfigValidator.validate(
        WholeConfigSuffixValidator('!'), cfg, sys.stderr),
      'WholeConfigValidator.validate() must be implemented'),
     (lambda cfg: MemberValidator.validate_member(
         IdentityValidator(), cfg, 'value', 'raw', sys.stderr),
      'MemberValidator.validate_member() must be implemented'),
     (lambda cfg: ValidationStep.apply(
         MemberValidationStep(['value'], IdentityValidator()),
         cfg, sys.stderr),
      'ValidationStep.apply() must be implemented')])
def test_validation_base_methods_report_not_implemented(
        capsys, call, message):
    """Test base validation methods when called directly."""
    cfg = EmptyValidationConfig()
    with pytest.raises(NotImplementedError) as exc:
        call(cfg)
    out, err = capsys.readouterr()
    assert message in str(exc.value)
    assert out == ''
    assert message in err


def test_str_validator_rejects_invalid_member_type(capsys):
    """Test that StrValidator rejects non-string values."""
    validator = StrValidator(['red', 'green'], ignore_case=False)
    assert_validate_member_failure(
        capsys, validator, 42, InvalidConfiguration,
        'Value for value is not a string.')


def test_str_validator_rejects_disallowed_value(capsys):
    """Test that StrValidator rejects unknown values."""
    validator = StrValidator(['red', 'green'], ignore_case=False)
    assert_validate_member_failure(
        capsys, validator, 'blue', InvalidConfigurationValue,
        'Value blue for value')


def test_str_validator_rejects_ambiguous_best_match(capsys):
    """Test that best-match validation rejects ambiguous prefixes."""
    validator = StrValidator(['blue', 'black'],
                             ignore_case=False,
                             best_match=True)
    assert_validate_member_failure(
        capsys, validator, 'bl', InvalidConfigurationValue,
        'Value bl for value')


def test_palette_config_uses_str_validator_on_default_values(capsys):
    """Test StrValidator integration in a derived config class."""
    cfg = PaletteConfig()
    out, err = capsys.readouterr()
    assert cfg.shade == 'green'
    assert cfg.accent == 'blue'
    assert out == ''
    assert err == ''


def test_palette_config_uses_str_validator_on_parsed_json(capsys):
    """Test StrValidator integration when values come from parsed JSON."""
    cfg = PaletteConfig(
        from_json_data_text='{"shade": "Red", "accent": "black"}')
    out, err = capsys.readouterr()
    assert cfg.shade == 'red'
    assert cfg.accent == 'black'
    assert out == ''
    assert err == ''


@pytest.mark.parametrize('kwargs, exc_type, message',
                         [({'method_name': 42,
                            'arg_name_value': 'value'}, TypeError,
                           'method_name must be a str'),
                          ({'method_name': '',
                            'arg_name_value': 'value'}, ValueError,
                           'method_name must be non-empty'),
                          ({'method_name': 'check_member',
                            'arg_name_value': ''}, ValueError,
                           'arg_name_value must be non-empty'),
                          ({'method_name': 'check_member',
                            'arg_name_value': 'value',
                            'arg_name_member_name': 42}, TypeError,
                           'arg_name_member_name must be a str'),
                          ({'method_name': 'check_member',
                            'arg_name_value': 'value',
                            'arg_name_member_name': ''}, ValueError,
                           'arg_name_member_name must be non-empty'),
                          ({'method_name': 'check_member',
                            'arg_name_value': 'value',
                            'other_args': []}, TypeError,
                           'other_args must be a mapping'),
                          ({'method_name': 'check_member',
                            'arg_name_value': 'value',
                            'other_args': {'': 1}}, ValueError,
                           'other_args key must be non-empty'),
                          ({'method_name': 'check_member',
                            'arg_name_value': 'value',
                            'normalizing': 'yes'}, TypeError,
                           'normalizing must be a bool'),
                          ({'method_name': 'check_member',
                            'arg_name_value': 'value',
                            'arg_name_member_name': 'value'}, ValueError,
                           'arg_name_member_name must differ '
                           'from arg_name_value'),
                          ({'method_name': 'check_member',
                            'arg_name_value': 'value',
                            'other_args': {'value': 1}}, ValueError,
                           "other_args must not contain generated argument "
                           "'value'"),
                          ({'method_name': 'check_member',
                            'arg_name_value': 'value',
                            'arg_name_member_name': 'member',
                            'other_args': {'member': 1}}, ValueError,
                           "other_args must not contain generated argument "
                           "'member'")])
def test_member_call_init_rejects_bad_args(kwargs, exc_type, message):
    """Test constructor validation for CallingMemberValidator."""
    with pytest.raises(exc_type) as exc:
        CallingMemberValidator(**cast(Any, kwargs))
    assert message in str(exc.value)


def test_calling_member_validator_init_copies_other_args():
    """Test that method-call validators detach stored extra arguments."""
    other_args = {'limit': 3}
    validator = CallingMemberValidator(method_name='check_member',
                                       arg_name_value='value',
                                       other_args=other_args)
    other_args['limit'] = 4
    assert validator.other_args == {'limit': 3}


@pytest.mark.parametrize('method_result', [None, True])
def test_member_call_validation_only_keeps_value(capsys, method_result):
    """Test validation-only member methods keep the original member value."""
    cfg = MethodCallConfig(member_result=method_result)
    validator = CallingMemberValidator(method_name='check_member',
                                       arg_name_value='value_arg',
                                       arg_name_member_name='member_arg',
                                       other_args={'limit': 3})
    result = validator.validate_member(cfg, 'value', 'raw', sys.stderr)
    out, err = capsys.readouterr()
    assert result == 'raw'
    assert cfg.member_calls() == [{
        'limit': 3,
        'value_arg': 'raw',
        'member_arg': 'value'
    }]
    assert out == ''
    assert err == ''


def test_member_call_validation_only_accepts_minimal_arguments(capsys):
    """Test validation-only member methods with only the value argument."""
    cfg = MethodCallConfig(member_result=True)
    validator = CallingMemberValidator(method_name='check_member',
                                       arg_name_value='value_arg')
    result = validator.validate_member(cfg, 'value', 'raw', sys.stderr)
    out, err = capsys.readouterr()
    assert result == 'raw'
    assert cfg.member_calls() == [{'value_arg': 'raw'}]
    assert out == ''
    assert err == ''


def test_calling_member_validator_normalizing_returns_method_value(capsys):
    """Test explicit normalizing mode writes back the method result."""
    cfg = MethodCallConfig()
    validator = CallingMemberValidator(method_name='normalize_member',
                                       arg_name_value='value',
                                       normalizing=True)
    result = validator.validate_member(cfg, 'value', 'raw', sys.stderr)
    out, err = capsys.readouterr()
    assert result == 'raw-normalized'
    assert cfg.member_calls() == [{'value': 'raw'}]
    assert out == ''
    assert err == ''


def test_calling_member_validator_normalizing_can_return_none(capsys):
    """Test that normalizing member methods may replace a value with None."""
    cfg = MethodCallConfig()
    validator = CallingMemberValidator(method_name='normalize_member',
                                       arg_name_value='value',
                                       normalizing=True)
    result = validator.validate_member(cfg, 'value', None, sys.stderr)
    out, err = capsys.readouterr()
    assert result is None
    assert cfg.member_calls() == [{'value': None}]
    assert out == ''
    assert err == ''


def test_calling_member_validator_rejects_false_return(capsys):
    """Test validation-only member methods reject False returns."""
    cfg = MethodCallConfig(member_result=False)
    validator = CallingMemberValidator(method_name='check_member',
                                       arg_name_value='value')
    with pytest.raises(InvalidConfiguration) as exc:
        validator.validate_member(cfg, 'value', 'raw', sys.stderr)
    out, err = capsys.readouterr()
    assert 'Method check_member returned False' in str(exc.value)
    assert out == ''
    assert 'Method check_member returned False' in err


def test_calling_member_validator_rejects_unexpected_return(capsys):
    """Test validation-only member methods reject surprising returns."""
    cfg = MethodCallConfig(member_result='valid')
    validator = CallingMemberValidator(method_name='check_member',
                                       arg_name_value='value')
    with pytest.raises(TypeError) as exc:
        validator.validate_member(cfg, 'value', 'raw', sys.stderr)
    out, err = capsys.readouterr()
    assert 'expected None, True, or False' in str(exc.value)
    assert out == ''
    assert 'expected None, True, or False' in err


@pytest.mark.parametrize('method_name, exc_type, message',
                         [('missing_method', AttributeError,
                           'Method missing_method not found in Config object'),
                          ('non_callable', TypeError,
                           'Method non_callable in Config object '
                           'is not callable')])
def test_member_call_rejects_method(capsys, method_name, exc_type, message):
    """Test method lookup failures in CallingMemberValidator."""
    cfg = MethodCallConfig()
    validator = CallingMemberValidator(method_name=method_name,
                                       arg_name_value='value')
    with pytest.raises(exc_type) as exc:
        validator.validate_member(cfg, 'value', 'raw', sys.stderr)
    out, err = capsys.readouterr()
    assert message in str(exc.value)
    assert out == ''
    assert message in err


@pytest.mark.parametrize('kwargs, exc_type, message',
                         [({'method_name': 42}, TypeError,
                           'method_name must be a str'),
                          ({'method_name': ''}, ValueError,
                           'method_name must be non-empty'),
                          ({'method_name': 'check_whole_config',
                            'other_args': []}, TypeError,
                           'other_args must be a mapping'),
                          ({'method_name': 'check_whole_config',
                            'other_args': {'': 1}}, ValueError,
                           'other_args key must be non-empty')])
def test_whole_call_init_rejects_bad_args(kwargs, exc_type, message):
    """Test constructor validation for CallingWholeConfigValidator."""
    with pytest.raises(exc_type) as exc:
        CallingWholeConfigValidator(**cast(Any, kwargs))
    assert message in str(exc.value)


def test_calling_whole_config_validator_calls_method(capsys):
    """Test whole-config method-call validation."""
    cfg = MethodCallConfig(whole_result=True)
    validator = CallingWholeConfigValidator(method_name='check_whole_config',
                                            other_args={'profile': 'fast'})
    validator.validate(cfg, sys.stderr)
    out, err = capsys.readouterr()
    assert cfg.whole_calls() == [{'profile': 'fast'}]
    assert out == ''
    assert err == ''


def test_calling_whole_config_validator_allows_mutation(capsys):
    """Test whole-config method-call validation may mutate config."""
    cfg = MethodCallConfig(whole_result=None)
    validator = CallingWholeConfigValidator(method_name='mutate_whole_config',
                                            other_args={'suffix': '!'})
    validator.validate(cfg, sys.stderr)
    out, err = capsys.readouterr()
    assert cfg.value == 'seed!'
    assert out == ''
    assert err == ''


def test_calling_whole_config_validator_rejects_false_return(capsys):
    """Test whole-config method-call validation rejects False returns."""
    cfg = MethodCallConfig(whole_result=False)
    validator = CallingWholeConfigValidator(method_name='check_whole_config')
    with pytest.raises(InvalidConfiguration) as exc:
        validator.validate(cfg, sys.stderr)
    out, err = capsys.readouterr()
    assert 'Method check_whole_config returned False' in str(exc.value)
    assert out == ''
    assert 'Method check_whole_config returned False' in err


def test_calling_whole_config_validator_rejects_unexpected_return(capsys):
    """Test whole-config method-call validation rejects surprising returns."""
    cfg = MethodCallConfig(whole_result='valid')
    validator = CallingWholeConfigValidator(method_name='check_whole_config')
    with pytest.raises(TypeError) as exc:
        validator.validate(cfg, sys.stderr)
    out, err = capsys.readouterr()
    assert 'expected None, True, or False' in str(exc.value)
    assert out == ''
    assert 'expected None, True, or False' in err


def test_method_call_validators_integrate_with_config(capsys):
    """Test method-call validators through Config.validate()."""
    cfg = MethodCallValidationConfig(
        from_json_data_text='{"name": " beta ", "count": 3}')
    out, err = capsys.readouterr()
    assert cfg.name == 'BETA!'
    assert cfg.count == 3
    assert out == ''
    assert err == ''


def test_method_call_validators_reject_invalid_config(capsys):
    """Test method-call validators reject invalid parsed config."""
    with pytest.raises(InvalidConfiguration) as exc:
        MethodCallValidationConfig(
            from_json_data_text='{"name": " beta ", "count": 0}',
            stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert 'Method check_count returned False' in str(exc.value)
    assert out == ''
    assert 'Method check_count returned False' in err


@pytest.mark.parametrize('validators, exc_type, message',
                         [(None, TypeError, 'validators must be a sequence'),
                          ([], ValueError, 'validators must be non-empty'),
                          ([object()], TypeError,
                           'validators[0] must be a MemberValidator')])
def test_member_sequence_init_rejects_bad_args(validators, exc_type, message):
    """Test constructor validation for MemberValidatorSequence."""
    with pytest.raises(exc_type) as exc:
        MemberValidatorSequence(cast(Any, validators))
    assert message in str(exc.value)


def test_member_validator_sequence_copies_validators() -> None:
    """Test that MemberValidatorSequence detaches the validator list."""
    validators: list[MemberValidator] = [IdentityValidator()]
    validator = MemberValidatorSequence(validators)
    validators.append(AppendTextValidator('!'))
    assert validator.validators == validators[:1]


def test_member_validator_sequence_applies_validators_in_order(capsys):
    """Test direct use of MemberValidatorSequence."""
    validator = MemberValidatorSequence([UppercaseValidator(),
                                         AppendTextValidator('!')])
    assert_validate_member_ok(capsys, validator, 'alpha', 'ALPHA!')


def test_member_validator_sequence_integrates_with_config(capsys):
    """Test MemberValidatorSequence through Config.validate()."""
    validator = MemberValidatorSequence([UppercaseValidator(),
                                         AppendTextValidator('!')])
    cfg = SingleMemberValidationConfig('value', 'alpha', validator)
    out, err = capsys.readouterr()
    assert getattr(cfg, 'value') == 'ALPHA!'
    assert out == ''
    assert err == ''


@pytest.mark.parametrize(
    'min_value, max_value, allowed_values, exc_type, message',
    [(None, None, None, ValueError,
      'At least one of min_value, max_value, or allowed_values'),
     (None, None, [], ValueError, 'allowed_values must be a non-empty'),
     (3, 2, None, ValueError,
      'min_value must be less than or equal to max_value'),
     (True, None, None, TypeError,
      'IntFloatValidator only supports exact int or float values'),
     (1, 2.0, None, TypeError, 'max_value must be of type int'),
     (None, 2.0, [1.0, 2], TypeError,
      'allowed_values must be a sequence of float')])
def test_int_float_validator_init_rejects_invalid_constraints(
        min_value, max_value, allowed_values, exc_type, message):
    """Test IntFloatValidator constructor validation."""
    with pytest.raises(exc_type) as exc:
        IntFloatValidator(min_value=min_value, max_value=max_value,
                          allowed_values=allowed_values)
    assert message in str(exc.value)


@pytest.mark.parametrize('validator, member_value, expected',
                         [(IntFloatValidator(1, 5, None), 1, 1),
                          (IntFloatValidator(0, 1, None), True, True),
                          (IntFloatValidator(1, 5, [2, 3, 5]), 3, 3),
                          (IntFloatValidator(None, 1.5, [0.5, 1.5]),
                           0.5, 0.5),
                          (IntFloatValidator(None, None, [2.0]), 2.0, 2.0)])
def test_int_float_validator_ok(capsys, validator, member_value, expected):
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
def test_int_float_validator_rejects_invalid_member_values(
        capsys, validator, member_value, exc_type, message):
    """Test IntFloatValidator failures for value type and constraints."""
    assert_validate_member_failure(
        capsys, validator, member_value, exc_type, message)


def test_int_float_validator_requires_allowed_value_to_be_in_range(capsys):
    """Test that allowed values do not bypass range validation."""
    validator = IntFloatValidator(1, 5, [6])
    cfg = EmptyValidationConfig()
    with pytest.raises(InvalidConfiguration) as exc:
        validator.validate_member(cfg, 'value', 6, sys.stderr)
    out, err = capsys.readouterr()
    assert 'Value 6 for value is greater than maximum 5' in str(exc.value)
    assert out == ''
    assert 'Value 6 for value is greater than maximum 5' in err


def test_int_float_validator_integration_uses_parsed_json(capsys):
    """Test IntFloatValidator integration through Config.validate()."""
    cfg = SingleMemberValidationConfig(
        'value', 2, IntFloatValidator(1, 5, [2, 3]),
        from_json_data_text='{"value": 3}')
    out, err = capsys.readouterr()
    assert getattr(cfg, 'value') == 3
    assert out == ''
    assert err == ''
