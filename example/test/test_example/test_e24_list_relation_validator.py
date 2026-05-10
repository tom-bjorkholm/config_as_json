#! /usr/local/bin/python3
"""Tests for the list relation validator teaching example."""

# Copyright (c) 2026 Tom Björkholm
# MIT License

from tempfile import TemporaryDirectory
from typing import cast
from pytest import CaptureFixture, MonkeyPatch
import example.e24_list_relation_validator as e24_module
from example.cmd_line_handling import SetValues
from example.e24_list_relation_validator import ExampleConfig24
from example.e24_list_relation_validator import e24_list_relation_print
from example.e24_list_relation_validator import e24_list_relation_set
from example.e24_list_relation_validator import main as e24_main
from .helpers import ExampleProgramSpec
from .helpers import assert_print_validator_error
from .helpers import assert_rt_out
from .helpers import assert_set_validator_error
from .helpers import assert_write_command_output


E24_SPEC = ExampleProgramSpec(module=e24_module,
                              factory_name='ExampleConfig24',
                              config_factory=ExampleConfig24,
                              set_command=e24_list_relation_set,
                              print_command=e24_list_relation_print,
                              config_basename='list_relation.cfg')


def test_e24_set_defaults(capsys: CaptureFixture[str]) -> None:
    """Write and read the default list relation example."""
    with TemporaryDirectory() as dirname:
        config_file = dirname + '/list_relation.cfg'
        e24_list_relation_set({}, config_file)
        config = ExampleConfig24(from_json_filename=config_file)
    assert_write_command_output(capsys, config_file)
    assert config.declared_routes == ['api', 'admin']
    assert config.route_handlers == {'admin': 'admin_handler',
                                     'api': 'api_handler'}


def test_e24_set_overrides(capsys: CaptureFixture[str]) -> None:
    """Accept matching declared routes and route handler keys."""
    set_values = cast(SetValues, {
        'declared_routes': ['api', 'metrics'],
        'route_handlers': {'api': 'api_handler',
                           'metrics': 'metrics_handler'}})
    with TemporaryDirectory() as dirname:
        config_file = dirname + '/list_relation.cfg'
        e24_list_relation_set(set_values, config_file)
        config = ExampleConfig24(from_json_filename=config_file)
    assert_write_command_output(capsys, config_file)
    assert config.declared_routes == ['api', 'metrics']
    assert config.route_handlers == {'api': 'api_handler',
                                     'metrics': 'metrics_handler'}


def test_e24_rejects_missing_handler(
        capsys: CaptureFixture[str], monkeypatch: MonkeyPatch) -> None:
    """Reject declared routes that do not match handler keys."""
    set_values = cast(SetValues, {
        'declared_routes': ['api'],
        'route_handlers': {'api': 'api_handler',
                           'admin': 'admin_handler'}})
    assert_set_validator_error(capsys, monkeypatch, E24_SPEC, set_values, [
        'Relation SET_EQUAL does not hold',
        'declared_routes',
        'route_handler_names'])


def test_e24_rejects_dup_route(
        capsys: CaptureFixture[str], monkeypatch: MonkeyPatch) -> None:
    """Reject duplicate declared routes before the relation check."""
    assert_print_validator_error(capsys, monkeypatch, E24_SPEC, {
        'declared_routes': ['api', 'api'],
        'route_handlers': {'api': 'api_handler'}
    }, [
        'declared_routes',
        'duplicates the value at index 0'])


def test_e24_rejects_bad_handler(
        capsys: CaptureFixture[str], monkeypatch: MonkeyPatch) -> None:
    """Reject a route handler value that is not a string."""
    assert_print_validator_error(capsys, monkeypatch, E24_SPEC, {
        'declared_routes': ['api'],
        'route_handlers': {'api': 7}
    }, [
        'route_handlers[api]',
        'not of type str'])


def test_e24_main_round_trip(capsys: CaptureFixture[str]) -> None:
    """Round-trip the list relation example through the CLI."""
    assert_rt_out(
        capsys, e24_main, 'list_relation.cfg',
        ['--declared-routes', 'api', 'metrics',
         '--route-handlers', 'api=api_handler',
         'metrics=metrics_handler'], [
             "Declared routes: ['api', 'metrics']",
             "Route handlers: {'api': 'api_handler', "
             "'metrics': 'metrics_handler'}",
             "Projected handler routes: ('api', 'metrics')"
        ])
