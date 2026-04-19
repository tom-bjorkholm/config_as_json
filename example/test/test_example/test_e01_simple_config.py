#! /usr/local/bin/python3
"""Tests for the first example program."""

# Copyright (c) 2026 Tom Björkholm
# MIT License

from tempfile import TemporaryDirectory
import pytest
from example.e01_simple_config import main
from .helpers import CONFIGURED_SIMPLE_CONFIG, DEFAULT_SIMPLE_CONFIG
from .helpers import assert_simple_config_written_by_main


def test_simple_config_set_uses_defaults_when_no_overrides(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Write a configuration file with only the default values."""
    json_text = assert_simple_config_written_by_main(
        capsys,
        main,
        [],
        DEFAULT_SIMPLE_CONFIG,
        read_json_text=True
    )
    assert json_text is not None
    assert '"confirmation": "ASK"' in json_text


def test_simple_config_set_stores_overrides(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Convert command line text to values and store them in JSON."""
    _ = assert_simple_config_written_by_main(
        capsys,
        main,
        ['--name', 'configured',
         '--answer', '7',
         '--approximation', '2.5',
         '--easy', 'FALSE',
         '--confirmation', 'nO'],
        CONFIGURED_SIMPLE_CONFIG
    )


def test_simple_config_print_reads_written_file(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Read a stored configuration file and print the values."""
    with TemporaryDirectory() as dirname:
        config_file = dirname + '/simple.cfg'
        main(['set',
              '--output', config_file,
              '--name', 'Ada',
              '--answer', '12',
              '--approximation', '2.75',
              '--easy', 'true',
              '--confirmation', 'yes'])
        _ = capsys.readouterr()
        main(['print', '--input', config_file])
    out, err = capsys.readouterr()
    assert err == ''
    assert out == '\n'.join([
        f'Configuration read from {config_file}',
        'Name: Ada',
        'Answer: 12',
        'Approximation: 2.75',
        'Easy: True',
        'Confirmation: YES'
    ]) + '\n'
