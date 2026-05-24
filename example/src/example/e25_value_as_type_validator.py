#! /usr/local/bin/python3
"""Teach how ValueAsTypeValidator normalizes configuration values.

``ValueAsTypeValidator`` is useful when the configuration file may contain
friendly or legacy representations, but application code wants one precise
Python type after validation has completed.

This example has two stored members:

- ``retry_count`` is used by the application as an ``int``. The validator
  also accepts text such as ``"5"`` and normalizes it with ``int("5")``.
- ``story_points`` is also used as an ``int``. Newer configuration files
  store the integer directly, but old files may still contain T-shirt
  sizes such as ``"M"`` or ``"XL"``.
"""

# Copyright (c) 2026 Tom Björkholm
# MIT License

import sys
from typing import Optional, TextIO
from config_as_json import Config, InvalidConfiguration, \
    InvalidConfigurationValue, MemberValidationStep, MemberValidatorSequence, \
    PathOrStr, ValidationPlan, ValueAsTypeValidator, ValueTypeValidator
from .cmd_line_handling import InputSpec, SetValues, cmd_line_handling


STORY_SIZE_POINTS = {
    'XS': 1,
    'S': 2,
    'M': 3,
    'L': 5,
    'XL': 8
}
"""Legacy T-shirt sizes mapped to integer story points."""


def story_points_from_text(value: object) -> int:
    """Convert text into integer story points.

    The command line always gives this example strings, and old
    configuration files may also contain strings. Numeric text is accepted
    because users may type ``--story-points 5``. T-shirt sizes are accepted
    for backward compatibility with older configuration files.

    Args:
        value: Configuration value to convert.

    Returns:
        Integer story points.

    Raises:
        AssertionError: If ``value`` is not a string.
        ValueError: If the string is not numeric and is not a known size.
    """
    assert isinstance(value, str)
    text = value.strip().upper()
    if text in STORY_SIZE_POINTS:
        return STORY_SIZE_POINTS[text]
    try:
        return int(text)
    except ValueError as exc:
        raise ValueError(f'Unknown story point size: {value}') from exc


class ExampleConfig25(Config):
    """Configuration using type-normalizing validators."""

    def __init__(self, from_json_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 stderr_file: TextIO = sys.stderr) -> None:
        """Initialize the configuration.

        Args:
            from_json_text: Optional JSON text to parse directly.
            from_json_filename: Optional path to a JSON file to read.
            stderr_file: Stream used for user-facing diagnostics.
        """
        # The application wants this value as an int. A JSON file or command
        # line override may still provide it as text, and the validator below
        # will normalize that text before application code uses it.
        self.retry_count: int = 3
        # The application wants story points as an int. Old configuration
        # files stored T-shirt sizes such as "M". This is not an enum case:
        # normal Enum/IntEnum reading has better support in Config through
        # parse_converters(), as shown in e38_write_side_hook.
        self.story_points: int = 3
        super().__init__(from_json_data_text=from_json_text,
                         from_json_filename=from_json_filename,
                         stderr_file=stderr_file)

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Return the ordered validation steps for this example."""
        _ = stderr_file
        # Direct conversion means "call the target type as a constructor".
        # Here a string like "5" is accepted because int("5") returns 5.
        as_int = ValueAsTypeValidator(int, direct_types=str)
        # Python's bool is a subclass of int. The normalizing validator keeps
        # an existing bool unchanged because it already satisfies
        # isinstance(value, int). The second validator therefore documents
        # the policy decision: retry_count is an int, but not a bool.
        int_not_bool = ValueTypeValidator(int, not_allowed_type=bool)
        retry_validator = MemberValidatorSequence([as_int, int_not_bool])
        # Callable conversion is for cases where the target constructor is
        # not enough. Here a string may be normal text like "5" or a legacy
        # T-shirt size such as "M", so a small function owns the rule.
        story_as_int = ValueAsTypeValidator(
            int, convertable_types={str: story_points_from_text})
        story_validator = MemberValidatorSequence([story_as_int,
                                                   int_not_bool])
        return [
            MemberValidationStep(member_names=['retry_count'],
                                 validator=retry_validator),
            MemberValidationStep(member_names=['story_points'],
                                 validator=story_validator)
        ]


# pylint: disable=duplicate-code
def e25_value_as_type_set(set_values: SetValues,
                          config_file: PathOrStr) -> None:
    """Create configuration, apply overrides, and store it.

    Args:
        set_values: Values that should differ from the defaults.
        config_file: Path where to write the configuration file.
    """
    config = ExampleConfig25()
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
def e25_value_as_type_print(config_file: PathOrStr) -> None:
    """Read a configuration file and show how the values are used.

    Args:
        config_file: Path to the configuration file to read.
    """
    try:
        config = ExampleConfig25(from_json_filename=config_file)
        print(f'Configuration read from {config_file}')
        print(f'Retry count: {config.retry_count}')
        print(f'Story points: {config.story_points}')
    except (InvalidConfiguration, InvalidConfigurationValue):
        pass  # Error already printed by the Config object.


INPUT_SPECS = [
    InputSpec(name='retry_count', single=True, value_type=str),
    InputSpec(name='story_points', single=True, value_type=str)
]
"""Command line values that the example exposes for ``set``.

Both values are accepted as text on purpose. The point of the example is that
validation normalizes the text before the file is written and again after the
file is read.
"""


def main(args: Optional[list[str]] = None) -> None:
    """Run the example command line interface.

    Args:
        args: Optional replacement for ``sys.argv[1:]``, mainly for tests.
    """
    cmd_line_handling(example_name='e25_value_as_type_validator',
                      input_specs=INPUT_SPECS,
                      set_command=e25_value_as_type_set,
                      print_command=e25_value_as_type_print, args=args)


if __name__ == '__main__':
    main()
    sys.exit(0)
