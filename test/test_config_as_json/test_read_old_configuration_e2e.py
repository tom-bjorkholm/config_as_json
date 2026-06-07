#! /usr/local/bin/python3
"""Test end-to-end old-shape parsing with ReadOldConfiguration."""

# Copyright (c) 2026 Tom Björkholm
# MIT License

import sys
from enum import Enum, auto
from io import StringIO
from typing import Optional, TextIO, override
import pytest
from config_as_json import Config, ConfigAutoChangeHook, ConfigNesting, \
    ConfigNestingKind, ConfigPath, JsonType, NestedConfigs, ParseConverter, \
    PathOrStr, ReadOldConfiguration, RocfKeyMove, RocfKeyRename, \
    RocfValueMigration, RocfValueWrite, ValidationPlan


class E2EFormat(Enum):
    """File formats used by end-to-end ROCF tests."""

    CSV = auto()
    TXT = auto()


class RecordingHook(ConfigAutoChangeHook):
    """Record backward-compatible auto-change callback arguments."""

    def __init__(self) -> None:
        """Initialize empty callback recording state."""
        super().__init__()
        self.calls: list[tuple[list[str], list[str]]] = []

    def __deepcopy__(self, memo: dict[int, object]) -> 'RecordingHook':
        """Return this recorder so tests can inspect callback results."""
        _ = memo
        return self

    def auto_changed(self, old_keys_handled: list[str],
                     rocf_vals_handled: list[str],
                     stderr_file: TextIO) -> None:
        """Record callback arguments for assertions."""
        _ = stderr_file
        self.calls.append((old_keys_handled, rocf_vals_handled))


class OldE2EExportConfig(Config):
    """Old nested export shape used for end-to-end ROCF tests."""

    def __init__(self, from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 stderr_file: TextIO = sys.stderr) -> None:
        """Initialize the old direct output object."""
        self.export_title: str = 'attendance'
        self.target_file: str = 'attendance.csv'
        self.format_name: E2EFormat = E2EFormat.CSV
        super().__init__(from_json_data_text=from_json_data_text,
                         from_json_filename=from_json_filename,
                         stderr_file=stderr_file)

    def parse_converters(self) -> dict[str, ParseConverter]:
        """Return conversions needed when reading enum values from JSON."""
        return {'format_name': self.get_converter_dict(E2EFormat)}

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Return no extra validation for this test shape."""
        _ = stderr_file
        return []


class OldE2EConfig(Config):
    """Old top-level shape used for end-to-end ROCF tests."""

    def __init__(self, from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 stderr_file: TextIO = sys.stderr) -> None:
        """Initialize the old top-level configuration object."""
        self.lesson_title: str = 'python-intro'
        self.fallback_format: E2EFormat = E2EFormat.TXT
        self.export: OldE2EExportConfig = OldE2EExportConfig(
            stderr_file=stderr_file)
        self.sections: list[JsonType] = [
            {'name': 'intro', 'duration': 15, 'stale': True,
             'attendance': 'required'},
            {'name': 'advanced', 'duration': 45, 'stale': True,
             'attendance': 'optional'}
        ]
        self.legacy_block: dict[str, JsonType] = {'drop': True}
        self.trace_enabled: bool = True
        super().__init__(from_json_data_text=from_json_data_text,
                         from_json_filename=from_json_filename,
                         stderr_file=stderr_file)

    @override
    def nested_configs(self) -> NestedConfigs:
        """Return nested Config declarations for the old shape."""
        return {
            'export': ConfigNesting(kind=ConfigNestingKind.MEMBER,
                                    config_type=OldE2EExportConfig)
        }

    def parse_converters(self) -> dict[str, ParseConverter]:
        """Return conversions needed when reading enum values from JSON."""
        return {'fallback_format': self.get_converter_dict(E2EFormat),
                'format_name': self.get_converter_dict(E2EFormat)}

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Return no extra validation for this test shape."""
        _ = stderr_file
        return []


class E2EExportConfig(Config):
    """Current nested export shape used for end-to-end ROCF tests."""

    def __init__(self, from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 stderr_file: TextIO = sys.stderr) -> None:
        """Initialize one current output object."""
        self.export_title: str = 'attendance'
        self.target_file: str = 'attendance.csv'
        self.selected_format: E2EFormat = E2EFormat.CSV
        self.char_encoding: str = 'utf-8'
        super().__init__(from_json_data_text=from_json_data_text,
                         from_json_filename=from_json_filename,
                         stderr_file=stderr_file)

    def parse_converters(self) -> dict[str, ParseConverter]:
        """Return conversions needed when reading enum values from JSON."""
        return {'selected_format': self.get_converter_dict(E2EFormat)}

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Return no extra validation for this test shape."""
        _ = stderr_file
        return []


def attendance_required(value: object) -> bool:
    """Convert an old attendance value to the current required flag."""
    assert isinstance(value, str)
    return value == 'required'


def attendance_label(value: object) -> str:
    """Convert an old attendance value to a current label."""
    assert isinstance(value, str)
    return value


class E2EReadOldConfig(ReadOldConfiguration):
    """Normalize old test data to the current test shape."""

    def get_json_key_renames(self) -> list[RocfKeyRename]:
        """Return old key names mapped to current key names."""
        return [RocfKeyRename(old='lesson_title', new='lesson_name')]

    def get_json_key_moves(self) -> list[RocfKeyMove]:
        """Return structural moves for old test data."""
        return [
            RocfKeyMove(old_path=('fallback_format',),
                        new_path=('fallback_export_format',)),
            RocfKeyMove(old_path=('export', 'format_name'),
                        new_path=('export', 'selected_format')),
            RocfKeyMove(old_path=('export',), new_path=('export_items', '[')),
            RocfKeyMove(old_path=('sections', '[', 'duration'),
                        new_path=('sections', '[', 'minutes'))
        ]

    def get_value_migrations(self) -> list[RocfValueMigration]:
        """Return value migrations for old test data."""
        return [
            RocfValueMigration(
                old_path=('sections', '[', 'attendance'),
                writes=[
                    RocfValueWrite(new_path=('sections', '[', 'required'),
                                   transform_value=attendance_required),
                    RocfValueWrite(new_path=('sections', '[',
                                             'attendance_label'),
                                   transform_value=attendance_label)])]

    def get_keys_to_prune(self) -> list[str]:
        """Return old key names removed everywhere in the input."""
        return ['trace_enabled']

    def get_keys_to_remove(self) -> list[ConfigPath]:
        """Return precise old paths removed from the input."""
        return [('legacy_block',), ('sections', '[', 'stale')]

    def get_missing_path_values(self) -> dict[ConfigPath, object]:
        """Return current values supplied when old data lacks them."""
        return {('schema_version',): 3,
                ('export_items', '[', 'char_encoding'): 'utf-8',
                ('sections', '[', 'required'): True,
                ('empty_tags',): []}


class E2EConfig(Config):
    """Current top-level shape used for end-to-end ROCF tests."""

    def __init__(self, from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 auto_ch_hook: Optional[ConfigAutoChangeHook] = None,
                 stderr_file: TextIO = sys.stderr) -> None:
        """Initialize the current top-level configuration object."""
        self.schema_version: int = 3
        self.lesson_name: str = 'python-intro'
        self.fallback_export_format: E2EFormat = E2EFormat.TXT
        self.export_items: list[E2EExportConfig] = [
            E2EExportConfig(stderr_file=stderr_file)]
        self.sections: list[JsonType] = []
        self.empty_tags: list[JsonType] = []
        super().__init__(from_json_data_text=from_json_data_text,
                         from_json_filename=from_json_filename,
                         auto_ch_hook=auto_ch_hook, stderr_file=stderr_file)

    @override
    def nested_configs(self) -> NestedConfigs:
        """Return nested Config declarations for the current shape."""
        return {
            'export_items': ConfigNesting(kind=ConfigNestingKind.LIST_ELEMENT,
                                          config_type=E2EExportConfig)
        }

    def _get_read_old_config(self) -> ReadOldConfiguration:
        """Return the object that normalizes old test data."""
        return E2EReadOldConfig()

    def parse_converters(self) -> dict[str, ParseConverter]:
        """Return conversions for both old and current enum key names."""
        converter = self.get_converter_dict(E2EFormat)
        return {'fallback_export_format': converter,
                'fallback_format': converter,
                'selected_format': converter,
                'format_name': converter}

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Return no extra validation for this test shape."""
        _ = stderr_file
        return []


def old_shape_json() -> str:
    """Return JSON text written by the old shape."""
    cfg = OldE2EConfig(stderr_file=StringIO())
    return cfg.as_json_string(stderr_file=StringIO())


def current_shape_json() -> str:
    """Return JSON text written by the current shape."""
    cfg = E2EConfig(stderr_file=StringIO())
    cfg.lesson_name = 'current-lesson'
    cfg.fallback_export_format = E2EFormat.CSV
    cfg.export_items[0].export_title = 'summary'
    cfg.export_items[0].char_encoding = 'latin-1'
    cfg.sections = [{'name': 'current', 'minutes': 30, 'required': False}]
    return cfg.as_json_string(stderr_file=StringIO())


def assert_old_shape_result(cfg: E2EConfig) -> None:
    """Assert values parsed from the old shape into the current shape."""
    assert cfg.schema_version == 3
    assert cfg.lesson_name == 'python-intro'
    assert cfg.fallback_export_format == E2EFormat.TXT
    assert len(cfg.export_items) == 1
    assert cfg.export_items[0].export_title == 'attendance'
    assert cfg.export_items[0].target_file == 'attendance.csv'
    assert cfg.export_items[0].selected_format == E2EFormat.CSV
    assert cfg.export_items[0].char_encoding == 'utf-8'
    assert cfg.sections == [
        {'name': 'intro', 'minutes': 15, 'required': True,
         'attendance_label': 'required'},
        {'name': 'advanced', 'minutes': 45, 'required': False,
         'attendance_label': 'optional'}
    ]
    assert not cfg.empty_tags


def test_old_shape_read(capsys: pytest.CaptureFixture[str]) -> None:
    """Test old-shape data read by the current Config class."""
    hook = RecordingHook()
    cfg = E2EConfig(from_json_data_text=old_shape_json(), auto_ch_hook=hook,
                    stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert out == ''
    assert err == ''
    assert_old_shape_result(cfg)
    assert hook.calls == [([
        'trace_enabled',
        'legacy_block',
        'sections[0][stale]',
        'sections[1][stale]',
        'lesson_title',
        'fallback_format -> fallback_export_format',
        'export[format_name] -> export[selected_format]',
        'export -> export_items[0]',
        'sections[0][duration] -> sections[0][minutes]',
        'sections[1][duration] -> sections[1][minutes]',
        'sections[0][attendance] -> sections[0][required]',
        'sections[0][attendance] -> sections[0][attendance_label]',
        'sections[1][attendance] -> sections[1][required]',
        'sections[1][attendance] -> sections[1][attendance_label]'
    ], [
        'schema_version',
        'export_items[0][char_encoding]',
        'empty_tags'
    ])]
    assert hook.old_paths_moved == [
        ('fallback_format', 'fallback_export_format'),
        ('export[format_name]', 'export[selected_format]'),
        ('export', 'export_items[0]'),
        ('sections[0][duration]', 'sections[0][minutes]'),
        ('sections[1][duration]', 'sections[1][minutes]'),
        ('sections[0][attendance]', 'sections[0][required]'),
        ('sections[0][attendance]', 'sections[0][attendance_label]'),
        ('sections[1][attendance]', 'sections[1][required]'),
        ('sections[1][attendance]', 'sections[1][attendance_label]')
    ]


def test_current_shape_noop(capsys: pytest.CaptureFixture[str]) -> None:
    """Test current-shape data read by the current Config class."""
    hook = RecordingHook()
    cfg = E2EConfig(from_json_data_text=current_shape_json(),
                    auto_ch_hook=hook, stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert out == ''
    assert err == ''
    assert cfg.schema_version == 3
    assert cfg.lesson_name == 'current-lesson'
    assert cfg.fallback_export_format == E2EFormat.CSV
    assert len(cfg.export_items) == 1
    assert cfg.export_items[0].export_title == 'summary'
    assert cfg.export_items[0].selected_format == E2EFormat.CSV
    assert cfg.export_items[0].char_encoding == 'latin-1'
    assert cfg.sections == [
        {'name': 'current', 'minutes': 30, 'required': False}
    ]
    assert not cfg.empty_tags
    assert not hook.calls
    assert not hook.old_paths_moved
