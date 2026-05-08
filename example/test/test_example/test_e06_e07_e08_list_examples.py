#! /usr/local/bin/python3
"""Tests for the list-validator teaching examples."""

# Copyright (c) 2026 Tom Björkholm
# MIT License

import json
from tempfile import TemporaryDirectory
from typing import Sequence, cast
import pytest
import example.e06_list_basic_validators as e06_module
import example.e07_list_order_vs_normalize as e07_module
import example.e08_combined_list_validators as e08_module
from example.cmd_line_handling import SetValues
from example.e06_list_basic_validators import ExampleConfig6
from example.e06_list_basic_validators import e06_list_basic_validators_print
from example.e06_list_basic_validators import e06_list_basic_validators_set
from example.e06_list_basic_validators import main as e06_main
from example.e07_list_order_vs_normalize import ExampleConfig7
from example.e07_list_order_vs_normalize import \
    e07_list_order_vs_normalize_print, e07_list_order_vs_normalize_set
from example.e07_list_order_vs_normalize import main as e07_main
from example.e08_combined_list_validators import ExampleConfig8
from example.e08_combined_list_validators import (
    e08_combined_list_validators_print
)
from example.e08_combined_list_validators import (
    e08_combined_list_validators_set
)
from example.e08_combined_list_validators import main as e08_main
from .helpers import ExampleProgramSpec
from .helpers import assert_main_round_trip_print_output
from .helpers import assert_print_command_reports_validator_error
from .helpers import assert_set_command_reports_validator_error
from .helpers import assert_write_command_output


E06_SPEC = ExampleProgramSpec(module=e06_module,
                              factory_name='ExampleConfig6',
                              config_factory=ExampleConfig6,
                              set_command=e06_list_basic_validators_set,
                              print_command=e06_list_basic_validators_print,
                              config_basename='list_basic_validators.cfg')

E07_SPEC = ExampleProgramSpec(module=e07_module,
                              factory_name='ExampleConfig7',
                              config_factory=ExampleConfig7,
                              set_command=e07_list_order_vs_normalize_set,
                              print_command=e07_list_order_vs_normalize_print,
                              config_basename='list_order_vs_normalize.cfg')

E08_SPEC = ExampleProgramSpec(module=e08_module,
                              factory_name='ExampleConfig8',
                              config_factory=ExampleConfig8,
                              set_command=e08_combined_list_validators_set,
                              print_command=e08_combined_list_validators_print,
                              config_basename='combined_list_validators.cfg')


def _pdf_formats(config: ExampleConfig6) -> Sequence[str]:
    """Return a patched report-format list for dynamic validation tests."""
    _ = config
    return ['json', 'html', 'pdf']


def read_json_data(config_file: str) -> dict[str, object]:
    """Read one JSON config file using UTF-8."""
    with open(config_file, encoding='UTF-8') as file_obj:
        loaded = json.load(file_obj)
    return cast(dict[str, object], loaded)


def test_e06_set_uses_defaults_when_no_overrides(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Write the default list configuration for the first list example."""
    with TemporaryDirectory() as dirname:
        config_file = dirname + '/list_basic_validators.cfg'
        e06_list_basic_validators_set({}, config_file)
        config = ExampleConfig6(from_json_filename=config_file)
        json_data = read_json_data(config_file)
    assert_write_command_output(capsys, config_file)
    assert config.retry_delays_seconds == [1, 5, 10]
    assert config.report_formats == ['json', 'html']
    assert config.backup_servers == ['backup-a', 'backup-b']
    assert json_data == {
        'retry_delays_seconds': [1, 5, 10],
        'report_formats': ['json', 'html'],
        'backup_servers': ['backup-a', 'backup-b']
    }


def test_e06_set_stores_valid_list_overrides(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Store valid list overrides without changing their order or values."""
    set_values: SetValues = {
        'retry_delays_seconds': [2, 4, 8],
        'report_formats': ['csv', 'json'],
        'backup_servers': ['backup-west']
    }
    with TemporaryDirectory() as dirname:
        config_file = dirname + '/list_basic_validators.cfg'
        e06_list_basic_validators_set(set_values, config_file)
        config = ExampleConfig6(from_json_filename=config_file)
        json_data = read_json_data(config_file)
    assert_write_command_output(capsys, config_file)
    assert config.retry_delays_seconds == [2, 4, 8]
    assert config.report_formats == ['csv', 'json']
    assert config.backup_servers == ['backup-west']
    assert json_data == {
        'retry_delays_seconds': [2, 4, 8],
        'report_formats': ['csv', 'json'],
        'backup_servers': ['backup-west']
    }


def test_e06_report_formats_are_dynamic(capsys: pytest.CaptureFixture[str],
                                        monkeypatch: pytest.MonkeyPatch) \
        -> None:
    """Show that report-format choices are read from a method."""
    monkeypatch.setattr(ExampleConfig6, 'allowed_report_formats', _pdf_formats)
    set_values: SetValues = {
        'report_formats': ['pdf']
    }
    with TemporaryDirectory() as dirname:
        config_file = dirname + '/list_basic_validators.cfg'
        e06_list_basic_validators_set(set_values, config_file)
        config = ExampleConfig6(from_json_filename=config_file)
    assert_write_command_output(capsys, config_file)
    assert config.report_formats == ['pdf']


def test_e06_set_reports_invalid_report_format(
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch) -> None:
    """Report an invalid string element in one list member."""
    assert_set_command_reports_validator_error(
        capsys,
        monkeypatch,
        E06_SPEC,
        {'report_formats': ['json', 'pdf']},
        ['report_formats', 'index 1', 'json, html, csv']
    )


def test_e06_print_reports_invalid_backup_server_count(
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch) -> None:
    """Report that the stored list is too small when reading it back."""
    assert_print_command_reports_validator_error(
        capsys,
        monkeypatch,
        E06_SPEC,
        {
            'retry_delays_seconds': [1, 5, 10],
            'report_formats': ['json'],
            'backup_servers': []
        },
        ['backup_servers', 'size 0', 'minimum 1']
    )


def test_e06_main_round_trip_prints_list_values(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Round-trip the first list example through the command line."""
    assert_main_round_trip_print_output(
        capsys,
        e06_main,
        'list_basic_validators.cfg',
        ['--retry-delays-seconds', '2', '4', '8',
         '--report-formats', 'csv', 'json',
         '--backup-servers', 'backup-west'],
        ['Retry delays in seconds: [2, 4, 8]',
         "Report formats: ['csv', 'json']",
         "Backup servers: ['backup-west']"]
    )


def test_e07_set_uses_defaults_when_no_overrides(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Write the default configuration for the order example."""
    with TemporaryDirectory() as dirname:
        config_file = dirname + '/list_order_vs_normalize.cfg'
        e07_list_order_vs_normalize_set({}, config_file)
        config = ExampleConfig7(from_json_filename=config_file)
        json_data = read_json_data(config_file)
    assert_write_command_output(capsys, config_file)
    assert config.alert_thresholds == pytest.approx([0.5, 0.75, 0.9])
    assert config.report_names == ['Alpha', 'beta', 'Summary']
    assert json_data == {
        'alert_thresholds': [0.5, 0.75, 0.9],
        'report_names': ['Alpha', 'beta', 'Summary']
    }


def test_e07_set_normalizes_report_names_with_custom_comparator(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Sort one list case-insensitively while leaving the other as given."""
    set_values: SetValues = {
        'alert_thresholds': [0.2, 0.4, 0.8],
        'report_names': ['summary', 'Alpha', 'beta']
    }
    with TemporaryDirectory() as dirname:
        config_file = dirname + '/list_order_vs_normalize.cfg'
        e07_list_order_vs_normalize_set(set_values, config_file)
        config = ExampleConfig7(from_json_filename=config_file)
        json_data = read_json_data(config_file)
    assert_write_command_output(capsys, config_file)
    assert config.alert_thresholds == pytest.approx([0.2, 0.4, 0.8])
    assert config.report_names == ['Alpha', 'beta', 'summary']
    assert json_data == {
        'alert_thresholds': [0.2, 0.4, 0.8],
        'report_names': ['Alpha', 'beta', 'summary']
    }


def test_e07_set_reports_invalid_threshold_order(
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch) -> None:
    """Reject threshold lists that are not already ordered."""
    assert_set_command_reports_validator_error(
        capsys,
        monkeypatch,
        E07_SPEC,
        {'alert_thresholds': [0.8, 0.4]},
        ['alert_thresholds', 'less than previous value 0.8']
    )


def test_e07_print_reports_invalid_report_name_type(
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch) -> None:
    """Reject non-string values in the list that should be sorted."""
    assert_print_command_reports_validator_error(
        capsys,
        monkeypatch,
        E07_SPEC,
        {
            'alert_thresholds': [0.5, 0.75, 0.9],
            'report_names': ['Alpha', 1]
        },
        ['report_names', 'index 1', 'not of type str']
    )


def test_e07_main_round_trip_prints_checked_and_normalized_lists(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Round-trip the order example through the command line."""
    assert_main_round_trip_print_output(
        capsys,
        e07_main,
        'list_order_vs_normalize.cfg',
        ['--alert-thresholds', '0.2', '0.4', '0.8',
         '--report-names', 'summary', 'Alpha', 'beta'],
        ['Alert thresholds: [0.2, 0.4, 0.8]',
         "Report names: ['Alpha', 'beta', 'summary']"]
    )


def test_e08_set_uses_defaults_when_no_overrides(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Write the default configuration for the combined example."""
    with TemporaryDirectory() as dirname:
        config_file = dirname + '/combined_list_validators.cfg'
        e08_combined_list_validators_set({}, config_file)
        config = ExampleConfig8(from_json_filename=config_file)
        json_data = read_json_data(config_file)
    assert_write_command_output(capsys, config_file)
    assert config.run_hours_utc == [3, 12, 18]
    assert json_data == {'run_hours_utc': [3, 12, 18]}


def test_e08_set_sorts_and_deduplicates_before_writing(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Normalize the stored run hours before they are written to JSON."""
    set_values: SetValues = {'run_hours_utc': [18, 3, 12, 3]}
    with TemporaryDirectory() as dirname:
        config_file = dirname + '/combined_list_validators.cfg'
        e08_combined_list_validators_set(set_values, config_file)
        config = ExampleConfig8(from_json_filename=config_file)
        json_data = read_json_data(config_file)
    assert_write_command_output(capsys, config_file)
    assert config.run_hours_utc == [3, 12, 18]
    assert json_data == {'run_hours_utc': [3, 12, 18]}


def test_e08_set_checks_size_after_deduplication(
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch) -> None:
    """Show that the size rule sees the normalized list from earlier steps."""
    assert_set_command_reports_validator_error(
        capsys,
        monkeypatch,
        E08_SPEC,
        {'run_hours_utc': [12, 12]},
        ['run_hours_utc', 'size 1', 'minimum 2']
    )


def test_e08_print_reports_invalid_hour_before_normalization(
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch) -> None:
    """Reject impossible values before later validators can normalize."""
    assert_print_command_reports_validator_error(
        capsys,
        monkeypatch,
        E08_SPEC,
        {'run_hours_utc': [4, 25]},
        ['run_hours_utc', 'greater than maximum 23']
    )


def test_e08_main_round_trip_prints_normalized_run_hours(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Round-trip the combined example through the command line."""
    assert_main_round_trip_print_output(
        capsys,
        e08_main,
        'combined_list_validators.cfg',
        ['--run-hours-utc', '18', '3', '12', '3'],
        ['Run hours in UTC: [3, 12, 18]',
         'Would run the job at UTC hours: 3, 12, 18']
    )
