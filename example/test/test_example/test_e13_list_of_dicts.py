#! /usr/local/bin/python3
"""Tests for the combined list-of-dicts validator teaching example."""

# Copyright (c) 2026 Tom Björkholm
# MIT License

import json
from tempfile import TemporaryDirectory
from typing import cast
import pytest
import example.e13_list_of_dicts as e13_module
from example.cmd_line_handling import SetValues
from example.e13_list_of_dicts import ExampleConfig13
from example.e13_list_of_dicts import e13_list_of_dicts_print
from example.e13_list_of_dicts import e13_list_of_dicts_set
from example.e13_list_of_dicts import main as e13_main
from .helpers import ExampleProgramSpec
from .helpers import assert_main_round_trip_print_output
from .helpers import assert_print_command_reports_validator_error
from .helpers import assert_write_command_output


E13_SPEC = ExampleProgramSpec(module=e13_module,
                              factory_name='ExampleConfig13',
                              config_factory=ExampleConfig13,
                              set_command=e13_list_of_dicts_set,
                              print_command=e13_list_of_dicts_print,
                              config_basename='list_of_dicts.cfg')


DEFAULT_WINDOW: dict[str, object] = {
    'name': 'weekday',
    'hours_utc': [8, 9, 10, 11, 12, 13, 14, 15, 16, 17],
    'priority': 5
}
"""Default maintenance window stored on the example configuration."""


def read_json_data(config_file: str) -> dict[str, object]:
    """Read one JSON config file using UTF-8."""
    with open(config_file, encoding='UTF-8') as file_obj:
        loaded = json.load(file_obj)
    return cast(dict[str, object], loaded)


def test_e13_set_uses_defaults_when_no_overrides(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Write the default list-of-dicts configuration."""
    with TemporaryDirectory() as dirname:
        config_file = dirname + '/list_of_dicts.cfg'
        e13_list_of_dicts_set({}, config_file)
        config = ExampleConfig13(from_json_filename=config_file)
        json_data = read_json_data(config_file)
    assert_write_command_output(capsys, config_file)
    assert config.maintenance_windows == [DEFAULT_WINDOW]
    assert json_data == {'maintenance_windows': [DEFAULT_WINDOW]}


def test_e13_set_accepts_window_without_optional_priority(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Accept a window that omits the optional priority key."""
    overrides = cast(SetValues, {
        'maintenance_windows': [{
            'name': 'weekend',
            'hours_utc': [10, 11, 12]
        }]
    })
    with TemporaryDirectory() as dirname:
        config_file = dirname + '/list_of_dicts.cfg'
        e13_list_of_dicts_set(overrides, config_file)
        config = ExampleConfig13(from_json_filename=config_file)
    assert_write_command_output(capsys, config_file)
    assert config.maintenance_windows == [{
        'name': 'weekend', 'hours_utc': [10, 11, 12]
    }]


def test_e13_print_reports_outer_list_too_short(
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch) -> None:
    """Reject an empty maintenance windows list."""
    assert_print_command_reports_validator_error(
        capsys,
        monkeypatch,
        E13_SPEC,
        {'maintenance_windows': []},
        ['maintenance_windows', 'size 0', 'minimum 1']
    )


def test_e13_print_reports_outer_list_too_long(
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch) -> None:
    """Reject a maintenance windows list that exceeds the maximum size."""
    too_many_windows = [
        {'name': 'weekday', 'hours_utc': [8]} for _ in range(21)
    ]
    assert_print_command_reports_validator_error(
        capsys,
        monkeypatch,
        E13_SPEC,
        {'maintenance_windows': too_many_windows},
        ['maintenance_windows', 'size 21', 'maximum 20']
    )


def test_e13_print_reports_missing_mandatory_window_key(
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch) -> None:
    """Reject a window dict that lacks a mandatory key."""
    assert_print_command_reports_validator_error(
        capsys,
        monkeypatch,
        E13_SPEC,
        {'maintenance_windows': [{'name': 'weekend'}]},
        ['maintenance_windows', "Mandatory key 'hours_utc'", 'missing']
    )


def test_e13_print_reports_unknown_window_key(
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch) -> None:
    """Reject a window dict that contains an unknown key."""
    assert_print_command_reports_validator_error(
        capsys,
        monkeypatch,
        E13_SPEC,
        {'maintenance_windows': [{
            'name': 'weekend',
            'hours_utc': [10, 11, 12],
            'extra': 'no'
        }]},
        ['maintenance_windows', "Unknown key 'extra'"]
    )


def test_e13_print_reports_inner_list_size_too_small(
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch) -> None:
    """Reject a window whose inner hours_utc list is empty."""
    assert_print_command_reports_validator_error(
        capsys,
        monkeypatch,
        E13_SPEC,
        {'maintenance_windows': [{
            'name': 'weekend',
            'hours_utc': []
        }]},
        ['hours_utc', 'size 0', 'minimum 1']
    )


def test_e13_print_reports_inner_list_value_out_of_range(
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch) -> None:
    """Reject an inner hours_utc element above the rule's maximum."""
    assert_print_command_reports_validator_error(
        capsys,
        monkeypatch,
        E13_SPEC,
        {'maintenance_windows': [{
            'name': 'weekend',
            'hours_utc': [10, 25]
        }]},
        ['hours_utc', 'greater than maximum 23']
    )


def test_e13_print_reports_invalid_window_name(
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch) -> None:
    """Reject a window name that is not in the allowed set."""
    assert_print_command_reports_validator_error(
        capsys,
        monkeypatch,
        E13_SPEC,
        {'maintenance_windows': [{
            'name': 'midweek',
            'hours_utc': [10, 11]
        }]},
        ['name', 'midweek', 'weekday', 'weekend', 'holiday', 'custom']
    )


def test_e13_print_reports_priority_above_maximum(
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch) -> None:
    """Reject a priority above the rule's maximum."""
    assert_print_command_reports_validator_error(
        capsys,
        monkeypatch,
        E13_SPEC,
        {'maintenance_windows': [{
            'name': 'weekend',
            'hours_utc': [10, 11],
            'priority': 99
        }]},
        ['priority', 'greater than maximum 9']
    )


def test_e13_main_round_trip_prints_default_windows(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Round-trip the example through its command-line entry point."""
    assert_main_round_trip_print_output(
        capsys,
        e13_main,
        'list_of_dicts.cfg',
        [],
        ["Maintenance windows: [{'hours_utc': "
         "[8, 9, 10, 11, 12, 13, 14, 15, 16, 17], "
         "'name': 'weekday', 'priority': 5}]",
         'Window 0: name=weekday, hours='
         '[8, 9, 10, 11, 12, 13, 14, 15, 16, 17]']
    )


def test_e13_main_round_trip_with_json_cli_override(
        capsys: pytest.CaptureFixture[str]) -> None:
    """The CLI accepts a list of dicts as one JSON-encoded token."""
    json_override = (
        '[{"name":"weekend","hours_utc":[10,11,12]},'
        '{"name":"weekday","hours_utc":[8,9],"priority":2}]'
    )
    assert_main_round_trip_print_output(
        capsys,
        e13_main,
        'list_of_dicts.cfg',
        ['--maintenance-windows', json_override],
        ["Maintenance windows: ["
         "{'hours_utc': [10, 11, 12], 'name': 'weekend'}, "
         "{'hours_utc': [8, 9], 'name': 'weekday', 'priority': 2}]",
         'Window 0: name=weekend, hours=[10, 11, 12]',
         'Window 1: name=weekday, hours=[8, 9]']
    )
