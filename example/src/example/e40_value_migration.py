#! /usr/local/bin/python3
"""Show value-producing read-old-configuration migrations.

This example extends the read-old-configuration examples with
``RocfValueMigration``. A value migration is useful when one old value cannot
be described as one fixed ``old_path -> new_path`` move.

The old file shape has these values:

- ``report_kind`` is either ``summary`` or ``detail``
- ``retention_days`` is one old scalar retention setting

The current file shape has these values instead:

- ``reports.summary.enabled`` and ``reports.detail.enabled``
- ``retention.min_days`` and ``retention.max_days``

That means the old ``report_kind`` value chooses between two possible current
paths, while the old ``retention_days`` value is split into two current
values.
"""

# Copyright (c) 2026 Tom Björkholm
# MIT License

import argparse
import sys
from typing import Optional, TextIO, cast
from config_as_json import Config, ConfigAutoChangeHook, ConfigPath, \
    JsonType, MigrateCfgWarnHook, PathOrStr, ReadOldConfiguration, \
    RocfValueMigration, RocfValueWrite, ValidationPlan, migrate_cfg


CURRENT_FORMAT_VERSION = 3
"""Current configuration file format version used by this example."""


class OldExampleConfig40(Config):
    """Old report configuration shape kept only for teaching migration."""

    def __init__(self, from_json_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 stderr_file: TextIO = sys.stderr,
                 member_name: Optional[str] = None) -> None:
        """Initialize the old configuration shape."""
        # Old application versions stored the selected report kind as one
        # scalar string. There was no nested "reports" object in old files.
        self.report_name: str = 'daily-summary'
        self.report_kind: str = 'summary'
        # Old files also had one retention value. The current configuration
        # separates this into a lower and upper retention boundary.
        self.retention_days: int = 30
        super().__init__(from_json_data_text=from_json_text,
                         from_json_filename=from_json_filename,
                         stderr_file=stderr_file, member_name=member_name)

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Return extra validation steps for this example configuration."""
        return empty_validation_plan(stderr_file)


def empty_validation_plan(stderr_file: TextIO) -> ValidationPlan:
    """Return the shared empty validation plan for e40 classes."""
    _ = stderr_file
    return []


def is_summary_report(value: object) -> bool:
    """Return whether the old report kind means summary output."""
    assert isinstance(value, str)
    return value == 'summary'


def is_detail_report(value: object) -> bool:
    """Return whether the old report kind means detail output."""
    assert isinstance(value, str)
    return value == 'detail'


def enabled_from_kind(value: object) -> bool:
    """Convert an accepted old report kind to an enabled flag."""
    # The condition has already decided that this write applies. The value is
    # still checked here because migration callbacks are application code, and
    # clear failures are better than silently accepting a surprising file.
    assert isinstance(value, str)
    return bool(value)


def min_retention_days(value: object) -> int:
    """Return the current lower retention boundary."""
    assert isinstance(value, int)
    return max(1, value // 2)


def max_retention_days(value: object) -> int:
    """Return the current upper retention boundary."""
    assert isinstance(value, int)
    return value


class Example40ReadOldConfig(ReadOldConfiguration):
    """Describe how old e40 configuration files are normalized."""

    def get_value_migrations(self) -> list[RocfValueMigration]:
        """Return value-producing migrations for old e40 files."""
        # The first migration demonstrates routing. Every declared current
        # path is considered for conflict detection, but only the write whose
        # condition returns True actually produces a value.
        report_kind = RocfValueMigration(
            old_path=('report_kind',),
            writes=[
                RocfValueWrite(new_path=('reports', 'summary', 'enabled'),
                               condition=is_summary_report,
                               transform_value=enabled_from_kind),
                RocfValueWrite(new_path=('reports', 'detail', 'enabled'),
                               condition=is_detail_report,
                               transform_value=enabled_from_kind)])
        # The second migration demonstrates splitting. One old scalar value
        # produces two current values at two different current paths.
        retention = RocfValueMigration(
            old_path=('retention_days',),
            writes=[
                RocfValueWrite(new_path=('retention', 'min_days'),
                               transform_value=min_retention_days),
                RocfValueWrite(new_path=('retention', 'max_days'),
                               transform_value=max_retention_days)])
        return [report_kind, retention]

    def get_missing_path_values(self) -> dict[ConfigPath, object]:
        """Return current values for paths missing from old files."""
        # Missing values run after value migrations. That is why the selected
        # report kind can write True first, and these False defaults only fill
        # the report kind that was not selected by the old file.
        return {('format_version',): CURRENT_FORMAT_VERSION,
                ('reports', 'summary', 'enabled'): False,
                ('reports', 'detail', 'enabled'): False}


class ExampleConfig40(Config):
    """Current report configuration shape with value migrations."""

    def __init__(self, from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 auto_ch_hook: Optional[ConfigAutoChangeHook] = None,
                 stderr_file: TextIO = sys.stderr,
                 member_name: Optional[str] = None) -> None:
        """Initialize the current configuration shape."""
        # Application code only sees the current shape. Old-file support is
        # declared in Example40ReadOldConfig, not scattered through the rest
        # of the program.
        self.format_version: int = CURRENT_FORMAT_VERSION
        self.report_name: str = 'daily-summary'
        self.reports: dict[str, JsonType] = {
            'summary': {'enabled': True},
            'detail': {'enabled': False}
        }
        self.retention: dict[str, JsonType] = {
            'min_days': 15,
            'max_days': 30
        }
        super().__init__(from_json_data_text=from_json_data_text,
                         from_json_filename=from_json_filename,
                         auto_ch_hook=auto_ch_hook, stderr_file=stderr_file,
                         member_name=member_name)

    def _get_read_old_config(self) -> ReadOldConfiguration:
        """Return the object that normalizes old e40 files."""
        return Example40ReadOldConfig()

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Return extra validation steps for this example configuration."""
        return empty_validation_plan(stderr_file)


class Example40MigrateWarnHook(MigrateCfgWarnHook):
    """Show an application-specific migration instruction message."""

    @classmethod
    def migrate_instructions(cls) -> str:
        """Return e40-specific migration instructions."""
        txt = 'For this example, migrate the file with:\n'
        txt += 'python3 -m example.e40_value_migration '
        txt += 'migrate --input OLD.cfg --output NEW.cfg\n\n'
        return txt


def report_enabled(config: ExampleConfig40, name: str) -> bool:
    """Return one current report enabled flag."""
    report = config.reports[name]
    assert isinstance(report, dict)
    value = report['enabled']
    assert isinstance(value, bool)
    return value


def retention_value(config: ExampleConfig40, name: str) -> int:
    """Return one current retention value."""
    value = config.retention[name]
    assert isinstance(value, int)
    return value


def e40_write_old_config(config_file: PathOrStr,
                         report_name: Optional[str] = None,
                         report_kind: Optional[str] = None,
                         retention_days: Optional[int] = None) -> None:
    """Write an old-shape configuration file."""
    config = OldExampleConfig40()
    if report_name is not None:
        config.report_name = report_name
    if report_kind is not None:
        config.report_kind = report_kind
    if retention_days is not None:
        config.retention_days = retention_days
    config.write(to_json_filename=config_file)
    print(f'Old configuration written to {config_file}')


def e40_write_new_config(config_file: PathOrStr,
                         report_name: Optional[str] = None,
                         summary_enabled: Optional[bool] = None,
                         detail_enabled: Optional[bool] = None,
                         retention_days: Optional[int] = None) -> None:
    """Write a current-shape configuration file."""
    config = ExampleConfig40()
    if report_name is not None:
        config.report_name = report_name
    if summary_enabled is not None:
        report = config.reports['summary']
        assert isinstance(report, dict)
        report['enabled'] = summary_enabled
    if detail_enabled is not None:
        report = config.reports['detail']
        assert isinstance(report, dict)
        report['enabled'] = detail_enabled
    if retention_days is not None:
        config.retention['min_days'] = max(1, retention_days // 2)
        config.retention['max_days'] = retention_days
    config.write(to_json_filename=config_file)
    print(f'Current configuration written to {config_file}')


def e40_print_config(config_file: PathOrStr) -> None:
    """Read either old or current configuration and print current values."""
    config = ExampleConfig40(from_json_filename=config_file,
                             auto_ch_hook=Example40MigrateWarnHook(),
                             stderr_file=sys.stderr)
    print(f'Configuration read from {config_file}')
    print(f'Format version: {config.format_version}')
    print(f'Report name: {config.report_name}')
    print(f'Summary report: {report_enabled(config, "summary")}')
    print(f'Detail report: {report_enabled(config, "detail")}')
    print(f'Retention min days: {retention_value(config, "min_days")}')
    print(f'Retention max days: {retention_value(config, "max_days")}')


def e40_migrate_config(infile: PathOrStr, outfile: PathOrStr) -> None:
    """Migrate an old or current file to the current file shape."""
    migrate_cfg(infile=infile, outfile=outfile, config_class=ExampleConfig40,
                stderr_file=sys.stderr)
    print(f'Configuration migrated to {outfile}')


# ----------------------------------------------------------------------------
# Only command line handling follows
# ----------------------------------------------------------------------------


def _bool_from_text(text: str) -> bool:
    """Convert command-line text to a boolean value."""
    values = {'true': True, 'false': False}
    try:
        return values[text.lower()]
    except KeyError as exc:
        raise argparse.ArgumentTypeError("Expected 'true' or 'false'.") \
            from exc


def _add_output_arg(parser: argparse.ArgumentParser) -> None:
    """Add the output-file option shared by writer subcommands."""
    parser.add_argument('-o', '--output', required=True)


def _add_input_arg(parser: argparse.ArgumentParser) -> None:
    """Add the input-file option shared by reader subcommands."""
    parser.add_argument('-i', '--input', required=True)


def _add_old_options(parser: argparse.ArgumentParser) -> None:
    """Add old-shape configuration options to one parser."""
    parser.add_argument('--report-name')
    parser.add_argument('--report-kind')
    parser.add_argument('--retention-days', type=int)


def _add_new_options(parser: argparse.ArgumentParser) -> None:
    """Add current-shape configuration options to one parser."""
    parser.add_argument('--report-name')
    parser.add_argument('--summary-enabled', type=_bool_from_text)
    parser.add_argument('--detail-enabled', type=_bool_from_text)
    parser.add_argument('--retention-days', type=int)


def _create_argument_parser() -> argparse.ArgumentParser:
    """Create the command-line parser for this example."""
    parser = argparse.ArgumentParser(prog='e40_value_migration')
    subparsers = parser.add_subparsers(dest='command')
    subparsers.required = True
    old_parser = subparsers.add_parser('write-old',
                                       help='Write an old e40 file.')
    _add_output_arg(old_parser)
    _add_old_options(old_parser)
    new_parser = subparsers.add_parser('write-new',
                                       help='Write a current e40 file.')
    _add_output_arg(new_parser)
    _add_new_options(new_parser)
    print_parser = subparsers.add_parser('print',
                                         help='Print current e40 values.')
    _add_input_arg(print_parser)
    migrate_parser = subparsers.add_parser('migrate',
                                           help='Migrate an e40 file.')
    _add_input_arg(migrate_parser)
    _add_output_arg(migrate_parser)
    return parser


def _handle_write_old(parsed_args: argparse.Namespace) -> None:
    """Handle the ``write-old`` subcommand."""
    e40_write_old_config(
        config_file=cast(str, parsed_args.output),
        report_name=cast(Optional[str], parsed_args.report_name),
        report_kind=cast(Optional[str], parsed_args.report_kind),
        retention_days=cast(Optional[int], parsed_args.retention_days))


def _handle_write_new(parsed_args: argparse.Namespace) -> None:
    """Handle the ``write-new`` subcommand."""
    e40_write_new_config(
        config_file=cast(str, parsed_args.output),
        report_name=cast(Optional[str], parsed_args.report_name),
        summary_enabled=cast(Optional[bool], parsed_args.summary_enabled),
        detail_enabled=cast(Optional[bool], parsed_args.detail_enabled),
        retention_days=cast(Optional[int], parsed_args.retention_days))


def main(args: Optional[list[str]] = None) -> None:
    """Run the example command line interface."""
    parsed_args = _create_argument_parser().parse_args(args)
    command = cast(str, parsed_args.command)
    handlers = {'write-old': _handle_write_old, 'write-new': _handle_write_new}
    if command in handlers:
        handlers[command](parsed_args)
    if command == 'print':
        e40_print_config(cast(str, parsed_args.input))
    if command == 'migrate':
        e40_migrate_config(infile=cast(str, parsed_args.input),
                           outfile=cast(str, parsed_args.output))


if __name__ == '__main__':
    main()
    sys.exit(0)
