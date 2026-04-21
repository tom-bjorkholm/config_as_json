#! /usr/local/bin/python3
"""Tests for the scalar validators example program."""

# Copyright (c) 2026 Tom Björkholm
# MIT License

import json
from io import StringIO
from tempfile import TemporaryDirectory
from typing import NamedTuple, Optional, TextIO
import pytest
from config_as_json.commontypes import PathOrStr
from example.cmd_line_handling import SetValues
import example.e03_scalar_validators as e03_module
from example.e03_scalar_validators import ExampleConfig, Severity
from example.e03_scalar_validators import e03_scalar_validators_print
from example.e03_scalar_validators import e03_scalar_validators_set, main


class ExpectedExampleConfig(NamedTuple):
    """Expected values for an ExampleConfig instance."""

    issue_type: str
    number_of_iterations: int
    estimate: int
    severity: Severity
    confidence: float


DEFAULT_EXAMPLE_CONFIG = ExpectedExampleConfig(
    issue_type='Story',
    number_of_iterations=10,
    estimate=5,
    severity=Severity.INFO,
    confidence=0.95
)
"""Default values used by the scalar validator example."""


CONFIGURED_EXAMPLE_CONFIG = ExpectedExampleConfig(
    issue_type='Bug',
    number_of_iterations=20,
    estimate=13,
    severity=Severity.ERROR,
    confidence=0.5
)
"""Representative overridden values used by scalar validator tests."""


def assert_example_config_values(
        config: ExampleConfig,
        expected: ExpectedExampleConfig) -> None:
    """Assert the stored values in an ExampleConfig instance."""
    assert config.issue_type == expected.issue_type
    assert config.number_of_iterations == expected.number_of_iterations
    assert config.estimate == expected.estimate
    assert config.severity == expected.severity
    assert config.confidence == pytest.approx(expected.confidence)


def assert_example_config_written_by_set_command(
        capsys: pytest.CaptureFixture[str],
        set_values: SetValues,
        expected: ExpectedExampleConfig,
        read_json_text: bool = False) -> Optional[str]:
    """Run the set helper and assert the written configuration."""
    with TemporaryDirectory() as dirname:
        config_file = dirname + '/scalar_validators.cfg'
        e03_scalar_validators_set(set_values, config_file)
        config = ExampleConfig(from_json_filename=config_file)
        json_text: Optional[str] = None
        if read_json_text:
            with open(config_file, encoding='UTF-8') as file_obj:
                json_text = file_obj.read()
        out, err = capsys.readouterr()
    assert out == f'Configuration written to {config_file}\n'
    assert err == ''
    assert_example_config_values(config, expected)
    return json_text


def write_example_config_json(
        config_file: str,
        extra_values: Optional[dict[str, object]] = None) -> None:
    """Write JSON text with the schema expected by ExampleConfig."""
    json_data: dict[str, object] = {
        'issue_type': 'Story',
        'number_of_iterations': 10,
        'estimate': 5,
        'severity': 'INFO',
        'confidence': 0.95
    }
    if extra_values is not None:
        json_data.update(extra_values)
    with open(config_file, 'w', encoding='UTF-8') as file_obj:
        json.dump(json_data, file_obj)


def patch_example_config_stderr(
        monkeypatch: pytest.MonkeyPatch,
        stderr_buffer: TextIO) -> None:
    """Patch the example module to use a predictable stderr stream."""

    class CapturingExampleConfig(ExampleConfig):
        """ExampleConfig variant that writes diagnostics to one stream."""

        def __init__(self, from_json_text: Optional[str] = None,
                     from_json_filename: Optional[PathOrStr] = None,
                     stderr_file: TextIO = stderr_buffer) -> None:
            _ = stderr_file
            super().__init__(from_json_text=from_json_text,
                             from_json_filename=from_json_filename,
                             stderr_file=stderr_buffer)

        def write(self, to_json_filename: PathOrStr,
                  stderr_file: TextIO = stderr_buffer) -> None:
            """Write configuration while forcing diagnostics to one stream."""
            _ = stderr_file
            super().write(to_json_filename, stderr_file=stderr_buffer)

    monkeypatch.setattr(e03_module, 'ExampleConfig', CapturingExampleConfig)


def test_e03_scalar_validators_set_uses_defaults_when_no_overrides(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Write a configuration file with the default scalar values."""
    json_text = assert_example_config_written_by_set_command(
        capsys,
        {},
        DEFAULT_EXAMPLE_CONFIG,
        read_json_text=True
    )
    assert json_text is not None
    assert '"issue_type": "Story"' in json_text


def test_e03_scalar_validators_set_stores_overrides_and_normalizes(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Write overridden values and normalize the string validator input."""
    set_values: SetValues = {
        'issue_type': 'bug',
        'number_of_iterations': 20,
        'estimate': 13,
        'severity': Severity.ERROR,
        'confidence': 0.5
    }
    json_text = assert_example_config_written_by_set_command(
        capsys,
        set_values,
        CONFIGURED_EXAMPLE_CONFIG,
        read_json_text=True
    )
    assert json_text is not None
    assert '"issue_type": "Bug"' in json_text


def test_e03_scalar_validators_set_reports_validator_error(
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch) -> None:
    """Show the validator message when writing an invalid value."""
    set_values: SetValues = {'confidence': 1.5}
    stderr_buffer = StringIO()
    patch_example_config_stderr(monkeypatch, stderr_buffer)
    with TemporaryDirectory() as dirname:
        config_file = dirname + '/scalar_validators.cfg'
        e03_scalar_validators_set(set_values, config_file)
        out, _ = capsys.readouterr()
    err = stderr_buffer.getvalue()
    assert out == ''
    assert 'confidence' in err
    assert 'greater than maximum 1.0' in err


def test_e03_scalar_validators_print_reports_invalid_stored_value(
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch) -> None:
    """Show the validator message when reading an invalid file."""
    stderr_buffer = StringIO()
    patch_example_config_stderr(monkeypatch, stderr_buffer)
    with TemporaryDirectory() as dirname:
        config_file = dirname + '/scalar_validators.cfg'
        write_example_config_json(config_file, {'issue_type': 'Feature'})
        e03_scalar_validators_print(config_file)
        out, _ = capsys.readouterr()
    err = stderr_buffer.getvalue()
    assert out == ''
    assert 'issue_type' in err
    assert 'not one of the allowed values' in err


def test_main_round_trip_prints_validated_values(
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
        config_file = dirname + '/scalar_validators.cfg'
        main(['set',
              '--output', config_file,
              '--issue-type', 'epic',
              '--number-of-iterations', '8',
              '--estimate', '8',
              '--severity', 'warning',
              '--confidence', '0.8'])
        _ = capsys.readouterr()
        main(['print', '--input', config_file])
        out, err = capsys.readouterr()
    assert err == ''
    lines = out.strip().splitlines()
    assert lines[0] == f'Configuration read from {config_file}'
    assert lines[1:] == expected_lines


def test_main_set_reports_validator_error(
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch) -> None:
    """Report validator errors from the command line interface."""
    stderr_buffer = StringIO()
    patch_example_config_stderr(monkeypatch, stderr_buffer)
    with TemporaryDirectory() as dirname:
        config_file = dirname + '/scalar_validators.cfg'
        main(['set',
              '--output', config_file,
              '--estimate', '4'])
        out, _ = capsys.readouterr()
    err = stderr_buffer.getvalue()
    assert out == ''
    assert 'estimate' in err
    assert 'not one of the allowed values' in err
