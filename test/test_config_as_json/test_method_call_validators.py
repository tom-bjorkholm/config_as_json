#! /usr/local/bin/python3
"""Test validators that call methods on Config objects."""

# Copyright (c) 2024-2026 Tom Björkholm
# MIT License

import sys
from typing import Optional, TextIO
import pytest
from pytest import CaptureFixture
from config_as_json.config import Config
from config_as_json.validator import CallingMemberValidator, \
    CallingWholeConfigValidator, InvalidConfiguration, MemberValidationStep, \
    ValidationPlan, WholeConfigValidationStep
from .validator_test_helpers import EmptyValidationConfig


class MethodCallConfig(EmptyValidationConfig):
    """Config class with callable methods used by method-call validators."""

    def __init__(self, member_result: object = None,
                 whole_result: object = None,
                 member_name: Optional[str] = None) -> None:
        """Construct the config object and store configured method results."""
        self._member_result = member_result
        self._whole_result = whole_result
        self._member_calls: list[dict[str, object]] = []
        self._whole_calls: list[dict[str, object]] = []
        self.non_callable = 'not callable'
        super().__init__(member_name=member_name)

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
                 stderr_file: TextIO = sys.stderr,
                 member_name: Optional[str] = None) -> None:
        """Construct a config object with method-call validation."""
        self.name = ' alpha '
        self.count = 2
        super().__init__(from_json_data_text=from_json_data_text,
                         from_json_filename=None, stderr_file=stderr_file,
                         member_name=member_name)

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
        name_validator = CallingMemberValidator(method_name='normalize_name',
                                                arg_name_value='value',
                                                normalizing=True)
        count_validator = CallingMemberValidator(method_name='check_count',
                                                 arg_name_value='value')
        whole_config_validator = CallingWholeConfigValidator(
            method_name='add_name_suffix', other_args={'suffix': '!'})
        return [
            MemberValidationStep(member_names=['name'],
                                 validator=name_validator),
            MemberValidationStep(member_names=['count'],
                                 validator=count_validator),
            WholeConfigValidationStep(validator=whole_config_validator)
        ]


@pytest.mark.parametrize(
    'kwargs, exc_type, message',
    [({'method_name': 42, 'arg_name_value': 'value'},
      TypeError, 'method_name must be a str'),
     ({'method_name': '', 'arg_name_value': 'value'},
      ValueError, 'method_name must be non-empty'),
     ({'method_name': 'check_member', 'arg_name_value': ''},
      ValueError, 'arg_name_value must be non-empty'),
     ({'method_name': 'check_member', 'arg_name_value': 'value',
       'arg_name_member_name': 42},
      TypeError, 'arg_name_member_name must be a str'),
     ({'method_name': 'check_member', 'arg_name_value': 'value',
       'arg_name_member_name': ''},
      ValueError, 'arg_name_member_name must be non-empty'),
     ({'method_name': 'check_member', 'arg_name_value': 'value',
       'other_args': []},
      TypeError, 'other_args must be a mapping'),
     ({'method_name': 'check_member', 'arg_name_value': 'value',
       'other_args': {'': 1}},
      ValueError, 'other_args key must be non-empty'),
     ({'method_name': 'check_member', 'arg_name_value': 'value',
       'normalizing': 'yes'},
      TypeError, 'normalizing must be a bool'),
     ({'method_name': 'check_member', 'arg_name_value': 'value',
       'arg_name_member_name': 'value'},
      ValueError, 'arg_name_member_name must differ from arg_name_value'),
     ({'method_name': 'check_member', 'arg_name_value': 'value',
       'other_args': {'value': 1}},
      ValueError, "other_args must not contain generated argument 'value'"),
     ({'method_name': 'check_member', 'arg_name_value': 'value',
       'arg_name_member_name': 'member', 'other_args': {'member': 1}},
      ValueError, "other_args must not contain generated argument 'member'")])
def test_member_call_init_bad_args(kwargs: dict[str, object],
                                   exc_type: type[Exception],
                                   message: str) -> None:
    """Test constructor validation for CallingMemberValidator."""
    with pytest.raises(exc_type) as exc:
        CallingMemberValidator(**kwargs)  # type: ignore[arg-type]
    assert message in str(exc.value)


def test_member_call_copies_args() -> None:
    """Test that method-call validators detach stored extra arguments."""
    other_args: dict[str, object] = {'limit': 3}
    validator = CallingMemberValidator(method_name='check_member',
                                       arg_name_value='value',
                                       other_args=other_args)
    other_args['limit'] = 4
    assert validator.other_args == {'limit': 3}


@pytest.mark.parametrize('method_result', [None, True])
def test_member_call_keeps_value(capsys: CaptureFixture[str],
                                 method_result: Optional[bool]) -> None:
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


def test_member_call_min_args(capsys: CaptureFixture[str]) -> None:
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


def test_member_call_normalizes(capsys: CaptureFixture[str]) -> None:
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


def test_member_call_normalizes_none(capsys: CaptureFixture[str]) -> None:
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


def test_member_call_rejects_false(capsys: CaptureFixture[str]) -> None:
    """Test validation-only member methods reject False returns."""
    cfg = MethodCallConfig(member_result=False)
    validator = CallingMemberValidator(method_name='check_member',
                                       arg_name_value='value')
    with pytest.raises(InvalidConfiguration) as exc:
        validator.validate_member(cfg, 'value', 'raw', sys.stderr)
    out, err = capsys.readouterr()
    assert 'Method check_member for value returned False' in str(exc.value)
    assert out == ''
    assert 'Method check_member for value returned False' in err


def test_member_call_rejects_other(capsys: CaptureFixture[str]) -> None:
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


@pytest.mark.parametrize(
    'method_name, exc_type, message',
    [('missing_method', AttributeError,
      'Method missing_method for value not found in Config object'),
     ('non_callable', TypeError, 'Method non_callable for value in Config '
      'object is not callable')])
def test_member_call_rejects_method(capsys: CaptureFixture[str],
                                    method_name: str,
                                    exc_type: type[Exception],
                                    message: str) -> None:
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


@pytest.mark.parametrize(
    'kwargs, exc_type, message',
    [({'method_name': 42}, TypeError, 'method_name must be a str'),
     ({'method_name': ''}, ValueError, 'method_name must be non-empty'),
     ({'method_name': 'check_whole_config', 'other_args': []},
      TypeError, 'other_args must be a mapping'),
     ({'method_name': 'check_whole_config', 'other_args': {'': 1}},
      ValueError, 'other_args key must be non-empty')])
def test_whole_call_init_bad_args(kwargs: dict[str, object],
                                  exc_type: type[Exception],
                                  message: str) -> None:
    """Test constructor validation for CallingWholeConfigValidator."""
    with pytest.raises(exc_type) as exc:
        CallingWholeConfigValidator(**kwargs)  # type: ignore[arg-type]
    assert message in str(exc.value)


def test_whole_call_calls_method(capsys: CaptureFixture[str]) -> None:
    """Test whole-config method-call validation."""
    cfg = MethodCallConfig(whole_result=True)
    validator = CallingWholeConfigValidator(method_name='check_whole_config',
                                            other_args={'profile': 'fast'})
    validator.validate(cfg, sys.stderr, member_name=None)
    out, err = capsys.readouterr()
    assert cfg.whole_calls() == [{'profile': 'fast'}]
    assert out == ''
    assert err == ''


def test_whole_call_allows_mutation(capsys: CaptureFixture[str]) -> None:
    """Test whole-config method-call validation may mutate config."""
    cfg = MethodCallConfig(whole_result=None)
    validator = CallingWholeConfigValidator(method_name='mutate_whole_config',
                                            other_args={'suffix': '!'})
    validator.validate(cfg, sys.stderr, member_name=None)
    out, err = capsys.readouterr()
    assert cfg.value == 'seed!'
    assert out == ''
    assert err == ''


def test_whole_call_rejects_false(capsys: CaptureFixture[str]) -> None:
    """Test whole-config method-call validation rejects False returns."""
    cfg = MethodCallConfig(whole_result=False)
    validator = CallingWholeConfigValidator(method_name='check_whole_config')
    with pytest.raises(InvalidConfiguration) as exc:
        validator.validate(cfg, sys.stderr, member_name=None)
    out, err = capsys.readouterr()
    assert 'Method check_whole_config returned False' in str(exc.value)
    assert out == ''
    assert 'Method check_whole_config returned False' in err


def test_whole_call_rejects_other(capsys: CaptureFixture[str]) -> None:
    """Test whole-config method-call validation rejects surprising returns."""
    cfg = MethodCallConfig(whole_result='valid')
    validator = CallingWholeConfigValidator(method_name='check_whole_config')
    with pytest.raises(TypeError) as exc:
        validator.validate(cfg, sys.stderr, member_name=None)
    out, err = capsys.readouterr()
    assert 'expected None, True, or False' in str(exc.value)
    assert out == ''
    assert 'expected None, True, or False' in err


def test_method_calls_integrate(capsys: CaptureFixture[str]) -> None:
    """Test method-call validators through Config.validate()."""
    cfg = MethodCallValidationConfig(
        from_json_data_text='{"name": " beta ", "count": 3}')
    out, err = capsys.readouterr()
    assert cfg.name == 'BETA!'
    assert cfg.count == 3
    assert out == ''
    assert err == ''


def test_method_calls_reject_config(capsys: CaptureFixture[str]) -> None:
    """Test method-call validators reject invalid parsed config."""
    with pytest.raises(InvalidConfiguration) as exc:
        MethodCallValidationConfig(
            from_json_data_text='{"name": " beta ", "count": 0}',
            stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert 'Method check_count for count returned False' in str(exc.value)
    assert out == ''
    assert 'Method check_count for count returned False' in err
