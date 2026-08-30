#! /usr/local/bin/python3
"""Show how to validate a projection of the whole configuration.

``ProjectedWholeConfigValidator`` is useful when the rule is about a value
that is calculated from several configuration members. The calculated value
is only a validation view. It is not stored back into the configuration.

This example has two stored members:

- ``primary_region`` is one deployment region.
- ``replica_regions`` is a list of additional deployment regions.

The application rule is that no region may be used twice. That rule is about
the combination of both members, so the validation plan projects the whole
config to one temporary list:

``[primary_region, *replica_regions]``

A normal ``ListIsOrderedValidator`` then checks that this projected list has
unique values.
"""

# Copyright (c) 2026 Tom Björkholm
# MIT License

import sys
from typing import Optional, TextIO, cast
from config_as_json import Config, InvalidConfiguration, \
    InvalidConfigurationValue, ListIsOrderedValidator, ListValueValidator, \
    MemberValidationStep, PathOrStr, ProjectedWholeConfigValidator, \
    StrValidator, ValidationPlan, WholeConfigValidationStep
from .cmd_line_handling import InputSpec, SetValues, cmd_line_handling

REGIONS = ['eu-north', 'us-east', 'us-west', 'ap-south']
"""Allowed deployment regions in this example application."""


def project_all_regions(config: Config, stderr_file: TextIO) -> object:
    """Return all deployment regions from the complete config object.

    Args:
        config: The complete Config object to project from.
        stderr_file: Diagnostic stream. It is not needed here because the
            inner validators own the validation messages.

    Returns:
        A list containing the primary region followed by replica regions.
    """
    _ = stderr_file
    region_config = cast(ExampleConfig23, config)
    return [region_config.primary_region, *region_config.replica_regions]


class ExampleConfig23(Config):
    """Configuration using a projected whole-config validator."""

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
        self.primary_region: str = 'eu-north'
        self.replica_regions: list[str] = ['us-east', 'ap-south']
        super().__init__(from_json_data_text=from_json_text,
                         from_json_filename=from_json_filename,
                         stderr_file=stderr_file, member_name=member_name)

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Return the ordered validation steps for this example."""
        _ = stderr_file
        # First validate and normalize the stored scalar member. The whole
        # config projection later sees this normalized value.
        primary_validator = StrValidator(allowed_values=REGIONS,
                                         ignore_case=True, normalize=True)
        # Then validate the stored list member. This checks that the value is
        # a list and that every replica region is one of the allowed strings.
        replicas_validator = ListValueValidator(min_value=None, max_value=None,
                                                allowed_values=REGIONS)
        # Finally validate a value that does not exist as a stored member.
        # The pseudo-member name ``all_regions`` is used only in diagnostics
        # from the inner validators.
        all_regions_validator = ProjectedWholeConfigValidator(
            projector=project_all_regions, pseudo_member_name='all_regions',
            validators=[
                ListIsOrderedValidator(str, is_ordered=False,
                                       unique_values=True)])
        return [
            MemberValidationStep(member_names=['primary_region'],
                                 validator=primary_validator),
            MemberValidationStep(member_names=['replica_regions'],
                                 validator=replicas_validator),
            WholeConfigValidationStep(validator=all_regions_validator)
        ]


# pylint: disable=duplicate-code
def e23_projected_whole_config_set(set_values: SetValues,
                                   config_file: PathOrStr) -> None:
    """Create configuration, apply overrides, and store it.

    Args:
        set_values: Values that should differ from the defaults.
        config_file: Path where to write the configuration file.
    """
    config = ExampleConfig23()
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
def e23_projected_whole_config_print(config_file: PathOrStr) -> None:
    """Read a configuration file and show how the values are used.

    Args:
        config_file: Path to the configuration file to read.
    """
    try:
        config = ExampleConfig23(from_json_filename=config_file)
        print(f'Configuration read from {config_file}')
        print(f'Primary region: {config.primary_region}')
        print(f'Replica regions: {config.replica_regions}')
        all_regions = project_all_regions(config, sys.stderr)
        print(f'Projected all regions: {all_regions}')
    except (InvalidConfiguration, InvalidConfigurationValue):
        pass  # Error already printed by the Config object.


INPUT_SPECS = [
    InputSpec(name='primary_region', single=True, value_type=str),
    InputSpec(name='replica_regions', single=False, value_type=str)
]
"""Command line values that the example exposes for ``set``.

``replica_regions`` is a normal list of strings, so it can use repeated
command-line values:

``--replica-regions us-east ap-south``
"""


def main(args: Optional[list[str]] = None) -> None:
    """Run the example command line interface.

    Args:
        args: Optional replacement for ``sys.argv[1:]``, mainly for tests.
    """
    cmd_line_handling(example_name='e23_projected_whole_config_validator',
                      input_specs=INPUT_SPECS,
                      set_command=e23_projected_whole_config_set,
                      print_command=e23_projected_whole_config_print,
                      args=args)


if __name__ == '__main__':
    main()
    sys.exit(0)
