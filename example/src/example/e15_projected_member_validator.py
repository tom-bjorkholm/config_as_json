#! /usr/local/bin/python3
"""Show how to validate a projected view of one configuration member.

This example builds on ``e13_list_of_dicts.py``. That example validates
each dict inside a list. This example adds one rule that is awkward to
express by looking at one dict at a time: the ``order`` values from all
steps must be unique and increasing.

The stored configuration member is still a list of dicts. The application
wants to keep that shape because each release step has several fields:

- ``name`` says which step to run
- ``order`` says where the step belongs in the release sequence
- ``duration_minutes`` is an estimate used elsewhere by the application

``ProjectedMemberValidator`` lets the validation plan compute a temporary
view of that member. In this example a source validator first checks the
stored list size. The projector then extracts just the list of ``order``
values. A normal ``ListIsOrderedValidator`` validates that projected list,
and the original list of dicts is kept as the configuration value.
"""

# Copyright (c) 2026 Tom Björkholm
# MIT License

import sys
from typing import Optional, TextIO, cast
from config_as_json import Config, PathOrStr, ValidationPlan, \
    MemberValidationStep, ListForEachValidator, ListSizeValidator, \
    ListIsOrderedValidator, DictKeysValidator, DictRule, \
    DictForEachValidator, IntFloatValidator, StrValidator, \
    ProjectedMemberValidator, InvalidConfiguration, \
    InvalidConfigurationValue
from .cmd_line_handling import InputSpec, SetValues, cmd_line_handling

STEP_NAMES = ['prepare', 'build', 'test', 'deploy']
"""Allowed normalized names for release steps."""


def project_step_orders(config: Config, member_name: str, member_value: object,
                        stderr_file: TextIO) -> object:
    """Return the ``order`` values from a list of release-step dicts.

    Args:
        config: The complete Config object. It is not needed here, but the
            projector receives it so more involved projections can use other
            configuration members.
        member_name: The name of the member being projected. It is not needed
            for this simple projection.
        member_value: The original list of release-step dictionaries.
        stderr_file: Diagnostic stream. It is not needed here because the
            inner list validator owns the validation messages.

    Returns:
        A list containing only the step order values.
    """
    _ = config, member_name, stderr_file
    steps = cast(list[dict[str, object]], member_value)
    return [step['order'] for step in steps]


# pylint: disable=duplicate-code
class ExampleConfig15(Config):
    """Configuration using a projected member validator."""

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
        # The member itself is a list, so Config's built-in dict check does
        # not inspect the inner dicts. The validation plan below owns both
        # the per-step dict checks and the projected order-list check.
        self.release_steps: list[dict[str, object]] = [
            {'name': 'prepare', 'order': 10, 'duration_minutes': 5},
            {'name': 'build', 'order': 20, 'duration_minutes': 15},
            {'name': 'deploy', 'order': 30, 'duration_minutes': 10}]
        super().__init__(from_json_data_text=from_json_text,
                         from_json_filename=from_json_filename,
                         stderr_file=stderr_file, member_name=member_name)

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Return the ordered validation steps for this example."""
        _ = stderr_file
        step_keys_validator = DictKeysValidator(
            mandatory_keys=['name', 'order', 'duration_minutes'])
        name_rule = DictRule(keys=['name'],
                             validators=[
                                 StrValidator(allowed_values=STEP_NAMES,
                                              ignore_case=True, normalize=True)
                             ])
        order_rule = DictRule(keys=['order'],
                              validators=[
                                  IntFloatValidator(min_value=1, max_value=100,
                                                    allowed_values=None)])
        duration_rule = DictRule(keys=['duration_minutes'],
                                 validators=[
                                     IntFloatValidator(min_value=1,
                                                       max_value=240,
                                                       allowed_values=None)])
        step_values_validator = DictForEachValidator(
            rules=[name_rule, order_rule, duration_rule])
        per_step_validator = ListForEachValidator(
            element_validators=[step_keys_validator, step_values_validator],
            element_type=dict)
        order_projection_validator = ProjectedMemberValidator(
            projector=project_step_orders,
            source_validator=ListSizeValidator(min_size=1, max_size=10),
            validators=[
                ListIsOrderedValidator(int, is_ordered=True,
                                       unique_values=True)])
        return [
            MemberValidationStep(member_names=['release_steps'],
                                 validator=per_step_validator),
            MemberValidationStep(member_names=['release_steps'],
                                 validator=order_projection_validator)
        ]


# pylint: disable=duplicate-code
def e15_projected_member_set(set_values: SetValues,
                             config_file: PathOrStr) -> None:
    """Create configuration, apply overrides, and store it.

    Args:
        set_values: Values that should differ from the defaults.
        config_file: Path where to write the configuration file.
    """
    config = ExampleConfig15()
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
def e15_projected_member_print(config_file: PathOrStr) -> None:
    """Read a configuration file and show how the values are used.

    Args:
        config_file: Path to the configuration file to read.
    """
    try:
        config = ExampleConfig15(from_json_filename=config_file)
        print(f'Configuration read from {config_file}')
        print(f'Release steps: {config.release_steps}')
        order_values = project_step_orders(config, 'release_steps',
                                           config.release_steps, sys.stderr)
        print(f'Projected order values: {order_values}')
    except (InvalidConfiguration, InvalidConfigurationValue):
        pass  # Error already printed by the Config object.


# -----------------------------------------------------------------------------
# The rest of this file is the command line handling code.
# This is to be able to run the example from the command line,
# but it could be done in any other way, and is not part of what this example
# is trying to teach.
# -----------------------------------------------------------------------------

INPUT_SPECS = [
    InputSpec(name='release_steps', single=True, value_type=str,
              json_value=True)
]
"""Command line values that the example exposes for ``set``.

``release_steps`` is a list of mixed-type dicts. The command line therefore
accepts the complete value as one JSON token, for example:

``--release-steps '[{"name":"BUILD","order":20,"duration_minutes":15}]'``
"""


def main(args: Optional[list[str]] = None) -> None:
    """Run the example command line interface.

    Args:
        args: Optional replacement for ``sys.argv[1:]``, mainly for tests.
    """
    cmd_line_handling(example_name='e15_projected_member_validator',
                      input_specs=INPUT_SPECS,
                      set_command=e15_projected_member_set,
                      print_command=e15_projected_member_print, args=args)


if __name__ == '__main__':
    main()
    sys.exit(0)
