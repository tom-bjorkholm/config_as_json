#! /usr/local/bin/python3
"""Teach dicts whose values are nested Config objects.

Example 34 showed a list of nested report configurations. A list is useful
when position is the natural identity of each item. Sometimes the application
instead has stable names for the repeated objects. In that case a dictionary
can be a better match.

This example keeps the same course export story. The course has several
report outputs, but each report is now keyed by a report id such as
``participants`` or ``audit``. The values are still real ``Config`` objects:
each value has its own defaults and validation rules.

The nested value class is imported from example 34 on purpose. That keeps the
new lesson focused on the dictionary nesting shape:

- the top-level member is a ``dict[str, ReportOutputConfig]``
- every dictionary key must be a string
- every dictionary value is declared with ``ConfigNestingKind.DICT_VALUE``
"""

# Copyright (c) 2026 Tom Björkholm
# MIT License

import json
import sys
from typing import Optional, TextIO, cast, override
from config_as_json import Config, ConfigNesting, ConfigNestingKind, \
    JsonType, NestedConfigs, PathOrStr, ValidationPlan
from .cmd_line_handling import InputSpec, SetValues, cmd_line_handling
from .e34_list_nested_configs import ReportOutputConfig


def _default_reports_by_id(stderr_file: TextIO) \
        -> dict[str, ReportOutputConfig]:
    """Create the default dictionary of nested report configurations.

    Args:
        stderr_file: Stream used for user-facing diagnostics.

    Returns:
        Default report configurations keyed by report id.
    """
    participant_report = ReportOutputConfig(stderr_file=stderr_file)
    audit_report = ReportOutputConfig(stderr_file=stderr_file)
    audit_report.name = 'audit'
    audit_report.file_name = 'audit.csv'
    return {'participants': participant_report, 'audit': audit_report}


class ExampleConfig35(Config):
    """Configuration with a dict of nested report output sections."""

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Return validation steps for the top-level configuration."""
        _ = stderr_file
        return []

    def __init__(self, from_json_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 stderr_file: TextIO = sys.stderr) -> None:
        """Initialize the course report configuration.

        Args:
            from_json_text: Optional JSON text to parse directly.
            from_json_filename: Optional path to a JSON file to read.
            stderr_file: Stream used for user-facing diagnostics.
        """
        self.course_name: str = 'python-intro'
        # The default may be an empty dict or a dict with ready-made nested
        # Config objects. Here the default contains two named reports so the
        # generated JSON immediately shows the shape of the dictionary.
        self.reports_by_id: dict[str, ReportOutputConfig] = \
            _default_reports_by_id(stderr_file=stderr_file)
        super().__init__(from_json_data_text=from_json_text,
                         from_json_filename=from_json_filename,
                         stderr_file=stderr_file)

    @override
    def nested_configs(self) -> NestedConfigs:
        """Return nested Config declarations."""
        # Use @override on this method so a type checker can catch a
        # misspelled method name.
        # This declaration says that the public member ``reports_by_id`` is a
        # dictionary and that each value in that dictionary must be a
        # ReportOutputConfig. The keys are plain strings, and will be written
        # to JSON and read from JSON as plain strings without conversions.
        # Only the values are constructed as nested Config objects.
        return {
            'reports_by_id': ConfigNesting(kind=ConfigNestingKind.DICT_VALUE,
                                           config_type=ReportOutputConfig)
        }


def _cmd_report_from_json_value(report_key: str,
                                report_data: JsonType) -> ReportOutputConfig:
    """Construct one report config from a command-line JSON value.

    Args:
        report_key: Dictionary key used in command-line diagnostics.
        report_data: JSON-shaped value describing one report.

    Returns:
        A ``ReportOutputConfig`` parsed from ``report_data``.

    Raises:
        ValueError: ``report_data`` is not a JSON object.
    """
    # The library does this automatically when it reads the configuration
    # file. This command helper only repeats the same construction step
    # because the command-line helper has already parsed the user's JSON
    # argument into Python values.
    if isinstance(report_data, dict):
        json_text = json.dumps(report_data)
        return ReportOutputConfig(from_json_data_text=json_text)
    msg = f'reports_by_id[{report_key}] must be a JSON object.'
    raise ValueError(msg)


def _cmd_reports_by_id_from_json(value: JsonType) \
        -> dict[str, ReportOutputConfig]:
    """Construct report configs from a command-line JSON dictionary.

    Args:
        value: JSON-shaped value supplied for the ``reports_by_id`` option.

    Returns:
        A dictionary of nested report configurations.

    Raises:
        ValueError: The value is not a JSON object whose values are objects.
    """
    if not isinstance(value, dict):
        raise ValueError('reports_by_id must be a JSON object.')
    reports: dict[str, ReportOutputConfig] = {}
    for report_key, report_data in value.items():
        if not isinstance(report_key, str):
            raise ValueError('reports_by_id keys must be strings.')
        reports[report_key] = _cmd_report_from_json_value(report_key,
                                                          report_data)
    return reports


def _apply_set_value(config: ExampleConfig35, key: str, value: object) -> None:
    """Apply one command-line value to the example configuration.

    Args:
        config: Configuration object receiving the value.
        key: Command-line key being applied.
        value: Command-line value.

    Raises:
        ValueError: The command-line helper supplied an unknown key.
    """
    if key == 'course_name':
        config.course_name = cast(str, value)
        return
    if key == 'reports_by_id':
        config.reports_by_id = _cmd_reports_by_id_from_json(
            cast(JsonType, value))
        return
    raise ValueError(f'Invalid key: {key}')


def e35_dict_nested_configs_set(set_values: SetValues,
                                config_file: PathOrStr) -> None:
    """Create configuration, apply overrides, and store it.

    Args:
        set_values: Values that should differ from the defaults.
        config_file: Path where to write the configuration file.
    """
    config = ExampleConfig35()
    for key, value in set_values.items():
        _apply_set_value(config=config, key=key, value=value)
    config.write(to_json_filename=config_file)
    print(f'Configuration written to {config_file}')


def _report_output_lines(report_key: str,
                         report: ReportOutputConfig) -> list[str]:
    """Return printable lines for one named report output.

    Args:
        report_key: Key that identifies the report in the dictionary.
        report: Nested report output configuration to describe.

    Returns:
        Lines that show the report configuration.
    """
    return [
        f'Report {report_key} name: {report.name}',
        f'Report {report_key} file: {report.file_name}',
        f'Report {report_key} format: {report.output_format}',
        f'Report {report_key} encoding: {report.encoding}']


def e35_dict_nested_configs_print(config_file: PathOrStr) -> None:
    """Read a configuration file and show how nested dict values are used.

    Args:
        config_file: Path to the configuration file to read.
    """
    config = ExampleConfig35(from_json_filename=config_file)
    print(f'Configuration read from {config_file}')
    print(f'Course name: {config.course_name}')
    print(f'Report count: {len(config.reports_by_id)}')
    for report_key in sorted(config.reports_by_id):
        for line in _report_output_lines(
                report_key, config.reports_by_id[report_key]):
            print(line)


INPUT_SPECS = [
    InputSpec(name='course_name', single=True, value_type=str),
    # The command accepts the full dictionary as one JSON value. That keeps
    # the example focused on DICT_VALUE instead of on a custom command-line
    # syntax for setting several nested object fields one at a time.
    InputSpec(name='reports_by_id', single=True, value_type=str,
              json_value=True)
]
"""Command line values that the example exposes for ``set``."""


def main(args: Optional[list[str]] = None) -> None:
    """Run the example command line interface.

    Args:
        args: Optional replacement for ``sys.argv[1:]``, mainly for tests.
    """
    cmd_line_handling(example_name='e35_dict_nested_configs',
                      input_specs=INPUT_SPECS,
                      set_command=e35_dict_nested_configs_set,
                      print_command=e35_dict_nested_configs_print, args=args)


if __name__ == '__main__':
    main()
    sys.exit(0)
