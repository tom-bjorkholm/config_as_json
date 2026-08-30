#! /usr/local/bin/python3
"""Show how to add validators to scalar configuration values.

This example is similar to e01_simple_config.py, but it also uses the
predefined validators from the config_as_json package.
The validators are added to the configuration class by overriding the
get_validation_plan method.
"""

# Copyright (c) 2026 Tom Björkholm
# MIT License

# pylint: disable=duplicate-code
from enum import Enum, auto
from typing import Optional, TextIO
import sys
from config_as_json import Config, ParseConverter, \
    PathOrStr, ValidationPlan, MemberValidationStep, \
    IntFloatValidator, StrValidator, InvalidConfiguration, \
    InvalidConfigurationValue
from .cmd_line_handling import InputSpec, SetValues, cmd_line_handling


# We define an enum just as we did in e01_simple_config.py.
# A special aspect of enums in the configuration is that the base class Config
# will by itself validate the enum members, so we do not need to add any
# validators for them (provided that all defined enum members are valid).


class Severity(Enum):
    """Enum for severity levels."""

    DEBUG = auto()
    INFO = auto()
    WARNING = auto()
    ERROR = auto()
    CRITICAL = auto()


# Here is an example configuration class, similar to e01_simple_config.py,
# but with validators added to the scalar values.

class ExampleConfig(Config):
    """Simple configuration.

    This example still uses only scalar values: a string, 2 integers, a
    float, and an enum. For this we add validators.
    """

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
        # The configuration parameters are public instance attributes,
        # and must be created before super().__init__() is called.
        # They define both the configuration schema and the default values.
        self.issue_type: str = 'Story'
        self.number_of_iterations: int = 10
        self.estimate: int = 5
        self.severity: Severity = Severity.INFO
        self.confidence: float = 0.95
        super().__init__(from_json_data_text=from_json_text,
                         from_json_filename=from_json_filename,
                         stderr_file=stderr_file, member_name=member_name)

    # pylint: disable=duplicate-code
    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Return extra validation steps for this example configuration."""
        # The method receives stderr_file because custom validators may need
        # it, but the predefined validators used in this example do not.
        _ = stderr_file
        # Here we state what validators to use for the configuration values.
        # In this example we use the validator classes defined in the
        # config_as_json package.
        # For number_of_iterations that is an integer, we specify the minimum
        # value to 1 and the maximum value to 100.
        num_iter_validator = IntFloatValidator(min_value=1, max_value=100,
                                               allowed_values=None)
        # For estimate that is an integer, we specify the allowed values.
        estimate_validator = IntFloatValidator(min_value=None, max_value=None,
                                               allowed_values=[1, 2, 3, 5, 8,
                                                               13, 20, 40])
        # For confidence that is a float, we specify the minimum value to 0.0
        # and the maximum value to 1.0.
        confidence_validator = IntFloatValidator(min_value=0.0, max_value=1.0,
                                                 allowed_values=None)
        # For issue_type that is a string, we specify the allowed values,
        # and that we should ignore case and normalize the string to match
        # the case of one of the allowed values. This is similar to how
        # enums have only a predefined set of allowed values, but this is for
        # when you need the type to be a string. (The allowed-values list
        # might be returned from 3rd party code, for example.)
        # This example keeps strings focused on allowed values. Free-form
        # strings can use StrLenValidator for length bounds, StrCaseValidator
        # to reject unwanted case, or StrCaseChangeValidator to normalize
        # case. They use the same MemberValidationStep pattern shown below.
        issue_type_validator = StrValidator(allowed_values=['Story', 'Task',
                                                            'Bug', 'Epic'],
                                            ignore_case=True, normalize=True)
        # Now we build the ValidationPlan for the Config object.
        # A ValidationPlan is an ordered list of step objects.
        #
        # In this example every predefined validator works on named members,
        # so each step is a MemberValidationStep. The step stores both
        # the validator and the list of member names that it should validate.
        #
        # Using MemberValidationStep makes it easy to apply one validator
        # class to one or several configuration attributes.
        return [MemberValidationStep(member_names=['number_of_iterations'],
                                     validator=num_iter_validator),
                MemberValidationStep(member_names=['estimate'],
                                     validator=estimate_validator),
                MemberValidationStep(member_names=['confidence'],
                                     validator=confidence_validator),
                MemberValidationStep(member_names=['issue_type'],
                                     validator=issue_type_validator)]

    def parse_converters(self) -> dict[str, ParseConverter]:
        """Return conversions needed when reading JSON.

        JSON stores enum members as strings. When reading the file back we
        therefore tell the base class how to reconstruct the enum member.
        """
        return {'severity': self.get_converter_dict(Severity)}


# Just to demonstrate the validation above we have set and print
# functions similar to e02_simple_config_get_setattr.py.


def e03_scalar_validators_set(set_values: SetValues,
                              config_file: PathOrStr) -> None:
    """Create configuration, apply overrides, and store it.

    Args:
        set_values: Values that should differ from the defaults.
        config_file: Path where to write the configuration file.
    """
    # This is the same as in e02_simple_config_get_setattr.py.
    # We start from the default configuration, apply only the values that
    # the caller explicitly asked to change, and then let Config.write()
    # validate everything before the JSON file is written.
    config = ExampleConfig()
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


# Here is a print function similar to e01_simple_config_print.py.

def e03_scalar_validators_print(config_file: PathOrStr) -> None:
    """Read a configuration file and show how the values are used.

    Args:
        config_file: Path to the configuration file to read.
    """
    # The reading and printing looks as in e01_simple_config.py
    # Reading the configuration also triggers validation. If the stored file
    # is invalid, the Config object prints the error and we stop quietly.
    try:
        config = ExampleConfig(from_json_filename=config_file)
        print(f'Configuration read from {config_file}')
        print(f'Issue type: {config.issue_type}')
        print(f'Number of iterations: {config.number_of_iterations}')
        print(f'Estimate: {config.estimate}')
        print(f'Severity: {config.severity.name}')
        print(f'Confidence: {config.confidence}')
    except (InvalidConfiguration, InvalidConfigurationValue):
        pass  # Error already printed by the Config object.


# -----------------------------------------------------------------------------
# The rest of this file is the command line handling code.
# This is to be able to run the example from the command line,
# but it could be done in any other way, and is not part of what this example
# is trying to teach.
# -----------------------------------------------------------------------------

# pylint: disable=duplicate-code
INPUT_SPECS = [
    InputSpec(name='issue_type', single=True, value_type=str),
    InputSpec(name='number_of_iterations', single=True, value_type=int),
    InputSpec(name='estimate', single=True, value_type=int),
    InputSpec(name='severity', single=True, value_type=Severity),
    InputSpec(name='confidence', single=True, value_type=float)
]
"""Command line values that the example exposes for ``set``."""


def main(args: Optional[list[str]] = None) -> None:
    """Run the example command line interface.

    Args:
        args: Optional replacement for ``sys.argv[1:]``, mainly for tests.
    """
    cmd_line_handling(example_name='e03_scalar_validators',
                      input_specs=INPUT_SPECS,
                      set_command=e03_scalar_validators_set,
                      print_command=e03_scalar_validators_print, args=args)


if __name__ == '__main__':
    main()
    sys.exit(0)
