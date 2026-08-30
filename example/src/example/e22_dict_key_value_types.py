#! /usr/local/bin/python3
"""Teach compact type validation for uniform dictionaries.

``DictKeyValueTypesValidator`` is for dictionaries where every key has the
same runtime type and every value has the same runtime type. That is a very
common shape for application configuration: service names mapped to ports,
feature names mapped to booleans, or user-defined names mapped to lists.

Earlier dict examples use ``DictKeysValidator`` and ``DictForEachValidator``
because each known key has its own policy. This example shows the simpler
case where the keys are open-ended but the type rule is uniform.

The example has 2 members:

- ``service_ports`` is a plain ``dict[str, int]``. One validator call checks
  the outer dict, all keys, and all values.
- ``sample_weights`` is a ``dict[str, list[float]]``. The dict validator
  checks that each value is a list, and a nested ``ListValueTypeValidator``
  checks that each item inside each list is a float.

The optional ``value_validator`` is used only for that second kind of case:
checking inside a composite value. If each key has different business rules,
``DictForEachValidator`` is clearer than hiding those rules inside
``value_validator``.
"""

# Copyright (c) 2026 Tom Björkholm
# MIT License

from typing import Optional, TextIO
import sys
from config_as_json import Config, DictKeyValueTypesValidator, \
    InvalidConfiguration, InvalidConfigurationValue, ListValueTypeValidator, \
    MemberValidationStep, PathOrStr, ValidationPlan
from .cmd_line_handling import InputSpec, SetValues, cmd_line_handling


class ExampleConfig22(Config):
    """Configuration that validates uniform dict key and value types."""

    def __init__(self, from_json_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 stderr_file: TextIO = sys.stderr,
                 member_name: Optional[str] = None) -> None:
        """Initialize the configuration.

        Args:
            from_json_text: Optional JSON text to parse directly.
            from_json_filename: Optional path to a JSON file to read.
            stderr_file: Stream used for user-facing diagnostics.
            member_name: Path for reaching this object from the top level
                configuration. ``None`` means that this object is the whole
                configuration and not a member of anything.
        """
        # These dictionaries are open-ended: an application can add more
        # service names or more weight profiles without changing this class.
        # The default keys therefore cannot be used as a closed schema by the
        # ``Config`` base class. We opt out and let the validators below own
        # the whole key/value policy.
        self._unchecked_dicts: list[str] = ['service_ports', 'sample_weights']
        # The annotations show the application-level intent. The validators
        # below are what enforce that intent when JSON or command-line input
        # is read.
        self.service_ports: dict[str, int] = {'http': 80, 'https': 443}
        self.sample_weights: dict[str, list[float]] = {
            'fast': [0.2, 0.8],
            'balanced': [0.5, 0.5]}
        super().__init__(from_json_data_text=from_json_text,
                         from_json_filename=from_json_filename,
                         stderr_file=stderr_file, member_name=member_name)

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Return validators for the two uniform dict members."""
        _ = stderr_file
        # This is the compact form for a simple ``dict[str, int]``. No
        # ``DictRule`` is needed because every key has the same value type.
        ports_validator = DictKeyValueTypesValidator(key_type=str,
                                                     value_type=int)
        # This member is still uniform at the dict level: every key is a
        # string and every value is a list. The nested validator is only about
        # the inside of each list, so the call site remains easy to read as
        # "a dict from strings to lists of floats".
        weights_validator = DictKeyValueTypesValidator(
            key_type=str, value_type=list,
            value_validator=ListValueTypeValidator(float))
        return [MemberValidationStep(member_names=['service_ports'],
                                     validator=ports_validator),
                MemberValidationStep(member_names=['sample_weights'],
                                     validator=weights_validator)]


# pylint: disable=duplicate-code
def e22_dict_key_value_types_set(set_values: SetValues,
                                 config_file: PathOrStr) -> None:
    """Create configuration, apply overrides, and store it.

    Args:
        set_values: Values that should differ from the defaults.
        config_file: Path where to write the configuration file.
    """
    config = ExampleConfig22()
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
def e22_dict_key_value_types_print(config_file: PathOrStr) -> None:
    """Read a configuration file and show how the dict values are used.

    Args:
        config_file: Path to the configuration file to read.
    """
    try:
        config = ExampleConfig22(from_json_filename=config_file)
        print(f'Configuration read from {config_file}')
        print(f'Service ports: {config.service_ports}')
        print(f'Sample weights: {config.sample_weights}')
        print(f'HTTP port: {config.service_ports.get("http")}')
        print(f'Fast weights: {config.sample_weights.get("fast")}')
    except (InvalidConfiguration, InvalidConfigurationValue):
        pass  # Error already printed by the Config object.


INPUT_SPECS = [
    # ``dict_kv=True`` is enough for the flat ``dict[str, int]`` member.
    # Each token is written as ``name=value`` and converted to one dict item.
    InputSpec(name='service_ports', single=False, value_type=int,
              dict_kv=True),
    # ``sample_weights`` has nested lists, so JSON is the honest command-line
    # shape. The example still validates the parsed value with the same
    # ``DictKeyValueTypesValidator`` used for file input.
    InputSpec(name='sample_weights', single=True, value_type=str,
              json_value=True)]
"""Command line values that the example exposes for ``set``.

``service_ports`` accepts key/value tokens:

``--service-ports http=8080 metrics=9090``

``sample_weights`` accepts one JSON value:

``--sample-weights '{"fast": [0.1, 0.9], "safe": [0.5, 0.5]}'``
"""


def main(args: Optional[list[str]] = None) -> None:
    """Run the example command line interface.

    Args:
        args: Optional replacement for ``sys.argv[1:]``, mainly for tests.
    """
    cmd_line_handling(example_name='e22_dict_key_value_types',
                      input_specs=INPUT_SPECS,
                      set_command=e22_dict_key_value_types_set,
                      print_command=e22_dict_key_value_types_print, args=args)


if __name__ == '__main__':
    main()
    sys.exit(0)
