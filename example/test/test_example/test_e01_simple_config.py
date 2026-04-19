#! /usr/local/bin/python3
"""Tests for the first example program."""

# Copyright (c) 2026 Tom Björkholm
# MIT License

from tempfile import TemporaryDirectory
import pytest
from example.e01_simple_config import SimpleConfig, YesNoAsk, main


def test_simple_config_set_uses_defaults_when_no_overrides(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Write a configuration file with only the default values."""
    with TemporaryDirectory() as dirname:
        config_file = dirname + '/simple.cfg'
        main(['set', '--output', config_file])
        config = SimpleConfig(from_json_filename=config_file)
        with open(config_file, encoding='UTF-8') as file_obj:
            json_text = file_obj.read()
    out, err = capsys.readouterr()
    assert out == f'Configuration written to {config_file}\n'
    assert err == ''
    assert config.name == 'simple or complex'
    assert config.answer == 42
    assert config.approximation == pytest.approx(3.14159)
    assert config.easy is True
    assert config.confirmation == YesNoAsk.ASK
    assert '"confirmation": "ASK"' in json_text


def test_simple_config_set_stores_overrides(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Convert command line text to values and store them in JSON."""
    with TemporaryDirectory() as dirname:
        config_file = dirname + '/simple.cfg'
        main(['set',
              '--output', config_file,
              '--name', 'configured',
              '--answer', '7',
              '--approximation', '2.5',
              '--easy', 'FALSE',
              '--confirmation', 'nO'])
        config = SimpleConfig(from_json_filename=config_file)
    out, err = capsys.readouterr()
    assert out == f'Configuration written to {config_file}\n'
    assert err == ''
    assert config.name == 'configured'
    assert config.answer == 7
    assert config.approximation == pytest.approx(2.5)
    assert config.easy is False
    assert config.confirmation == YesNoAsk.NO


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
