#! /usr/local/bin/python3
"""Show how to compose validators that work on every element of a list.

This example is for readers who already understood the earlier list
examples ``e06``, ``e07`` and ``e08``. Those all used lists of scalar
values with the built-in list validators. This example introduces
``ListForEachValidator``, which is the general composition tool for
per-element validation.

``ListForEachValidator`` does one small job: iterate the outer list and
apply a sequence of inner validators to every element, in order. It
does not care what an element is, so the same mechanism fits many
different shapes of configuration data:

- lists of lists, where each inner list is checked with other list
  validators (the concrete example below)
- lists of dicts, where each element is checked with a user-defined
  validator that looks at the dict keys
- lists of scalar values, where each element is checked or normalised
  by a user-defined validator; for instance a custom
  ``MemberValidator`` might spell-check each string or convert each
  string to upper case

Because ``ListForEachValidator`` is itself a ``MemberValidator``, one
instance can be an element validator of another, so nesting is not
limited to a single inner layer.

The concrete example below demonstrates the list-of-lists case because
it is the one that the built-in validators alone cannot handle. The
configuration member is a list of daily work-hour ranges. Each day is
represented as a ``[start_hour, end_hour]`` pair. The validation rules
are:

- The outer list may have between 1 and 7 entries (1 to 7 scheduled
  days).
- Every inner list must have exactly 2 elements.
- Every hour value must be between 0 and 23 inclusive.

The example intentionally uses 3 separate validators so that the reader
can see how ``ListForEachValidator`` fits together with
``ListSizeValidator`` and ``ListValueValidator`` instead of duplicating
their work.
"""

# Copyright (c) 2026 Tom Björkholm
# MIT License

from typing import Optional, TextIO
import sys
from config_as_json import Config, PathOrStr, ValidationPlan, \
    MemberValidationStep, ListForEachValidator, ListSizeValidator, \
    ListValueValidator, InvalidConfiguration, InvalidConfigurationValue
from .cmd_line_handling import InputSpec, SetValues, cmd_line_handling


class ExampleConfig9(Config):
    """Configuration with a list-of-lists member validated per element."""

    def __init__(self, from_json_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 stderr_file: TextIO = sys.stderr) -> None:
        """Initialize the configuration.

        Args:
            from_json_text: Optional JSON text to parse directly.
            from_json_filename: Optional path to a JSON file to read.
            stderr_file: Stream used for user-facing diagnostics.
        """
        # The new thing in this example is that one configuration
        # member is a list of lists. Each inner list is a pair of
        # hour values describing one work block during one day.
        #
        # The outer list can hold between 1 and 7 such days, and the
        # default covers a single day with one morning block and one
        # afternoon block.
        self.daily_hour_ranges: list[list[int]] = [[8, 12], [14, 18]]
        super().__init__(from_json_data_text=from_json_text,
                         from_json_filename=from_json_filename,
                         stderr_file=stderr_file)

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Return the ordered validation steps for this example."""
        _ = stderr_file
        # Step 1: outer list size. We use the purpose-built size
        # validator rather than teaching ``ListForEachValidator`` to do
        # its own size checking. That keeps every validator in the
        # plan responsible for exactly one thing.
        outer_size_validator = ListSizeValidator(min_size=1, max_size=7)
        # Step 2: validators applied to every inner list, in order.
        # ``ListForEachValidator`` does not try to understand the
        # elements itself; it only delegates the work to these two
        # existing validators.
        #
        # The first inner validator rejects inner lists of any size
        # other than 2. The second one rejects impossible hour values.
        # Because the first inner validator runs first, a badly shaped
        # inner list is reported with a clear "size" error before the
        # value validator has a chance to complain about missing
        # elements.
        inner_size_validator = ListSizeValidator(min_size=2, max_size=2)
        inner_value_validator = ListValueValidator(min_value=0, max_value=23,
                                                   allowed_values=None)
        per_day_validator = ListForEachValidator(
            element_validators=[inner_size_validator, inner_value_validator],
            element_type=list
        )
        return [MemberValidationStep(
                    member_names=['daily_hour_ranges'],
                    validator=outer_size_validator),
                MemberValidationStep(
                    member_names=['daily_hour_ranges'],
                    validator=per_day_validator)]


def e09_list_for_each_set(  # pylint: disable=duplicate-code
        set_values: SetValues, config_file: PathOrStr) -> None:
    """Create configuration, apply overrides, and store it.

    Args:
        set_values: Values that should differ from the defaults.
        config_file: Path where to write the configuration file.
    """
    config = ExampleConfig9()
    # The set pattern here is the same explicit one from the earlier
    # examples so the reader can focus on the validation plan rather
    # than on helper functions.
    #
    # The matrix member is exposed on the command line via the shared
    # command line helper using ``nested=True`` in the input spec below.
    # Each CLI token describes one inner list using comma-separated
    # values, so a full override looks like
    # ``--daily-hour-ranges 6,10 13,17 20,22``.
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


def e09_list_for_each_print(  # pylint: disable=duplicate-code
        config_file: PathOrStr) -> None:
    """Read a configuration file and show how the values are used.

    Args:
        config_file: Path to the configuration file to read.
    """
    try:
        config = ExampleConfig9(from_json_filename=config_file)
        print(f'Configuration read from {config_file}')
        print(f'Daily hour ranges: {config.daily_hour_ranges}')
        for day_index, hour_range in enumerate(config.daily_hour_ranges):
            start_hour, end_hour = hour_range
            print(f'Day {day_index}: from {start_hour} to {end_hour}')
    except (InvalidConfiguration, InvalidConfigurationValue):
        pass  # Error already printed by the Config object.


# -----------------------------------------------------------------------------
# The rest of this file is the command line handling code.
# This is to be able to run the example from the command line,
# but it could be done in any other way, and is not part of what this example
# is trying to teach.
# -----------------------------------------------------------------------------

INPUT_SPECS = [
    InputSpec(name='daily_hour_ranges', single=False, value_type=int,
              nested=True)
]
"""Command line values that the example exposes for ``set``.

The ``nested=True`` flag tells the shared command line helper that each
CLI token is itself a comma-separated list of ``int`` values. The
resulting Python value is therefore a ``list[list[int]]`` matrix, just
like the ``daily_hour_ranges`` configuration member.
"""


def main(args: Optional[list[str]] = None) -> None:
    """Run the example command line interface.

    Args:
        args: Optional replacement for ``sys.argv[1:]``, mainly for tests.
    """
    cmd_line_handling(example_name='e09_list_for_each',
                      input_specs=INPUT_SPECS,
                      set_command=e09_list_for_each_set,
                      print_command=e09_list_for_each_print,
                      args=args)


if __name__ == '__main__':
    main()
    sys.exit(0)
