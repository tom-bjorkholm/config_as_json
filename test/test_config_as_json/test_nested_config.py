#! /usr/local/bin/python3
"""Test Config classes that contain several nested Config members."""

# Copyright (c) 2026 Tom Björkholm
# MIT License

import json
import sys
from typing import Optional, TextIO, cast
import pytest
from pytest import CaptureFixture
import config_as_json
from config_as_json.config import Config
from config_as_json.config_nesting import ConfigNesting, ConfigNestingKind
from config_as_json.commontypes import PathOrStr
from config_as_json.validator import InvalidConfiguration, \
    MemberValidationStep, StrValidator, ValidationPlan, \
    WholeConfigValidationStep, WholeConfigValidator


class ParticipantSection(Config):
    """Nested configuration for participant output settings."""

    def __init__(self, from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 stderr_file: TextIO = sys.stderr) -> None:
        """Construct participant output settings."""
        self.file_name = 'participants.csv'
        self.columns = ['name', 'email']
        super().__init__(from_json_data_text=from_json_data_text,
                         from_json_filename=from_json_filename,
                         stderr_file=stderr_file)

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Return validation steps for participant output settings."""
        _ = stderr_file
        return []


class AuditSection(Config):
    """Nested configuration for audit log output settings."""

    def __init__(self, from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 stderr_file: TextIO = sys.stderr) -> None:
        """Construct audit log output settings."""
        self.file_name = 'audit.csv'
        self.include_actor = True
        super().__init__(from_json_data_text=from_json_data_text,
                         from_json_filename=from_json_filename,
                         stderr_file=stderr_file)

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Return validation steps for audit log output settings."""
        _ = stderr_file
        return []


class MultiSectionConfig(Config):
    """Configuration with mixed nested Config members."""

    def __init__(self, from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 stderr_file: TextIO = sys.stderr) -> None:
        """Construct a configuration with several nested sections."""
        self.course_name = 'python-intro'
        self.participants = ParticipantSection(stderr_file=stderr_file)
        self.audit_log = AuditSection(stderr_file=stderr_file)
        self.backup_participants: Optional[ParticipantSection] = None
        self._nested_configs = {
            'participants': ConfigNesting(kind=ConfigNestingKind.MEMBER,
                                          config_type=ParticipantSection),
            'audit_log': ConfigNesting(kind=ConfigNestingKind.MEMBER,
                                       config_type=AuditSection),
            'backup_participants': ConfigNesting(
                kind=ConfigNestingKind.OPTIONAL_MEMBER,
                config_type=ParticipantSection)
        }
        super().__init__(from_json_data_text=from_json_data_text,
                         from_json_filename=from_json_filename,
                         stderr_file=stderr_file)

    def _omit_none_from_json(self) -> list[str]:
        """Return optional members omitted while their value is None."""
        return ['backup_participants']

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Return validation steps for the parent configuration."""
        _ = stderr_file
        return []


def test_multi_nested_parse(capsys: CaptureFixture[str]) -> None:
    """Test more than one nested Config member in one parent."""
    cfg = MultiSectionConfig(
        from_json_data_text='{"course_name": "math", '
        '"participants": {"file_name": "participants.txt", '
        '"columns": ["name"]}, '
        '"audit_log": {"file_name": "audit.txt", '
        '"include_actor": false}, '
        '"backup_participants": {"file_name": "backup.txt", '
        '"columns": ["email"]}}',
        stderr_file=sys.stderr)
    json_data = json.loads(cfg.as_json_string(stderr_file=sys.stderr))
    out, err = capsys.readouterr()
    assert out == ''
    assert err == ''
    assert isinstance(cfg.participants, ParticipantSection)
    assert isinstance(cfg.audit_log, AuditSection)
    assert isinstance(cfg.backup_participants, ParticipantSection)
    assert cfg.participants.file_name == 'participants.txt'
    assert cfg.audit_log.include_actor is False
    assert cfg.backup_participants.columns == ['email']
    assert json_data == {
        'audit_log': {
            'file_name': 'audit.txt',
            'include_actor': False
        },
        'backup_participants': {
            'columns': ['email'],
            'file_name': 'backup.txt'
        },
        'course_name': 'math',
        'participants': {
            'columns': ['name'],
            'file_name': 'participants.txt'
        }
    }


def test_nested_api_import_paths() -> None:
    """Test supported public import paths for nested configuration APIs."""
    assert config_as_json.ConfigNesting is ConfigNesting
    assert config_as_json.ConfigNestingKind is ConfigNestingKind


@pytest.mark.parametrize('backup_json', ['', ', "backup_participants": null'])
def test_multi_nested_optional_omit(capsys: CaptureFixture[str],
                                    backup_json: str) -> None:
    """Test mixed MEMBER and OPTIONAL_MEMBER declarations together."""
    json_text = ('{"course_name": "math", '
                 '"participants": {"file_name": "participants.txt", '
                 '"columns": ["name"]}, '
                 '"audit_log": {"file_name": "audit.txt", '
                 '"include_actor": false}' + backup_json + '}')
    cfg = MultiSectionConfig(from_json_data_text=json_text,
                             stderr_file=sys.stderr)
    json_data = json.loads(cfg.as_json_string(stderr_file=sys.stderr))
    out, err = capsys.readouterr()
    assert out == ''
    assert err == ''
    assert cfg.backup_participants is None
    assert json_data == {
        'audit_log': {
            'file_name': 'audit.txt',
            'include_actor': False
        },
        'course_name': 'math',
        'participants': {
            'columns': ['name'],
            'file_name': 'participants.txt'
        }
    }


class ReportSection(Config):
    """Nested configuration for one report output."""

    def __init__(self, from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 stderr_file: TextIO = sys.stderr) -> None:
        """Construct one report output configuration."""
        self.name = 'participants'
        self.file_name = 'participants.csv'
        self.output_format = 'CSV'
        super().__init__(from_json_data_text=from_json_data_text,
                         from_json_filename=from_json_filename,
                         stderr_file=stderr_file)

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Return validation steps for one report output."""
        _ = stderr_file
        return [MemberValidationStep(
            member_names=['output_format'],
            validator=StrValidator(['CSV', 'TXT'], ignore_case=True,
                                   normalize=True))]


# pylint: disable-next=too-few-public-methods
class ReportListValidator(WholeConfigValidator):
    """Validate that nested list elements were normalized first."""

    def validate(self, config: Config,
                 stderr_file: TextIO = sys.stderr) -> None:
        """Validate normalized report formats on the parent object."""
        assert isinstance(config, ReportListConfig)
        for report in config.reports:
            if report.output_format in ('CSV', 'TXT'):
                continue
            msg = 'Report format was not normalized before parent'
            print(msg, file=stderr_file)
            raise InvalidConfiguration(msg)


class ReportListConfig(Config):
    """Configuration with a list of nested report outputs."""

    def __init__(self, from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 stderr_file: TextIO = sys.stderr,
                 default_reports: Optional[list[ReportSection]] = None
                 ) -> None:
        """Construct a parent configuration with nested list elements."""
        self.course_name = 'python-intro'
        self.reports = [] if default_reports is None else default_reports
        self._nested_configs = {
            'reports': ConfigNesting(kind=ConfigNestingKind.LIST_ELEMENT,
                                     config_type=ReportSection)
        }
        super().__init__(from_json_data_text=from_json_data_text,
                         from_json_filename=from_json_filename,
                         stderr_file=stderr_file)

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Return validation steps for the parent configuration."""
        _ = stderr_file
        return [WholeConfigValidationStep(validator=ReportListValidator())]


def _reports_json(config: ReportListConfig,
                  capsys: CaptureFixture[str]) -> dict[str, object]:
    """Serialize one report-list configuration and verify silence."""
    json_text = config.as_json_string(stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert out == ''
    assert err == ''
    loaded = json.loads(json_text)
    return cast(dict[str, object], loaded)


def test_list_nested_default_empty(capsys: CaptureFixture[str]) -> None:
    """Test that an empty list is a valid LIST_ELEMENT default."""
    cfg = ReportListConfig(stderr_file=sys.stderr)
    assert _reports_json(cfg, capsys) == {
        'course_name': 'python-intro',
        'reports': []
    }


def test_list_nested_default_values(capsys: CaptureFixture[str]) -> None:
    """Test that default list elements are validated and serialized."""
    report = ReportSection(stderr_file=sys.stderr)
    report.name = 'audit'
    report.file_name = 'audit.txt'
    report.output_format = 'txt'
    cfg = ReportListConfig(default_reports=[report], stderr_file=sys.stderr)
    assert report.output_format == 'TXT'
    assert _reports_json(cfg, capsys) == {
        'course_name': 'python-intro',
        'reports': [{
            'file_name': 'audit.txt',
            'name': 'audit',
            'output_format': 'TXT'
        }]
    }


def test_list_nested_parse_write(capsys: CaptureFixture[str]) -> None:
    """Test parsing and writing a list of nested Config objects."""
    cfg = ReportListConfig(
        from_json_data_text='{"course_name": "math", "reports": ['
        '{"name": "participants", "file_name": "participants.txt", '
        '"output_format": "txt"}, '
        '{"name": "audit", "file_name": "audit.csv", '
        '"output_format": "csv"}]}',
        stderr_file=sys.stderr)
    json_data = _reports_json(cfg, capsys)
    assert len(cfg.reports) == 2
    assert isinstance(cfg.reports[0], ReportSection)
    assert cfg.reports[0].output_format == 'TXT'
    assert cfg.reports[1].output_format == 'CSV'
    assert json_data == {
        'course_name': 'math',
        'reports': [{
            'file_name': 'participants.txt',
            'name': 'participants',
            'output_format': 'TXT'
        }, {
            'file_name': 'audit.csv',
            'name': 'audit',
            'output_format': 'CSV'
        }]
    }


def test_list_nested_order(capsys: CaptureFixture[str]) -> None:
    """Test that list element validation runs before parent validation."""
    cfg = ReportListConfig(default_reports=[ReportSection()],
                           stderr_file=sys.stderr)
    cfg.reports[0].output_format = 'txt'
    cfg.validate(stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert out == ''
    assert err == ''
    assert cfg.reports[0].output_format == 'TXT'


def test_list_nested_bad_json_list(capsys: CaptureFixture[str]) -> None:
    """Test that LIST_ELEMENT JSON data must be a list."""
    with pytest.raises(KeyError) as exc:
        _ = ReportListConfig(
            from_json_data_text='{"course_name": "math", '
            '"reports": {"name": "bad"}}',
            stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert out == ''
    assert 'Nested Config member reports must be a JSON list' in err
    assert 'JSON list' in str(exc.value)


@pytest.mark.parametrize('bad_element', [None, 7, ['not-object']])
def test_list_nested_bad_json_item(capsys: CaptureFixture[str],
                                   bad_element: object) -> None:
    """Test that every LIST_ELEMENT JSON item must be an object."""
    json_text = json.dumps({'course_name': 'math',
                            'reports': [bad_element]})
    with pytest.raises(KeyError) as exc:
        _ = ReportListConfig(from_json_data_text=json_text,
                             stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert out == ''
    assert 'Nested Config member reports[0] must be a JSON object' in err
    assert 'reports[0]' in str(exc.value)


def test_list_nested_bad_member(capsys: CaptureFixture[str]) -> None:
    """Test that the runtime LIST_ELEMENT member must be a list."""
    cfg = ReportListConfig(stderr_file=sys.stderr)
    cfg.reports = cast(list[ReportSection], 'not-a-list')
    with pytest.raises(TypeError) as exc:
        cfg.validate(stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert out == ''
    assert 'Nested Config member reports must be a list' in err
    assert 'must be a list' in str(exc.value)


def test_list_nested_bad_element(capsys: CaptureFixture[str]) -> None:
    """Test that every runtime list item must be the configured type."""
    cfg = ReportListConfig(stderr_file=sys.stderr)
    cfg.reports = cast(list[ReportSection], [object()])
    with pytest.raises(TypeError) as exc:
        cfg.validate(stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert out == ''
    assert 'Nested Config member reports[0] must be ReportSection' in err
    assert 'reports[0]' in str(exc.value)
