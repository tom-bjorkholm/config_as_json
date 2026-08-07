#! /usr/local/bin/python3
"""Show how to read and migrate old configuration files.

Applications often need to read configuration files written by older
versions. This example shows three common compatibility cases:

- an old key name is accepted and renamed to the current key name
- a key that is mandatory today is missing in the old file and receives a
  value chosen by the current application
- a key that existed only in the old file is accepted and removed

The old file shape in this example uses ``title`` and ``refresh_interval``.
The current file shape uses ``report_name`` and ``refresh_seconds`` instead,
and also requires ``format_version`` and ``max_items``. The old file shape
also has ``debug_trace``, which no longer exists in the current
configuration. The current configuration class declares the compatibility
rules, so application code can read either file shape and work with the
current member names.

This example also shows the easy way to tell the user exactly what was
changed: ``ConfigAutoChangeHook.print_changes()``. See
``e37_read_old_nested_configuration_file`` for the other way, where the
application reads the structured change records itself.
"""

# Copyright (c) 2026 Tom Björkholm
# MIT License

import argparse
import sys
from enum import Enum, auto
from typing import Optional, TextIO, cast, override
from config_as_json import Config, ConfigAutoChangeHook, MigrateCfgWarnHook, \
    ConfigPath, ParseConverter, PathOrStr, ReadOldConfiguration, \
    RocfKeyRename, ValidationPlan, string_to_enum_best_match, migrate_cfg


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
        # This class deliberately models the file shape produced by an older
        # application version. Real applications usually do not need to keep
        # an old Config class in production code; it is here so the example
        # can write old files for experimentation.
        self.title: str = 'daily-summary'
        self.output_format: OutputFormat = OutputFormat.HTML
        self.refresh_interval: int = 300
        self.debug_trace: bool = False
        super().__init__(from_json_data_text=from_json_text,
                         from_json_filename=from_json_filename,
                         stderr_file=stderr_file)

    def parse_converters(self) -> dict[str, ParseConverter]:
        """Return conversions needed when reading enum values from JSON."""
        # Enum values in JSON are strings. Config uses this converter while
        # parsing so application code receives OutputFormat members.
        return {'output_format': self.get_converter_dict(OutputFormat)}

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Return extra validation steps for this example configuration."""
        _ = stderr_file
        return []


class Example31ReadOldConfig(ReadOldConfiguration):
    """Describe how old e31 configuration files are normalized."""

    def get_missing_path_values(self) -> dict[ConfigPath, object]:
        """Return current values for paths missing from old files."""
        # These keys are mandatory in the current shape, but old files never
        # contained them. The values are inserted after old names have been
        # removed or renamed.
        return {('format_version',): CURRENT_FORMAT_VERSION,
                ('max_items',): 25}

    def get_keys_to_prune(self) -> list[str]:
        """Return old key names that are no longer in current files."""
        # Recursive removal is useful when an old setting could appear in more
        # than one place. It removes every matching JSON object member.
        return ['debug_trace']

    def get_json_key_renames(self) -> list[RocfKeyRename]:
        """Return old key names that should be mapped to current names."""
        # Key renames are name-based and recursive. They are best for simple
        # "same meaning, new name" changes.
        return [RocfKeyRename(old='title', new='report_name'),
                RocfKeyRename(old='refresh_interval', new='refresh_seconds')]


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
        # The current Config class contains only the current public shape.
        # Old-file support is kept in Example31ReadOldConfig below, so normal
        # application code can use current attribute names everywhere.
        self.format_version: int = CURRENT_FORMAT_VERSION
        self.report_name: str = 'daily-summary'
        self.output_format: OutputFormat = OutputFormat.HTML
        self.refresh_seconds: int = 300
        self.max_items: int = 25
        super().__init__(from_json_data_text=from_json_data_text,
                         from_json_filename=from_json_filename,
                         auto_ch_hook=auto_ch_hook, stderr_file=stderr_file)

    def _get_read_old_config(self) -> ReadOldConfiguration:
        """Return the object that normalizes old e31 files."""
        # Config.parse_json() calls this hook after JSON has been parsed and
        # enum strings have been converted, but before required-key checking.
        return Example31ReadOldConfig()

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Return extra validation steps for this example configuration."""
        _ = stderr_file
        return []

    def parse_converters(self) -> dict[str, ParseConverter]:
        """Return conversions needed when reading enum values from JSON."""
        # The enum key has the same name in the old and current shape, so only
        # one converter entry is needed in this simple example.
        return {'output_format': self.get_converter_dict(OutputFormat)}


class Example31MigrateWarnHook(MigrateCfgWarnHook):
    """Warn about old files and print what was changed automatically."""

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

    @override
    def auto_changed(self, old_keys_handled: list[str],
                     rocf_vals_handled: list[str],
                     stderr_file: TextIO) -> None:
        """Print the migration warning and then every automatic change.

        Args:
            old_keys_handled: Old keys and paths that were accepted.
            rocf_vals_handled: Current paths that received a value.
            stderr_file: Stream used for user-facing diagnostics.
        """
        # Config calls this once after parsing, but only when at least one
        # automatic change was actually applied. MigrateCfgWarnHook already
        # implements it and prints the standard "please migrate" warning, so
        # call it through super() before adding anything of our own.
        super().auto_changed(old_keys_handled=old_keys_handled,
                             rocf_vals_handled=rocf_vals_handled,
                             stderr_file=stderr_file)
        # The two list arguments above are the old summary form. They are kept
        # unchanged forever, so old hook classes keep working, but they cannot
        # say whether "old_name -> new_name" means a real move or an old value
        # that was thrown away because the current value won.
        #
        # print_changes() prints one line per actual change, with that
        # distinction included. It is the recommended way to report details:
        # it needs no knowledge at all of how the hook stores its records, so
        # it keeps working unchanged when a future config_as_json records
        # more details than it does today.
        #
        # A hook that wants the details as data instead of as text reads the
        # records in self.changes. That is shown in
        # e37_read_old_nested_configuration_file.
        self.print_changes(stderr_file=stderr_file)


def output_format_from_text(text: str) -> OutputFormat:
    """Convert command-line text to ``OutputFormat``."""
    return string_to_enum_best_match(text, OutputFormat)


def e31_write_old_config(config_file: PathOrStr, title: Optional[str] = None,
                         output_format: Optional[OutputFormat] = None,
                         refresh_interval: Optional[int] = None,
                         debug_trace: Optional[bool] = None) -> None:
    """Write an old-shape configuration file.

    Args:
        config_file: Path where to write the old configuration file.
        title: Optional report title override.
        output_format: Optional output format override.
        refresh_interval: Optional refresh interval override.
        debug_trace: Optional old debug trace override.
    """
    config = OldExampleConfig31()
    if title is not None:
        config.title = title
    if output_format is not None:
        config.output_format = output_format
    if refresh_interval is not None:
        config.refresh_interval = refresh_interval
    if debug_trace is not None:
        config.debug_trace = debug_trace
    config.write(to_json_filename=config_file)
    print(f'Old configuration written to {config_file}')


def e31_write_new_config(config_file: PathOrStr,
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
    # The caller always receives ExampleConfig31 with current member names.
    # If an old file was normalized, the hook prints a migration hint.
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
    # migrate_cfg() simply reads through ExampleConfig31 and writes it back.
    # That means the same read-old rules are used for printing and migration.
    migrate_cfg(infile=infile, outfile=outfile, config_class=ExampleConfig31,
                stderr_file=sys.stderr)
    print(f'Configuration migrated to {outfile}')


# ----------------------------------------------------------------------------
# Only command line handling follows
# ----------------------------------------------------------------------------


def _create_argument_parser() -> argparse.ArgumentParser:
    """Create the command-line parser for this example."""
    parser = argparse.ArgumentParser(prog='e31_read_old_configuration_file')
    subparsers = parser.add_subparsers(dest='command')
    subparsers.required = True
    old_parser = subparsers.add_parser(
        'write-old', help='Write an old-format configuration file.')
    old_parser.add_argument('-o', '--output', required=True)
    old_parser.add_argument('--title')
    old_parser.add_argument('--output-format', type=output_format_from_text)
    old_parser.add_argument('--refresh-interval', type=int)
    old_parser.add_argument('--debug-trace', action='store_true')
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
        output_format=cast(Optional[OutputFormat], parsed_args.output_format),
        refresh_interval=cast(Optional[int], parsed_args.refresh_interval),
        debug_trace=cast(bool, parsed_args.debug_trace))


def _handle_write_new(parsed_args: argparse.Namespace) -> None:
    """Handle the ``write-new`` subcommand."""
    e31_write_new_config(
        config_file=cast(str, parsed_args.output),
        report_name=cast(Optional[str], parsed_args.report_name),
        output_format=cast(Optional[OutputFormat], parsed_args.output_format),
        refresh_seconds=cast(Optional[int], parsed_args.refresh_seconds),
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
