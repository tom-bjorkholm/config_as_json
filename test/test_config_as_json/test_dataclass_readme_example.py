#! /usr/local/bin/python3
"""Simple dataclass example for README_pypi.md with tests."""

# Copyright (c) 2024-2026 Tom Björkholm
# MIT License

# pylint: disable=duplicate-code
# ------------------------------------------------------------
# Example code to copy-paste into README_pypi.md
# ------------------------------------------------------------

from typing import Optional, TextIO
from dataclasses import dataclass
import sys
from config_as_json import Config, PathOrStr, ValidationPlan


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
        """Return an empty validation plan."""
        return []


def application(config_filename: PathOrStr, update_config: bool) -> None:
    """Simulate a simple application that uses MyConfig."""
    # Read configuration from file that already exists
    config = MyConfig(from_json_filename=config_filename,
                      stderr_file=sys.stderr)
    # A lot of application code not shown here
    print(f'Report name: {config.report_name}')
    # ...
    if update_config:
        config.write(config_filename)


# ------------------------------------------------------------
# Example above - Test code below - not shown in README_pypi.md
# ------------------------------------------------------------

# pylint: enable=duplicate-code
# pylint: disable=wrong-import-position,wrong-import-order
import pytest  # noqa: E402
from tempfile import TemporaryDirectory  # noqa: E402


# pylint: disable=duplicate-code
def test_dataclass_no_file(capsys: pytest.CaptureFixture[str]) -> None:
    """Test the simple readme example with no file."""
    config_filename = 'test_config.cfg'
    with pytest.raises(SystemExit):
        application(config_filename=config_filename, update_config=False)
    out, err = capsys.readouterr()
    assert out == ''
    assert 'File test_config.cfg with configuration' in err
    assert 'does not exist. Cannot proceed.' in err


def test_dataclass_with_file(capsys: pytest.CaptureFixture[str]) -> None:
    """Test the simple readme example with a file."""
    with TemporaryDirectory() as tmp_dir:
        config_filename = tmp_dir + '/test_config.cfg'
        MyConfig().write(config_filename)
        application(config_filename=config_filename, update_config=False)
    out, err = capsys.readouterr()
    assert 'Report name: My Report' in out
    assert err == ''


def test_dataclass_reads_values(capsys: pytest.CaptureFixture[str]) -> None:
    """Test that third-party values are read by the readme example."""
    with TemporaryDirectory() as tmp_dir:
        config_filename = tmp_dir + '/test_config.cfg'
        config = MyConfig()
        config.report_name = 'Sprint report'
        config.story_points = 13
        config.is_done = True
        config.write(config_filename)
        application(config_filename=config_filename, update_config=False)
    out, err = capsys.readouterr()
    assert out == 'Report name: Sprint report\n'
    assert err == ''


def test_dataclass_updates_file(capsys: pytest.CaptureFixture[str]) -> None:
    """Test that the dataclass readme example writes the read config."""
    with TemporaryDirectory() as tmp_dir:
        config_filename = tmp_dir + '/test_config.cfg'
        config = MyConfig()
        config.report_name = 'Updated report'
        config.story_points = 8
        config.is_done = True
        config.write(config_filename)
        application(config_filename=config_filename, update_config=True)
        written_config = MyConfig(from_json_filename=config_filename)
    out, err = capsys.readouterr()
    assert out == 'Report name: Updated report\n'
    assert err == ''
    assert written_config.report_name == 'Updated report'
    assert written_config.story_points == 8
    assert written_config.is_done
# pylint: enable=duplicate-code
