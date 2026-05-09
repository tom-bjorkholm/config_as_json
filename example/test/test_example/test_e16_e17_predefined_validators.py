#! /usr/local/bin/python3
"""Tests for the e16 and e17 predefined-validator examples."""

# Copyright (c) 2026 Tom Björkholm
# MIT License

import json
from tempfile import TemporaryDirectory
from typing import cast
import pytest
import example.e16_type_and_list_of_dicts_validators as e16_module
import example.e17_csv_dialect_and_encoding as e17_module
from example.cmd_line_handling import SetValues
from example.e16_type_and_list_of_dicts_validators import ExampleConfig16
from example.e16_type_and_list_of_dicts_validators import e16_validators_print
from example.e16_type_and_list_of_dicts_validators import e16_validators_set
from example.e16_type_and_list_of_dicts_validators import main as e16_main
from example.e17_csv_dialect_and_encoding import ExampleConfig17
from example.e17_csv_dialect_and_encoding import \
    e17_csv_dialect_and_encoding_print
from example.e17_csv_dialect_and_encoding import \
    e17_csv_dialect_and_encoding_set
from example.e17_csv_dialect_and_encoding import main as e17_main
from .helpers import ExampleProgramSpec
from .helpers import assert_rt_out
from .helpers import assert_print_validator_error
from .helpers import assert_set_validator_error
from .helpers import assert_write_command_output

E16_SPEC = ExampleProgramSpec(module=e16_module,
                              factory_name='ExampleConfig16',
                              config_factory=ExampleConfig16,
                              set_command=e16_validators_set,
                              print_command=e16_validators_print,
                              config_basename='type_validators.cfg')
"""Shared test description for the e16 example."""

E17_SPEC = ExampleProgramSpec(
    module=e17_module, factory_name='ExampleConfig17',
    config_factory=ExampleConfig17,
    set_command=e17_csv_dialect_and_encoding_set,
    print_command=(e17_csv_dialect_and_encoding_print),
    config_basename='csv_encoding.cfg')
"""Shared test description for the e17 example."""

DEFAULT_PIPELINE_STEPS: list[dict[str, object]] = [{
    'name': 'extract',
    'enabled': True
}, {
    'name': 'load',
    'enabled': True,
    'owner': 'data'
}]
"""Default pipeline steps stored on the e16 example configuration."""


def read_json_data(config_file: str) -> dict[str, object]:
    """Read one JSON config file using UTF-8."""
    with open(config_file, encoding='UTF-8') as file_obj:
        loaded = json.load(file_obj)
    return cast(dict[str, object], loaded)


def default_csv_dialect() -> dict[str, object]:
    """Return the default CSV dialect from ExampleConfig17."""
    return dict(ExampleConfig17().csv_dialect)


def e16_json_data(**overrides: object) -> dict[str, object]:
    """Return complete JSON data for ExampleConfig16."""
    json_data: dict[str, object] = {
        'worker_count': 2,
        'alert_recipients': ['ops@example.com'],
        'pipeline_steps': DEFAULT_PIPELINE_STEPS
    }
    json_data.update(overrides)
    return json_data


def e17_json_data(**overrides: object) -> dict[str, object]:
    """Return complete JSON data for ExampleConfig17."""
    json_data: dict[str, object] = {
        'input_encoding': 'utf_8_sig',
        'output_encoding': 'utf-8',
        'csv_dialect': default_csv_dialect()
    }
    json_data.update(overrides)
    return json_data


def test_e16_set_uses_defaults_when_no_overrides(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Write the default e16 configuration."""
    with TemporaryDirectory() as dirname:
        config_file = dirname + '/type_validators.cfg'
        e16_validators_set({}, config_file)
        config = ExampleConfig16(from_json_filename=config_file)
        json_data = read_json_data(config_file)
    assert_write_command_output(capsys, config_file)
    assert config.worker_count == 2
    assert config.alert_recipients == ['ops@example.com']
    assert config.pipeline_steps == DEFAULT_PIPELINE_STEPS
    assert json_data == e16_json_data()


def test_e16_set_accepts_shape_only_overrides(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Accept values that satisfy the three small shape validators."""
    set_values = cast(
        SetValues,
        {
            'worker_count':
            4,
            'alert_recipients': ['ops@example.com', 'dev@example.com'],
            'pipeline_steps': [{
                'name': 'extract',
                'enabled': True
            }, {
                'name': 'publish',
                'enabled': False,
                'owner': 'release'
            }]
        })
    with TemporaryDirectory() as dirname:
        config_file = dirname + '/type_validators.cfg'
        e16_validators_set(set_values, config_file)
        config = ExampleConfig16(from_json_filename=config_file)
    assert_write_command_output(capsys, config_file)
    assert config.worker_count == 4
    assert config.alert_recipients == ['ops@example.com', 'dev@example.com']
    assert config.pipeline_steps[1]['owner'] == 'release'


def test_e16_set_reports_scalar_type_error(
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch) -> None:
    """Reject a scalar member with the wrong runtime type."""
    assert_set_validator_error(capsys, monkeypatch, E16_SPEC,
                               {'worker_count': 'two'},
                               ['worker_count', 'not of type int'])


def test_e16_print_reports_list_element_type_error(
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch) -> None:
    """Reject a list member with an element of the wrong runtime type."""
    assert_print_validator_error(
        capsys, monkeypatch, E16_SPEC,
        e16_json_data(alert_recipients=['ops@example.com', 3]),
        ['alert_recipients', 'index 1', 'not of type str'])


def test_e16_print_reports_missing_step_key(
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch) -> None:
    """Reject a pipeline step missing a mandatory key."""
    assert_print_validator_error(capsys, monkeypatch, E16_SPEC,
                                 e16_json_data(pipeline_steps=[{
                                     'name': 'extract'
                                     }]),
                                 [
                                     'pipeline_steps[0]',
                                     "Mandatory key 'enabled'",
                                     'missing',
                                 ])


def test_e16_print_reports_unknown_step_key(
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch) -> None:
    """Reject a pipeline step that contains an unknown key."""
    assert_print_validator_error(capsys, monkeypatch, E16_SPEC,
                                 e16_json_data(pipeline_steps=[{
                                     'name': 'extract',
                                     'enabled': True,
                                     'extra': 'boom'
                                     }]),
                                 ['pipeline_steps[0]', "Unknown key 'extra'"])


def test_e16_print_reports_non_dict_step(
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch) -> None:
    """Reject a pipeline step that is not a dict."""
    assert_print_validator_error(capsys, monkeypatch, E16_SPEC,
                                 e16_json_data(pipeline_steps=[{
                                     'name': 'extract',
                                     'enabled': True
                                     }, 'load']),
                                 [
                                     'pipeline_steps[1]',
                                     'type str',
                                     'expected dict',
                                 ])


def test_e16_main_round_trip_with_json_cli_override(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Round-trip e16 through its command-line entry point."""
    steps_json = ('[{"name":"extract","enabled":true},'
                  '{"name":"publish","enabled":false,"owner":"release"}]')
    assert_rt_out(
        capsys, e16_main, 'type_validators.cfg', [
            '--worker-count', '4', '--alert-recipients', 'ops@example.com',
            'dev@example.com', '--pipeline-steps', steps_json
        ], [
            'Worker count: 4',
            "Alert recipients: ['ops@example.com', 'dev@example.com']",
            "Pipeline steps: [{'enabled': True, 'name': 'extract'}, "
            "{'enabled': False, 'name': 'publish', 'owner': 'release'}]"])


def test_e17_set_uses_defaults_when_no_overrides(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Write the default e17 configuration."""
    with TemporaryDirectory() as dirname:
        config_file = dirname + '/csv_encoding.cfg'
        e17_csv_dialect_and_encoding_set({}, config_file)
        config = ExampleConfig17(from_json_filename=config_file)
        json_data = read_json_data(config_file)
    assert_write_command_output(capsys, config_file)
    assert config.input_encoding == 'utf_8_sig'
    assert config.output_encoding == 'utf-8'
    assert config.csv_dialect == default_csv_dialect()
    assert json_data == e17_json_data()


def test_e17_set_normalizes_minimal_csv_dialect(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Accept a minimal CSV dialect and fill optional keys with None."""
    set_values = cast(SetValues, {'csv_dialect': {'name': 'csv.excel_tab'}})
    with TemporaryDirectory() as dirname:
        config_file = dirname + '/csv_encoding.cfg'
        e17_csv_dialect_and_encoding_set(set_values, config_file)
        config = ExampleConfig17(from_json_filename=config_file)
    assert_write_command_output(capsys, config_file)
    assert config.csv_dialect == {
        'name': 'csv.excel_tab',
        'delimiter': None,
        'quoting': None,
        'quotechar': None,
        'lineterminator': None,
        'escapechar': None
    }


def test_e17_set_reports_invalid_encoding(
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch) -> None:
    """Reject an encoding that Python does not recognize."""
    assert_set_validator_error(capsys, monkeypatch, E17_SPEC,
                               {'input_encoding': 'not-an-encoding'},
                               ['not-an-encoding', 'input_encoding'])


def test_e17_print_reports_missing_csv_dialect_name(
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch) -> None:
    """Reject a CSV dialect without the required name key."""
    assert_print_validator_error(capsys, monkeypatch, E17_SPEC,
                                 e17_json_data(csv_dialect={'delimiter': ';'}),
                                 [
                                     'csv_dialect',
                                     "Required key 'name' is missing",
                                 ])


def test_e17_print_reports_unknown_csv_quoting(
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch) -> None:
    """Reject a CSV dialect whose quoting value cannot be built."""
    assert_print_validator_error(
        capsys, monkeypatch, E17_SPEC,
        e17_json_data(
            csv_dialect={
                'name': 'csv.excel',
                'quoting': 'csv.quote_sometimes'
            }), ['csv_dialect', 'Unknown csv quoting: csv.quote_sometimes'])


def test_e17_main_round_trip_with_csv_cli_override(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Round-trip e17 through its command-line entry point."""
    dialect_json = ('{"name":"csv.excel_tab","delimiter":";",'
                    '"quotechar":"|","lineterminator":"\\n"}')
    assert_rt_out(capsys, e17_main, 'csv_encoding.cfg',
                  [
                      '--input-encoding',
                      'utf-8',
                      '--output-encoding',
                      'latin-1',
                      '--csv-dialect',
                      dialect_json,
                  ],
                  [
                      'Input encoding: utf-8',
                      'Output encoding: latin-1',
                      'CSV delimiter: ;',
                      'CSV quotechar: |',
                      "CSV line terminator: '\\n'",
                  ])
