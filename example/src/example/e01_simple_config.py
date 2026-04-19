#! /usr/local/bin/python3
"""Show a first small configuration class backed by JSON.

This example keeps the configuration deliberately small so that the main
ideas are easy to see:

- defaults are ordinary instance attributes
- the configuration can be written to a JSON file
- the configuration can be read back later
- the application can then use the values as normal Python attributes
"""

# Copyright (c) 2026 Tom Björkholm
# MIT License

from enum import Enum, auto
from typing import Optional, TextIO
import sys
from config_as_json.config import Config, ParseConverter
from config_as_json.commontypes import PathOrStr
from config_as_json.validator import ValidationList
from .cmd_line_handling import InputSpec, SetValues, cmd_line_handling


# We define an enum just to show how configuration classes can use enums.
# When using enums, the base class Config will store the enum member as a
# string in the JSON file, so that the configuration file is easy to read
# and edit by a human. The case class Config will also convert the string
# back to the enum member when reading the configuration file back, and
# will flag an error if the string is not a valid enum member.

class YesNoAsk(Enum):
    """Enum for yes/no/ask.

    This is just a simple example enum to show how configuration
    classes can use enums.
    """

    YES = auto()
    NO = auto()
    ASK = auto()


# Here is the first example configuration class.
# It is a simple configuration class that uses only scalar values:
# a string, an integer, a float, a boolean and an enum.
# Our configuration class is derived from the base class Config
# and may have any name and any number of instance attributes.
# The instance attributes are the configuration values.
# Later examples will teach more complex patterns,
# but what is shown here is actually enough for many applications.

class SimpleConfig(Config):
    """Simple configuration.

    This first example uses only scalar values: a string, an integer, a
    float, a boolean and an enum. That is enough to show the basic pattern
    without mixing in validation or nested data structures.
    """

    def __init__(self, from_json_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 stderr_file: TextIO = sys.stderr) -> None:
        """Initialize the configuration.

        Args:
            from_json_text: Optional JSON text to parse directly.
            from_json_filename: Optional path to a JSON file to read.
            stderr_file: Stream used for user-facing diagnostics.
        """
        # The configuration parameters are public instance attributes,
        # and must be created before super().__init__() is called.
        # They define both the configuration schema and the default values.
        self.name: str = 'simple or complex'
        self.answer: int = 42
        self.approximation: float = 3.14159
        self.easy: bool = True
        self.confirmation: YesNoAsk = YesNoAsk.ASK
        super().__init__(from_json_data_text=from_json_text,
                         from_json_filename=from_json_filename,
                         stderr_file=stderr_file)

    def get_validation_list(self, stderr_file: TextIO) -> ValidationList:
        """Return extra validators for this example configuration."""
        # In this example we do not need any additional validation.
        # Thus we return an empty list.
        # Later examples will teach how to add validation.
        _ = stderr_file
        return []

    def parse_converters(self) -> dict[str, ParseConverter]:
        """Return conversions needed when reading JSON.

        JSON stores enum members as strings. When reading the file back we
        therefore tell the base class how to reconstruct the enum member.
        """
        return {'confirmation': self.get_converter_dict(YesNoAsk)}


# Here is a function that shows how to set the configuration
# values to something else than the defaults, and how to store
# the configuration in a JSON file.
# In this example, this function is called by the command line helper
# when the user wants to set the configuration values.

def e01_simple_config_set(set_values: SetValues,
                          config_file: PathOrStr) -> None:
    """Create configuration, apply overrides, and store it.

    Args:
        set_values: Values that should differ from the defaults.
        config_file: Path where to write the configuration file.
    """
    # When calling the constructor of the configuration object,
    # without any arguments, the configuration object is created with the
    # default values.
    config = SimpleConfig()
    # We apply the overrides to the configuration object.
    # This is done by setting the normal instance attributes of
    # the configuration object.
    # This can be done by ordinary assignments to the instance attributes,
    # or by using the setattr function.
    for key, value in set_values.items():
        # Here we use simple assignments to the instance attributes.
        if key == 'name':
            assert isinstance(value, str)  # just to keep mypy happy
            config.name = value
        elif key == 'answer':
            assert isinstance(value, int)  # just to keep mypy happy
            config.answer = value
        elif key == 'approximation':
            assert isinstance(value, float)  # just to keep mypy happy
            config.approximation = value
        elif key == 'easy':
            assert isinstance(value, bool)  # just to keep mypy happy
            config.easy = value
        elif key == 'confirmation':
            assert isinstance(value, YesNoAsk)  # just to keep mypy happy
            config.confirmation = value
        else:
            raise ValueError(f'Invalid key: {key}')
    # We store the configuration in a JSON file, by simply calling the write
    # method of the configuration object.
    config.write(to_json_filename=config_file)
    print(f'Configuration written to {config_file}')


# Here is a function that shows how to read the configuration
# values from a JSON file and use them.
# In this example, this function is called by the command line helper
# when the user wants to print the configuration values.

def e01_simple_config_print(config_file: PathOrStr) -> None:
    """Read a configuration file and show how the values are used.

    Args:
        config_file: Path to the configuration file to read.
    """
    # We read the configuration from a JSON file, by simply providing
    # the from_json_filename argument to the configuration constructor.
    config = SimpleConfig(from_json_filename=config_file)
    print(f'Configuration read from {config_file}')
    print(f'Name: {config.name}')
    print(f'Answer: {config.answer}')
    print(f'Approximation: {config.approximation}')
    print(f'Easy: {config.easy}')
    print(f'Confirmation: {config.confirmation.name}')


# -----------------------------------------------------------------------------
# The rest of this file is the command line handling code.
# This is to be able to run the example from the command line,
# but it could be done in any other way, and is not part of the
# what this example is trying to teach.
# -----------------------------------------------------------------------------

INPUT_SPECS = [
    InputSpec(name='name', single=True, value_type=str),
    InputSpec(name='answer', single=True, value_type=int),
    InputSpec(name='approximation', single=True, value_type=float),
    InputSpec(name='easy', single=True, value_type=bool),
    InputSpec(name='confirmation', single=True, value_type=YesNoAsk)
]
"""Command line values that the example exposes for ``set``."""


def main(args: Optional[list[str]] = None) -> None:
    """Run the example command line interface.

    Args:
        args: Optional replacement for ``sys.argv[1:]``, mainly for tests.
    """
    cmd_line_handling(example_name='e01_simple_config',
                      input_specs=INPUT_SPECS,
                      set_command=e01_simple_config_set,
                      print_command=e01_simple_config_print,
                      args=args)


if __name__ == '__main__':
    main()
    sys.exit(0)
