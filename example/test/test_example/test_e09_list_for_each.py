#! /usr/local/bin/python3
"""Tests for the list-of-lists validator teaching example."""

# Copyright (c) 2026 Tom Björkholm
# MIT License

import json
from tempfile import TemporaryDirectory
from typing import cast
import pytest
import example.e09_list_for_each as e09_module
from example.cmd_line_handling import SetValues
from example.e09_list_for_each import ExampleConfig9
from example.e09_list_for_each import e09_list_for_each_print
from example.e09_list_for_each import e09_list_for_each_set
from example.e09_list_for_each import main as e09_main
from .helpers import ExampleProgramSpec
from .helpers import assert_main_round_trip_print_output
from .helpers import assert_print_command_reports_validator_error
from .helpers import assert_write_command_output


E09_SPEC = ExampleProgramSpec(module=e09_module,
                              factory_name='ExampleConfig9',
                              config_factory=ExampleConfig9,
                              set_command=e09_list_for_each_set,
                              print_command=e09_list_for_each_print,
                              config_basename='list_for_each.cfg')


def read_json_data(config_file: str) -> dict[str, object]:
    """Read one JSON config file using UTF-8."""
    with open(config_file, encoding='UTF-8') as file_obj:
        loaded = json.load(file_obj)
    return cast(dict[str, object], loaded)


def test_e09_set_uses_defaults_when_no_overrides(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Write the default configuration for the list-of-lists example."""
    with TemporaryDirectory() as dirname:
        config_file = dirname + '/list_for_each.cfg'
        e09_list_for_each_set({}, config_file)
        config = ExampleConfig9(from_json_filename=config_file)
        json_data = read_json_data(config_file)
    assert_write_command_output(capsys, config_file)
    assert config.daily_hour_ranges == [[8, 12], [14, 18]]
    assert json_data == {'daily_hour_ranges': [[8, 12], [14, 18]]}


def test_e09_print_reads_valid_nested_list(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Read a valid list-of-lists configuration without errors."""
    with TemporaryDirectory() as dirname:
        config_file = dirname + '/list_for_each.cfg'
        with open(config_file, 'w', encoding='UTF-8') as file_obj:
            json.dump({'daily_hour_ranges': [[6, 10], [13, 17], [20, 22]]},
                      file_obj)
        e09_list_for_each_print(config_file)
    out, err = capsys.readouterr()
    assert err == ''
    assert 'Daily hour ranges: [[6, 10], [13, 17], [20, 22]]' in out
    assert 'Day 0: from 6 to 10' in out
    assert 'Day 1: from 13 to 17' in out
    assert 'Day 2: from 20 to 22' in out


def test_e09_print_reports_outer_list_too_short(
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch) -> None:
    """Reject an empty outer list before the per-element step runs."""
    assert_print_command_reports_validator_error(
        capsys,
        monkeypatch,
        E09_SPEC,
        {'daily_hour_ranges': []},
        ['daily_hour_ranges', 'size 0', 'minimum 1']
    )


def test_e09_print_reports_outer_list_too_long(
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch) -> None:
    """Reject an outer list with more than the allowed number of days."""
    too_many_days = [[h, h + 1] for h in range(8)]
    assert_print_command_reports_validator_error(
        capsys,
        monkeypatch,
        E09_SPEC,
        {'daily_hour_ranges': too_many_days},
        ['daily_hour_ranges', 'size 8', 'maximum 7']
    )


def test_e09_print_reports_invalid_element_type(
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch) -> None:
    """Reject an outer element that is not itself a list."""
    assert_print_command_reports_validator_error(
        capsys,
        monkeypatch,
        E09_SPEC,
        {'daily_hour_ranges': [[8, 12], 14]},
        ['daily_hour_ranges[1]', 'type int', 'expected list']
    )


def test_e09_print_reports_inner_list_wrong_size(
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch) -> None:
    """Reject an inner list whose size is not exactly 2."""
    assert_print_command_reports_validator_error(
        capsys,
        monkeypatch,
        E09_SPEC,
        {'daily_hour_ranges': [[8, 12, 15]]},
        ['daily_hour_ranges[0]', 'size 3', 'maximum 2']
    )


def test_e09_print_reports_invalid_hour_value(
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch) -> None:
    """Reject an hour value that is outside the allowed range."""
    assert_print_command_reports_validator_error(
        capsys,
        monkeypatch,
        E09_SPEC,
        {'daily_hour_ranges': [[8, 12], [14, 25]]},
        ['daily_hour_ranges[1]', 'index 1', 'greater than maximum 23']
    )


def test_e09_main_round_trip_prints_default_ranges(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Round-trip the example through its command-line entry point."""
    assert_main_round_trip_print_output(
        capsys,
        e09_main,
        'list_for_each.cfg',
        [],
        ['Daily hour ranges: [[8, 12], [14, 18]]',
         'Day 0: from 8 to 12',
         'Day 1: from 14 to 18']
    )


def test_e09_set_accepts_nested_list_overrides(
        capsys: pytest.CaptureFixture[str]) -> None:
    """The set helper accepts the nested list the CLI parses from tokens."""
    overrides: SetValues = {
        'daily_hour_ranges': [[6, 10], [13, 17], [20, 22]]
    }
    with TemporaryDirectory() as dirname:
        config_file = dirname + '/list_for_each.cfg'
        e09_list_for_each_set(overrides, config_file)
        config = ExampleConfig9(from_json_filename=config_file)
        json_data = read_json_data(config_file)
    assert_write_command_output(capsys, config_file)
    assert config.daily_hour_ranges == [[6, 10], [13, 17], [20, 22]]
    assert json_data == {
        'daily_hour_ranges': [[6, 10], [13, 17], [20, 22]]
    }


def test_e09_main_round_trip_with_nested_cli_override(
        capsys: pytest.CaptureFixture[str]) -> None:
    """The CLI accepts a matrix via comma-separated nested tokens."""
    assert_main_round_trip_print_output(
        capsys,
        e09_main,
        'list_for_each.cfg',
        ['--daily-hour-ranges', '6,10', '13,17', '20,22'],
        ['Daily hour ranges: [[6, 10], [13, 17], [20, 22]]',
         'Day 0: from 6 to 10',
         'Day 1: from 13 to 17',
         'Day 2: from 20 to 22']
    )


def test_e09_main_round_trip_with_single_day_cli_override(
        capsys: pytest.CaptureFixture[str]) -> None:
    """A single CLI token becomes a matrix with one inner list."""
    assert_main_round_trip_print_output(
        capsys,
        e09_main,
        'list_for_each.cfg',
        ['--daily-hour-ranges', '9,17'],
        ['Daily hour ranges: [[9, 17]]',
         'Day 0: from 9 to 17']
    )
