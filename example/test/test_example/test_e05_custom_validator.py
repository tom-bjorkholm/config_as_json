#! /usr/local/bin/python3
"""Tests for the custom-validator teaching example."""

# Copyright (c) 2026 Tom Björkholm
# MIT License

import sys
from io import StringIO
from tempfile import TemporaryDirectory
import pytest
import example.e05_custom_validator as e05_module
from example.cmd_line_handling import SetValues
from example.e05_custom_validator import ExampleConfig5
from example.e05_custom_validator import OutputFormatSubtypeValidator
from example.e05_custom_validator import e05_custom_validator_print
from example.e05_custom_validator import e05_custom_validator_set
from example.e05_custom_validator import main
from .helpers import assert_main_round_trip_print_output
from .helpers import assert_validator_error_output, assert_write_command_output
from .helpers import patch_config_factory_stderr, write_json_file


def test_custom_validator_set_uses_defaults_when_no_overrides(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Write a configuration file with the default values."""
    with TemporaryDirectory() as dirname:
        config_file = dirname + '/custom_validator.cfg'
        e05_custom_validator_set({}, config_file)
        config = ExampleConfig5(from_json_filename=config_file)
        with open(config_file, encoding='UTF-8') as file_obj:
            json_text = file_obj.read()
    assert_write_command_output(capsys, config_file)
    assert config.output_format == 'Excel'
    assert config.output_subtype == 'OpenPyxl'
    assert '"output_format": "Excel"' in json_text
    assert '"output_subtype": "OpenPyxl"' in json_text


def test_custom_validator_set_stores_overrides_and_normalizes(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Write overridden values and normalize them to the chosen spelling."""
    set_values: SetValues = {
        'output_format': 'csv',
        'output_subtype': 'unixdialect'
    }
    with TemporaryDirectory() as dirname:
        config_file = dirname + '/custom_validator.cfg'
        e05_custom_validator_set(set_values, config_file)
        config = ExampleConfig5(from_json_filename=config_file)
        with open(config_file, encoding='UTF-8') as file_obj:
            json_text = file_obj.read()
    assert_write_command_output(capsys, config_file)
    assert config.output_format == 'CSV'
    assert config.output_subtype == 'unixDialect'
    assert '"output_format": "CSV"' in json_text
    assert '"output_subtype": "unixDialect"' in json_text


def test_custom_validator_set_reports_invalid_format_subtype_pair(
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch) -> None:
    """Show the custom validator message when writing an invalid pair."""
    stderr_buffer = StringIO()
    patch_config_factory_stderr(monkeypatch,
                                e05_module,
                                'ExampleConfig5',
                                ExampleConfig5,
                                stderr_buffer)
    with TemporaryDirectory() as dirname:
        config_file = dirname + '/custom_validator.cfg'
        e05_custom_validator_set({'output_format': 'CSV',
                                  'output_subtype': 'OpenPyxl'},
                                 config_file)
    assert_validator_error_output(
        capsys,
        stderr_buffer,
        ['output_subtype OpenPyxl',
         'output_format CSV',
         'excelDialect, unixDialect']
    )


def test_custom_validator_print_reports_invalid_stored_pair(
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch) -> None:
    """Show the custom validator message when reading an invalid file."""
    stderr_buffer = StringIO()
    patch_config_factory_stderr(monkeypatch,
                                e05_module,
                                'ExampleConfig5',
                                ExampleConfig5,
                                stderr_buffer)
    with TemporaryDirectory() as dirname:
        config_file = dirname + '/custom_validator.cfg'
        write_json_file(config_file,
                        {'output_format': 'Excel',
                         'output_subtype': 'unixDialect'})
        e05_custom_validator_print(config_file)
    assert_validator_error_output(
        capsys,
        stderr_buffer,
        ['output_subtype unixDialect',
         'output_format Excel',
         'PylightXL, OpenPyxl, XlsxWriter']
    )


def test_custom_validator_main_round_trip_prints_values(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Round-trip configuration through the example command line."""
    assert_main_round_trip_print_output(
        capsys,
        main,
        'custom_validator.cfg',
        ['--output-format', 'excel',
         '--output-subtype', 'xlsxwriter'],
        ['Output format: Excel',
         'Output subtype: XlsxWriter',
         'Would write Excel output with the XlsxWriter backend.']
    )


def test_custom_validator_rejects_member_validation_entry_point(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Reject using the whole-config validator as a member validator."""
    validator = OutputFormatSubtypeValidator()
    config = ExampleConfig5()
    with pytest.raises(RuntimeError) as exc:
        validator.validate_member(config, 'output_subtype',
                                  config.output_subtype, sys.stderr)
    out, err = capsys.readouterr()
    assert 'Do not use OutputFormatSubtypeValidator' in str(exc.value)
    assert 'member_names=None' in str(exc.value)
    assert out == ''
    assert 'Do not use OutputFormatSubtypeValidator' in err
