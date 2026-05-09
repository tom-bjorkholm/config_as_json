#! /usr/local/bin/python3
"""Teach CSV dialect and character encoding validators.

This example shows two validators for configuration values that are strings
or dicts in JSON, but need to be checked against Python runtime facilities:

- ``CharEncodingValidator`` checks that a string names a recognized text
  encoding
- ``CsvDialectValidator`` checks and normalizes a JSON-friendly
  ``csv.Dialect`` description
"""

# Copyright (c) 2026 Tom Björkholm
# MIT License

from csv import Dialect
from typing import Optional, TextIO
import sys
from config_as_json import CharEncodingValidator, Config, CsvDialectConfig, \
    CsvDialectValidator, InvalidConfiguration, InvalidConfigurationValue, \
    MemberValidationStep, PathOrStr, ValidationPlan, get_csv_dialect
from .cmd_line_handling import InputSpec, SetValues, cmd_line_handling

# pylint: disable=duplicate-code


class ExampleConfig17(Config):
    """Configuration with CSV dialect and character encoding settings."""

    def __init__(self, from_json_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 stderr_file: TextIO = sys.stderr) -> None:
        """Initialize the configuration.

        Args:
            from_json_text: Optional JSON text to parse directly.
            from_json_filename: Optional path to a JSON file to read.
            stderr_file: Stream used for user-facing diagnostics.
        """
        self.input_encoding: str = 'utf_8_sig'
        self.output_encoding: str = 'utf-8'
        self.csv_dialect: CsvDialectConfig = {}
        self.csv_dialect['name'] = 'csv.excel'
        self.csv_dialect['delimiter'] = ','
        self.csv_dialect['quoting'] = None
        self.csv_dialect['quotechar'] = '"'
        self.csv_dialect['lineterminator'] = None
        self.csv_dialect['escapechar'] = None
        self._unchecked_dicts = ['csv_dialect']
        super().__init__(from_json_data_text=from_json_text,
                         from_json_filename=from_json_filename,
                         stderr_file=stderr_file)

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Return the ordered validation steps for this example."""
        _ = stderr_file
        return [
            MemberValidationStep(
                member_names=['input_encoding', 'output_encoding'],
                validator=CharEncodingValidator()),
            MemberValidationStep(member_names=['csv_dialect'],
                                 validator=CsvDialectValidator())]

    def get_csv_dialect(self, stderr_file: TextIO = sys.stderr) -> Dialect:
        """Return the configured CSV dialect as a standard-library object.

        Args:
            stderr_file: Stream used for user-facing diagnostics.

        Returns:
            The configured ``csv.Dialect`` object.
        """
        return get_csv_dialect(
            name=self.csv_dialect['name'],
            delimiter=self.csv_dialect['delimiter'],
            quoting=self.csv_dialect['quoting'],
            quotechar=self.csv_dialect['quotechar'],
            lineterminator=self.csv_dialect['lineterminator'],
            escapechar=self.csv_dialect['escapechar'], stderr_file=stderr_file)


# pylint: disable=duplicate-code
def e17_csv_dialect_and_encoding_set(set_values: SetValues,
                                     config_file: PathOrStr) -> None:
    """Create configuration, apply overrides, and store it.

    Args:
        set_values: Values that should differ from the defaults.
        config_file: Path where to write the configuration file.
    """
    config = ExampleConfig17()
    for key, value in set_values.items():
        if hasattr(config, key):
            setattr(config, key, value)
        else:
            raise ValueError(f'Invalid key: {key}')
    try:
        config.write(to_json_filename=config_file)
        print(f'Configuration written to {config_file}')
    except (InvalidConfiguration, InvalidConfigurationValue):
        pass  # Error already printed by the Config object.


def e17_csv_dialect_and_encoding_print(config_file: PathOrStr) -> None:
    """Read a configuration file and show how the values are used.

    Args:
        config_file: Path to the configuration file to read.
    """
    try:
        config = ExampleConfig17(from_json_filename=config_file)
        dialect = config.get_csv_dialect()
        print(f'Configuration read from {config_file}')
        print(f'Input encoding: {config.input_encoding}')
        print(f'Output encoding: {config.output_encoding}')
        print(f'CSV delimiter: {dialect.delimiter}')
        print(f'CSV quotechar: {dialect.quotechar}')
        print(f'CSV line terminator: {dialect.lineterminator!r}')
    except (InvalidConfiguration, InvalidConfigurationValue):
        pass  # Error already printed by the Config object.


INPUT_SPECS = [
    InputSpec(name='input_encoding', single=True, value_type=str),
    InputSpec(name='output_encoding', single=True, value_type=str),
    InputSpec(name='csv_dialect', single=True, value_type=str, json_value=True)
]
"""Command line values that the example exposes for ``set``."""


def main(args: Optional[list[str]] = None) -> None:
    """Run the example command line interface.

    Args:
        args: Optional replacement for ``sys.argv[1:]``, mainly for tests.
    """
    cmd_line_handling(example_name='e17_csv_dialect_and_encoding',
                      input_specs=INPUT_SPECS,
                      set_command=e17_csv_dialect_and_encoding_set,
                      print_command=e17_csv_dialect_and_encoding_print,
                      args=args)


if __name__ == '__main__':
    main()
    sys.exit(0)
