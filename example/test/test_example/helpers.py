#! /usr/local/bin/python3
"""Shared helpers for example program tests."""

# Copyright (c) 2026 Tom Björkholm
# MIT License

from tempfile import TemporaryDirectory
from typing import Callable, NamedTuple, Optional
import pytest
from config_as_json.commontypes import PathOrStr
from example.cmd_line_handling import SetValues
from example.e01_simple_config import SimpleConfig, YesNoAsk


class ExpectedSimpleConfig(NamedTuple):
    """Expected values for a SimpleConfig instance."""

    name: str
    answer: int
    approximation: float
    easy: bool
    confirmation: YesNoAsk


DEFAULT_SIMPLE_CONFIG = ExpectedSimpleConfig(
    name='simple or complex',
    answer=42,
    approximation=3.14159,
    easy=True,
    confirmation=YesNoAsk.ASK
)
"""Default values used by the simple example configuration."""


CONFIGURED_SIMPLE_CONFIG = ExpectedSimpleConfig(
    name='configured',
    answer=7,
    approximation=2.5,
    easy=False,
    confirmation=YesNoAsk.NO
)
"""Representative overridden values used by simple config tests."""


def assert_simple_config_values(
        config: SimpleConfig,
        expected: ExpectedSimpleConfig) -> None:
    """Assert the stored values in a simple example configuration."""
    assert config.name == expected.name
    assert config.answer == expected.answer
    assert config.approximation == pytest.approx(expected.approximation)
    assert config.easy is expected.easy
    assert config.confirmation == expected.confirmation


def assert_write_command_output(
        capsys: pytest.CaptureFixture[str], config_file: str) -> None:
    """Assert the standard output from the example set command."""
    out, err = capsys.readouterr()
    assert out == f'Configuration written to {config_file}\n'
    assert err == ''


def assert_simple_config_written_by_main(
        capsys: pytest.CaptureFixture[str],
        main_func: Callable[[Optional[list[str]]], None],
        extra_args: list[str],
        expected: ExpectedSimpleConfig,
        read_json_text: bool = False) -> Optional[str]:
    """Run an example main function and assert the written config."""
    with TemporaryDirectory() as dirname:
        config_file = dirname + '/simple.cfg'
        main_func(['set', '--output', config_file, *extra_args])
        return _assert_written_simple_config(
            capsys,
            config_file,
            expected,
            read_json_text
        )


def assert_simple_config_written_by_set_command(
        capsys: pytest.CaptureFixture[str],
        set_command: Callable[[SetValues, PathOrStr], None],
        set_values: SetValues,
        expected: ExpectedSimpleConfig) -> None:
    """Run a direct set command and assert the written config."""
    with TemporaryDirectory() as dirname:
        config_file = dirname + '/simple.cfg'
        set_command(set_values, config_file)
        _ = _assert_written_simple_config(
            capsys,
            config_file,
            expected
        )


def _assert_written_simple_config(
        capsys: pytest.CaptureFixture[str],
        config_file: str,
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
