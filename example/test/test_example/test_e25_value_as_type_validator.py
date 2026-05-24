#! /usr/local/bin/python3
"""Tests for the value-as-type validator teaching example."""

# Copyright (c) 2026 Tom Björkholm
# MIT License

import json
from tempfile import TemporaryDirectory
from typing import cast
from pytest import CaptureFixture, MonkeyPatch
import example.e25_value_as_type_validator as e25_module
from example.cmd_line_handling import SetValues
from example.e25_value_as_type_validator import ExampleConfig25
from example.e25_value_as_type_validator import e25_value_as_type_print
from example.e25_value_as_type_validator import e25_value_as_type_set
from example.e25_value_as_type_validator import main as e25_main
from .helpers import ExampleProgramSpec
from .helpers import assert_print_validator_error
from .helpers import assert_rt_out
from .helpers import assert_set_validator_error
from .helpers import assert_write_command_output


E25_SPEC = ExampleProgramSpec(module=e25_module,
                              factory_name='ExampleConfig25',
                              config_factory=ExampleConfig25,
                              set_command=e25_value_as_type_set,
                              print_command=e25_value_as_type_print,
                              config_basename='value_as_type.cfg')


def read_json_data(config_file: str) -> dict[str, object]:
    """Read one JSON config file using UTF-8."""
    with open(config_file, encoding='UTF-8') as file_obj:
        loaded = json.load(file_obj)
    return cast(dict[str, object], loaded)


def test_e25_set_defaults(capsys: CaptureFixture[str]) -> None:
    """Write and read the default value-as-type example."""
    with TemporaryDirectory() as dirname:
        config_file = dirname + '/value_as_type.cfg'
        e25_value_as_type_set({}, config_file)
        config = ExampleConfig25(from_json_filename=config_file)
        json_data = read_json_data(config_file)
    assert_write_command_output(capsys, config_file)
    assert config.retry_count == 3
    assert config.story_points == 3
    assert json_data == {'retry_count': 3, 'story_points': 3}


def test_e25_set_normalizes_text(capsys: CaptureFixture[str]) -> None:
    """Accept text values and write their normalized representation."""
    set_values = cast(SetValues, {'retry_count': '5',
                                  'story_points': 'XL'})
    with TemporaryDirectory() as dirname:
        config_file = dirname + '/value_as_type.cfg'
        e25_value_as_type_set(set_values, config_file)
        config = ExampleConfig25(from_json_filename=config_file)
        json_data = read_json_data(config_file)
    assert_write_command_output(capsys, config_file)
    assert config.retry_count == 5
    assert config.story_points == 8
    assert json_data == {'retry_count': 5, 'story_points': 8}


def test_e25_accepts_lower_size(capsys: CaptureFixture[str]) -> None:
    """Accept old T-shirt sizes without requiring exact capitalization."""
    set_values = cast(SetValues, {'story_points': 'm'})
    with TemporaryDirectory() as dirname:
        config_file = dirname + '/value_as_type.cfg'
        e25_value_as_type_set(set_values, config_file)
        config = ExampleConfig25(from_json_filename=config_file)
        json_data = read_json_data(config_file)
    assert_write_command_output(capsys, config_file)
    assert config.story_points == 3
    assert json_data == {'retry_count': 3, 'story_points': 3}


def test_e25_rejects_bad_retry_text(capsys: CaptureFixture[str],
                                    monkeypatch: MonkeyPatch) -> None:
    """Reject retry_count text that cannot be converted to int."""
    set_values = cast(SetValues, {'retry_count': 'five'})
    assert_set_validator_error(capsys, monkeypatch, E25_SPEC, set_values, [
        'retry_count',
        'could not be converted to int'])


def test_e25_rejects_bool_retry(capsys: CaptureFixture[str],
                                monkeypatch: MonkeyPatch) -> None:
    """Reject JSON booleans even though bool is an int subclass."""
    assert_print_validator_error(capsys, monkeypatch, E25_SPEC, {
        'retry_count': True,
        'story_points': 3
    }, [
        'retry_count',
        'must not be of type bool'])


def test_e25_rejects_bad_points(capsys: CaptureFixture[str],
                                monkeypatch: MonkeyPatch) -> None:
    """Reject story point text that is not numeric or a known size."""
    set_values = cast(SetValues, {'story_points': 'sideways'})
    assert_set_validator_error(capsys, monkeypatch, E25_SPEC, set_values, [
        'story_points',
        'could not be converted to int'])


def test_e25_rejects_bool_points(capsys: CaptureFixture[str],
                                 monkeypatch: MonkeyPatch) -> None:
    """Reject JSON booleans even though bool is an int subclass."""
    assert_print_validator_error(capsys, monkeypatch, E25_SPEC, {
        'retry_count': 3,
        'story_points': True
    }, [
        'story_points',
        'must not be of type bool'])


def test_e25_main_round_trip(capsys: CaptureFixture[str]) -> None:
    """Round-trip the value-as-type example through the CLI."""
    assert_rt_out(
        capsys, e25_main, 'value_as_type.cfg',
        ['--retry-count', '6', '--story-points', 'L'], [
            'Retry count: 6',
            'Story points: 5'
        ])
