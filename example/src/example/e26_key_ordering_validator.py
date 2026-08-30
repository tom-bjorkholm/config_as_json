#! /usr/local/bin/python3
"""Normalize a list of dicts with ListKeyOrderingValidator.

This example builds on the list-of-dicts examples. Those examples show how
to check the shape of every dict in a list. This example adds one normalizing
step after those checks: it sorts the list of dicts by one key inside each
dict.

The configuration member is ``release_steps``. Each release step is stored as
a dict because the application needs more than one value per step:

- ``step`` is the numeric ordering key
- ``name`` is the human-readable step name
- ``owner`` is optional

The important distinction is that the list elements are dicts, but the
ordering value is an int. ``ListKeyOrderingValidator`` connects those two
views. It keeps the original dicts in the final list and uses the projected
integer key only for sorting and duplicate removal.
"""

# Copyright (c) 2026 Tom Björkholm
# MIT License

from typing import Optional, TextIO
import sys
from config_as_json import Config, DictForEachValidator, DictKeysValidator, \
    DictRule, IntFloatValidator, InvalidConfiguration, \
    InvalidConfigurationValue, ListForEachValidator, \
    ListKeyOrderingValidator, MemberValidationStep, PathOrStr, \
    ValidationPlan, ValueTypeValidator
from .cmd_line_handling import InputSpec, SetValues, cmd_line_handling


def release_step_order(step: dict[str, object]) -> int:
    """Return the numeric ordering key for one release step.

    The validation plan checks the dict shape before this function is used.
    That is why the function can be small: it only extracts the application
    key that defines the order.
    """
    step_number = step['step']
    assert isinstance(step_number, int)
    return step_number


class ExampleConfig26(Config):
    """Configuration that normalizes a list of release-step dicts."""

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
        # The default is intentionally out of order. When ``Config`` calls
        # ``get_validation_plan`` from ``super().__init__``, the ordering
        # validator below normalizes this list before application code sees
        # the configuration object.
        self.release_steps: list[dict[str, object]] = [
            {'step': 30, 'name': 'deploy', 'owner': 'ops'},
            {'step': 10, 'name': 'build'},
            {'step': 20, 'name': 'test', 'owner': 'qa'}
        ]
        super().__init__(from_json_data_text=from_json_text,
                         from_json_filename=from_json_filename,
                         stderr_file=stderr_file, member_name=member_name)

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Return the ordered validation steps for this example."""
        _ = stderr_file
        # Step 1 checks that every list element is a dict with the keys
        # needed by the application. This protects the key function from
        # missing ``step`` keys.
        release_step_keys = DictKeysValidator(mandatory_keys=['step', 'name'],
                                              allowed_keys=['owner'])
        # Step 2 checks values inside each dict. The order key must be an
        # int, and the text fields must be strings. These checks also make
        # the ``assert`` in ``release_step_order`` a statement about a
        # validated invariant, not a hidden validation rule.
        step_rule = DictRule(
            keys=['step'],
            validators=[IntFloatValidator(min_value=1, max_value=99,
                                          allowed_values=None)])
        name_rule = DictRule(keys=['name'],
                             validators=[ValueTypeValidator(str)])
        owner_rule = DictRule(keys=['owner'],
                              validators=[ValueTypeValidator(str)])
        release_step_values = DictForEachValidator(
            rules=[step_rule, name_rule, owner_rule])
        per_step_validator = ListForEachValidator(
            element_validators=[release_step_keys, release_step_values],
            element_type=dict)
        # Step 3 is the new normalizing part. ``order=True`` is the default,
        # but it is written explicitly here because sorting is the point of
        # this example. The validator sorts by the integer returned from
        # ``release_step_order``. If two dicts have the same ``step`` value,
        # ``keep_only_unique`` keeps the first one after sorting and removes
        # later duplicate-key entries.
        order_validator = ListKeyOrderingValidator(element_type=dict,
                                                   key=release_step_order,
                                                   key_type=int, order=True,
                                                   keep_only_unique=True)
        return [MemberValidationStep(member_names=['release_steps'],
                                     validator=per_step_validator),
                MemberValidationStep(member_names=['release_steps'],
                                     validator=order_validator)]


# pylint: disable=duplicate-code
def e26_key_ordering_set(set_values: SetValues,
                         config_file: PathOrStr) -> None:
    """Create configuration, apply overrides, and store it.

    Args:
        set_values: Values that should differ from the defaults.
        config_file: Path where to write the configuration file.
    """
    config = ExampleConfig26()
    # The command line helper parses ``release_steps`` as JSON, so the
    # assigned value is already a Python list/dict structure before
    # validation runs during ``write``.
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
def e26_key_ordering_print(config_file: PathOrStr) -> None:
    """Read a configuration file and show how the values are used.

    Args:
        config_file: Path to the configuration file to read.
    """
    try:
        config = ExampleConfig26(from_json_filename=config_file)
        print(f'Configuration read from {config_file}')
        print(f'Release steps: {config.release_steps}')
        for index, step in enumerate(config.release_steps):
            step_number = step['step']
            name = step['name']
            owner = step.get('owner', 'unassigned')
            print(f'Step {index}: {step_number} {name} owned by {owner}')
    except (InvalidConfiguration, InvalidConfigurationValue):
        pass  # Error already printed by the Config object.


INPUT_SPECS = [
    InputSpec(name='release_steps', single=True, value_type=str,
              json_value=True)
]
"""Command line values that the example exposes for ``set``.

``release_steps`` is a list of dicts, so the example accepts it as one
JSON-encoded command line token. This keeps the command line parser simple
and lets the validator example focus on configuration validation.

For example:

``--release-steps '[{"step":20,"name":"test"},
{"step":10,"name":"build"},{"step":20,"name":"duplicate"}]'``
"""


def main(args: Optional[list[str]] = None) -> None:
    """Run the example command line interface.

    Args:
        args: Optional replacement for ``sys.argv[1:]``, mainly for tests.
    """
    cmd_line_handling(example_name='e26_key_ordering_validator',
                      input_specs=INPUT_SPECS,
                      set_command=e26_key_ordering_set,
                      print_command=e26_key_ordering_print, args=args)


if __name__ == '__main__':
    main()
    sys.exit(0)
