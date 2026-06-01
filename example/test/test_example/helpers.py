#! /usr/local/bin/python3
"""Shared helpers for example program tests."""

# Copyright (c) 2026 Tom Björkholm
# MIT License

import json
from io import StringIO
from types import ModuleType
from tempfile import TemporaryDirectory
from typing import Callable, Generic, NamedTuple, Optional, Protocol, TextIO
from typing import TypeVar
import pytest
from config_as_json.commontypes import PathOrStr
from example.cmd_line_handling import SetValues
from example.e01_simple_config import SimpleConfig, YesNoAsk
from example.e03_scalar_validators import Severity


class ExpectedSimpleConfig(NamedTuple):
    """Expected values for a SimpleConfig instance."""

    name: str
    answer: int
    approximation: float
    easy: bool
    confirmation: YesNoAsk


DEFAULT_SIMPLE_CONFIG = ExpectedSimpleConfig(name='simple or complex',
                                             answer=42, approximation=3.14159,
                                             easy=True,
                                             confirmation=YesNoAsk.ASK)
"""Default values used by the simple example configuration."""

CONFIGURED_SIMPLE_CONFIG = ExpectedSimpleConfig(name='configured', answer=7,
                                                approximation=2.5, easy=False,
                                                confirmation=YesNoAsk.NO)
"""Representative overridden values used by simple config tests."""


# pylint: disable=too-few-public-methods
class SupportsWrite(Protocol):
    """Protocol for config objects that can be written to a file."""

    def write(self, to_json_filename: PathOrStr,
              stderr_file: TextIO = ...) -> None:
        """Write the configuration to a file."""


WriteConfigInstance_co = TypeVar('WriteConfigInstance_co', bound=SupportsWrite,
                                 covariant=True)


class WriteConfigFactory(Protocol[WriteConfigInstance_co]):
    """Factory protocol for config classes that support write()."""

    def __call__(self, from_json_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 stderr_file: TextIO = ...) -> WriteConfigInstance_co:
        """Create a writable config instance."""


class SupportsValidatedExampleConfig(Protocol):
    """Protocol for the e03 and e04 example configuration objects."""

    issue_type: str
    number_of_iterations: int
    estimate: int
    severity: Severity
    confidence: float


class SupportsValidatedConfigWrite(SupportsWrite,
                                   SupportsValidatedExampleConfig, Protocol):
    """Protocol for validated example configs that can be written."""


ConfigInstance_co = TypeVar('ConfigInstance_co',
                            bound=SupportsValidatedConfigWrite, covariant=True)


class ValidatedExampleConfigFactory(WriteConfigFactory[ConfigInstance_co],
                                    Protocol[ConfigInstance_co]):
    """Factory protocol for the e03 and e04 example config classes."""


# pylint: enable=too-few-public-methods


class ExpectedValidatedExampleConfig(NamedTuple):
    """Expected values for the e03 and e04 example configurations."""

    issue_type: str
    number_of_iterations: int
    estimate: int
    severity: Severity
    confidence: float


DEFAULT_VALIDATED_EXAMPLE_CONFIG = ExpectedValidatedExampleConfig(
    issue_type='Story', number_of_iterations=10, estimate=5,
    severity=Severity.INFO, confidence=0.95)
"""Default values used by the e03 and e04 example configurations."""

CONFIGURED_VALIDATED_EXAMPLE_CONFIG = ExpectedValidatedExampleConfig(
    issue_type='Bug', number_of_iterations=20, estimate=13,
    severity=Severity.ERROR, confidence=0.5)
"""Representative overridden values used by the e03 and e04 tests."""


class ValidatedExampleSpec(NamedTuple):
    """Describe one example program that uses the shared validator tests."""

    test_id: str
    module: ModuleType
    factory_name: str
    config_factory: ValidatedExampleConfigFactory[SupportsValidatedConfigWrite]
    set_command: Callable[[SetValues, PathOrStr], None]
    print_command: Callable[[PathOrStr], None]
    main_func: Callable[[Optional[list[str]]], None]
    config_basename: str


ExampleProgramInstance_co = TypeVar('ExampleProgramInstance_co',
                                    bound=SupportsWrite, covariant=True)


class ExampleProgramSpec(NamedTuple, Generic[ExampleProgramInstance_co]):
    """Describe one example program for shared set/print helper tests."""

    module: ModuleType
    factory_name: str
    config_factory: WriteConfigFactory[ExampleProgramInstance_co]
    set_command: Callable[[SetValues, PathOrStr], None]
    print_command: Callable[[PathOrStr], None]
    config_basename: str


def assert_simple_config_values(config: SimpleConfig,
                                expected: ExpectedSimpleConfig) -> None:
    """Assert the stored values in a simple example configuration."""
    assert config.name == expected.name
    assert config.answer == expected.answer
    assert config.approximation == pytest.approx(expected.approximation)
    assert config.easy is expected.easy
    assert config.confirmation == expected.confirmation


def assert_write_command_output(capsys: pytest.CaptureFixture[str],
                                config_file: str) -> None:
    """Assert the standard output from the example set command."""
    out, err = capsys.readouterr()
    assert out == f'Configuration written to {config_file}\n'
    assert err == ''


def write_json_file(config_file: str, json_data: dict[str, object]) -> None:
    """Write one JSON object to a file using UTF-8."""
    with open(config_file, 'w', encoding='UTF-8') as file_obj:
        json.dump(json_data, file_obj)


def patch_config_factory_stderr(
        monkeypatch: pytest.MonkeyPatch, module: ModuleType, factory_name: str,
        config_factory: WriteConfigFactory[WriteConfigInstance_co],
        stderr_buffer: TextIO) -> None:
    """Patch one config factory so all diagnostics go to one stream."""

    def create_config(from_json_text: Optional[str] = None,
                      from_json_filename: Optional[PathOrStr] = None,
                      stderr_file: TextIO = stderr_buffer) -> \
            WriteConfigInstance_co:
        """Create one config instance with patched diagnostics."""
        _ = stderr_file
        config = config_factory(from_json_text=from_json_text,
                                from_json_filename=from_json_filename,
                                stderr_file=stderr_buffer)
        original_write = config.write

        def capturing_write(to_json_filename: PathOrStr,
                            stderr_file: TextIO = stderr_buffer) -> None:
            """Write using the patched stderr stream."""
            _ = stderr_file
            original_write(to_json_filename, stderr_file=stderr_buffer)

        setattr(config, 'write', capturing_write)
        return config

    monkeypatch.setattr(module, factory_name, create_config)


def assert_rt_out(capsys: pytest.CaptureFixture[str],
                  main_func: Callable[[Optional[list[str]]], None],
                  config_basename: str, set_args: list[str],
                  expected_lines: list[str]) -> None:
    """Run one example through set then print and assert the output."""
    with TemporaryDirectory() as dirname:
        config_file = dirname + '/' + config_basename
        main_func(['set', '--output', config_file, *set_args])
        _ = capsys.readouterr()
        main_func(['print', '--input', config_file])
        out, err = capsys.readouterr()
    assert err == ''
    assert out == '\n'.join(
        [f'Configuration read from {config_file}', *expected_lines]) + '\n'


def assert_simple_config_written_by_main(
        capsys: pytest.CaptureFixture[str],
        main_func: Callable[[Optional[list[str]]], None],
        extra_args: list[str], expected: ExpectedSimpleConfig,
        read_json_text: bool = False) -> Optional[str]:
    """Run an example main function and assert the written config."""
    with TemporaryDirectory() as dirname:
        config_file = dirname + '/simple.cfg'
        main_func(['set', '--output', config_file, *extra_args])
        return _assert_written_simple_config(capsys, config_file, expected,
                                             read_json_text)


def assert_simple_config_written_by_set_command(
        capsys: pytest.CaptureFixture[str],
        set_command: Callable[[SetValues, PathOrStr], None],
        set_values: SetValues, expected: ExpectedSimpleConfig) -> None:
    """Run a direct set command and assert the written config."""
    with TemporaryDirectory() as dirname:
        config_file = dirname + '/simple.cfg'
        set_command(set_values, config_file)
        _ = _assert_written_simple_config(capsys, config_file, expected)


def _assert_written_simple_config(
        capsys: pytest.CaptureFixture[str], config_file: str,
        expected: ExpectedSimpleConfig,
        read_json_text: bool = False) -> Optional[str]:
    """Read a written config file and assert its contents."""
    config = SimpleConfig(from_json_filename=config_file)
    json_text: Optional[str] = None
    if read_json_text:
        with open(config_file, encoding='UTF-8') as file_obj:
            json_text = file_obj.read()
    assert_write_command_output(capsys, config_file)
    assert_simple_config_values(config, expected)
    return json_text


def assert_validated_example_config_values(
        config: SupportsValidatedExampleConfig,
        expected: ExpectedValidatedExampleConfig) -> None:
    """Assert the stored values in an e03 or e04 example config."""
    assert config.issue_type == expected.issue_type
    assert config.number_of_iterations == expected.number_of_iterations
    assert config.estimate == expected.estimate
    assert config.severity == expected.severity
    assert config.confidence == pytest.approx(expected.confidence)


def assert_validated_example_config_written_by_set_command(
        capsys: pytest.CaptureFixture[str], example_spec: ValidatedExampleSpec,
        set_values: SetValues, expected: ExpectedValidatedExampleConfig,
        read_json_text: bool = False) -> Optional[str]:
    """Run a validated-example set helper and assert the written config."""
    with TemporaryDirectory() as dirname:
        config_file = dirname + '/' + example_spec.config_basename
        example_spec.set_command(set_values, config_file)
        config = example_spec.config_factory(from_json_filename=config_file)
        json_text: Optional[str] = None
        if read_json_text:
            with open(config_file, encoding='UTF-8') as file_obj:
                json_text = file_obj.read()
        assert_write_command_output(capsys, config_file)
    assert_validated_example_config_values(config, expected)
    return json_text


def write_validated_example_config_json(
        config_file: str,
        extra_values: Optional[dict[str, object]] = None) -> None:
    """Write JSON text with the schema expected by the e03/e04 examples."""
    json_data: dict[str, object] = {
        'issue_type': 'Story',
        'number_of_iterations': 10,
        'estimate': 5,
        'severity': 'INFO',
        'confidence': 0.95
    }
    if extra_values is not None:
        json_data.update(extra_values)
    write_json_file(config_file, json_data)


def patch_validated_config_stderr(monkeypatch: pytest.MonkeyPatch,
                                  example_spec: ValidatedExampleSpec,
                                  stderr_buffer: TextIO) -> None:
    """Patch an e03/e04 config factory to force diagnostics to one stream."""
    patch_config_factory_stderr(monkeypatch, example_spec.module,
                                example_spec.factory_name,
                                example_spec.config_factory, stderr_buffer)


def assert_validator_error_output(capsys: pytest.CaptureFixture[str],
                                  stderr_buffer: StringIO,
                                  expected_fragments: list[str]) -> None:
    """Assert that validation failed and reported the expected message."""
    out, _ = capsys.readouterr()
    err = stderr_buffer.getvalue()
    assert out == ''
    for expected_fragment in expected_fragments:
        assert expected_fragment in err


def assert_set_validator_error(
        capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch,
        example_spec: ExampleProgramSpec[ExampleProgramInstance_co],
        set_values: SetValues, expected_fragments: list[str]) -> None:
    """Assert that one example reports a write-time validation error."""
    stderr_buffer = StringIO()
    patch_config_factory_stderr(monkeypatch, example_spec.module,
                                example_spec.factory_name,
                                example_spec.config_factory, stderr_buffer)
    with TemporaryDirectory() as dirname:
        config_file = dirname + '/' + example_spec.config_basename
        example_spec.set_command(set_values, config_file)
    assert_validator_error_output(capsys, stderr_buffer, expected_fragments)


def assert_print_validator_error(
        capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch,
        example_spec: ExampleProgramSpec[ExampleProgramInstance_co],
        json_data: dict[str, object], expected_fragments: list[str]) -> None:
    """Assert that one example reports a read-time validation error."""
    stderr_buffer = StringIO()
    patch_config_factory_stderr(monkeypatch, example_spec.module,
                                example_spec.factory_name,
                                example_spec.config_factory, stderr_buffer)
    with TemporaryDirectory() as dirname:
        config_file = dirname + '/' + example_spec.config_basename
        write_json_file(config_file, json_data)
        example_spec.print_command(config_file)
    assert_validator_error_output(capsys, stderr_buffer, expected_fragments)
