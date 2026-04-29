#! /usr/local/bin/python3
"""Tests for the config-factory teaching example."""

# Copyright (c) 2026 Tom Björkholm
# MIT License

import json
import sys
from tempfile import TemporaryDirectory
from typing import cast
import pytest
from config_as_json import Config, config_factory_from_json
from config_as_json.config_auto_change_hook import ConfigAutoChangeHook
from example.cmd_line_handling import SetValues
from example.e32_config_factory import Cad2DConfig, Cad3DConfig, \
    e32_config_factory_print, e32_config_factory_set, MATCH_CONFIGS
from example.e32_config_factory import main as e32_main
from .helpers import assert_main_round_trip_print_output, \
    assert_write_command_output, write_json_file


def read_json_data(config_file: str) -> dict[str, object]:
    """Read one JSON config file using UTF-8."""
    with open(config_file, encoding='UTF-8') as file_obj:
        loaded = json.load(file_obj)
    return cast(dict[str, object], loaded)


def e32_config_factory_read(config_file: str) -> Config:
    """Read a configuration file through the config factory."""
    return config_factory_from_json(match_configs=MATCH_CONFIGS,
                                    auto_ch_hook=ConfigAutoChangeHook(),
                                    from_json_filename=config_file,
                                    stderr_file=sys.stderr)


def test_e32_set_writes_default_2d_config(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Write a default 2D configuration when no mode is selected."""
    with TemporaryDirectory() as dirname:
        config_file = dirname + '/cad.cfg'
        e32_config_factory_set({}, config_file)
        config = e32_config_factory_read(config_file)
        json_data = read_json_data(config_file)
    assert_write_command_output(capsys, config_file)
    assert isinstance(config, Cad2DConfig)
    assert config.mode == '2D'
    assert config.project_name == 'demo-part'
    assert config.grid_size_mm == pytest.approx(1.0)
    assert config.drawing_plane == 'XY'
    assert json_data == {'drawing_plane': 'XY',
                         'grid_size_mm': 1.0,
                         'mode': '2D',
                         'project_name': 'demo-part'}


def test_e32_set_writes_3d_config_with_common_overrides(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Write a 3D configuration and override shared values."""
    set_values = cast(SetValues, {
        'mode': '3d',
        'project_name': 'gearbox',
        'grid_size_mm': 0.5
    })
    with TemporaryDirectory() as dirname:
        config_file = dirname + '/cad.cfg'
        e32_config_factory_set(set_values, config_file)
        config = e32_config_factory_read(config_file)
        json_data = read_json_data(config_file)
    assert_write_command_output(capsys, config_file)
    assert isinstance(config, Cad3DConfig)
    assert config.space == '3D'
    assert config.project_name == 'gearbox'
    assert config.grid_size_mm == pytest.approx(0.5)
    assert config.default_view == 'isometric'
    assert config.show_shadows is True
    assert json_data == {'default_view': 'isometric',
                         'grid_size_mm': 0.5,
                         'project_name': 'gearbox',
                         'show_shadows': True,
                         'space': '3D'}


def test_e32_print_reads_3d_config_with_factory(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Print a 3D file selected by the config factory."""
    set_values = cast(SetValues, {'mode': '3D'})
    with TemporaryDirectory() as dirname:
        config_file = dirname + '/cad.cfg'
        e32_config_factory_set(set_values, config_file)
        _ = capsys.readouterr()
        e32_config_factory_print(config_file)
        out, err = capsys.readouterr()
    assert err == ''
    assert out == '\n'.join([
        f'Configuration read from {config_file}',
        'Configuration class: Cad3DConfig',
        'Selector space: 3D',
        'Project name: demo-part',
        'Grid size: 1.0 mm',
        'Default view: isometric',
        'Show shadows: True'
    ]) + '\n'


def test_e32_main_round_trip_prints_default_2d_values(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Round-trip default 2D values through the command line."""
    assert_main_round_trip_print_output(
        capsys,
        e32_main,
        'cad.cfg',
        [],
        ['Configuration class: Cad2DConfig',
         'Selector mode: 2D',
         'Project name: demo-part',
         'Grid size: 1.0 mm',
         'Drawing plane: XY']
    )


def test_e32_main_round_trip_with_3d_overrides(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Round-trip a 3D configuration through the command line."""
    assert_main_round_trip_print_output(
        capsys,
        e32_main,
        'cad.cfg',
        ['--mode', '3D',
         '--project-name', 'gearbox',
         '--grid-size-mm', '0.5'],
        ['Configuration class: Cad3DConfig',
         'Selector space: 3D',
         'Project name: gearbox',
         'Grid size: 0.5 mm',
         'Default view: isometric',
         'Show shadows: True']
    )


@pytest.mark.parametrize(
    'json_data',
    [{'mode': '4D',
      'project_name': 'demo-part',
      'grid_size_mm': 1.0},
     {'project_name': 'demo-part',
      'grid_size_mm': 1.0}]
)
def test_e32_read_fails_when_no_mode_matches(
        capsys: pytest.CaptureFixture[str],
        json_data: dict[str, object]) -> None:
    """Fail when the factory cannot choose a config class."""
    with TemporaryDirectory() as dirname:
        config_file = dirname + '/cad.cfg'
        write_json_file(config_file, json_data)
        with pytest.raises(SystemExit):
            e32_config_factory_print(config_file)
    out, err = capsys.readouterr()
    assert out == ''
    assert 'No matching config class found' in err
