#! /usr/local/bin/python3
"""Show the difference between checking order and normalizing order.

This example teaches 2 related list validators:

- ``ListIsOrderedValidator`` rejects lists that are not already ordered
- ``ListOrderingValidator`` reorders the list and stores the normalized
  result

The example also shows one custom less-than comparator for
case-insensitive string sorting. The same style of comparator can also be
passed to ``ListIsOrderedValidator`` when you want to *check* a custom
ordering rule instead of normalizing the list.
"""

# Copyright (c) 2026 Tom Björkholm
# MIT License

from typing import Optional, TextIO
import sys
from config_as_json import Config, PathOrStr, ValidationPlan, \
    MemberValidationStep, ListIsOrderedValidator, ListOrderingValidator, \
    InvalidConfiguration
from .cmd_line_handling import InputSpec, SetValues, cmd_line_handling


def casefold_lt(left: str, right: str) -> bool:
    """Compare strings case-insensitively for alphabetical order."""
    return left.casefold() < right.casefold()


class ExampleConfig7(Config):
    """Configuration that contrasts list checking with list normalization."""

    def __init__(self, from_json_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 stderr_file: TextIO = sys.stderr) -> None:
        """Initialize the configuration.

        Args:
            from_json_text: Optional JSON text to parse directly.
            from_json_filename: Optional path to a JSON file to read.
            stderr_file: Stream used for user-facing diagnostics.
        """
        # ``alert_thresholds`` is the kind of list where the user usually
        # wants a validation error if the thresholds were entered in the
        # wrong order.
        self.alert_thresholds: list[float] = [0.5, 0.75, 0.9]
        # ``report_names`` shows the opposite design choice.
        # There we choose to normalize the order for the user.
        self.report_names: list[str] = ['Alpha', 'beta', 'Summary']
        super().__init__(from_json_data_text=from_json_text,
                         from_json_filename=from_json_filename,
                         stderr_file=stderr_file)

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Return the validation steps for this ordering example."""
        _ = stderr_file
        # The first validator only checks. It does not modify the list.
        # The alert thresholds must already be in ascending order, and the
        # values must also be unique.
        threshold_validator = ListIsOrderedValidator(
            element_type=float,
            unique_values=True
        )
        # The second validator normalizes the list. It sorts the strings
        # case-insensitively, but it keeps the original spelling of each
        # string in the final stored list.
        report_name_validator = ListOrderingValidator(
            element_type=str,
            lt_comparator=casefold_lt
        )
        return [MemberValidationStep(
                    member_names=['alert_thresholds'],
                    validator=threshold_validator),
                MemberValidationStep(
                    member_names=['report_names'],
                    validator=report_name_validator)]


def e07_list_order_vs_normalize_set(  # pylint: disable=duplicate-code
        set_values: SetValues, config_file: PathOrStr) -> None:
    """Create configuration, apply overrides, and store it.

    Args:
        set_values: Values that should differ from the defaults.
        config_file: Path where to write the configuration file.
    """
    config = ExampleConfig7()
    # The code is intentionally explicit here so the reader can see the
    # ordinary pattern for changing configuration values before writing.
    for key, value in set_values.items():
        if hasattr(config, key):
            setattr(config, key, value)
        else:
            raise ValueError(f'Invalid key: {key}')
    try:
        config.write(to_json_filename=config_file)
        print(f'Configuration written to {config_file}')
    except InvalidConfiguration:
        pass  # Error already printed by the Config object.


def e07_list_order_vs_normalize_print(  # pylint: disable=duplicate-code
        config_file: PathOrStr) -> None:
    """Read a configuration file and show how the values are used.

    Args:
        config_file: Path to the configuration file to read.
    """
    try:
        config = ExampleConfig7(from_json_filename=config_file)
        print(f'Configuration read from {config_file}')
        print(f'Alert thresholds: {config.alert_thresholds}')
        print(f'Report names: {config.report_names}')
    except InvalidConfiguration:
        pass  # Error already printed by the Config object.


# -----------------------------------------------------------------------------
# The rest of this file is the command line handling code.
# This is to be able to run the example from the command line,
# but it could be done in any other way, and is not part of what this example
# is trying to teach.
# -----------------------------------------------------------------------------

INPUT_SPECS = [
    InputSpec(name='alert_thresholds', single=False, value_type=float),
    InputSpec(name='report_names', single=False, value_type=str)
]
"""Command line values that the example exposes for ``set``."""


def main(args: Optional[list[str]] = None) -> None:
    """Run the example command line interface.

    Args:
        args: Optional replacement for ``sys.argv[1:]``, mainly for tests.
    """
    cmd_line_handling(example_name='e07_list_order_vs_normalize',
                      input_specs=INPUT_SPECS,
                      set_command=e07_list_order_vs_normalize_set,
                      print_command=e07_list_order_vs_normalize_print,
                      args=args)


if __name__ == '__main__':
    main()
    sys.exit(0)
