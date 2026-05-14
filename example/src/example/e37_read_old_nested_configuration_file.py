#! /usr/local/bin/python3
"""Show how old files can migrate into nested Config structures.

This example builds on e31. The old configuration has one optional direct
``output`` object. The current configuration has ``outputs``, a list whose
elements are nested ``ReportOutputConfig`` objects.

The example also shows one detail that follows from the parse order. JSON
values are converted by ``parse_converters()`` before the
``ReadOldConfiguration`` rules run. Therefore, enum-valued settings need
converters for both old and current key names when a migration moves or
renames those keys.
"""

# Copyright (c) 2026 Tom Björkholm
# MIT License

import argparse
import sys
from enum import Enum, auto
from typing import Any, Callable, Optional, Protocol, TextIO, cast, override
from config_as_json import Config, ConfigAutoChangeHook, ConfigNesting, \
    ConfigNestingKind, MigrateCfgWarnHook, NestedConfigs, ParseConverter, \
    PathOrStr, ReadOldConfiguration, RocfKeyMove, RocfKeyRename, RocfPath, \
    ValidationPlan, migrate_cfg, string_to_enum_best_match


CURRENT_FORMAT_VERSION = 2
"""Current configuration file format version used by this example."""


# pylint: disable-next=too-few-public-methods
class _Subparsers(Protocol):
    """Small protocol for the subparser object returned by argparse."""

    def add_parser(self, name: str, **kwargs: Any) \
            -> argparse.ArgumentParser:
        """Add one subparser and return it."""
        raise NotImplementedError


class OutputFormat(Enum):
    """Select the generated output file format."""

    CSV = auto()
    TXT = auto()


class OldOutputConfig(Config):
    """Old optional direct output object."""

    def __init__(self, from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 stderr_file: TextIO = sys.stderr) -> None:
        """Initialize the old nested output shape."""
        self.name: str = 'participants'
        self.file_name: str = 'participants.csv'
        # The old nested object used the short key ``format``.
        self.format: OutputFormat = OutputFormat.CSV
        self.encoding: str = 'utf-8'
        super().__init__(from_json_data_text=from_json_data_text,
                         from_json_filename=from_json_filename,
                         stderr_file=stderr_file)

    def parse_converters(self) -> dict[str, ParseConverter]:
        """Return conversions needed when reading enum values from JSON."""
        converter = self.get_converter_dict(OutputFormat)
        return {'format': converter}

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Return extra validation steps for this example configuration."""
        _ = stderr_file
        plan: ValidationPlan = []
        return plan


class OldExampleConfig37(Config):
    """Old course export configuration shape."""

    def __init__(self, from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 stderr_file: TextIO = sys.stderr) -> None:
        """Initialize the old top-level configuration shape."""
        self.course_title: str = 'python-intro'
        self.default_format: OutputFormat = OutputFormat.CSV
        self.output: Optional[OldOutputConfig] = None
        self.debug_trace: bool = False
        super().__init__(from_json_data_text=from_json_data_text,
                         from_json_filename=from_json_filename,
                         stderr_file=stderr_file)

    @override
    def _omit_none_from_json(self) -> list[str]:
        """Return optional members omitted while their value is None."""
        return ['output']

    @override
    def nested_configs(self) -> NestedConfigs:
        """Return nested Config declarations for the old shape."""
        return {
            'output': ConfigNesting(kind=ConfigNestingKind.OPTIONAL_MEMBER,
                                    config_type=OldOutputConfig)
        }

    def parse_converters(self) -> dict[str, ParseConverter]:
        """Return conversions needed when reading enum values from JSON."""
        return {'default_format': self.get_converter_dict(OutputFormat),
                'format': self.get_converter_dict(OutputFormat)}

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Return extra validation steps for this example configuration."""
        _ = stderr_file
        return []


class ReportOutputConfig(Config):
    """Current configuration for one generated output file."""

    def __init__(self, from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 stderr_file: TextIO = sys.stderr) -> None:
        """Initialize one current report output configuration."""
        self.name: str = 'participants'
        self.output_format: OutputFormat = OutputFormat.CSV
        self.file_name: str = 'participants.csv'
        self.encoding: str = 'utf-8'
        super().__init__(from_json_data_text=from_json_data_text,
                         from_json_filename=from_json_filename,
                         stderr_file=stderr_file)

    def parse_converters(self) -> dict[str, ParseConverter]:
        """Return conversions needed when reading enum values from JSON."""
        converter = self.get_converter_dict(OutputFormat)
        return {'output_format': converter}

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Return extra validation steps for this example configuration."""
        _ = stderr_file
        plan: ValidationPlan = []
        return plan


class Example37ReadOldConfig(ReadOldConfiguration):
    """Describe how old e37 configuration files are normalized."""

    def get_json_key_renames(self) -> list[RocfKeyRename]:
        """Return old key names that should be mapped to current names."""
        return [RocfKeyRename(old='course_title', new='course_name')]

    def get_json_key_moves(self) -> list[RocfKeyMove]:
        """Return old paths that should be moved to current paths."""
        return [
            RocfKeyMove(old_path=('default_format',),
                        new_path=('default_output_format',)),
            RocfKeyMove(old_path=('output', 'format'),
                        new_path=('output', 'output_format')),
            RocfKeyMove(old_path=('output',), new_path=('outputs', '['))
        ]

    def get_keys_to_remove_recursively(self) -> list[str]:
        """Return old key names that are no longer in current files."""
        return ['debug_trace']

    def get_values_for_missing_json_keys(self) -> dict[RocfPath, object]:
        """Return current values for paths missing from old files."""
        # The old ``output`` member was optional. If it is absent, the current
        # ``outputs`` list should exist but be empty.
        return {('format_version',): CURRENT_FORMAT_VERSION,
                ('outputs',): []}


class ExampleConfig37(Config):
    """Current course export configuration shape."""

    def __init__(self, from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 auto_ch_hook: Optional[ConfigAutoChangeHook] = None,
                 stderr_file: TextIO = sys.stderr) -> None:
        """Initialize the current top-level configuration shape."""
        self.format_version: int = CURRENT_FORMAT_VERSION
        self.course_name: str = 'python-intro'
        self.default_output_format: OutputFormat = OutputFormat.CSV
        self.outputs: list[ReportOutputConfig] = [
            ReportOutputConfig(stderr_file=stderr_file)]
        super().__init__(from_json_data_text=from_json_data_text,
                         from_json_filename=from_json_filename,
                         auto_ch_hook=auto_ch_hook, stderr_file=stderr_file)

    @override
    def nested_configs(self) -> NestedConfigs:
        """Return nested Config declarations for the current shape."""
        return {
            'outputs': ConfigNesting(kind=ConfigNestingKind.LIST_ELEMENT,
                                     config_type=ReportOutputConfig)
        }

    def _get_read_old_configuration(self) -> ReadOldConfiguration:
        """Return the object that normalizes old e37 files."""
        return Example37ReadOldConfig()

    def parse_converters(self) -> dict[str, ParseConverter]:
        """Return conversions needed when reading enum values from JSON."""
        # ``default_format`` and ``format`` are old keys. They are listed
        # because converters run before ReadOldConfiguration moves values.
        return {'default_output_format': self.get_converter_dict(OutputFormat),
                'default_format': self.get_converter_dict(OutputFormat),
                'output_format': self.get_converter_dict(OutputFormat),
                'format': self.get_converter_dict(OutputFormat)}

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Return extra validation steps for this example configuration."""
        _ = stderr_file
        return []


class Example37MigrateWarnHook(MigrateCfgWarnHook):
    """Show an application-specific migration instruction message."""

    @classmethod
    def migrate_instructions(cls) -> str:
        """Return e37-specific migration instructions."""
        txt = 'For this example, migrate the file with:\n'
        txt += 'python3 -m example.e37_read_old_nested_configuration_file '
        txt += 'migrate --input OLD.cfg --output NEW.cfg\n\n'
        return txt


def output_format_from_text(text: str) -> OutputFormat:
    """Convert command-line text to ``OutputFormat``."""
    return string_to_enum_best_match(text, OutputFormat)


def _apply_old_output_values(config: OldExampleConfig37,
                             output_name: Optional[str],
                             output_format: Optional[OutputFormat],
                             output_encoding: Optional[str],
                             output_file_name: Optional[str]) -> None:
    """Apply command-line overrides to the old optional output object."""
    assert config.output is not None
    if output_name is not None:
        config.output.name = output_name
    if output_format is not None:
        config.output.format = output_format
    if output_encoding is not None:
        config.output.encoding = output_encoding
    if output_file_name is not None:
        config.output.file_name = output_file_name


# pylint: disable-next=too-many-arguments,too-many-positional-arguments
def e37_write_old_config(config_file: PathOrStr,
                         course_title: Optional[str] = None,
                         default_format: Optional[OutputFormat] = None,
                         without_output: bool = False,
                         output_name: Optional[str] = None,
                         output_format: Optional[OutputFormat] = None,
                         output_encoding: Optional[str] = None,
                         output_file_name: Optional[str] = None,
                         debug_trace: Optional[bool] = None) -> None:
    """Write an old-shape configuration file."""
    config = OldExampleConfig37()
    if course_title is not None:
        config.course_title = course_title
    if default_format is not None:
        config.default_format = default_format
    if without_output:
        config.output = None
    else:
        config.output = OldOutputConfig()
        if any(value is not None for value in [
                output_name, output_format, output_encoding,
                output_file_name]):
            _apply_old_output_values(config, output_name, output_format,
                                     output_encoding, output_file_name)
    if debug_trace is not None:
        config.debug_trace = debug_trace
    config.write(to_json_filename=config_file)
    print(f'Old configuration written to {config_file}')


def _apply_new_output_values(config: ExampleConfig37,
                             output_name: Optional[str],
                             output_format: Optional[OutputFormat],
                             output_encoding: Optional[str],
                             output_file_name: Optional[str]) -> None:
    """Apply command-line overrides to the first current output object."""
    if not config.outputs:
        config.outputs = [ReportOutputConfig()]
    output = config.outputs[0]
    if output_name is not None:
        output.name = output_name
    if output_format is not None:
        output.output_format = output_format
    if output_encoding is not None:
        output.encoding = output_encoding
    if output_file_name is not None:
        output.file_name = output_file_name


# pylint: disable-next=too-many-arguments,too-many-positional-arguments
def e37_write_new_config(config_file: PathOrStr,
                         course_name: Optional[str] = None,
                         default_output_format: Optional[OutputFormat] = None,
                         without_outputs: bool = False,
                         output_name: Optional[str] = None,
                         output_format: Optional[OutputFormat] = None,
                         output_encoding: Optional[str] = None,
                         output_file_name: Optional[str] = None) -> None:
    """Write a current-shape configuration file."""
    config = ExampleConfig37()
    if course_name is not None:
        config.course_name = course_name
    if default_output_format is not None:
        config.default_output_format = default_output_format
    if without_outputs:
        config.outputs = []
    elif any(value is not None for value in [
            output_name, output_format, output_encoding, output_file_name]):
        _apply_new_output_values(config, output_name, output_format,
                                 output_encoding, output_file_name)
    config.write(to_json_filename=config_file)
    print(f'Current configuration written to {config_file}')


def _print_output(output_index: int, output: ReportOutputConfig) -> None:
    """Print one current output object."""
    print(f'Output {output_index} name: {output.name}')
    print(f'Output {output_index} file: {output.file_name}')
    print(f'Output {output_index} format: {output.output_format.name}')
    print(f'Output {output_index} encoding: {output.encoding}')


def e37_print_config(config_file: PathOrStr) -> None:
    """Read either old or current configuration and print current values."""
    config = ExampleConfig37(from_json_filename=config_file,
                             auto_ch_hook=Example37MigrateWarnHook(),
                             stderr_file=sys.stderr)
    print(f'Configuration read from {config_file}')
    print(f'Format version: {config.format_version}')
    print(f'Course name: {config.course_name}')
    print(f'Default output format: {config.default_output_format.name}')
    print(f'Output count: {len(config.outputs)}')
    for output_index, output in enumerate(config.outputs):
        _print_output(output_index, output)


def e37_migrate_config(infile: PathOrStr, outfile: PathOrStr) -> None:
    """Migrate an old or current file to the current file shape."""
    migrate_cfg(infile=infile, outfile=outfile, config_class=ExampleConfig37,
                stderr_file=sys.stderr)
    print(f'Configuration migrated to {outfile}')


# ----------------------------------------------------------------------------
# Only command line handling follows
# ----------------------------------------------------------------------------


def _create_argument_parser() -> argparse.ArgumentParser:
    """Create the command-line parser for this example."""
    parser = argparse.ArgumentParser(
        prog='e37_read_old_nested_configuration_file')
    subparsers = parser.add_subparsers(dest='command')
    subparsers.required = True
    _add_write_old_parser(subparsers)
    _add_write_new_parser(subparsers)
    _add_reading_parsers(subparsers)
    return parser


def _add_write_old_parser(subparsers: _Subparsers) -> None:
    """Add the ``write-old`` subcommand parser."""
    old_parser = subparsers.add_parser(
        'write-old', help='Write an old-format configuration file.')
    old_parser.add_argument('-o', '--output', required=True)
    old_parser.add_argument('--course-title')
    old_parser.add_argument('--default-format', type=output_format_from_text)
    old_parser.add_argument('--without-output', action='store_true')
    old_parser.add_argument('--output-name')
    old_parser.add_argument('--output-format', type=output_format_from_text)
    old_parser.add_argument('--output-encoding')
    old_parser.add_argument('--output-file-name')
    old_parser.add_argument('--debug-trace', action='store_true')


def _add_write_new_parser(subparsers: _Subparsers) -> None:
    """Add the ``write-new`` subcommand parser."""
    new_parser = subparsers.add_parser(
        'write-new', help='Write a current-format configuration file.')
    new_parser.add_argument('-o', '--output', required=True)
    new_parser.add_argument('--course-name')
    new_parser.add_argument('--default-output-format',
                            type=output_format_from_text)
    new_parser.add_argument('--without-outputs', action='store_true')
    new_parser.add_argument('--output-name')
    new_parser.add_argument('--output-format', type=output_format_from_text)
    new_parser.add_argument('--output-encoding')
    new_parser.add_argument('--output-file-name')


def _add_reading_parsers(subparsers: _Subparsers) -> None:
    """Add subcommand parsers that read existing configuration files."""
    parser_specs = [
        ('print', 'Read a configuration file and print current values.'),
        ('migrate', 'Write a current-format copy of a config file.')
    ]
    for command, help_text in parser_specs:
        command_parser = subparsers.add_parser(command, help=help_text)
        command_parser.add_argument('-i', '--input', required=True)
        if command == 'migrate':
            command_parser.add_argument('-o', '--output', required=True)


def _handle_write_old(parsed_args: argparse.Namespace) -> None:
    """Handle the ``write-old`` subcommand."""
    e37_write_old_config(
        config_file=cast(str, parsed_args.output),
        course_title=cast(Optional[str], parsed_args.course_title),
        default_format=cast(Optional[OutputFormat],
                            parsed_args.default_format),
        without_output=cast(bool, parsed_args.without_output),
        output_name=cast(Optional[str], parsed_args.output_name),
        output_format=cast(Optional[OutputFormat], parsed_args.output_format),
        output_encoding=cast(Optional[str], parsed_args.output_encoding),
        output_file_name=cast(Optional[str], parsed_args.output_file_name),
        debug_trace=cast(bool, parsed_args.debug_trace))


def _handle_write_new(parsed_args: argparse.Namespace) -> None:
    """Handle the ``write-new`` subcommand."""
    e37_write_new_config(
        config_file=cast(str, parsed_args.output),
        course_name=cast(Optional[str], parsed_args.course_name),
        default_output_format=cast(
            Optional[OutputFormat], parsed_args.default_output_format),
        without_outputs=cast(bool, parsed_args.without_outputs),
        output_name=cast(Optional[str], parsed_args.output_name),
        output_format=cast(Optional[OutputFormat], parsed_args.output_format),
        output_encoding=cast(Optional[str], parsed_args.output_encoding),
        output_file_name=cast(Optional[str], parsed_args.output_file_name))


def _handle_print(parsed_args: argparse.Namespace) -> None:
    """Handle the ``print`` subcommand."""
    e37_print_config(cast(str, parsed_args.input))


def _handle_migrate(parsed_args: argparse.Namespace) -> None:
    """Handle the ``migrate`` subcommand."""
    e37_migrate_config(infile=cast(str, parsed_args.input),
                       outfile=cast(str, parsed_args.output))


def main(args: Optional[list[str]] = None) -> None:
    """Run the example command line interface."""
    parsed_args = _create_argument_parser().parse_args(args)
    command = cast(str, parsed_args.command)
    handlers: dict[str, Callable[[argparse.Namespace], None]] = {
        'write-old': _handle_write_old,
        'write-new': _handle_write_new,
        'print': _handle_print,
        'migrate': _handle_migrate
    }
    handlers[command](parsed_args)


if __name__ == '__main__':
    main()
    sys.exit(0)
