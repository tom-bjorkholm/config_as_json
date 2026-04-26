#! /usr/local/bin/python3
"""Tests for the discriminated-dict validator teaching example."""

# Copyright (c) 2026 Tom Björkholm
# MIT License

import json
from tempfile import TemporaryDirectory
from typing import cast
import pytest
import example.e14_discriminated_dict_validator as e14_module
from example.cmd_line_handling import SetValues
from example.e14_discriminated_dict_validator import ExampleConfig14
from example.e14_discriminated_dict_validator import \
    e14_discriminated_dict_validator_print
from example.e14_discriminated_dict_validator import \
    e14_discriminated_dict_validator_set
from example.e14_discriminated_dict_validator import main as e14_main
from .helpers import ExampleProgramSpec
from .helpers import assert_main_round_trip_print_output
from .helpers import assert_print_command_reports_validator_error
from .helpers import assert_write_command_output


E14_SPEC = ExampleProgramSpec(
    module=e14_module,
    factory_name='ExampleConfig14',
    config_factory=ExampleConfig14,
    set_command=e14_discriminated_dict_validator_set,
    print_command=e14_discriminated_dict_validator_print,
    config_basename='discriminated_dict_validator.cfg'
)


DEFAULT_EXPORT_TARGET: dict[str, object] = {
    'kind': 'file',
    'filename': 'report.json',
    'format': 'json'
}
"""Default export target stored on the example configuration."""


def read_json_data(config_file: str) -> dict[str, object]:
    """Read one JSON config file using UTF-8."""
    with open(config_file, encoding='UTF-8') as file_obj:
        loaded = json.load(file_obj)
    return cast(dict[str, object], loaded)


def test_e14_set_uses_defaults_when_no_overrides(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Write the default discriminated-dict configuration."""
    with TemporaryDirectory() as dirname:
        config_file = dirname + '/discriminated_dict_validator.cfg'
        e14_discriminated_dict_validator_set({}, config_file)
        config = ExampleConfig14(from_json_filename=config_file)
        json_data = read_json_data(config_file)
    assert_write_command_output(capsys, config_file)
    assert config.export_target == DEFAULT_EXPORT_TARGET
    assert json_data == {'export_target': DEFAULT_EXPORT_TARGET}


def test_e14_set_accepts_queue_variant_and_normalizes_values(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Accept the queue variant and normalize the discriminator and queue."""
    set_values = cast(SetValues, {
        'export_target': {
            'kind': 'QUEUE',
            'queue': 'ALERTS',
            'batch_size': 50
        }
    })
    with TemporaryDirectory() as dirname:
        config_file = dirname + '/discriminated_dict_validator.cfg'
        e14_discriminated_dict_validator_set(set_values, config_file)
        config = ExampleConfig14(from_json_filename=config_file)
        json_data = read_json_data(config_file)
    expected = {'kind': 'queue', 'queue': 'alerts', 'batch_size': 50}
    assert_write_command_output(capsys, config_file)
    assert config.export_target == expected
    assert json_data == {'export_target': expected}


def test_e14_set_accepts_file_variant_without_optional_format(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Accept the file variant when the optional format key is absent."""
    set_values = cast(SetValues, {
        'export_target': {
            'kind': 'file',
            'filename': 'report.csv'
        }
    })
    with TemporaryDirectory() as dirname:
        config_file = dirname + '/discriminated_dict_validator.cfg'
        e14_discriminated_dict_validator_set(set_values, config_file)
        config = ExampleConfig14(from_json_filename=config_file)
    assert_write_command_output(capsys, config_file)
    assert config.export_target == {'kind': 'file',
                                    'filename': 'report.csv'}


def test_e14_print_reports_missing_discriminator(
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch) -> None:
    """Reject an export target without the discriminator key."""
    assert_print_command_reports_validator_error(
        capsys,
        monkeypatch,
        E14_SPEC,
        {'export_target': {'filename': 'report.json'}},
        ['export_target', "Discriminator key 'kind'", 'missing']
    )


def test_e14_print_reports_invalid_kind(
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch) -> None:
    """Reject an export target whose kind is not allowed."""
    assert_print_command_reports_validator_error(
        capsys,
        monkeypatch,
        E14_SPEC,
        {'export_target': {'kind': 'smtp', 'filename': 'report.json'}},
        ['export_target[kind]', 'smtp', 'file', 'queue']
    )


def test_e14_print_reports_missing_variant_key(
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch) -> None:
    """Reject the file variant when filename is missing."""
    assert_print_command_reports_validator_error(
        capsys,
        monkeypatch,
        E14_SPEC,
        {'export_target': {'kind': 'file', 'format': 'json'}},
        ['export_target', "Mandatory key 'filename'", 'missing']
    )


def test_e14_print_reports_key_from_other_variant(
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch) -> None:
    """Reject queue-only keys when the file variant is selected."""
    assert_print_command_reports_validator_error(
        capsys,
        monkeypatch,
        E14_SPEC,
        {'export_target': {
            'kind': 'file',
            'filename': 'report.json',
            'queue': 'reports'
        }},
        ['export_target', "Unknown key 'queue'"]
    )


def test_e14_print_reports_invalid_file_format(
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch) -> None:
    """Reject a file format outside the file variant's allowed values."""
    assert_print_command_reports_validator_error(
        capsys,
        monkeypatch,
        E14_SPEC,
        {'export_target': {
            'kind': 'file',
            'filename': 'report.json',
            'format': 'xml'
        }},
        ['export_target[format]', 'xml', 'json', 'csv']
    )


def test_e14_print_reports_queue_batch_size_above_maximum(
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch) -> None:
    """Reject a queue batch size above the selected variant's maximum."""
    assert_print_command_reports_validator_error(
        capsys,
        monkeypatch,
        E14_SPEC,
        {'export_target': {
            'kind': 'queue',
            'queue': 'reports',
            'batch_size': 1001
        }},
        ['export_target[batch_size]', 'greater than maximum 1000']
    )


def test_e14_main_round_trip_prints_default_file_target(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Round-trip the default file target through the command line."""
    assert_main_round_trip_print_output(
        capsys,
        e14_main,
        'discriminated_dict_validator.cfg',
        [],
        ["Export target: {'filename': 'report.json', 'format': 'json', "
         "'kind': 'file'}",
         'Export kind: file',
         'Filename: report.json']
    )


def test_e14_main_round_trip_with_json_queue_override(
        capsys: pytest.CaptureFixture[str]) -> None:
    """The CLI accepts the discriminated dict as one JSON token."""
    json_override = '{"kind":"QUEUE","queue":"ALERTS","batch_size":50}'
    assert_main_round_trip_print_output(
        capsys,
        e14_main,
        'discriminated_dict_validator.cfg',
        ['--export-target', json_override],
        ["Export target: {'batch_size': 50, 'kind': 'queue', "
         "'queue': 'alerts'}",
         'Export kind: queue',
         'Queue: alerts']
    )
