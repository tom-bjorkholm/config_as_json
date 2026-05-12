#! /usr/local/bin/python3
"""Test declaration rules for DICT_VALUE_BY_KEY nesting."""

# Copyright (c) 2026 Tom Björkholm
# MIT License

import sys
from tempfile import TemporaryDirectory
from typing import Optional, TextIO, cast
import pytest
from pytest import CaptureFixture
from config_as_json.config import Config
from config_as_json.config_nesting import ConfigNesting, ConfigNestingKind, \
    NestedConfigs
from config_as_json.validator import ValidationPlan
from .test_config_2 import BadNestedParentConfig, NestedOutputConfig
from .test_nested_config import AuditSection, ReportByKeyConfig, ReportSection


def _by_key_nesting(key: Optional[str]) -> ConfigNesting:
    """Return one DICT_VALUE_BY_KEY declaration."""
    return ConfigNesting(kind=ConfigNestingKind.DICT_VALUE_BY_KEY,
                         config_type=NestedOutputConfig, discriminator_key=key)


def _plain_nesting(kind: ConfigNestingKind) -> ConfigNesting:
    """Return one non-keyed declaration."""
    return ConfigNesting(kind=kind, config_type=NestedOutputConfig)


class ShapeParentConfig(Config):
    """Parent config used for valid declaration-shape tests."""

    def __init__(self, nested_configs: NestedConfigs, child_value: object,
                 stderr_file: TextIO = sys.stderr) -> None:
        """Construct a parent with caller supplied nested declarations."""
        self.child = child_value
        self._nested_configs: NestedConfigs = nested_configs
        super().__init__(from_json_data_text=None, from_json_filename=None,
                         stderr_file=stderr_file)

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Return no validation steps for declaration-shape tests."""
        _ = stderr_file
        return []


class BadShapeParentConfig(Config):
    """Parent config used for invalid declaration-shape tests."""

    def __init__(self, nested_configs: object,
                 stderr_file: TextIO = sys.stderr) -> None:
        """Construct a parent with intentionally unchecked metadata."""
        self.child: dict[str, object] = {}
        self._nested_configs = cast(NestedConfigs, nested_configs)
        super().__init__(from_json_data_text=None, from_json_filename=None,
                         stderr_file=stderr_file)

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Return no validation steps for declaration-shape tests."""
        _ = stderr_file
        return []


class SameTypeByKeyConfig(ReportByKeyConfig):
    """Configuration with selected same-type Config values in a dict."""

    @staticmethod
    def _audit_config_type() -> type[Config]:
        """Return the nested Config type used for the audit key."""
        return ReportSection

    @staticmethod
    def _default_reports(stderr_file: TextIO) -> dict[str, object]:
        """Return default same-type report data for keyed dict tests."""
        reports = ReportByKeyConfig._default_reports(stderr_file)
        audit = ReportSection(stderr_file=stderr_file)
        audit.name = 'audit'
        audit.file_name = 'audit.csv'
        reports['audit'] = audit
        return reports


def _nested_output(stderr_file: TextIO) -> NestedOutputConfig:
    """Return a nested output object for declaration-shape tests."""
    return NestedOutputConfig(stderr_file=stderr_file)


def _assert_silent(capsys: CaptureFixture[str]) -> None:
    """Assert that a test emitted no captured output."""
    out, err = capsys.readouterr()
    assert out == ''
    assert err == ''


def _valid_shape_data(case_name: str, stderr_file: TextIO) \
        -> tuple[NestedConfigs, object]:
    """Return valid ``_nested_configs`` metadata and matching member data."""
    cases: dict[str, tuple[NestedConfigs, object]] = {
        'member': (
            {'child': _plain_nesting(ConfigNestingKind.MEMBER)},
            _nested_output(stderr_file)),
        'optional': (
            {'child': _plain_nesting(ConfigNestingKind.OPTIONAL_MEMBER)},
            None),
        'list': (
            {'child': _plain_nesting(ConfigNestingKind.LIST_ELEMENT)}, []),
        'dict': (
            {'child': _plain_nesting(ConfigNestingKind.DICT_VALUE)}, {}),
        'direct-by-key': (
            {'child': _by_key_nesting('primary')},
            {'primary': _nested_output(stderr_file), 'plain': 'ok'}),
        'one-by-key-list': (
            {'child': [_by_key_nesting('primary')]},
            {'primary': _nested_output(stderr_file), 'plain': 'ok'}),
        'two-by-key-list': (
            {'child': [_by_key_nesting('primary'),
                       _by_key_nesting('secondary')]},
            {'primary': _nested_output(stderr_file),
             'secondary': _nested_output(stderr_file), 'plain': 'ok'})
    }
    return cases[case_name]


@pytest.mark.parametrize('case_name', [
    'member',
    'optional',
    'list',
    'dict',
    'direct-by-key',
    'one-by-key-list',
    'two-by-key-list'
])
def test_good_nesting_shapes(capsys: CaptureFixture[str],
                             case_name: str) -> None:
    """Test valid ``_nested_configs`` declaration shapes."""
    nested_configs, child_value = _valid_shape_data(case_name, sys.stderr)
    _ = ShapeParentConfig(nested_configs=nested_configs,
                          child_value=child_value, stderr_file=sys.stderr)
    _assert_silent(capsys)


def test_by_key_one_file_io(capsys: CaptureFixture[str]) -> None:
    """Test file round trip with one selected nested Config dict value."""
    cfg = ReportByKeyConfig(stderr_file=sys.stderr)
    participants = cast(ReportSection, cfg.reports_by_id['participants'])
    participants.file_name = 'participants.txt'
    participants.output_format = 'txt'
    cfg.course_name = 'math'
    cfg.reports_by_id = {
        'participants': participants,
        'note': 'reviewed',
        'retry_count': 2
    }
    with TemporaryDirectory() as dirname:
        filename = dirname + '/dict_by_key_one.cfg'
        cfg.write(to_json_filename=filename, stderr_file=sys.stderr)
        read_cfg = ReportByKeyConfig(from_json_filename=filename,
                                     stderr_file=sys.stderr)
    _assert_silent(capsys)
    assert read_cfg.course_name == 'math'
    assert sorted(read_cfg.reports_by_id) == [
        'note', 'participants', 'retry_count']
    read_participants = cast(
        ReportSection, read_cfg.reports_by_id['participants'])
    assert read_cfg.reports_by_id['note'] == 'reviewed'
    assert read_cfg.reports_by_id['retry_count'] == 2
    assert read_participants.file_name == 'participants.txt'
    assert read_participants.output_format == 'TXT'


def test_by_key_same_type_file_io(capsys: CaptureFixture[str]) -> None:
    """Test file round trip with two same-type keyed Config values."""
    cfg = SameTypeByKeyConfig(stderr_file=sys.stderr)
    participants = cast(ReportSection, cfg.reports_by_id['participants'])
    audit = cast(ReportSection, cfg.reports_by_id['audit'])
    participants.file_name = 'participants.txt'
    participants.output_format = 'txt'
    audit.file_name = 'audit.txt'
    audit.output_format = 'csv'
    cfg.course_name = 'math'
    cfg.reports_by_id['note'] = 'reviewed'
    cfg.reports_by_id['retry_count'] = 2
    with TemporaryDirectory() as dirname:
        filename = dirname + '/dict_by_key_same_type.cfg'
        cfg.write(to_json_filename=filename, stderr_file=sys.stderr)
        read_cfg = SameTypeByKeyConfig(from_json_filename=filename,
                                       stderr_file=sys.stderr)
    _assert_silent(capsys)
    assert read_cfg.course_name == 'math'
    assert read_cfg.reports_by_id['note'] == 'reviewed'
    assert read_cfg.reports_by_id['retry_count'] == 2
    read_participants = cast(
        ReportSection, read_cfg.reports_by_id['participants'])
    read_audit = cast(ReportSection, read_cfg.reports_by_id['audit'])
    assert read_participants.file_name == 'participants.txt'
    assert read_participants.output_format == 'TXT'
    assert read_audit.file_name == 'audit.txt'
    assert read_audit.output_format == 'CSV'


def test_by_key_two_type_file_io(capsys: CaptureFixture[str]) -> None:
    """Test file round trip with two different keyed Config value types."""
    cfg = ReportByKeyConfig(stderr_file=sys.stderr)
    participants = cast(ReportSection, cfg.reports_by_id['participants'])
    audit = cast(AuditSection, cfg.reports_by_id['audit'])
    participants.file_name = 'participants.txt'
    participants.output_format = 'txt'
    audit.file_name = 'audit.txt'
    audit.include_actor = False
    cfg.course_name = 'math'
    cfg.reports_by_id['note'] = 'reviewed'
    cfg.reports_by_id['retry_count'] = 2
    cfg.reports_by_id['plain_dict'] = {'owner': 'ops'}
    with TemporaryDirectory() as dirname:
        filename = dirname + '/dict_by_key_nested_config.cfg'
        cfg.write(to_json_filename=filename, stderr_file=sys.stderr)
        read_cfg = ReportByKeyConfig(from_json_filename=filename,
                                     stderr_file=sys.stderr)
    _assert_silent(capsys)
    assert read_cfg.course_name == 'math'
    assert read_cfg.reports_by_id['note'] == 'reviewed'
    assert read_cfg.reports_by_id['retry_count'] == 2
    assert read_cfg.reports_by_id['plain_dict'] == {'owner': 'ops'}
    read_participants = cast(
        ReportSection, read_cfg.reports_by_id['participants'])
    read_audit = cast(AuditSection, read_cfg.reports_by_id['audit'])
    assert read_participants.file_name == 'participants.txt'
    assert read_participants.output_format == 'TXT'
    assert read_audit.file_name == 'audit.txt'
    assert read_audit.include_actor is False


def test_by_key_empty_file_io(capsys: CaptureFixture[str]) -> None:
    """Test file round trip with an empty keyed nested dictionary."""
    cfg = ReportByKeyConfig(stderr_file=sys.stderr)
    cfg.course_name = 'math'
    cfg.reports_by_id = {}
    with TemporaryDirectory() as dirname:
        filename = dirname + '/dict_by_key_empty.cfg'
        cfg.write(to_json_filename=filename, stderr_file=sys.stderr)
        read_cfg = ReportByKeyConfig(from_json_filename=filename,
                                     stderr_file=sys.stderr)
    _assert_silent(capsys)
    assert read_cfg.course_name == 'math'
    assert read_cfg.reports_by_id == {}


def _bad_shape_data(case_name: str) -> tuple[object, type[Exception], str]:
    """Return bad ``_nested_configs`` metadata and expected diagnostic text."""
    bad_disc = ConfigNesting(kind=ConfigNestingKind.DICT_VALUE_BY_KEY,
                             config_type=NestedOutputConfig,
                             discriminator_key=cast(Optional[str], 7))
    reserved_disc = ConfigNesting(kind=ConfigNestingKind.MEMBER,
                                  config_type=NestedOutputConfig,
                                  discriminator_key='primary')
    bad_kind = ConfigNesting(kind=cast(ConfigNestingKind, 'bad'),
                             config_type=NestedOutputConfig)
    bad_config_object = ConfigNesting(kind=ConfigNestingKind.MEMBER,
                                      config_type=cast(type[Config], 'bad'))
    bad_config_type = ConfigNesting(kind=ConfigNestingKind.MEMBER,
                                    config_type=cast(type[Config], str))
    cases: dict[str, tuple[object, type[Exception], str]] = {
        'not-dict': (
            'bad', TypeError, '_nested_configs must be a dict'),
        'bad-key': (
            {7: _by_key_nesting('child')}, TypeError,
            '_nested_configs keys must be strings'),
        'unknown-key': (
            {'missing': _by_key_nesting('child')}, KeyError,
            '_nested_configs returned unknown key missing'),
        'bad-value': (
            {'child': 'bad'}, TypeError,
            '_nested_configs[child] must be ConfigNesting or list'),
        'empty-list': (
            {'child': []}, ValueError,
            '_nested_configs[child] list must not be empty'),
        'bad-list-entry': (
            {'child': ['bad']}, TypeError,
            '_nested_configs[child] list entries must be ConfigNesting'),
        'member-list': (
            {'child': [_plain_nesting(ConfigNestingKind.MEMBER)]},
            ValueError, 'list may only contain DICT_VALUE_BY_KEY'),
        'mixed-list': (
            {'child': [_by_key_nesting('primary'),
                       _plain_nesting(ConfigNestingKind.MEMBER)]},
            ValueError, 'list may only contain DICT_VALUE_BY_KEY'),
        'duplicate-key': (
            {'child': [_by_key_nesting('primary'),
                       _by_key_nesting('primary')]},
            ValueError, 'duplicate discriminator_key primary'),
        'missing-disc': (
            {'child': _by_key_nesting(None)}, ValueError,
            'requires discriminator_key'),
        'bad-disc-type': (
            {'child': bad_disc}, TypeError,
            '_nested_configs[child].discriminator_key must be a string'),
        'reserved-disc': (
            {'child': reserved_disc}, ValueError,
            'discriminator_key is reserved for DICT_VALUE_BY_KEY'),
        'bad-kind': (
            {'child': bad_kind}, TypeError,
            '_nested_configs[child].kind must be ConfigNestingKind'),
        'bad-config-type-object': (
            {'child': bad_config_object}, TypeError,
            '_nested_configs[child].config_type must be a type'),
        'bad-config-type': (
            {'child': bad_config_type}, TypeError,
            '_nested_configs[child].config_type must derive from Config')
    }
    return cases[case_name]


@pytest.mark.parametrize('case_name', [
    'not-dict',
    'bad-key',
    'unknown-key',
    'bad-value',
    'empty-list',
    'bad-list-entry',
    'member-list',
    'mixed-list',
    'duplicate-key',
    'missing-disc',
    'bad-disc-type',
    'reserved-disc',
    'bad-kind',
    'bad-config-type-object',
    'bad-config-type'
])
def test_bad_nesting_shapes(capsys: CaptureFixture[str],
                            case_name: str) -> None:
    """Test invalid ``_nested_configs`` declaration shapes."""
    nested_configs, exception_type, message = _bad_shape_data(case_name)
    with pytest.raises(exception_type) as exc:
        _ = BadShapeParentConfig(nested_configs=nested_configs,
                                 stderr_file=sys.stderr)
    _assert_silent(capsys)
    assert message in str(exc.value)


def test_by_key_needs_disc(capsys: CaptureFixture[str]) -> None:
    """Test that DICT_VALUE_BY_KEY requires a discriminator key."""
    with pytest.raises(ValueError) as exc:
        _ = BadNestedParentConfig(_by_key_nesting(None),
                                  stderr_file=sys.stderr)
    _assert_silent(capsys)
    assert 'requires discriminator_key' in str(exc.value)


def test_empty_nesting_list(capsys: CaptureFixture[str]) -> None:
    """Test that a nested declaration list must not be empty."""
    with pytest.raises(ValueError) as exc:
        _ = BadNestedParentConfig([], stderr_file=sys.stderr)
    _assert_silent(capsys)
    assert 'list must not be empty' in str(exc.value)


def test_nesting_list_entry_type(capsys: CaptureFixture[str]) -> None:
    """Test that declaration list entries must be ConfigNesting objects."""
    with pytest.raises(TypeError) as exc:
        _ = BadNestedParentConfig(['bad'], stderr_file=sys.stderr)
    _assert_silent(capsys)
    assert 'list entries must be ConfigNesting' in str(exc.value)


def test_single_nesting_list(capsys: CaptureFixture[str]) -> None:
    """Test that a single non-keyed declaration may not be in a list."""
    nesting = ConfigNesting(kind=ConfigNestingKind.MEMBER,
                            config_type=NestedOutputConfig)
    with pytest.raises(ValueError) as exc:
        _ = BadNestedParentConfig([nesting], stderr_file=sys.stderr)
    _assert_silent(capsys)
    assert 'may only contain DICT_VALUE_BY_KEY' in str(exc.value)


def test_mixed_nesting_list(capsys: CaptureFixture[str]) -> None:
    """Test that multiple list entries must all be DICT_VALUE_BY_KEY."""
    member_nesting = ConfigNesting(kind=ConfigNestingKind.MEMBER,
                                   config_type=NestedOutputConfig)
    with pytest.raises(ValueError) as exc:
        _ = BadNestedParentConfig([_by_key_nesting('child'), member_nesting],
                                  stderr_file=sys.stderr)
    _assert_silent(capsys)
    assert 'may only contain DICT_VALUE_BY_KEY' in str(exc.value)


def test_duplicate_disc(capsys: CaptureFixture[str]) -> None:
    """Test that DICT_VALUE_BY_KEY declarations need unique keys."""
    with pytest.raises(ValueError) as exc:
        _ = BadNestedParentConfig([_by_key_nesting('child'),
                                   _by_key_nesting('child')],
                                  stderr_file=sys.stderr)
    _assert_silent(capsys)
    assert 'duplicate discriminator_key child' in str(exc.value)
