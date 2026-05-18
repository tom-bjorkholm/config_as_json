#! /usr/local/bin/python3
"""Validated dataclass example for README_pypi.md with tests."""

# Copyright (c) 2024-2026 Tom Björkholm
# MIT License

# pylint: disable=duplicate-code
# ------------------------------------------------------------
# Example code to copy-paste into README_pypi.md
# ------------------------------------------------------------

from typing import Optional, TextIO
from dataclasses import dataclass
import sys
from config_as_json import Config, IntFloatValidator, \
    MemberValidationStep, PathOrStr, ValidationPlan


@dataclass
class ThirdPartyConfig:
    """Configuration for my application."""

    report_name: str = 'My Report'
    story_points: int = 5
    is_done: bool = False


class MyConfig(ThirdPartyConfig, Config):
    """Configuration for my application."""

    def __init__(self, from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 stderr_file: TextIO = sys.stderr) -> None:
        """Construct configuration for my application."""
        # Initialize the third-party configuration before Config
        ThirdPartyConfig.__init__(self)
        Config.__init__(self, from_json_data_text=from_json_data_text,
                        from_json_filename=from_json_filename,
                        stderr_file=stderr_file)

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Return the validation plan for my application."""
        _ = stderr_file
        story_point_validator = IntFloatValidator(
            min_value=None, max_value=None,
            allowed_values=[0, 1, 2, 3, 5, 8, 13, 20, 40, 100])
        return [MemberValidationStep(member_names=['story_points'],
                                     validator=story_point_validator)]


def application(config_filename: PathOrStr, update_config: bool,
                read_file: bool) -> None:
    """Simulate a simple application that uses MyConfig."""
    config = MyConfig(stderr_file=sys.stderr)
    if read_file:
        config.read(config_filename, stderr_file=sys.stderr)
    # A lot of application code not shown here
    print(f'Report name: {config.report_name}')
    # ...
    if update_config:
        config.write(config_filename)


# ------------------------------------------------------------
# Example above - Test code below - not shown in README_pypi.md
# ------------------------------------------------------------

# pylint: enable=duplicate-code
# pylint: disable=wrong-import-position,wrong-import-order,ungrouped-imports
import json  # noqa: E402
import pytest  # noqa: E402
from tempfile import TemporaryDirectory  # noqa: E402
from config_as_json import InvalidConfigurationValue  # noqa: E402


def write_config_data(filename: str, data: dict[str, object]) -> None:
    """Write raw JSON configuration data for a test."""
    with open(file=filename, mode='w', encoding='UTF-8') as file:
        json.dump(data, file)


# pylint: disable=duplicate-code
def test_validated_uses_defaults(capsys: pytest.CaptureFixture[str]) -> None:
    """Test that the validated readme example can use defaults."""
    application(config_filename='unused.cfg', update_config=False,
                read_file=False)
    out, err = capsys.readouterr()
    assert out == 'Report name: My Report\n'
    assert err == ''


def test_validated_writes_defaults(capsys: pytest.CaptureFixture[str]) -> None:
    """Test that the validated readme example can write defaults."""
    with TemporaryDirectory() as tmp_dir:
        config_filename = tmp_dir + '/test_config.cfg'
        application(config_filename=config_filename, update_config=True,
                    read_file=False)
        written_config = MyConfig(from_json_filename=config_filename)
    out, err = capsys.readouterr()
    assert out == 'Report name: My Report\n'
    assert err == ''
    assert written_config.report_name == 'My Report'
    assert written_config.story_points == 5
    assert not written_config.is_done


def test_validated_reads_file(capsys: pytest.CaptureFixture[str]) -> None:
    """Test that the validated readme example reads valid values."""
    with TemporaryDirectory() as tmp_dir:
        config_filename = tmp_dir + '/test_config.cfg'
        config = MyConfig()
        config.report_name = 'Sprint report'
        config.story_points = 13
        config.is_done = True
        config.write(config_filename)
        application(config_filename=config_filename, update_config=False,
                    read_file=True)
    out, err = capsys.readouterr()
    assert out == 'Report name: Sprint report\n'
    assert err == ''


def test_validated_rejects_points(capsys: pytest.CaptureFixture[str]) -> None:
    """Test that the validated readme example rejects invalid points."""
    with TemporaryDirectory() as tmp_dir:
        config_filename = tmp_dir + '/test_config.cfg'
        write_config_data(config_filename, {
            'report_name': 'Sprint report',
            'story_points': 4,
            'is_done': False})
        with pytest.raises(InvalidConfigurationValue):
            application(config_filename=config_filename, update_config=False,
                        read_file=True)
    out, err = capsys.readouterr()
    assert out == ''
    assert 'Value 4 for story_points is not one of' in err
# pylint: enable=duplicate-code
