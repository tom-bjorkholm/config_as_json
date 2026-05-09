#! /usr/local/bin/python3
"""Show the basic list validators for element values and list size.

This example is the first teaching example that uses list-valued
configuration members. It keeps the lesson deliberately small by showing
2 common validation patterns:

- ``ListValueValidator`` checks each element in a list separately
- ``ListSizeValidator`` checks the size of the list as a whole

The ``report_formats`` rule also shows that ``ListValueValidator`` can get
its allowed values from a function. That is useful when the application
calculates allowed values from installed plugins, enabled features, or other
runtime state.

Readers who want the general introduction to ``ValidationPlan`` should
first read ``e03_scalar_validators.py``. This example only repeats the
parts that are important for understanding list validators.
"""

# Copyright (c) 2026 Tom Björkholm
# MIT License

from typing import Optional, Sequence, TextIO
import sys
from config_as_json import Config, PathOrStr, ValidationPlan, \
    MemberValidationStep, ListValueValidator, ListSizeValidator, \
    InvalidConfiguration, InvalidConfigurationValue
from .cmd_line_handling import InputSpec, SetValues, cmd_line_handling


class ExampleConfig6(Config):
    """Configuration that introduces the most basic list validators."""

    def __init__(self, from_json_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 stderr_file: TextIO = sys.stderr) -> None:
        """Initialize the configuration.

        Args:
            from_json_text: Optional JSON text to parse directly.
            from_json_filename: Optional path to a JSON file to read.
            stderr_file: Stream used for user-facing diagnostics.
        """
        # As in the earlier examples, the public instance attributes define
        # both the configuration schema and the default values.
        #
        # The new thing here is that ordinary Python lists are allowed as
        # configuration members.
        self.retry_delays_seconds: list[int] = [1, 5, 10]
        self.report_formats: list[str] = ['json', 'html']
        self.backup_servers: list[str] = ['backup-a', 'backup-b']
        super().__init__(from_json_data_text=from_json_text,
                         from_json_filename=from_json_filename,
                         stderr_file=stderr_file)

    def allowed_report_formats(self) -> Sequence[str]:
        """Return report formats currently enabled by the application."""
        return ['json', 'html', 'csv']

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Return the validation steps for this list example."""
        _ = stderr_file
        # ``ValidationPlan`` is an ordered list of validation steps.
        # In this example every rule validates one named member, so each
        # step is a ``MemberValidationStep``.
        #
        # ``ListValueValidator`` checks the elements one by one.
        # Here we use it twice:
        #
        # - the retry delays must each stay within an integer range
        # - the report formats must each be one of the strings returned by
        #   ``allowed_report_formats()``
        #
        # ``ListSizeValidator`` is different. It does not inspect the
        # element values at all. It only checks how many elements the list
        # contains.
        get_formats = self.allowed_report_formats
        retry_values = ListValueValidator(1, 60, None)
        report_values = ListValueValidator(None, None, get_formats)
        server_count = ListSizeValidator(1, 3)
        return [MemberValidationStep(['retry_delays_seconds'], retry_values),
                MemberValidationStep(['report_formats'], report_values),
                MemberValidationStep(['backup_servers'], server_count)]


# pylint: disable=duplicate-code
def e06_list_basic_validators_set(set_values: SetValues,
                                  config_file: PathOrStr) -> None:
    """Create configuration, apply overrides, and store it.

    Args:
        set_values: Values that should differ from the defaults.
        config_file: Path where to write the configuration file.
    """
    config = ExampleConfig6()
    # The set command follows the same pattern as earlier examples:
    # start with defaults, apply only the requested overrides, and let
    # ``Config.write()`` validate everything before JSON is written.
    for key, value in set_values.items():
        if hasattr(config, key):
            setattr(config, key, value)
        else:
            raise ValueError(f'Invalid key: {key}')
    # Validation happens during ``write()``.
    # If a value is invalid, the Config base class prints the error message
    # for the user, so this example only needs to stop quietly.
    try:
        config.write(to_json_filename=config_file)
        print(f'Configuration written to {config_file}')
    except (InvalidConfiguration, InvalidConfigurationValue):
        pass  # Error already printed by the Config object.


# pylint: disable=duplicate-code
def e06_list_basic_validators_print(config_file: PathOrStr) -> None:
    """Read a configuration file and show how the values are used.

    Args:
        config_file: Path to the configuration file to read.
    """
    # Reading from JSON also validates the data.
    # That means the application sees either a fully validated config
    # object, or an error message and an early return.
    try:
        config = ExampleConfig6(from_json_filename=config_file)
        print(f'Configuration read from {config_file}')
        print(f'Retry delays in seconds: {config.retry_delays_seconds}')
        print(f'Report formats: {config.report_formats}')
        print(f'Backup servers: {config.backup_servers}')
    except (InvalidConfiguration, InvalidConfigurationValue):
        pass  # Error already printed by the Config object.


# -----------------------------------------------------------------------------
# The rest of this file is the command line handling code.
# This is to be able to run the example from the command line,
# but it could be done in any other way, and is not part of what this example
# is trying to teach.
# -----------------------------------------------------------------------------

INPUT_SPECS = [
    InputSpec(name='retry_delays_seconds', single=False, value_type=int),
    InputSpec(name='report_formats', single=False, value_type=str),
    InputSpec(name='backup_servers', single=False, value_type=str)
]
"""Command line values that the example exposes for ``set``."""


def main(args: Optional[list[str]] = None) -> None:
    """Run the example command line interface.

    Args:
        args: Optional replacement for ``sys.argv[1:]``, mainly for tests.
    """
    cmd_line_handling(example_name='e06_list_basic_validators',
                      input_specs=INPUT_SPECS,
                      set_command=e06_list_basic_validators_set,
                      print_command=e06_list_basic_validators_print, args=args)


if __name__ == '__main__':
    main()
    sys.exit(0)
