#! /usr/local/bin/python3
"""Tests shared by the e03 and e04 example programs."""

# Copyright (c) 2026 Tom Björkholm
# MIT License

from io import StringIO
from tempfile import TemporaryDirectory
import pytest
import example.e03_scalar_validators as e03_module
import example.e04_third_party_class as e04_module
from example.cmd_line_handling import SetValues
from example.e03_scalar_validators import ExampleConfig, Severity
from example.e03_scalar_validators import e03_scalar_validators_print
from example.e03_scalar_validators import e03_scalar_validators_set
from example.e03_scalar_validators import main as e03_main
from example.e04_third_party_class import ExampleConfig4
from example.e04_third_party_class import e04_third_party_class_print
from example.e04_third_party_class import e04_third_party_class_set
from example.e04_third_party_class import main as e04_main
from .helpers import CONFIGURED_VALIDATED_EXAMPLE_CONFIG
from .helpers import DEFAULT_VALIDATED_EXAMPLE_CONFIG
from .helpers import ValidatedExampleSpec
from .helpers import assert_validated_example_config_written_by_set_command
from .helpers import assert_validator_error_output
from .helpers import patch_validated_example_config_stderr
from .helpers import write_validated_example_config_json


EXAMPLE_SPECS = [
    ValidatedExampleSpec(
        test_id='e03_scalar_validators',
        module=e03_module,
        factory_name='ExampleConfig',
        config_factory=ExampleConfig,
        set_command=e03_scalar_validators_set,
        print_command=e03_scalar_validators_print,
        main_func=e03_main,
        config_basename='scalar_validators.cfg'
    ),
    ValidatedExampleSpec(
        test_id='e04_third_party_class',
        module=e04_module,
        factory_name='ExampleConfig4',
        config_factory=ExampleConfig4,
        set_command=e04_third_party_class_set,
        print_command=e04_third_party_class_print,
        main_func=e04_main,
        config_basename='third_party_class.cfg'
    )
]
"""Validated example programs that share the same test behavior."""


def example_spec_id(example_spec: ValidatedExampleSpec) -> str:
    """Return the pytest id for one validated example specification."""
    return example_spec.test_id


@pytest.mark.parametrize('example_spec', EXAMPLE_SPECS, ids=example_spec_id)
def test_validated_example_set_uses_defaults_when_no_overrides(
        example_spec: ValidatedExampleSpec,
        capsys: pytest.CaptureFixture[str]) -> None:
    """Write a configuration file with the default validated values."""
    json_text = assert_validated_example_config_written_by_set_command(
        capsys,
        example_spec,
        {},
        DEFAULT_VALIDATED_EXAMPLE_CONFIG,
        read_json_text=True
    )
    assert json_text is not None
    assert '"issue_type": "Story"' in json_text


@pytest.mark.parametrize('example_spec', EXAMPLE_SPECS, ids=example_spec_id)
def test_validated_example_set_stores_overrides_and_normalizes(
        example_spec: ValidatedExampleSpec,
        capsys: pytest.CaptureFixture[str]) -> None:
    """Write overridden values and normalize the string validator input."""
    set_values: SetValues = {
        'issue_type': 'bug',
        'number_of_iterations': 20,
        'estimate': 13,
        'severity': Severity.ERROR,
        'confidence': 0.5
    }
    json_text = assert_validated_example_config_written_by_set_command(
        capsys,
        example_spec,
        set_values,
        CONFIGURED_VALIDATED_EXAMPLE_CONFIG,
        read_json_text=True
    )
    assert json_text is not None
    assert '"issue_type": "Bug"' in json_text


@pytest.mark.parametrize('example_spec', EXAMPLE_SPECS, ids=example_spec_id)
def test_validated_example_set_reports_validator_error(
        example_spec: ValidatedExampleSpec,
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch) -> None:
    """Show the validator message when writing an invalid value."""
    stderr_buffer = StringIO()
    patch_validated_example_config_stderr(
        monkeypatch,
        example_spec,
        stderr_buffer
    )
    with TemporaryDirectory() as dirname:
        config_file = dirname + '/' + example_spec.config_basename
        example_spec.set_command({'confidence': 1.5}, config_file)
    assert_validator_error_output(
        capsys,
        stderr_buffer,
        ['confidence', 'greater than maximum 1.0']
    )


@pytest.mark.parametrize('example_spec', EXAMPLE_SPECS, ids=example_spec_id)
def test_validated_example_print_reports_invalid_stored_value(
        example_spec: ValidatedExampleSpec,
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch) -> None:
    """Show the validator message when reading an invalid file."""
    stderr_buffer = StringIO()
    patch_validated_example_config_stderr(
        monkeypatch,
        example_spec,
        stderr_buffer
    )
    with TemporaryDirectory() as dirname:
        config_file = dirname + '/' + example_spec.config_basename
        write_validated_example_config_json(
            config_file,
            {'issue_type': 'Feature'}
        )
        example_spec.print_command(config_file)
    assert_validator_error_output(
        capsys,
        stderr_buffer,
        ['issue_type', 'not one of the allowed values']
    )


@pytest.mark.parametrize('example_spec', EXAMPLE_SPECS, ids=example_spec_id)
def test_validated_example_main_round_trip_prints_values(
        example_spec: ValidatedExampleSpec,
        capsys: pytest.CaptureFixture[str]) -> None:
    """Round-trip configuration through the example command line."""
    expected_lines = [
        'Issue type: Epic',
        'Number of iterations: 8',
        'Estimate: 8',
        'Severity: WARNING',
        'Confidence: 0.8'
    ]
    with TemporaryDirectory() as dirname:
        config_file = dirname + '/' + example_spec.config_basename
        example_spec.main_func(['set',
                                '--output', config_file,
                                '--issue-type', 'epic',
                                '--number-of-iterations', '8',
                                '--estimate', '8',
                                '--severity', 'warning',
                                '--confidence', '0.8'])
        _ = capsys.readouterr()
        example_spec.main_func(['print', '--input', config_file])
        out, err = capsys.readouterr()
    assert err == ''
    lines = out.strip().splitlines()
    assert lines[0] == f'Configuration read from {config_file}'
    assert lines[1:] == expected_lines


@pytest.mark.parametrize('example_spec', EXAMPLE_SPECS, ids=example_spec_id)
def test_validated_example_main_set_reports_validator_error(
        example_spec: ValidatedExampleSpec,
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch) -> None:
    """Report write-time validator errors from the command line."""
    stderr_buffer = StringIO()
    patch_validated_example_config_stderr(
        monkeypatch,
        example_spec,
        stderr_buffer
    )
    with TemporaryDirectory() as dirname:
        config_file = dirname + '/' + example_spec.config_basename
        example_spec.main_func(['set',
                                '--output', config_file,
                                '--estimate', '4'])
    assert_validator_error_output(
        capsys,
        stderr_buffer,
        ['estimate', 'not one of the allowed values']
    )


@pytest.mark.parametrize('example_spec', EXAMPLE_SPECS, ids=example_spec_id)
def test_validated_example_main_print_reports_validator_error(
        example_spec: ValidatedExampleSpec,
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch) -> None:
    """Report read-time validator errors from the command line."""
    stderr_buffer = StringIO()
    patch_validated_example_config_stderr(
        monkeypatch,
        example_spec,
        stderr_buffer
    )
    with TemporaryDirectory() as dirname:
        config_file = dirname + '/' + example_spec.config_basename
        write_validated_example_config_json(
            config_file,
            {'number_of_iterations': 0}
        )
        example_spec.main_func(['print', '--input', config_file])
    assert_validator_error_output(
        capsys,
        stderr_buffer,
        ['number_of_iterations', 'less than minimum 1']
    )
