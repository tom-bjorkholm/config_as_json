#! /usr/local/bin/python3
"""Show how to call existing methods from a validation plan.

This example is for configuration classes that already inherit validation
or normalization methods from another class. Instead of wrapping those
methods in small custom validator classes, the validation plan can use
``CallingMemberValidator`` and ``CallingWholeConfigValidator``.

The example also introduces ``MemberValidatorSequence``. It lets one
member run several ``MemberValidator`` objects immediately after each
other, so each validator sees the value returned by the previous one.
"""

# Copyright (c) 2026 Tom Björkholm
# MIT License

# pylint: disable=duplicate-code
from typing import Optional, TextIO
import sys
from config_as_json import Config, PathOrStr, ValidationPlan, \
    MemberValidationStep, WholeConfigValidationStep, ValueTypeValidator, \
    StrValidator, CallingMemberValidator, CallingWholeConfigValidator, \
    MemberValidatorSequence, InvalidConfiguration, InvalidConfigurationValue
from .cmd_line_handling import InputSpec, SetValues, cmd_line_handling


ALLOWED_REGIONS = ['eu-west', 'us-east']
"""Region names accepted by the third-party job library."""


class ThirdPartyJobOptions:  # pylint: disable=too-few-public-methods
    """Pretend third-party options class with useful check methods."""

    def __init__(self) -> None:
        """Initialize third-party defaults."""
        self.region: str = 'eu-west'
        self.retry_count: int = 3
        self.endpoint: str = 'https://eu-west.example.invalid/jobs'

    def normalize_region_text(self, value: str) -> str:
        """Normalize user-friendly region text."""
        return value.strip().lower().replace('_', '-')

    def check_retry_count(self, value: int, minimum: int,
                          maximum: int) -> Optional[bool]:
        """Return whether ``value`` is inside the accepted retry range."""
        return minimum <= value <= maximum

    def check_endpoint_matches_region(self) -> Optional[bool]:
        """Return whether the endpoint belongs to the selected region."""
        return f'//{self.region}.' in self.endpoint


class ExampleConfig19(ThirdPartyJobOptions, Config):
    """Configuration that reuses third-party validation methods."""

    def __init__(self, from_json_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 stderr_file: TextIO = sys.stderr) -> None:
        """Initialize the configuration.

        Args:
            from_json_text: Optional JSON text to parse directly.
            from_json_filename: Optional path to a JSON file to read.
            stderr_file: Stream used for user-facing diagnostics.
        """
        ThirdPartyJobOptions.__init__(self)
        Config.__init__(self, from_json_data_text=from_json_text,
                        from_json_filename=from_json_filename,
                        stderr_file=stderr_file)

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Return the ordered validation steps for this example."""
        _ = stderr_file
        # The region checks are one conceptual pipeline for one member:
        # reject wrong types, normalize user-friendly text, then verify that
        # the normalized value is one of the names accepted by the application.
        #
        # The same behavior could be expressed as several MemberValidationStep
        # objects for "region". That is useful when one validator should run
        # over many members before the next validator starts. Here the useful
        # order is instead "finish region completely before validating the next
        # member", and MemberValidatorSequence makes that order explicit while
        # keeping the validation plan below at one step per member.
        region_validators = [
            # First, reject non-string values before calling a string method.
            ValueTypeValidator(str),
            # The third-party method normalizes text such as " EU_WEST ".
            CallingMemberValidator(method_name='normalize_region_text',
                                   arg_name_value='value', normalizing=True),
            # Then a normal built-in validator checks the normalized value.
            StrValidator(ALLOWED_REGIONS, ignore_case=False)]
        region_validator = MemberValidatorSequence(region_validators)
        # The retry count has the same shape: a built-in validator protects
        # the third-party method from receiving a value of the wrong type, and
        # the third-party method contains the domain rule for the accepted
        # range. Keeping them in one sequence says that these two checks belong
        # together for this one member.
        retry_validators = [
            ValueTypeValidator(int),
            # This method is validation-only. The default behaviour keeps
            # the original member value when the method returns None or True.
            CallingMemberValidator(method_name='check_retry_count',
                                   arg_name_value='value',
                                   other_args={'minimum': 1, 'maximum': 5})]
        retry_validator = MemberValidatorSequence(retry_validators)
        endpoint_validator = ValueTypeValidator(str)
        return [
            MemberValidationStep(member_names=['region'],
                                 validator=region_validator),
            MemberValidationStep(member_names=['retry_count'],
                                 validator=retry_validator),
            MemberValidationStep(member_names=['endpoint'],
                                 validator=endpoint_validator),
            # The whole-config method checks a relation between members.
            WholeConfigValidationStep(validator=CallingWholeConfigValidator(
                    method_name='check_endpoint_matches_region'))]


def e19_config_method_validators_set(set_values: SetValues,
                                     config_file: PathOrStr) -> None:
    """Create configuration, apply overrides, and store it.

    Args:
        set_values: Values that should differ from the defaults.
        config_file: Path where to write the configuration file.
    """
    config = ExampleConfig19()
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


def e19_config_method_validators_print(config_file: PathOrStr) -> None:
    """Read a configuration file and show how the values are used.

    Args:
        config_file: Path to the configuration file to read.
    """
    try:
        config = ExampleConfig19(from_json_filename=config_file)
        print(f'Configuration read from {config_file}')
        print(f'Region: {config.region}')
        print(f'Retry count: {config.retry_count}')
        print(f'Endpoint: {config.endpoint}')
    except (InvalidConfiguration, InvalidConfigurationValue):
        pass  # Error already printed by the Config object.


# -----------------------------------------------------------------------------
# The rest of this file is the command line handling code.
# This is to be able to run the example from the command line,
# but it could be done in any other way, and is not part of what this example
# is trying to teach.
# -----------------------------------------------------------------------------

INPUT_SPECS = [
    InputSpec(name='region', single=True, value_type=str),
    InputSpec(name='retry_count', single=True, value_type=int),
    InputSpec(name='endpoint', single=True, value_type=str)]
"""Command line values that the example exposes for ``set``."""


def main(args: Optional[list[str]] = None) -> None:
    """Run the example command line interface.

    Args:
        args: Optional replacement for ``sys.argv[1:]``, mainly for tests.
    """
    cmd_line_handling(example_name='e19_config_method_validators',
                      input_specs=INPUT_SPECS,
                      set_command=e19_config_method_validators_set,
                      print_command=e19_config_method_validators_print,
                      args=args)


if __name__ == '__main__':
    main()
    sys.exit(0)
