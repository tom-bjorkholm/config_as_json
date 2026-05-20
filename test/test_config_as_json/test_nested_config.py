#! /usr/local/bin/python3
"""Test Config classes that contain several nested Config members."""

# Copyright (c) 2026 Tom Björkholm
# MIT License

import json
import sys
from tempfile import TemporaryDirectory
from typing import Optional, TextIO, cast, override
import pytest
from pytest import CaptureFixture
import config_as_json
from config_as_json import StrValidator
from config_as_json.config import Config
from config_as_json.config_nesting import ConfigNesting, ConfigNestingKind, \
    NestedConfigs
from config_as_json.commontypes import PathOrStr
from config_as_json.validator import InvalidConfiguration, \
    MemberValidationStep, ValidationPlan, WholeConfigValidationStep, \
    WholeConfigValidator


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
        super().__init__(from_json_data_text=from_json_data_text,
                         from_json_filename=from_json_filename,
                         stderr_file=stderr_file)

    @override
    def nested_configs(self) -> NestedConfigs:
        """Return nested Config declarations."""
        return {
            'participants': ConfigNesting(kind=ConfigNestingKind.MEMBER,
                                          config_type=ParticipantSection),
            'audit_log': ConfigNesting(kind=ConfigNestingKind.MEMBER,
                                       config_type=AuditSection),
            'backup_participants': ConfigNesting(
                kind=ConfigNestingKind.OPTIONAL_MEMBER,
                config_type=ParticipantSection)
        }

    @override
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
    assert config_as_json.NestedConfigs is NestedConfigs


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


def test_multi_nested_roundtrip_file(capsys: CaptureFixture[str]) -> None:
    """Test writing and reading direct and optional nested members."""
    cfg = MultiSectionConfig(stderr_file=sys.stderr)
    cfg.course_name = 'math'
    cfg.participants.file_name = 'participants.txt'
    cfg.participants.columns = ['email']
    cfg.audit_log.file_name = 'audit.txt'
    cfg.audit_log.include_actor = False
    cfg.backup_participants = ParticipantSection(stderr_file=sys.stderr)
    cfg.backup_participants.file_name = 'backup.txt'
    cfg.backup_participants.columns = ['name']
    with TemporaryDirectory() as dirname:
        filename = dirname + '/multi_nested_config.cfg'
        cfg.write(to_json_filename=filename, stderr_file=sys.stderr)
        read_cfg = MultiSectionConfig(from_json_filename=filename,
                                      stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert out == ''
    assert err == ''
    assert read_cfg.course_name == 'math'
    assert isinstance(read_cfg.participants, ParticipantSection)
    assert isinstance(read_cfg.audit_log, AuditSection)
    assert isinstance(read_cfg.backup_participants, ParticipantSection)
    assert read_cfg.participants.file_name == 'participants.txt'
    assert read_cfg.participants.columns == ['email']
    assert read_cfg.audit_log.file_name == 'audit.txt'
    assert read_cfg.audit_log.include_actor is False
    assert read_cfg.backup_participants.file_name == 'backup.txt'
    assert read_cfg.backup_participants.columns == ['name']


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
        super().__init__(from_json_data_text=from_json_data_text,
                         from_json_filename=from_json_filename,
                         stderr_file=stderr_file)

    @override
    def nested_configs(self) -> NestedConfigs:
        """Return nested Config declarations."""
        return {
            'reports': ConfigNesting(kind=ConfigNestingKind.LIST_ELEMENT,
                                     config_type=ReportSection)
        }

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


def _changed_reports(stderr_file: TextIO) \
        -> tuple[ReportSection, ReportSection]:
    """Return two non-default report sections."""
    participants = ReportSection(stderr_file=stderr_file)
    participants.name = 'participants'
    participants.file_name = 'participants.txt'
    participants.output_format = 'txt'
    audit = ReportSection(stderr_file=stderr_file)
    audit.name = 'audit'
    audit.file_name = 'audit.csv'
    audit.output_format = 'csv'
    return participants, audit


def test_list_nested_file_round_trip(capsys: CaptureFixture[str]) -> None:
    """Test writing and reading non-default nested list values."""
    participants, audit = _changed_reports(sys.stderr)
    cfg = ReportListConfig(default_reports=[participants, audit],
                           stderr_file=sys.stderr)
    cfg.course_name = 'math'
    with TemporaryDirectory() as dirname:
        filename = dirname + '/list_nested_config.cfg'
        cfg.write(to_json_filename=filename, stderr_file=sys.stderr)
        read_cfg = ReportListConfig(from_json_filename=filename,
                                    stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert out == ''
    assert err == ''
    assert read_cfg.course_name == 'math'
    assert len(read_cfg.reports) == 2
    assert isinstance(read_cfg.reports[0], ReportSection)
    assert isinstance(read_cfg.reports[1], ReportSection)
    assert read_cfg.reports[0].file_name == 'participants.txt'
    assert read_cfg.reports[0].output_format == 'TXT'
    assert read_cfg.reports[1].file_name == 'audit.csv'
    assert read_cfg.reports[1].output_format == 'CSV'


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


# pylint: disable-next=too-few-public-methods
class ReportDictValidator(WholeConfigValidator):
    """Validate that nested dict values were normalized first."""

    def validate(self, config: Config,
                 stderr_file: TextIO = sys.stderr) -> None:
        """Validate normalized report formats on the parent object."""
        assert isinstance(config, ReportDictConfig)
        for report_key, report in config.reports_by_id.items():
            if report.output_format in ('CSV', 'TXT'):
                continue
            msg = f'Report {report_key} format was not normalized'
            print(msg, file=stderr_file)
            raise InvalidConfiguration(msg)


class ReportDictConfig(Config):
    """Configuration with a dict of nested report outputs."""

    def __init__(self, from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 stderr_file: TextIO = sys.stderr,
                 default_reports: Optional[dict[str, ReportSection]] = None
                 ) -> None:
        """Construct a parent configuration with nested dict values."""
        self.course_name = 'python-intro'
        if default_reports is None:
            self.reports_by_id: dict[str, ReportSection] = {}
        else:
            self.reports_by_id = default_reports
        super().__init__(from_json_data_text=from_json_data_text,
                         from_json_filename=from_json_filename,
                         stderr_file=stderr_file)

    @override
    def nested_configs(self) -> NestedConfigs:
        """Return nested Config declarations."""
        return {
            'reports_by_id': ConfigNesting(kind=ConfigNestingKind.DICT_VALUE,
                                           config_type=ReportSection)
        }

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Return validation steps for the parent configuration."""
        _ = stderr_file
        return [WholeConfigValidationStep(validator=ReportDictValidator())]


def _report_dict_json(config: ReportDictConfig,
                      capsys: CaptureFixture[str]) -> dict[str, object]:
    """Serialize one report-dict configuration and verify silence."""
    json_text = config.as_json_string(stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert out == ''
    assert err == ''
    loaded = json.loads(json_text)
    return cast(dict[str, object], loaded)


def test_dict_nested_default_empty(capsys: CaptureFixture[str]) -> None:
    """Test that an empty dict is a valid DICT_VALUE default."""
    cfg = ReportDictConfig(stderr_file=sys.stderr)
    assert _report_dict_json(cfg, capsys) == {
        'course_name': 'python-intro',
        'reports_by_id': {}
    }


def test_dict_nested_default_values(capsys: CaptureFixture[str]) -> None:
    """Test that default dict values are validated and serialized."""
    report = ReportSection(stderr_file=sys.stderr)
    report.name = 'audit'
    report.file_name = 'audit.txt'
    report.output_format = 'txt'
    cfg = ReportDictConfig(default_reports={'audit': report},
                           stderr_file=sys.stderr)
    assert report.output_format == 'TXT'
    assert _report_dict_json(cfg, capsys) == {
        'course_name': 'python-intro',
        'reports_by_id': {
            'audit': {
                'file_name': 'audit.txt',
                'name': 'audit',
                'output_format': 'TXT'
            }
        }
    }


def test_dict_nested_parse_write(capsys: CaptureFixture[str]) -> None:
    """Test parsing and writing a dict of nested Config objects."""
    cfg = ReportDictConfig(
        from_json_data_text='{"course_name": "math", "reports_by_id": {'
        '"participants": {"name": "participants", '
        '"file_name": "participants.txt", "output_format": "txt"}, '
        '"audit": {"name": "audit", "file_name": "audit.csv", '
        '"output_format": "csv"}}}',
        stderr_file=sys.stderr)
    json_data = _report_dict_json(cfg, capsys)
    assert sorted(cfg.reports_by_id.keys()) == ['audit', 'participants']
    assert isinstance(cfg.reports_by_id['audit'], ReportSection)
    assert cfg.reports_by_id['participants'].output_format == 'TXT'
    assert cfg.reports_by_id['audit'].output_format == 'CSV'
    assert json_data == {
        'course_name': 'math',
        'reports_by_id': {
            'audit': {
                'file_name': 'audit.csv',
                'name': 'audit',
                'output_format': 'CSV'
            },
            'participants': {
                'file_name': 'participants.txt',
                'name': 'participants',
                'output_format': 'TXT'
            }
        }
    }


def test_dict_nested_file_round_trip(capsys: CaptureFixture[str]) -> None:
    """Test writing and reading non-default nested dict values."""
    participants, audit = _changed_reports(sys.stderr)
    cfg = ReportDictConfig(
        default_reports={'participants': participants, 'audit': audit},
        stderr_file=sys.stderr)
    cfg.course_name = 'math'
    with TemporaryDirectory() as dirname:
        filename = dirname + '/dict_nested_config.cfg'
        cfg.write(to_json_filename=filename, stderr_file=sys.stderr)
        read_cfg = ReportDictConfig(from_json_filename=filename,
                                    stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert out == ''
    assert err == ''
    assert read_cfg.course_name == 'math'
    assert sorted(read_cfg.reports_by_id) == ['audit', 'participants']
    assert isinstance(read_cfg.reports_by_id['audit'], ReportSection)
    assert read_cfg.reports_by_id['participants'].file_name == \
        'participants.txt'
    assert read_cfg.reports_by_id['participants'].output_format == 'TXT'
    assert read_cfg.reports_by_id['audit'].file_name == 'audit.csv'
    assert read_cfg.reports_by_id['audit'].output_format == 'CSV'


def test_dict_nested_order(capsys: CaptureFixture[str]) -> None:
    """Test that dict value validation runs before parent validation."""
    cfg = ReportDictConfig(default_reports={'audit': ReportSection()},
                           stderr_file=sys.stderr)
    cfg.reports_by_id['audit'].output_format = 'txt'
    cfg.validate(stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert out == ''
    assert err == ''
    assert cfg.reports_by_id['audit'].output_format == 'TXT'


def test_dict_nested_bad_json_dict(capsys: CaptureFixture[str]) -> None:
    """Test that DICT_VALUE JSON data must be an object."""
    with pytest.raises(KeyError) as exc:
        _ = ReportDictConfig(
            from_json_data_text='{"course_name": "math", '
            '"reports_by_id": [{"name": "bad"}]}',
            stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert out == ''
    assert 'Nested Config member reports_by_id must be a JSON object' in err
    assert 'JSON object' in str(exc.value)


@pytest.mark.parametrize('bad_value', [None, 7, ['not-object']])
def test_dict_nested_bad_json_value(capsys: CaptureFixture[str],
                                    bad_value: object) -> None:
    """Test that every DICT_VALUE JSON value must be an object."""
    json_text = json.dumps({'course_name': 'math',
                            'reports_by_id': {'audit': bad_value}})
    with pytest.raises(KeyError) as exc:
        _ = ReportDictConfig(from_json_data_text=json_text,
                             stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert out == ''
    assert 'reports_by_id[audit] must be a JSON object' in err
    assert 'reports_by_id[audit]' in str(exc.value)


def test_dict_nested_bad_member(capsys: CaptureFixture[str]) -> None:
    """Test that the runtime DICT_VALUE member must be a dict."""
    cfg = ReportDictConfig(stderr_file=sys.stderr)
    cfg.reports_by_id = cast(dict[str, ReportSection], 'not-a-dict')
    with pytest.raises(TypeError) as exc:
        cfg.validate(stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert out == ''
    assert 'Nested Config member reports_by_id must be a dict' in err
    assert 'must be a dict' in str(exc.value)


def test_dict_nested_bad_key(capsys: CaptureFixture[str]) -> None:
    """Test that every runtime dict key must be a string."""
    cfg = ReportDictConfig(stderr_file=sys.stderr)
    cfg.reports_by_id = cast(
        dict[str, ReportSection], {7: ReportSection(stderr_file=sys.stderr)})
    with pytest.raises(TypeError) as exc:
        cfg.validate(stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert out == ''
    assert 'Nested Config member reports_by_id keys must be strings' in err
    assert 'keys must be strings' in str(exc.value)


def test_dict_nested_bad_value(capsys: CaptureFixture[str]) -> None:
    """Test that every runtime dict value must be the configured type."""
    cfg = ReportDictConfig(stderr_file=sys.stderr)
    cfg.reports_by_id = cast(dict[str, ReportSection], {'audit': object()})
    with pytest.raises(TypeError) as exc:
        cfg.validate(stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert out == ''
    assert 'reports_by_id[audit] must be ReportSection' in err
    assert 'reports_by_id[audit]' in str(exc.value)


# pylint: disable-next=too-few-public-methods
class ReportByKeyValidator(WholeConfigValidator):
    """Validate that keyed nested dict values were normalized first."""

    def validate(self, config: Config,
                 stderr_file: TextIO = sys.stderr) -> None:
        """Validate normalized report formats on the parent object."""
        assert isinstance(config, ReportByKeyConfig)
        report = config.reports_by_id.get('participants')
        if report is None:
            return
        if isinstance(report, ReportSection) and \
                report.output_format in ('CSV', 'TXT'):
            return
        msg = 'Participants report format was not normalized'
        print(msg, file=stderr_file)
        raise InvalidConfiguration(msg)


class ReportByKeyConfig(Config):
    """Configuration with selected nested Config values in a dict."""

    def __init__(self, from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 stderr_file: TextIO = sys.stderr,
                 default_reports: Optional[dict[str, object]] = None) -> None:
        """Construct a parent configuration with keyed nested dict values."""
        self.course_name = 'python-intro'
        if default_reports is None:
            self.reports_by_id: dict[str, object] = \
                self._default_reports(stderr_file)
        else:
            self.reports_by_id = default_reports
        super().__init__(from_json_data_text=from_json_data_text,
                         from_json_filename=from_json_filename,
                         stderr_file=stderr_file)

    @override
    def nested_configs(self) -> NestedConfigs:
        """Return nested Config declarations."""
        participant_nesting = ConfigNesting(
            kind=ConfigNestingKind.DICT_VALUE_BY_KEY,
            config_type=ReportSection, discriminator_key='participants')
        audit_nesting = ConfigNesting(kind=ConfigNestingKind.DICT_VALUE_BY_KEY,
                                      config_type=self._audit_config_type(),
                                      discriminator_key='audit')
        return {
            'reports_by_id': [participant_nesting, audit_nesting]
        }

    @staticmethod
    def _audit_config_type() -> type[Config]:
        """Return the nested Config type used for the audit key."""
        return AuditSection

    @staticmethod
    def _default_reports(stderr_file: TextIO) -> dict[str, object]:
        """Return default mixed report data for keyed dict tests."""
        participants = ReportSection(stderr_file=stderr_file)
        audit = AuditSection(stderr_file=stderr_file)
        return {
            'participants': participants,
            'audit': audit,
            'note': 'draft',
            'retry_count': 3
        }

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Return validation steps for the parent configuration."""
        _ = stderr_file
        return [WholeConfigValidationStep(validator=ReportByKeyValidator())]


def _report_by_key_json(config: ReportByKeyConfig,
                        capsys: CaptureFixture[str]) -> dict[str, object]:
    """Serialize one keyed report-dict config and verify silence."""
    json_text = config.as_json_string(stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert out == ''
    assert err == ''
    loaded = json.loads(json_text)
    return cast(dict[str, object], loaded)


def _report_by_key_json_text() -> str:
    """Return JSON for a dict with selected nested Config values."""
    return ('{"course_name": "math", "reports_by_id": {'
            '"participants": {"name": "participants", '
            '"file_name": "participants.txt", "output_format": "txt"}, '
            '"audit": {"file_name": "audit.txt", '
            '"include_actor": false}, '
            '"note": "reviewed", "retry_count": 2, '
            '"plain_dict": {"owner": "ops"}}}')


def test_dict_by_key_default_values(capsys: CaptureFixture[str]) -> None:
    """Test default keyed nested dict values and plain values."""
    cfg = ReportByKeyConfig(stderr_file=sys.stderr)
    assert _report_by_key_json(cfg, capsys) == {
        'course_name': 'python-intro',
        'reports_by_id': {
            'audit': {
                'file_name': 'audit.csv',
                'include_actor': True
            },
            'note': 'draft',
            'participants': {
                'file_name': 'participants.csv',
                'name': 'participants',
                'output_format': 'CSV'
            },
            'retry_count': 3
        }
    }


def test_dict_by_key_parse_write(capsys: CaptureFixture[str]) -> None:
    """Test parsing and writing selected nested Config dict values."""
    cfg = ReportByKeyConfig(from_json_data_text=_report_by_key_json_text(),
                            stderr_file=sys.stderr)
    json_data = _report_by_key_json(cfg, capsys)
    participants = cfg.reports_by_id['participants']
    audit = cfg.reports_by_id['audit']
    assert isinstance(participants, ReportSection)
    assert isinstance(audit, AuditSection)
    assert cfg.reports_by_id['note'] == 'reviewed'
    assert cfg.reports_by_id['retry_count'] == 2
    assert cfg.reports_by_id['plain_dict'] == {'owner': 'ops'}
    assert participants.output_format == 'TXT'
    assert audit.include_actor is False
    assert json_data == {
        'course_name': 'math',
        'reports_by_id': {
            'audit': {
                'file_name': 'audit.txt',
                'include_actor': False
            },
            'note': 'reviewed',
            'participants': {
                'file_name': 'participants.txt',
                'name': 'participants',
                'output_format': 'TXT'
            },
            'plain_dict': {'owner': 'ops'},
            'retry_count': 2
        }
    }


def test_dict_by_key_empty_dict(capsys: CaptureFixture[str]) -> None:
    """Test that an empty dict is valid for DICT_VALUE_BY_KEY."""
    cfg = ReportByKeyConfig(
        from_json_data_text='{"course_name": "math", "reports_by_id": {}}',
        stderr_file=sys.stderr)
    assert _report_by_key_json(cfg, capsys) == {
        'course_name': 'math',
        'reports_by_id': {}
    }


def test_dict_by_key_bad_json_dict(capsys: CaptureFixture[str]) -> None:
    """Test that DICT_VALUE_BY_KEY JSON data must be an object."""
    with pytest.raises(KeyError) as exc:
        _ = ReportByKeyConfig(
            from_json_data_text='{"course_name": "math", '
            '"reports_by_id": [{"name": "bad"}]}',
            stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert out == ''
    assert 'Nested Config member reports_by_id must be a JSON object' in err
    assert 'JSON object' in str(exc.value)


@pytest.mark.parametrize('bad_value', [None, 7, ['not-object']])
def test_dict_by_key_bad_json_value(capsys: CaptureFixture[str],
                                    bad_value: object) -> None:
    """Test that declared DICT_VALUE_BY_KEY values must be objects."""
    json_text = json.dumps({'course_name': 'math',
                            'reports_by_id': {'participants': bad_value}})
    with pytest.raises(KeyError) as exc:
        _ = ReportByKeyConfig(from_json_data_text=json_text,
                              stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert out == ''
    assert 'reports_by_id[participants] must be a JSON object' in err
    assert 'reports_by_id[participants]' in str(exc.value)


def test_dict_by_key_bad_member(capsys: CaptureFixture[str]) -> None:
    """Test that the runtime DICT_VALUE_BY_KEY member must be a dict."""
    cfg = ReportByKeyConfig(stderr_file=sys.stderr)
    cfg.reports_by_id = cast(dict[str, object], 'not-a-dict')
    with pytest.raises(TypeError) as exc:
        cfg.validate(stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert out == ''
    assert 'Nested Config member reports_by_id must be a dict' in err
    assert 'must be a dict' in str(exc.value)


def test_dict_by_key_bad_key(capsys: CaptureFixture[str]) -> None:
    """Test that runtime DICT_VALUE_BY_KEY keys must be strings."""
    cfg = ReportByKeyConfig(stderr_file=sys.stderr)
    cfg.reports_by_id = cast(dict[str, object], {
        7: 'bad',
        'participants': ReportSection(stderr_file=sys.stderr)
    })
    with pytest.raises(TypeError) as exc:
        cfg.validate(stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert out == ''
    assert 'Nested Config member reports_by_id keys must be strings' in err
    assert 'keys must be strings' in str(exc.value)


def test_by_key_bad_declared(capsys: CaptureFixture[str]) -> None:
    """Test that declared dict keys must contain the configured type."""
    cfg = ReportByKeyConfig(stderr_file=sys.stderr)
    cfg.reports_by_id['participants'] = AuditSection(stderr_file=sys.stderr)
    with pytest.raises(TypeError) as exc:
        cfg.validate(stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert out == ''
    assert 'reports_by_id[participants] must be ReportSection' in err
    assert 'reports_by_id[participants]' in str(exc.value)


def test_by_key_unlisted_config(capsys: CaptureFixture[str]) -> None:
    """Test that unlisted dict keys may not contain Config objects."""
    cfg = ReportByKeyConfig(stderr_file=sys.stderr)
    cfg.reports_by_id['summary'] = ReportSection(stderr_file=sys.stderr)
    with pytest.raises(TypeError) as exc:
        cfg.validate(stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert out == ''
    assert 'reports_by_id[summary] has no DICT_VALUE_BY_KEY' in err
    assert 'reports_by_id[summary]' in str(exc.value)
