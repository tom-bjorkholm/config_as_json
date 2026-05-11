#! /usr/local/bin/python3
"""Teach lists whose elements are nested Config objects.

This example is the next step after ``e33_nested_configs``. Example 33
showed one mandatory nested object and one optional nested object. This file
shows the repeated-object case: one top-level member is a list, and every
list element is a real ``Config`` object with its own defaults and
validation.

The story is still a course export tool. A course can produce several output
reports, such as a participant report and an audit report. Each report has
the same small group of settings:

- a report name
- a file name
- an output format
- a character encoding

That repeated group belongs in its own ``ReportOutputConfig`` class. The
top-level ``ExampleConfig34`` class then stores
``list[ReportOutputConfig]`` and declares that list with
``ConfigNestingKind.LIST_ELEMENT``.
"""

# Copyright (c) 2026 Tom Björkholm
# MIT License

import json
import sys
from typing import Optional, TextIO, cast
from config_as_json import Config, ConfigNesting, ConfigNestingKind, \
    JsonType, MemberValidationStep, PathOrStr, StrValidator, ValidationPlan
from .cmd_line_handling import InputSpec, SetValues, cmd_line_handling


class ReportOutputConfig(Config):
    """Configuration for one generated report file."""

    def __init__(self, from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 stderr_file: TextIO = sys.stderr) -> None:
        """Initialize one report output configuration.

        Args:
            from_json_data_text: Optional JSON text to parse directly.
            from_json_filename: Optional path to a JSON file to read.
            stderr_file: Stream used for user-facing diagnostics.
        """
        # This class is ordinary ``Config``. It does not know whether it will
        # be used alone, as a direct member, or as one element in a list.
        #
        # The only important rule is the familiar Config rule: assign the
        # public defaults before calling ``super().__init__()``.
        self.output_format: str = 'CSV'
        self.name: str = 'participants'
        self.encoding: str = 'utf-8'
        self.file_name: str = 'participants.csv'
        super().__init__(from_json_data_text=from_json_data_text,
                         from_json_filename=from_json_filename,
                         stderr_file=stderr_file)

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Return validation steps for one report output."""
        _ = stderr_file
        steps: ValidationPlan = [
            # Each list element has its own validation plan. The parent does
            # not need to repeat these checks for every report.
            MemberValidationStep(
                member_names=['output_format'],
                validator=StrValidator(['CSV', 'TXT'], ignore_case=True,
                                       normalize=True))
        ]
        return steps


class ExampleConfig34(Config):
    """Configuration with a list of nested report output sections."""

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
        # The default may be an empty list or a list with ready-made nested
        # Config objects. This example uses two defaults because a real
        # course export often has more than one report.
        audit_report = ReportOutputConfig(stderr_file=stderr_file)
        audit_report.name = 'audit'
        audit_report.file_name = 'audit.csv'
        self.reports: list[ReportOutputConfig] = [
            ReportOutputConfig(stderr_file=stderr_file), audit_report]
        # This is the key line of the example. The member name is still the
        # public top-level attribute, ``reports``. The ``config_type`` is the
        # type of each element, not the type of the outer list.
        self._nested_configs = {
            'reports': ConfigNesting(kind=ConfigNestingKind.LIST_ELEMENT,
                                     config_type=ReportOutputConfig)
        }
        super().__init__(from_json_data_text=from_json_text,
                         from_json_filename=from_json_filename,
                         stderr_file=stderr_file)

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Return validation steps for the top-level configuration."""
        _ = stderr_file
        validation_steps: ValidationPlan = []
        return validation_steps


def _cmd_report_from_json_value(report_data: JsonType,
                                report_index: int) -> ReportOutputConfig:
    """Construct one report config from a command-line JSON value.

    Args:
        report_data: JSON-shaped value describing one report.
        report_index: Index used in a helpful error message.

    Returns:
        A ``ReportOutputConfig`` parsed from ``report_data``.

    Raises:
        ValueError: ``report_data`` is not a JSON object.
    """
    if not isinstance(report_data, dict):
        msg = f'reports[{report_index}] must be a JSON object.'
        raise ValueError(msg)
    # The library itself uses the same constructor shape when it reads a
    # LIST_ELEMENT member from a configuration file. Here the example does it
    # manually only because the command-line helper has already parsed one
    # JSON token into Python values.
    return ReportOutputConfig(from_json_data_text=json.dumps(report_data))


def _cmd_reports_from_json_value(value: JsonType) -> list[ReportOutputConfig]:
    """Construct a list of reports from a command-line JSON value.

    Args:
        value: JSON-shaped value supplied for the ``reports`` option.

    Returns:
        A list of nested report configurations.

    Raises:
        ValueError: The value is not a JSON list of JSON objects.
    """
    if not isinstance(value, list):
        raise ValueError('reports must be a JSON list.')
    return [_cmd_report_from_json_value(report_data, index)
            for index, report_data in enumerate(value)]


def e34_list_nested_configs_set(set_values: SetValues,
                                config_file: PathOrStr) -> None:
    """Create configuration, apply overrides, and store it.

    Args:
        set_values: Values that should differ from the defaults.
        config_file: Path where to write the configuration file.
    """
    config = ExampleConfig34()
    for key, value in set_values.items():
        if key == 'course_name':
            config.course_name = cast(str, value)
        elif key == 'reports':
            config.reports = _cmd_reports_from_json_value(
                cast(JsonType, value))
        else:
            raise ValueError(f'Invalid key: {key}')
    config.write(to_json_filename=config_file)
    print(f'Configuration written to {config_file}')


def _print_report(report_index: int, report: ReportOutputConfig) -> None:
    """Print one report output configuration.

    Args:
        report_index: Position of the report in the configured list.
        report: Nested report output configuration to print.
    """
    print(f'Report {report_index} name: {report.name}')
    print(f'Report {report_index} file: {report.file_name}')
    print(f'Report {report_index} format: {report.output_format}')
    print(f'Report {report_index} encoding: {report.encoding}')


def e34_list_nested_configs_print(config_file: PathOrStr) -> None:
    """Read a configuration file and show how nested list values are used.

    Args:
        config_file: Path to the configuration file to read.
    """
    config = ExampleConfig34(from_json_filename=config_file)
    print(f'Configuration read from {config_file}')
    print(f'Course name: {config.course_name}')
    print(f'Report count: {len(config.reports)}')
    for report_index, report in enumerate(config.reports):
        _print_report(report_index, report)


INPUT_SPECS = [
    InputSpec(name='course_name', single=True, value_type=str),
    # The interesting API is the Config nesting declaration above. The command
    # line helper is intentionally simple, so it accepts the whole report list
    # as one JSON value instead of inventing a new separator syntax for
    # objects inside lists.
    InputSpec(name='reports', single=True, value_type=str, json_value=True)
]
"""Command line values that the example exposes for ``set``."""


def main(args: Optional[list[str]] = None) -> None:
    """Run the example command line interface.

    Args:
        args: Optional replacement for ``sys.argv[1:]``, mainly for tests.
    """
    cmd_line_handling(example_name='e34_list_nested_configs',
                      input_specs=INPUT_SPECS,
                      set_command=e34_list_nested_configs_set,
                      print_command=e34_list_nested_configs_print, args=args)


if __name__ == '__main__':
    main()
    sys.exit(0)
