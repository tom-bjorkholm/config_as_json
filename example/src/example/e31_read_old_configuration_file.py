#! /usr/local/bin/python3
"""Show how to read and migrate old configuration files.

Applications often need to read configuration files written by older
versions. This example shows two common compatibility cases:

- an old key name is accepted and renamed to the current key name
- a key that is mandatory today is missing in the old file and receives a
  value chosen by the current application

The old file shape in this example uses ``title`` and ``refresh_interval``.
The current file shape uses ``report_name`` and ``refresh_seconds`` instead,
and also requires ``format_version`` and ``max_items``. The current
configuration class declares the compatibility rules, so application code can
read either file shape and work with the current member names.
"""

# Copyright (c) 2026 Tom Björkholm
# MIT License

import argparse
import sys
from enum import Enum, auto
from os.path import exists
from typing import Optional, TextIO, cast
from config_as_json import Config, ConfigAutoChangeHook, JsonType, \
    MigrateCfgWarnHook, ParseConverter, PathOrStr, RocfKeyRename, \
    ValidationPlan, string_to_enum_best_match


CURRENT_FORMAT_VERSION = 2
"""Current configuration file format version used by this example."""


class OutputFormat(Enum):
    """Select the report file format."""

    HTML = auto()
    TEXT = auto()


class OldExampleConfig31(Config):
    """Old report configuration shape kept only for teaching migration."""

    def __init__(self, from_json_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 stderr_file: TextIO = sys.stderr) -> None:
        """Initialize the old configuration shape.

        Args:
            from_json_text: Optional JSON text to parse directly.
            from_json_filename: Optional path to a JSON file to read.
            stderr_file: Stream used for user-facing diagnostics.
        """
        self.title: str = 'daily-summary'
        self.output_format: OutputFormat = OutputFormat.HTML
        self.refresh_interval: int = 300
        super().__init__(from_json_data_text=from_json_text,
                         from_json_filename=from_json_filename,
                         stderr_file=stderr_file)

    def parse_converters(self) -> dict[str, ParseConverter]:
        """Return conversions needed when reading enum values from JSON."""
        return {'output_format': self.get_converter_dict(OutputFormat)}

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Return extra validation steps for this example configuration."""
        _ = stderr_file
        return []


class ExampleConfig31(Config):
    """Current report configuration shape with old-file compatibility."""

    def __init__(self, from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 auto_ch_hook: Optional[ConfigAutoChangeHook] = None,
                 stderr_file: TextIO = sys.stderr) -> None:
        """Initialize the current configuration shape.

        Args:
            from_json_data_text: Optional JSON text to parse directly.
            from_json_filename: Optional path to a JSON file to read.
            auto_ch_hook: Hook notified if old-file compatibility was used.
            stderr_file: Stream used for user-facing diagnostics.
        """
        self.format_version: int = CURRENT_FORMAT_VERSION
        self.report_name: str = 'daily-summary'
        self.output_format: OutputFormat = OutputFormat.HTML
        self.refresh_seconds: int = 300
        self.max_items: int = 25
        super().__init__(from_json_data_text=from_json_data_text,
                         from_json_filename=from_json_filename,
                         auto_ch_hook=auto_ch_hook,
                         stderr_file=stderr_file)

    def _rocf_values_for_missing_json_keys(self) -> dict[str, JsonType]:
        """Return current values for keys missing from old files."""
        return {'format_version': CURRENT_FORMAT_VERSION,
                'max_items': 25}

    def _rocf_get_json_key_renames(self) -> list[RocfKeyRename]:
        """Return old key names that should be mapped to current names."""
        return [RocfKeyRename(old='title', new='report_name'),
                RocfKeyRename(old='refresh_interval',
                              new='refresh_seconds')]

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Return extra validation steps for this example configuration."""
        _ = stderr_file
        return []

    def parse_converters(self) -> dict[str, ParseConverter]:
        """Return conversions needed when reading enum values from JSON."""
        return {'output_format': self.get_converter_dict(OutputFormat)}


class Example31MigrateWarnHook(MigrateCfgWarnHook):
    """Show an application-specific migration instruction message."""

    @classmethod
    def migrate_instructions(cls) -> str:
        """Return e31-specific migration instructions.

        Returns:
            Text that explains how to migrate this example configuration file.
        """
        txt = 'For this example, migrate the file with:\n'
        txt += 'python3 -m example.e31_read_old_configuration_file '
        txt += 'migrate --input OLD.cfg --output NEW.cfg\n\n'
        return txt


def output_format_from_text(text: str) -> OutputFormat:
    """Convert command-line text to ``OutputFormat``."""
    return string_to_enum_best_match(text, OutputFormat)


def e31_write_old_config(
        config_file: PathOrStr,
        title: Optional[str] = None,
        output_format: Optional[OutputFormat] = None,
        refresh_interval: Optional[int] = None) -> None:
    """Write an old-shape configuration file.

    Args:
        config_file: Path where to write the old configuration file.
        title: Optional report title override.
        output_format: Optional output format override.
        refresh_interval: Optional refresh interval override.
    """
    config = OldExampleConfig31()
    if title is not None:
        config.title = title
    if output_format is not None:
        config.output_format = output_format
    if refresh_interval is not None:
        config.refresh_interval = refresh_interval
    config.write(to_json_filename=config_file)
    print(f'Old configuration written to {config_file}')


def e31_write_new_config(
        config_file: PathOrStr,
        report_name: Optional[str] = None,
        output_format: Optional[OutputFormat] = None,
        refresh_seconds: Optional[int] = None,
        max_items: Optional[int] = None) -> None:
    """Write a current-shape configuration file.

    Args:
        config_file: Path where to write the current configuration file.
        report_name: Optional report name override.
        output_format: Optional output format override.
        refresh_seconds: Optional refresh seconds override.
        max_items: Optional maximum item count override.
    """
    config = ExampleConfig31()
    if report_name is not None:
        config.report_name = report_name
    if output_format is not None:
        config.output_format = output_format
    if refresh_seconds is not None:
        config.refresh_seconds = refresh_seconds
    if max_items is not None:
        config.max_items = max_items
    config.write(to_json_filename=config_file)
    print(f'Current configuration written to {config_file}')


def e31_print_config(config_file: PathOrStr) -> None:
    """Read either old or current configuration and print current values.

    Args:
        config_file: Path to the configuration file to read.
    """
    config = ExampleConfig31(from_json_filename=config_file,
                             auto_ch_hook=Example31MigrateWarnHook(),
                             stderr_file=sys.stderr)
    print(f'Configuration read from {config_file}')
    print(f'Format version: {config.format_version}')
    print(f'Report name: {config.report_name}')
    print(f'Output format: {config.output_format.name}')
    print(f'Refresh seconds: {config.refresh_seconds}')
    print(f'Max items: {config.max_items}')


def e31_migrate_config(infile: PathOrStr, outfile: PathOrStr) -> None:
    """Migrate an old or current file to the current file shape.

    Args:
        infile: Existing configuration file to read.
        outfile: New file that should receive current-format JSON.
    """
    if not exists(infile):
        print(f'Cannot find input configuration file {infile}',
              file=sys.stderr)
        sys.exit(1)
    if exists(outfile):
        print(f'Output configuration file {outfile} already exists.\n' +
              'Cowardly refusing to overwrite existing configuration file.',
              file=sys.stderr)
        sys.exit(1)
    config = ExampleConfig31(from_json_filename=infile,
                             auto_ch_hook=ConfigAutoChangeHook(),
                             stderr_file=sys.stderr)
    config.write(to_json_filename=outfile)
    print(f'Configuration migrated to {outfile}')


# ----------------------------------------------------------------------------
# Only command line handling follows
# ----------------------------------------------------------------------------


def _create_argument_parser() -> argparse.ArgumentParser:
    """Create the command-line parser for this example."""
    parser = argparse.ArgumentParser(
        prog='e31_read_old_configuration_file')
    subparsers = parser.add_subparsers(dest='command')
    subparsers.required = True
    old_parser = subparsers.add_parser(
        'write-old', help='Write an old-format configuration file.')
    old_parser.add_argument('-o', '--output', required=True)
    old_parser.add_argument('--title')
    old_parser.add_argument('--output-format', type=output_format_from_text)
    old_parser.add_argument('--refresh-interval', type=int)
    new_parser = subparsers.add_parser(
        'write-new', help='Write a current-format configuration file.')
    new_parser.add_argument('-o', '--output', required=True)
    new_parser.add_argument('--report-name')
    new_parser.add_argument('--output-format', type=output_format_from_text)
    new_parser.add_argument('--refresh-seconds', type=int)
    new_parser.add_argument('--max-items', type=int)
    print_parser = subparsers.add_parser(
        'print', help='Read a configuration file and print current values.')
    print_parser.add_argument('-i', '--input', required=True)
    migrate_parser = subparsers.add_parser(
        'migrate', help='Write a current-format copy of a config file.')
    migrate_parser.add_argument('-i', '--input', required=True)
    migrate_parser.add_argument('-o', '--output', required=True)
    return parser


def _handle_write_old(parsed_args: argparse.Namespace) -> None:
    """Handle the ``write-old`` subcommand."""
    e31_write_old_config(
        config_file=cast(str, parsed_args.output),
        title=cast(Optional[str], parsed_args.title),
        output_format=cast(Optional[OutputFormat],
                           parsed_args.output_format),
        refresh_interval=cast(Optional[int],
                              parsed_args.refresh_interval))


def _handle_write_new(parsed_args: argparse.Namespace) -> None:
    """Handle the ``write-new`` subcommand."""
    e31_write_new_config(
        config_file=cast(str, parsed_args.output),
        report_name=cast(Optional[str], parsed_args.report_name),
        output_format=cast(Optional[OutputFormat],
                           parsed_args.output_format),
        refresh_seconds=cast(Optional[int],
                             parsed_args.refresh_seconds),
        max_items=cast(Optional[int], parsed_args.max_items))


def main(args: Optional[list[str]] = None) -> None:
    """Run the example command line interface.

    Args:
        args: Optional replacement for ``sys.argv[1:]``, mainly for tests.
    """
    parsed_args = _create_argument_parser().parse_args(args)
    command = cast(str, parsed_args.command)
    if command == 'write-old':
        _handle_write_old(parsed_args)
    elif command == 'write-new':
        _handle_write_new(parsed_args)
    elif command == 'print':
        e31_print_config(cast(str, parsed_args.input))
    elif command == 'migrate':
        e31_migrate_config(infile=cast(str, parsed_args.input),
                           outfile=cast(str, parsed_args.output))


if __name__ == '__main__':
    main()
    sys.exit(0)
