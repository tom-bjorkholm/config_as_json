#! /usr/local/bin/python3
"""Tests for the projected-member validator teaching example."""

# Copyright (c) 2026 Tom Björkholm
# MIT License

import json
from tempfile import TemporaryDirectory
from typing import cast
import pytest
import example.e15_projected_member_validator as e15_module
from example.cmd_line_handling import SetValues
from example.e15_projected_member_validator import ExampleConfig15
from example.e15_projected_member_validator import \
    e15_projected_member_validator_print
from example.e15_projected_member_validator import \
    e15_projected_member_validator_set
from example.e15_projected_member_validator import main as e15_main
from .helpers import ExampleProgramSpec
from .helpers import assert_main_round_trip_print_output
from .helpers import assert_print_command_reports_validator_error
from .helpers import assert_write_command_output


E15_SPEC = ExampleProgramSpec(
    module=e15_module,
    factory_name='ExampleConfig15',
    config_factory=ExampleConfig15,
    set_command=e15_projected_member_validator_set,
    print_command=e15_projected_member_validator_print,
    config_basename='projected_member_validator.cfg'
)


DEFAULT_RELEASE_STEPS: list[dict[str, object]] = [
    {'name': 'prepare', 'order': 10, 'duration_minutes': 5},
    {'name': 'build', 'order': 20, 'duration_minutes': 15},
    {'name': 'deploy', 'order': 30, 'duration_minutes': 10}
]
"""Default release steps stored on the example configuration."""


def read_json_data(config_file: str) -> dict[str, object]:
    """Read one JSON config file using UTF-8."""
    with open(config_file, encoding='UTF-8') as file_obj:
        loaded = json.load(file_obj)
    return cast(dict[str, object], loaded)


def test_e15_set_uses_defaults_when_no_overrides(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Write the default projected-member configuration."""
    with TemporaryDirectory() as dirname:
        config_file = dirname + '/projected_member_validator.cfg'
        e15_projected_member_validator_set({}, config_file)
        config = ExampleConfig15(from_json_filename=config_file)
        json_data = read_json_data(config_file)
    assert_write_command_output(capsys, config_file)
    assert config.release_steps == DEFAULT_RELEASE_STEPS
    assert json_data == {'release_steps': DEFAULT_RELEASE_STEPS}


def test_e15_set_accepts_steps_and_normalizes_names(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Accept a valid release-step list and normalize step names."""
    set_values = cast(SetValues, {
        'release_steps': [
            {'name': 'PREPARE', 'order': 1, 'duration_minutes': 5},
            {'name': 'TEST', 'order': 2, 'duration_minutes': 30},
            {'name': 'DEPLOY', 'order': 3, 'duration_minutes': 10}
        ]
    })
    expected = [
        {'name': 'prepare', 'order': 1, 'duration_minutes': 5},
        {'name': 'test', 'order': 2, 'duration_minutes': 30},
        {'name': 'deploy', 'order': 3, 'duration_minutes': 10}
    ]
    with TemporaryDirectory() as dirname:
        config_file = dirname + '/projected_member_validator.cfg'
        e15_projected_member_validator_set(set_values, config_file)
        config = ExampleConfig15(from_json_filename=config_file)
        json_data = read_json_data(config_file)
    assert_write_command_output(capsys, config_file)
    assert config.release_steps == expected
    assert json_data == {'release_steps': expected}


def test_e15_print_reports_empty_source_list(
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch) -> None:
    """Reject an empty source list before projecting order values."""
    assert_print_command_reports_validator_error(
        capsys,
        monkeypatch,
        E15_SPEC,
        {'release_steps': []},
        ['release_steps', 'size 0', 'less than minimum 1']
    )


def test_e15_print_reports_missing_step_key(
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch) -> None:
    """Reject a step dict that is missing a mandatory key."""
    assert_print_command_reports_validator_error(
        capsys,
        monkeypatch,
        E15_SPEC,
        {'release_steps': [
            {'name': 'prepare', 'duration_minutes': 5}
        ]},
        ['release_steps[0]', "Mandatory key 'order'", 'missing']
    )


def test_e15_print_reports_invalid_step_name(
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch) -> None:
    """Reject a step name outside the allowed values."""
    assert_print_command_reports_validator_error(
        capsys,
        monkeypatch,
        E15_SPEC,
        {'release_steps': [
            {'name': 'package', 'order': 1, 'duration_minutes': 5}
        ]},
        ['release_steps[0][name]', 'package', 'prepare', 'deploy']
    )


def test_e15_print_reports_order_type_error(
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch) -> None:
    """Reject a step whose order value is not an integer."""
    assert_print_command_reports_validator_error(
        capsys,
        monkeypatch,
        E15_SPEC,
        {'release_steps': [
            {'name': 'prepare', 'order': '1', 'duration_minutes': 5}
        ]},
        ['release_steps[0][order]', 'not of type int']
    )


def test_e15_print_reports_duplicate_projected_order(
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch) -> None:
    """Reject duplicate values in the projected order list."""
    assert_print_command_reports_validator_error(
        capsys,
        monkeypatch,
        E15_SPEC,
        {'release_steps': [
            {'name': 'prepare', 'order': 1, 'duration_minutes': 5},
            {'name': 'build', 'order': 1, 'duration_minutes': 15}
        ]},
        ['release_steps', 'duplicates the value at index 0']
    )


def test_e15_print_reports_decreasing_projected_order(
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch) -> None:
    """Reject a projected order list that is not increasing."""
    assert_print_command_reports_validator_error(
        capsys,
        monkeypatch,
        E15_SPEC,
        {'release_steps': [
            {'name': 'build', 'order': 20, 'duration_minutes': 15},
            {'name': 'prepare', 'order': 10, 'duration_minutes': 5}
        ]},
        ['release_steps', 'at index 1', 'less than previous value 20']
    )


def test_e15_main_round_trip_prints_default_steps(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Round-trip the default release steps through the command line."""
    assert_main_round_trip_print_output(
        capsys,
        e15_main,
        'projected_member_validator.cfg',
        [],
        ["Release steps: [{'duration_minutes': 5, 'name': 'prepare', "
         "'order': 10}, {'duration_minutes': 15, 'name': 'build', "
         "'order': 20}, {'duration_minutes': 10, 'name': 'deploy', "
         "'order': 30}]",
         'Projected order values: [10, 20, 30]']
    )


def test_e15_main_round_trip_with_json_steps_override(
        capsys: pytest.CaptureFixture[str]) -> None:
    """The CLI accepts the release-step list as one JSON token."""
    json_override = '['
    json_override += '{"name":"PREPARE","order":1,"duration_minutes":5},'
    json_override += '{"name":"TEST","order":2,"duration_minutes":30},'
    json_override += '{"name":"DEPLOY","order":3,"duration_minutes":10}'
    json_override += ']'
    assert_main_round_trip_print_output(
        capsys,
        e15_main,
        'projected_member_validator.cfg',
        ['--release-steps', json_override],
        ["Release steps: [{'duration_minutes': 5, 'name': 'prepare', "
         "'order': 1}, {'duration_minutes': 30, 'name': 'test', "
         "'order': 2}, {'duration_minutes': 10, 'name': 'deploy', "
         "'order': 3}]",
         'Projected order values: [1, 2, 3]']
    )
