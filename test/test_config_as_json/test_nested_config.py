#! /usr/local/bin/python3
"""Test Config classes that contain several nested Config members."""

# Copyright (c) 2026 Tom Björkholm
# MIT License

import json
import sys
from typing import Optional, TextIO
import pytest
from pytest import CaptureFixture
import config_as_json
import config_as_json.config as config_module
from config_as_json.config import Config
from config_as_json.config_nesting import ConfigNesting, ConfigNestingKind
from config_as_json.commontypes import PathOrStr
from config_as_json.validator import ValidationPlan


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
    assert not hasattr(config_module, 'ConfigNesting')
    assert not hasattr(config_module, 'ConfigNestingKind')


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
