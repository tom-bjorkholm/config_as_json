#! /usr/local/bin/python3
"""Show how to derive a validator class for dependent values.

This example combines two common needs:

- deriving your own class from ``Validator``
- validating 2 configuration values that depend on each other

The example pretends that an output library can write either CSV or
Excel files. The allowed ``output_subtype`` values depend on the chosen
``output_format``. This is a typical case where a small custom validator
is clearer than trying to encode all rules as separate scalar validators.
"""

# Copyright (c) 2026 Tom Björkholm
# MIT License

# pylint: disable=duplicate-code
from typing import Optional, TextIO
import sys
from config_as_json import Config, PathOrStr, ValidationList, Validation, \
    StrValidator, Validator, InvalidConfiguration, InvalidConfigurationValue
from .cmd_line_handling import InputSpec, SetValues, cmd_line_handling


OUTPUT_SUBTYPES_BY_FORMAT = {
    'CSV': ['excelDialect', 'unixDialect'],
    'Excel': ['PylightXL', 'OpenPyxl', 'XlsxWriter']
}
"""Allowed output subtypes for each output format."""


def allowed_output_formats() -> list[str]:
    """Return the allowed output formats."""
    return list(OUTPUT_SUBTYPES_BY_FORMAT.keys())


def allowed_output_subtypes() -> list[str]:
    """Return the allowed output subtypes from all formats."""
    subtypes: list[str] = []
    for output_format in allowed_output_formats():
        subtypes.extend(OUTPUT_SUBTYPES_BY_FORMAT[output_format])
    return subtypes


class OutputLibraryStub:  # pylint: disable=too-few-public-methods
    """Small stub of a library that writes the configured output."""

    def __init__(self, output_format: str, output_subtype: str) -> None:
        """Store the selected output format and subtype."""
        self.output_format: str = output_format
        self.output_subtype: str = output_subtype

    def description(self) -> str:
        """Return a short description of the configured writer."""
        if self.output_format == 'CSV':
            return 'Would write CSV output with the ' + \
                f'{self.output_subtype} dialect.'
        return 'Would write Excel output with the ' + \
            f'{self.output_subtype} backend.'


class OutputFormatSubtypeValidator(Validator):
    """Validate that ``output_format`` and ``output_subtype`` match."""

    def validate(self, config: Config,
                 stderr_file: TextIO = sys.stderr) -> None:
        """Validate the dependency between the 2 configuration values."""
        # This validator uses validate() for the whole Config object, rather
        # than validate_member() for one member. That is the important
        # teaching point of this example: the rule depends on the combination
        # of 2 configuration values, so we validate the complete object.
        #
        # The validator base class only knows that it received some Config
        # object, so we fetch the attributes by name from that object.
        # An alternative design could have been to first do
        # "assert isinstance(config, ExampleConfig5)" and then use the
        # attributes directly.
        output_format = getattr(config, 'output_format', None)
        output_subtype = getattr(config, 'output_subtype', None)
        if not isinstance(output_format, str):
            msg = 'Invalid configuration: output_format must be a string.'
            print(msg, file=stderr_file)
            raise InvalidConfiguration(msg)
        if not isinstance(output_subtype, str):
            msg = 'Invalid configuration: output_subtype must be a string.'
            print(msg, file=stderr_file)
            raise InvalidConfiguration(msg)
        # The earlier StrValidator objects in get_validation_list() have
        # already normalized the 2 strings to the exact spellings we want.
        # That means we can now do a simple lookup and membership test.
        allowed_subtypes = OUTPUT_SUBTYPES_BY_FORMAT.get(output_format)
        if allowed_subtypes is None:
            msg = 'Invalid configuration: '
            msg += f'Unknown output_format {output_format}.'
            print(msg, file=stderr_file)
            raise InvalidConfiguration(msg)
        if output_subtype in allowed_subtypes:
            return
        msg = 'Invalid configuration: '
        msg += f'output_subtype {output_subtype} is not valid for '
        msg += f'output_format {output_format}. '
        msg += 'Allowed values: ' + ', '.join(allowed_subtypes)
        print(msg, file=stderr_file)
        raise InvalidConfiguration(msg)

    def validate_member(self, config: Config, member_name: str,
                        member_value: object,
                        stderr_file: TextIO = sys.stderr) -> Optional[object]:
        """Reject use of this validator as a member validator."""
        # We deliberately reject validate_member() here to make the example
        # clearer for the reader. A member validator is called for one member
        # at a time, but this rule is about the relationship between 2
        # members. In this teaching example we therefore want the reader to
        # use Validation(member_names=None, ...) instead.
        _ = config
        _ = member_name
        _ = member_value
        msg = 'Do not use OutputFormatSubtypeValidator as a member '
        msg += 'validator. Use Validation(member_names=None, '
        msg += 'validator=...) instead.'
        print(msg, file=stderr_file)
        # We raise a RuntimeError here instead of InvalidConfiguration to
        # indicate that this is a programming error, not an error in the
        # configuration file.
        raise RuntimeError(msg)


class ExampleConfig5(Config):
    """Configuration for the output-library teaching example."""

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
        self.output_format: str = 'Excel'
        self.output_subtype: str = 'OpenPyxl'
        super().__init__(from_json_data_text=from_json_text,
                         from_json_filename=from_json_filename,
                         stderr_file=stderr_file)

    def get_validation_list(self, stderr_file: TextIO) -> ValidationList:
        """Return the validators for this example configuration."""
        _ = stderr_file
        format_validator = StrValidator(allowed_values=allowed_output_formats,
                                        ignore_case=True, normalize=True)
        subtype_validator = StrValidator(
            allowed_values=allowed_output_subtypes,
            ignore_case=True,
            normalize=True
        )
        # The order matters. First we normalize the 2 strings to the exact
        # spellings we want to keep in the config file. Then our custom
        # validator checks that the normalized values form an allowed pair.
        return [Validation(member_names=['output_format'],
                           validator=format_validator),
                Validation(member_names=['output_subtype'],
                           validator=subtype_validator),
                Validation(member_names=None,
                           validator=OutputFormatSubtypeValidator())]


def e05_custom_validator_set(set_values: SetValues,
                             config_file: PathOrStr) -> None:
    """Create configuration, apply overrides, and store it.

    Args:
        set_values: Values that should differ from the defaults.
        config_file: Path where to write the configuration file.
    """
    config = ExampleConfig5()
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


def e05_custom_validator_print(config_file: PathOrStr) -> None:
    """Read a configuration file and show how the values are used.

    Args:
        config_file: Path to the configuration file to read.
    """
    try:
        config = ExampleConfig5(from_json_filename=config_file)
        output_library = OutputLibraryStub(config.output_format,
                                           config.output_subtype)
        print(f'Configuration read from {config_file}')
        print(f'Output format: {config.output_format}')
        print(f'Output subtype: {config.output_subtype}')
        print(output_library.description())
    except (InvalidConfiguration, InvalidConfigurationValue):
        pass  # Error already printed by the Config object.


# -----------------------------------------------------------------------------
# The rest of this file is the command line handling code.
# This is to be able to run the example from the command line,
# but it could be done in any other way, and is not part of what this example
# is trying to teach.
# -----------------------------------------------------------------------------

INPUT_SPECS = [
    InputSpec(name='output_format', single=True, value_type=str),
    InputSpec(name='output_subtype', single=True, value_type=str)
]
"""Command line values that the example exposes for ``set``."""


def main(args: Optional[list[str]] = None) -> None:
    """Run the example command line interface.

    Args:
        args: Optional replacement for ``sys.argv[1:]``, mainly for tests.
    """
    cmd_line_handling(example_name='e05_custom_validator',
                      input_specs=INPUT_SPECS,
                      set_command=e05_custom_validator_set,
                      print_command=e05_custom_validator_print,
                      args=args)


if __name__ == '__main__':
    main()
    sys.exit(0)
