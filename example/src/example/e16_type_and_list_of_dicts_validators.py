#! /usr/local/bin/python3
"""Teach simple type checks and list-of-dicts key validation.

This example introduces 3 small predefined validators:

- ``ValueTypeValidator`` checks that one member value has a runtime type
- ``ListValueTypeValidator`` checks that a member is a list whose elements
  all have one runtime type
- ``ListOfDictsKeysValidator`` checks that every dict in a list has the
  expected mandatory and optional keys

These validators are intentionally narrow. They are useful when the shape of
configuration data matters, but no range, ordering, or allowed-values rule is
needed.
"""

# Copyright (c) 2026 Tom Björkholm
# MIT License

from typing import Optional, TextIO
import sys
from config_as_json import Config, InvalidConfiguration, \
    InvalidConfigurationValue, ListOfDictsKeysValidator, \
    ListValueTypeValidator, MemberValidationStep, PathOrStr, \
    ValidationPlan, ValueTypeValidator
from .cmd_line_handling import InputSpec, SetValues, cmd_line_handling

# pylint: disable=duplicate-code


class ExampleConfig16(Config):
    """Configuration using the simplest predefined shape validators."""

    def __init__(self, from_json_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 stderr_file: TextIO = sys.stderr) -> None:
        """Initialize the configuration.

        Args:
            from_json_text: Optional JSON text to parse directly.
            from_json_filename: Optional path to a JSON file to read.
            stderr_file: Stream used for user-facing diagnostics.
        """
        self.worker_count: int = 2
        self.alert_recipients: list[str] = ['ops@example.com']
        self.pipeline_steps: list[dict[str, object]] = [
            {'name': 'extract', 'enabled': True},
            {'name': 'load', 'enabled': True, 'owner': 'data'}
        ]
        super().__init__(from_json_data_text=from_json_text,
                         from_json_filename=from_json_filename,
                         stderr_file=stderr_file)

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Return the ordered validation steps for this example."""
        _ = stderr_file
        return [
            MemberValidationStep(
                member_names=['worker_count'],
                validator=ValueTypeValidator(int)),
            MemberValidationStep(
                member_names=['alert_recipients'],
                validator=ListValueTypeValidator(str)),
            MemberValidationStep(
                member_names=['pipeline_steps'],
                validator=ListOfDictsKeysValidator(
                    mandatory_keys=['name', 'enabled'],
                    allowed_keys=['owner']))]


def e16_validators_set(  # pylint: disable=duplicate-code
        set_values: SetValues, config_file: PathOrStr) -> None:
    """Create configuration, apply overrides, and store it.

    Args:
        set_values: Values that should differ from the defaults.
        config_file: Path where to write the configuration file.
    """
    config = ExampleConfig16()
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


def e16_validators_print(config_file: PathOrStr) -> None:
    """Read a configuration file and show how the values are used.

    Args:
        config_file: Path to the configuration file to read.
    """
    try:
        config = ExampleConfig16(from_json_filename=config_file)
        print(f'Configuration read from {config_file}')
        print(f'Worker count: {config.worker_count}')
        print(f'Alert recipients: {config.alert_recipients}')
        print(f'Pipeline steps: {config.pipeline_steps}')
    except (InvalidConfiguration, InvalidConfigurationValue):
        pass  # Error already printed by the Config object.


INPUT_SPECS = [
    InputSpec(name='worker_count', single=True, value_type=int),
    InputSpec(name='alert_recipients', single=False, value_type=str),
    InputSpec(name='pipeline_steps', single=True, value_type=str,
              json_value=True)
]
"""Command line values that the example exposes for ``set``."""


def main(args: Optional[list[str]] = None) -> None:
    """Run the example command line interface.

    Args:
        args: Optional replacement for ``sys.argv[1:]``, mainly for tests.
    """
    cmd_line_handling(
        example_name='e16_type_and_list_of_dicts_validators',
        input_specs=INPUT_SPECS,
        set_command=e16_validators_set,
        print_command=e16_validators_print,
        args=args)


if __name__ == '__main__':
    main()
    sys.exit(0)
