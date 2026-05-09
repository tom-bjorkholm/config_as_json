#! /usr/local/bin/python3
"""Show how several list validators can cooperate on one member.

This example uses 3 validators on the same list member to teach that the
order of the validation steps matters:

1. ``ListValueValidator`` rejects impossible hour values
2. ``ListOrderingValidator`` sorts the list and removes duplicates
3. ``ListSizeValidator`` checks the size of the normalized list

The important lesson is that each validator sees the result returned by
the previous validator. That makes the ``ValidationPlan`` order part of
the design, not just a coding detail.
"""

# Copyright (c) 2026 Tom Björkholm
# MIT License

from typing import Optional, TextIO
import sys
from config_as_json import Config, PathOrStr, ValidationPlan, \
    MemberValidationStep, ListValueValidator, ListOrderingValidator, \
    ListSizeValidator, InvalidConfiguration, InvalidConfigurationValue
from .cmd_line_handling import InputSpec, SetValues, cmd_line_handling


class ExampleConfig8(Config):
    """Configuration that combines several validators on one list member."""

    def __init__(self, from_json_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 stderr_file: TextIO = sys.stderr) -> None:
        """Initialize the configuration.

        Args:
            from_json_text: Optional JSON text to parse directly.
            from_json_filename: Optional path to a JSON file to read.
            stderr_file: Stream used for user-facing diagnostics.
        """
        self.run_hours_utc: list[int] = [3, 12, 18]
        super().__init__(from_json_data_text=from_json_text,
                         from_json_filename=from_json_filename,
                         stderr_file=stderr_file)

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Return the ordered validation steps for this example."""
        _ = stderr_file
        # Step 1: reject impossible values before we try to normalize.
        # If one hour is outside 0..23, we want a clear error about that
        # specific bad element.
        hour_value_validator = ListValueValidator(min_value=0, max_value=23,
                                                  allowed_values=None)
        # Step 2: sort the list and keep only the first occurrence of each
        # hour. After this step later validators see the normalized list,
        # not the original user input.
        hour_ordering_validator = ListOrderingValidator(element_type=int,
                                                        keep_only_unique=True)
        # Step 3: check the size after normalization.
        # This means that ``[12, 12]`` fails here because step 2 turns it
        # into ``[12]`` before the size check runs.
        hour_count_validator = ListSizeValidator(min_size=2, max_size=6)
        return [MemberValidationStep(member_names=['run_hours_utc'],
                                     validator=hour_value_validator),
                MemberValidationStep(member_names=['run_hours_utc'],
                                     validator=hour_ordering_validator),
                MemberValidationStep(member_names=['run_hours_utc'],
                                     validator=hour_count_validator)]


# pylint: disable=duplicate-code
def e08_combined_list_validators_set(set_values: SetValues,
                                     config_file: PathOrStr) -> None:
    """Create configuration, apply overrides, and store it.

    Args:
        set_values: Values that should differ from the defaults.
        config_file: Path where to write the configuration file.
    """
    config = ExampleConfig8()
    # This example keeps the same explicit set pattern as the earlier
    # examples so the reader can focus on the validation plan rather than
    # on helper functions.
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


# pylint: disable=duplicate-code
def e08_combined_validators_print(config_file: PathOrStr) -> None:
    """Read a configuration file and show how the values are used.

    Args:
        config_file: Path to the configuration file to read.
    """
    try:
        config = ExampleConfig8(from_json_filename=config_file)
        print(f'Configuration read from {config_file}')
        print(f'Run hours in UTC: {config.run_hours_utc}')
        print('Would run the job at UTC hours: ' +
              ', '.join(str(hour) for hour in config.run_hours_utc))
    except (InvalidConfiguration, InvalidConfigurationValue):
        pass  # Error already printed by the Config object.


# -----------------------------------------------------------------------------
# The rest of this file is the command line handling code.
# This is to be able to run the example from the command line,
# but it could be done in any other way, and is not part of what this example
# is trying to teach.
# -----------------------------------------------------------------------------

INPUT_SPECS = [
    InputSpec(name='run_hours_utc', single=False, value_type=int)
]
"""Command line values that the example exposes for ``set``."""


def main(args: Optional[list[str]] = None) -> None:
    """Run the example command line interface.

    Args:
        args: Optional replacement for ``sys.argv[1:]``, mainly for tests.
    """
    cmd_line_handling(example_name='e08_combined_list_validators',
                      input_specs=INPUT_SPECS,
                      set_command=e08_combined_list_validators_set,
                      print_command=e08_combined_validators_print, args=args)


if __name__ == '__main__':
    main()
    sys.exit(0)
