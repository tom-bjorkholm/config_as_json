#! /usr/local/bin/python3
"""Teach direct nested Config members.

Some applications have a repeated group of related settings. A course
registration tool might need one table-like output for the registered
participants and another optional table-like output for an administrator
audit log. Both outputs need the same small group of settings:

- file name
- output format
- character encoding

This example puts that repeated group in its own ``TableOutputConfig`` class.
The main configuration then stores one mandatory nested instance and one
optional nested instance.
"""

# Copyright (c) 2026 Tom Björkholm
# MIT License

from typing import Optional, TextIO
import sys
from config_as_json import CharEncodingValidator, Config, ConfigNesting, \
    ConfigNestingKind, MemberValidationStep, PathOrStr, StrValidator, \
    ValidationPlan
from .cmd_line_handling import InputSpec, SetValues, cmd_line_handling


class TableOutputConfig(Config):
    """Configuration for one table-like output file."""

    def __init__(self, from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 stderr_file: TextIO = sys.stderr) -> None:
        """Initialize one output section.

        Args:
            from_json_data_text: Optional JSON text to parse directly.
            from_json_filename: Optional path to a JSON file to read.
            stderr_file: Stream used for user-facing diagnostics.
        """
        # This class is itself a normal Config class. The values assigned
        # before super().__init__() are the defaults for one output section.
        self.file_name: str = 'participants.csv'
        self.output_format: str = 'CSV'
        self.encoding: str = 'utf-8'
        super().__init__(from_json_data_text=from_json_data_text,
                         from_json_filename=from_json_filename,
                         stderr_file=stderr_file)

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Return validation steps for one output section."""
        _ = stderr_file
        return [
            MemberValidationStep(
                member_names=['output_format'],
                validator=StrValidator(['CSV', 'TXT'], ignore_case=True,
                                       normalize=True)),
            MemberValidationStep(member_names=['encoding'],
                                 validator=CharEncodingValidator())
        ]


class ExampleConfig33(Config):
    """Configuration with one mandatory and one optional nested section."""

    def __init__(self, from_json_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 stderr_file: TextIO = sys.stderr) -> None:
        """Initialize the course export configuration.

        Args:
            from_json_text: Optional JSON text to parse directly.
            from_json_filename: Optional path to a JSON file to read.
            stderr_file: Stream used for user-facing diagnostics.
        """
        self.course_name: str = 'python-intro'
        # The participant output is mandatory, so the default is a real
        # nested Config object.
        self.participant_output: TableOutputConfig = TableOutputConfig(
            stderr_file=stderr_file)
        # The audit output is optional. Its default is None, and
        # _omit_none_from_json() below tells Config that this member may be
        # absent in JSON and should be omitted while it remains None.
        self.audit_output: Optional[TableOutputConfig] = None
        # Every nested Config member is listed in _nested_configs. The kind
        # tells Config how that public member should behave when JSON is read
        # and written: MEMBER is a mandatory nested section, and
        # OPTIONAL_MEMBER is either None or a nested section. The config_type
        # tells Config which class to construct when JSON contains a nested
        # object for that member.
        self._nested_configs = {
            'participant_output': ConfigNesting(kind=ConfigNestingKind.MEMBER,
                                                config_type=TableOutputConfig),
            'audit_output': ConfigNesting(
                kind=ConfigNestingKind.OPTIONAL_MEMBER,
                config_type=TableOutputConfig)
        }
        super().__init__(from_json_data_text=from_json_text,
                         from_json_filename=from_json_filename,
                         stderr_file=stderr_file)

    def _omit_none_from_json(self) -> list[str]:
        """Return optional members omitted while their value is None."""
        return ['audit_output']

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Return validation steps for the top-level configuration."""
        _ = stderr_file
        return []


def _ensure_audit_output(config: ExampleConfig33) -> TableOutputConfig:
    """Return the optional audit output, creating defaults if needed.

    Args:
        config: Configuration whose optional audit output is needed.

    Returns:
        The existing or newly created audit output configuration.
    """
    if config.audit_output is None:
        # Creating the nested object only when an audit value is set keeps
        # the default JSON compact: no audit section is written unless the
        # user asked for one.
        config.audit_output = TableOutputConfig()
        config.audit_output.file_name = 'audit-log.csv'
    return config.audit_output


def _set_output_value(output: TableOutputConfig, key: str,
                      value: object) -> bool:
    """Apply one flat command-line value to one nested output.

    Args:
        output: Nested output configuration to update.
        key: Command-line key being applied.
        value: Command-line value.

    Returns:
        ``True`` if the key belonged to an output setting.
    """
    if key == 'file_name':
        assert isinstance(value, str)
        output.file_name = value
        return True
    if key == 'output_format':
        assert isinstance(value, str)
        output.output_format = value
        return True
    if key == 'encoding':
        assert isinstance(value, str)
        output.encoding = value
        return True
    return False


def _apply_set_value(config: ExampleConfig33, key: str, value: object) -> None:
    """Apply one command-line value to the appropriate config object.

    Args:
        config: Configuration object to update.
        key: Command-line key being applied.
        value: Command-line value.

    Raises:
        ValueError: The command-line helper supplied an unknown key.
    """
    if key == 'course_name':
        assert isinstance(value, str)
        config.course_name = value
        return
    if key.startswith('participant_'):
        output_key = key.removeprefix('participant_')
        if _set_output_value(config.participant_output, output_key, value):
            return
    if key.startswith('audit_'):
        output_key = key.removeprefix('audit_')
        if _set_output_value(_ensure_audit_output(config), output_key, value):
            return
    raise ValueError(f'Invalid key: {key}')


def e33_nested_configs_set(set_values: SetValues,
                           config_file: PathOrStr) -> None:
    """Create configuration, apply overrides, and store it.

    Args:
        set_values: Values that should differ from the defaults.
        config_file: Path where to write the configuration file.
    """
    config = ExampleConfig33()
    for key, value in set_values.items():
        _apply_set_value(config, key, value)
    config.write(to_json_filename=config_file)
    print(f'Configuration written to {config_file}')


def _print_output(label: str, output: TableOutputConfig) -> None:
    """Print one nested output configuration.

    Args:
        label: Human-readable label for the output.
        output: Nested output configuration to print.
    """
    print(f'{label} file: {output.file_name}')
    print(f'{label} format: {output.output_format}')
    print(f'{label} encoding: {output.encoding}')


def e33_nested_configs_print(config_file: PathOrStr) -> None:
    """Read a configuration file and show how nested values are used.

    Args:
        config_file: Path to the configuration file to read.
    """
    config = ExampleConfig33(from_json_filename=config_file)
    print(f'Configuration read from {config_file}')
    print(f'Course name: {config.course_name}')
    _print_output('Participant output', config.participant_output)
    if config.audit_output is None:
        print('Audit output: not configured')
    else:
        _print_output('Audit output', config.audit_output)


INPUT_SPECS = [
    InputSpec(name='course_name', single=True, value_type=str),
    InputSpec(name='participant_file_name', single=True, value_type=str),
    InputSpec(name='participant_output_format', single=True, value_type=str),
    InputSpec(name='participant_encoding', single=True, value_type=str),
    InputSpec(name='audit_file_name', single=True, value_type=str),
    InputSpec(name='audit_output_format', single=True, value_type=str),
    InputSpec(name='audit_encoding', single=True, value_type=str)
]
"""Command line values that the example exposes for ``set``."""


def main(args: Optional[list[str]] = None) -> None:
    """Run the example command line interface.

    Args:
        args: Optional replacement for ``sys.argv[1:]``, mainly for tests.
    """
    cmd_line_handling(example_name='e33_nested_configs',
                      input_specs=INPUT_SPECS,
                      set_command=e33_nested_configs_set,
                      print_command=e33_nested_configs_print, args=args)


if __name__ == '__main__':
    main()
    sys.exit(0)
