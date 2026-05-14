#! /usr/local/bin/python3
"""Test validators for dictionary-shaped member views."""

# Copyright (c) 2026 Tom Björkholm
# MIT License

import sys
from collections.abc import Hashable
from typing import Optional, TextIO
import pytest
from pytest import CaptureFixture
from config_as_json import AsDictViewValidator as PublicAsDictViewValidator
from config_as_json import public_attrs_to_dict as public_public_attrs
from config_as_json.as_dict_view_validator import AsDictViewValidator, \
    public_attrs_to_dict
from config_as_json.config import Config
from config_as_json.dict_validators import DictForEachValidator, \
    DictKeysValidator, DictRule
from config_as_json.validator import InvalidConfiguration, \
    InvalidConfigurationValue, MemberValidationStep, MemberValidator, \
    StrValidator, ValidationPlan
from .validator_test_helpers import EmptyValidationConfig, \
    SingleMemberValidationConfig, assert_validate_member_failure, \
    assert_validate_member_ok


# pylint: disable-next=too-few-public-methods
class _Settings:
    """Application-defined settings object used by tests."""

    def __init__(self, mode: str = 'FAST', count: int = 2) -> None:
        """Initialize the settings object."""
        self.mode: str = mode
        self.count: int = count
        self.values: list[int] = [1, 2]
        self._secret: str = 'hidden'

    def helper(self) -> str:
        """Return a helper value that must not be part of the dict view."""
        return 'helper'


class _DictSubclass(dict[str, object]):
    """Small dict subclass used to document ``isinstance`` behavior."""


# pylint: disable-next=too-few-public-methods
class _NoDictSlots:
    """Object that cannot be projected with ``vars()``."""

    __slots__ = ('mode', )

    def __init__(self) -> None:
        """Initialize the slotted object."""
        self.mode = 'FAST'


# pylint: disable-next=too-few-public-methods
class _ProjectionRecorder:
    """Recorder whose method projects settings to a fixed dictionary."""

    def __init__(self) -> None:
        """Initialize the call recording."""
        self.calls: list[tuple[Config, str, object, TextIO]] = []

    def project(self, config: Config, member_name: str, member_value: object,
                stderr_file: TextIO) -> dict[Hashable, object]:
        """Record one projection call and return a valid settings view."""
        self.calls.append((config, member_name, member_value, stderr_file))
        return {'mode': 'slow'}


# pylint: disable-next=too-few-public-methods
class _WholeDictReplacementValidator(MemberValidator):
    """Whole-dict validator used to assert validation order."""

    def __init__(self, recording: list[tuple[str, str, object]]) -> None:
        """Store the recording destination."""
        self.recording: list[tuple[str, str, object]] = recording

    def validate_member(self, config: Config, member_name: str,
                        member_value: object,
                        stderr_file: TextIO = sys.stderr) -> Optional[object]:
        """Record one validation call and return a replacement dict."""
        _ = config, stderr_file
        self.recording.append(('whole', member_name, member_value))
        return {'mode': 'SLOW', 'count': 4}


# pylint: disable-next=too-few-public-methods
class _BadDictValidator(MemberValidator):
    """Validator that returns a non-dict value."""

    def validate_member(self, config: Config, member_name: str,
                        member_value: object,
                        stderr_file: TextIO = sys.stderr) -> Optional[object]:
        """Return a value that is not a dictionary."""
        _ = config, member_name, member_value, stderr_file
        return 'not-a-dict'


def _project_to_list(config: Config, member_name: str, member_value: object,
                     stderr_file: TextIO) -> object:
    """Return a non-dict projection for rejection tests."""
    _ = config, member_name, member_value, stderr_file
    return ['mode', 'fast']


class AsDictConfig(Config):
    """Config class used for integration tests."""

    def __init__(self, validator: MemberValidator, member_value: object,
                 from_json_data_text: Optional[str] = None) -> None:
        """Construct one config object with an injected member validator."""
        self._validator = validator
        self.settings = member_value
        super().__init__(from_json_data_text=from_json_data_text,
                         from_json_filename=None, stderr_file=sys.stderr)

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Get the validation plan for this test config."""
        _ = stderr_file
        return [MemberValidationStep(member_names=['settings'],
                                     validator=self._validator)]


def _mode_rule() -> DictRule:
    """Return a rule that validates and normalizes the ``mode`` key."""
    return DictRule(keys=['mode'], validators=[
        StrValidator(allowed_values=['fast', 'slow'], ignore_case=True,
                     normalize=True)])


def _mode_validator() -> AsDictViewValidator:
    """Return a validator for a settings object or dict."""
    return AsDictViewValidator(non_dict_type=_Settings, rules=[_mode_rule()],
                               to_dict=public_attrs_to_dict,
                               validators=[DictKeysValidator(
                                   mandatory_keys=['mode'],
                                   allow_extra_dict_keys=True)])


def _validate_public_attrs(member_value: object, capsys: CaptureFixture[str]) \
        -> dict[Hashable, object]:
    """Project public attributes and assert no diagnostics were printed."""
    cfg = EmptyValidationConfig()
    result: dict[Hashable, object] = public_attrs_to_dict(
        cfg, 'value', member_value, sys.stderr)
    out, err = capsys.readouterr()
    assert out == ''
    assert err == ''
    return result


def test_as_dict_view_exports() -> None:
    """The public package exports the as-dict-view helpers."""
    assert PublicAsDictViewValidator is AsDictViewValidator
    assert public_public_attrs is public_attrs_to_dict


def test_public_attrs_filters(capsys: CaptureFixture[str]) -> None:
    """The helper projects public non-callable attributes only."""
    settings = _Settings()
    projected = _validate_public_attrs(settings, capsys)
    assert projected == {'mode': 'FAST', 'count': 2, 'values': [1, 2]}
    assert projected['values'] is settings.values


def test_public_attrs_rejects_slots(capsys: CaptureFixture[str]) -> None:
    """The helper reports a clear error when ``vars()`` is not available."""
    cfg = EmptyValidationConfig()
    with pytest.raises(InvalidConfiguration) as exc:
        public_attrs_to_dict(cfg, 'value', _NoDictSlots(), sys.stderr)
    out, err = capsys.readouterr()
    assert 'cannot be projected to a dict from public attributes' in str(
        exc.value)
    assert out == ''
    assert 'cannot be projected to a dict from public attributes' in err


@pytest.mark.parametrize(
    'non_dict_type, rules, to_dict, validators, exc_type, message',
    [(object(), [_mode_rule()], public_attrs_to_dict, None, TypeError,
      'non_dict_type must be a type'),
     (dict, [_mode_rule()], public_attrs_to_dict, None, TypeError,
      'non_dict_type may not be dict or a dict subclass'),
     (_DictSubclass, [_mode_rule()], public_attrs_to_dict, None, TypeError,
      'non_dict_type may not be dict or a dict subclass'),
     (_Settings, None, public_attrs_to_dict, None, TypeError,
      'rules must be a sequence'),
     (_Settings, [object()], public_attrs_to_dict, None, TypeError,
      'rules[0] must be a DictRule'),
     (_Settings, [_mode_rule()], object(), None, TypeError,
      'to_dict must be callable'),
     (_Settings, [_mode_rule()], public_attrs_to_dict, object(), TypeError,
      'validators must be None or a sequence'),
     (_Settings, [_mode_rule()], public_attrs_to_dict, [object()],
      TypeError, 'validators[0] must be a MemberValidator'),
     (_Settings, [], public_attrs_to_dict, None, ValueError,
      'rules must be non-empty when validators is None or empty'),
     (_Settings, [], public_attrs_to_dict, [], ValueError,
      'rules must be non-empty when validators is None or empty')])
# pylint: disable-next=too-many-arguments,too-many-positional-arguments
def test_as_dict_view_init_rejects(
        non_dict_type: object, rules: object, to_dict: object,
        validators: object, exc_type: type[Exception], message: str) -> None:
    """Constructor arguments are validated before use."""
    with pytest.raises(exc_type) as exc:
        AsDictViewValidator(
            non_dict_type=non_dict_type,  # type: ignore[arg-type]
            rules=rules,  # type: ignore[arg-type]
            to_dict=to_dict,  # type: ignore[arg-type]
            validators=validators)  # type: ignore[arg-type]
    assert message in str(exc.value)


def test_as_dict_view_init_stores() -> None:
    """Constructor arguments are copied to the validator."""
    rule = _mode_rule()
    key_validator = DictKeysValidator(['mode'], allow_extra_dict_keys=True)
    validator = AsDictViewValidator(non_dict_type=_Settings, rules=[rule],
                                    to_dict=public_attrs_to_dict,
                                    validators=[key_validator])
    assert validator.non_dict_type is _Settings
    assert validator.rules == [rule]
    assert validator.to_dict is public_attrs_to_dict
    assert validator.validators[0] is key_validator
    assert isinstance(validator.validators[1], DictForEachValidator)
    assert validator.validators[1].rules == [rule]


def test_as_dict_view_empty_rules(capsys: CaptureFixture[str]) -> None:
    """Rules may be empty when a whole-dict validator is supplied."""
    validator = AsDictViewValidator(
        non_dict_type=_Settings, rules=[], to_dict=public_attrs_to_dict,
        validators=[DictKeysValidator(['mode'], allow_extra_dict_keys=True)])
    settings = {'mode': 'FAST', 'extra': 1}
    assert_validate_member_ok(capsys, validator, settings, settings)


def test_as_dict_view_normalizes(capsys: CaptureFixture[str]) -> None:
    """A real dict input returns the normalized dictionary."""
    member_value = {'mode': 'FAST', 'count': 2}
    assert_validate_member_ok(capsys, _mode_validator(), member_value,
                              {'mode': 'fast', 'count': 2})
    assert member_value == {'mode': 'FAST', 'count': 2}


def test_as_dict_view_dict_subclass(capsys: CaptureFixture[str]) \
        -> None:
    """Dict subclasses are accepted through ``isinstance(value, dict)``."""
    member_value = _DictSubclass({'mode': 'SLOW', 'count': 2})
    assert_validate_member_ok(capsys, _mode_validator(), member_value,
                              {'mode': 'slow', 'count': 2})


def test_as_dict_view_keeps_object(capsys: CaptureFixture[str]) -> None:
    """A non-dict object is validated through a projected dict view."""
    settings = _Settings(mode='FAST')
    cfg = EmptyValidationConfig()
    result = _mode_validator().validate_member(cfg, 'value', settings,
                                               sys.stderr)
    out, err = capsys.readouterr()
    assert result is settings
    assert settings.mode == 'FAST'
    assert out == ''
    assert err == ''


def test_as_dict_view_projector_args(capsys: CaptureFixture[str]) -> None:
    """The projector receives config, member name, value, and diagnostics."""
    settings = _Settings(mode='slow')
    recorder = _ProjectionRecorder()
    validator = AsDictViewValidator(non_dict_type=_Settings,
                                    rules=[_mode_rule()],
                                    to_dict=recorder.project)
    cfg = EmptyValidationConfig()
    result = validator.validate_member(cfg, 'value', settings, sys.stderr)
    out, err = capsys.readouterr()
    assert result is settings
    assert recorder.calls == [(cfg, 'value', settings, sys.stderr)]
    assert out == ''
    assert err == ''


def test_as_dict_view_order(capsys: CaptureFixture[str]) -> None:
    """Whole-dict validators run before per-key rules."""
    recording: list[tuple[str, str, object]] = []
    validator = AsDictViewValidator(
        non_dict_type=_Settings, rules=[_mode_rule()],
        to_dict=public_attrs_to_dict,
        validators=[_WholeDictReplacementValidator(recording)])
    assert_validate_member_ok(capsys, validator, {'mode': 'FAST'},
                              {'mode': 'slow', 'count': 4})
    assert recording == [('whole', 'value', {'mode': 'FAST'})]


def test_as_dict_view_rejects_type(capsys: CaptureFixture[str]) -> None:
    """Reject values that are neither dict nor the configured object type."""
    assert_validate_member_failure(capsys, _mode_validator(), ['mode', 'fast'],
                                   InvalidConfiguration,
                                   'Value for value is not a dict or '
                                   '_Settings')


def test_as_dict_view_rejects_proj(capsys: CaptureFixture[str]) -> None:
    """Reject projector results that are not dictionaries."""
    proj = _project_to_list
    validator = AsDictViewValidator(non_dict_type=_Settings,
                                    rules=[_mode_rule()],
                                    to_dict=proj)  # type: ignore[arg-type]
    assert_validate_member_failure(capsys, validator, _Settings(),
                                   InvalidConfiguration,
                                   'Dictionary view for value is not a dict')


def test_as_dict_view_reject_valid(capsys: CaptureFixture[str]) -> None:
    """Reject whole-dict validator results that are not dictionaries."""
    validator = AsDictViewValidator(non_dict_type=_Settings,
                                    rules=[_mode_rule()],
                                    to_dict=public_attrs_to_dict,
                                    validators=[_BadDictValidator()])
    assert_validate_member_failure(capsys, validator, {'mode': 'FAST'},
                                   InvalidConfiguration,
                                   'Dictionary view for value is not a dict')


def test_as_dict_view_rule_failure(capsys: CaptureFixture[str]) -> None:
    """Failures from per-key validators keep the inner key name."""
    assert_validate_member_failure(capsys, _mode_validator(),
                                   {'mode': 'invalid'},
                                   InvalidConfigurationValue,
                                   'Value invalid for value[mode] is not one '
                                   'of the allowed values')


def test_as_dict_view_config_dict() -> None:
    """Validation through Config stores normalized dict inputs."""
    config = SingleMemberValidationConfig('settings', {'mode': 'FAST'},
                                          _mode_validator())
    assert getattr(config, 'settings') == {'mode': 'fast'}


def test_as_dict_view_config_object() -> None:
    """Validation through Config keeps object inputs as objects."""
    settings = _Settings(mode='FAST')
    config = AsDictConfig(_mode_validator(), settings)
    assert config.settings is settings
    assert settings.mode == 'FAST'
