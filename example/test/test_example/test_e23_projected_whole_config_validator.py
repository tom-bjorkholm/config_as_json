#! /usr/local/bin/python3
"""Tests for the projected whole-config validator teaching example."""

# Copyright (c) 2026 Tom Björkholm
# MIT License

from tempfile import TemporaryDirectory
from typing import cast
from pytest import CaptureFixture, MonkeyPatch
import example.e23_projected_whole_config_validator as e23_module
from example.cmd_line_handling import SetValues
from example.e23_projected_whole_config_validator import ExampleConfig23
from example.e23_projected_whole_config_validator import \
    e23_projected_whole_config_print
from example.e23_projected_whole_config_validator import \
    e23_projected_whole_config_set
from example.e23_projected_whole_config_validator import main as e23_main
from .helpers import ExampleProgramSpec
from .helpers import assert_print_validator_error
from .helpers import assert_rt_out
from .helpers import assert_set_validator_error
from .helpers import assert_write_command_output


E23_SPEC = ExampleProgramSpec(module=e23_module,
                              factory_name='ExampleConfig23',
                              config_factory=ExampleConfig23,
                              set_command=e23_projected_whole_config_set,
                              print_command=e23_projected_whole_config_print,
                              config_basename='projected_whole_config.cfg')


def test_e23_set_defaults(capsys: CaptureFixture[str]) -> None:
    """Write and read the default projected whole-config example."""
    with TemporaryDirectory() as dirname:
        config_file = dirname + '/projected_whole_config.cfg'
        e23_projected_whole_config_set({}, config_file)
        config = ExampleConfig23(from_json_filename=config_file)
    assert_write_command_output(capsys, config_file)
    assert config.primary_region == 'eu-north'
    assert config.replica_regions == ['us-east', 'ap-south']


def test_e23_set_overrides(capsys: CaptureFixture[str]) -> None:
    """Accept distinct regions and normalize the primary region."""
    set_values = cast(SetValues, {
        'primary_region': 'US-WEST',
        'replica_regions': ['eu-north', 'ap-south']})
    with TemporaryDirectory() as dirname:
        config_file = dirname + '/projected_whole_config.cfg'
        e23_projected_whole_config_set(set_values, config_file)
        config = ExampleConfig23(from_json_filename=config_file)
    assert_write_command_output(capsys, config_file)
    assert config.primary_region == 'us-west'
    assert config.replica_regions == ['eu-north', 'ap-south']


def test_e23_rejects_dup_region(
        capsys: CaptureFixture[str], monkeypatch: MonkeyPatch) -> None:
    """Reject duplicate values in the projected whole-config list."""
    set_values = cast(SetValues, {
        'primary_region': 'eu-north',
        'replica_regions': ['eu-north', 'ap-south']})
    assert_set_validator_error(capsys, monkeypatch, E23_SPEC, set_values, [
        'all_regions',
        'duplicates the value at index 0'])


def test_e23_rejects_unknown_replica(
        capsys: CaptureFixture[str], monkeypatch: MonkeyPatch) -> None:
    """Reject an invalid replica region before whole-config projection."""
    assert_print_validator_error(capsys, monkeypatch, E23_SPEC, {
        'primary_region': 'eu-north',
        'replica_regions': ['unknown']
    }, [
        'replica_regions',
        'is not one of the allowed values'])


def test_e23_main_round_trip(capsys: CaptureFixture[str]) -> None:
    """Round-trip the projected whole-config example through the CLI."""
    assert_rt_out(
        capsys, e23_main, 'projected_whole_config.cfg',
        ['--primary-region', 'US-WEST',
         '--replica-regions', 'eu-north', 'ap-south'], [
             'Primary region: us-west',
             "Replica regions: ['eu-north', 'ap-south']",
             "Projected all regions: ['us-west', 'eu-north', 'ap-south']"
        ])
