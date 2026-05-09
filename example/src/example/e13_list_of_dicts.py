#! /usr/local/bin/python3
"""Show how list and dict validators compose into one another.

This is one of the advanced examples in the validator series. It is for
readers who already understood the earlier list and dict examples (``e06``
to ``e12``) and now want to see how the building blocks fit together when
the configuration shape mixes lists and dicts.

The configuration has one member ``maintenance_windows`` that is a
list of dicts: every element of the list is itself a dict describing
one maintenance window with these keys:

- ``name``: a string tag for the kind of window
- ``hours_utc``: a list of UTC hour values when the window is active
- ``priority``: an optional integer priority

Two composition directions are visible in this single example:

- **Dict in list** is taught by using ``DictKeysValidator`` and
  ``DictForEachValidator`` as ``element_validators`` of a
  ``ListForEachValidator``. The earlier ``e09_list_for_each`` example
  used list validators in that role; this example uses the built-in
  dict validators in exactly the same slot.
- **List in dict** is taught by using ``ListSizeValidator`` and
  ``ListValueValidator`` inside a ``DictRule``. The same dict rule
  could equally well include another ``DictForEachValidator`` for a
  nested dict shape; nesting is unbounded.

The lesson is that ``MemberValidator`` is the lingua franca of
composition. Any built-in or user-defined ``MemberValidator`` can be
plugged into any of the composition slots without special handling.
"""

# Copyright (c) 2026 Tom Björkholm
# MIT License

from typing import Optional, TextIO
import sys
from config_as_json import Config, PathOrStr, ValidationPlan, \
    MemberValidationStep, ListForEachValidator, ListSizeValidator, \
    ListValueValidator, DictKeysValidator, DictRule, \
    DictForEachValidator, IntFloatValidator, StrValidator, \
    InvalidConfiguration, InvalidConfigurationValue
from .cmd_line_handling import InputSpec, SetValues, cmd_line_handling


WINDOW_NAMES = ['weekday', 'weekend', 'holiday', 'custom']
"""Allowed values for the ``name`` key of one maintenance window."""


class ExampleConfig13(Config):
    """Configuration with a list of dicts validated by composition."""

    def __init__(self, from_json_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 stderr_file: TextIO = sys.stderr) -> None:
        """Initialize the configuration.

        Args:
            from_json_text: Optional JSON text to parse directly.
            from_json_filename: Optional path to a JSON file to read.
            stderr_file: Stream used for user-facing diagnostics.
        """
        # The new thing in this example is that one configuration
        # member is a list of dicts. Each inner dict describes one
        # maintenance window.
        #
        # Note: there is no ``_unchecked_dicts`` entry here because the
        # member itself is a list, not a dict. The ``Config`` base
        # class only runs its own dict-shape check on dict members, so
        # the per-element dict validators below are already the only
        # thing that inspects the inner dicts.
        self.maintenance_windows: list[dict[str, object]] = [{
            'name': 'weekday',
            'hours_utc': [8, 9, 10, 11, 12, 13, 14, 15, 16, 17],
            'priority': 5
        }]
        super().__init__(from_json_data_text=from_json_text,
                         from_json_filename=from_json_filename,
                         stderr_file=stderr_file)

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Return the ordered validation steps for this example."""
        _ = stderr_file
        # Step 1: outer list size. Just like ``e09_list_for_each``,
        # the size rule lives in its own validator so each component
        # in the plan stays single-purpose.
        outer_size_validator = ListSizeValidator(min_size=1, max_size=20)
        # Step 2: per-element validation. The element validators here
        # are *dict validators* instead of the *list validators* that
        # ``e09_list_for_each`` used. That is the dict-in-list lesson.
        per_window_keys_validator = DictKeysValidator(
            mandatory_keys=['name', 'hours_utc'], allowed_keys=['priority'])
        # The per-key value rules show the list-in-dict lesson: one
        # rule contains list validators, and they validate the list
        # value stored at one dict key.
        name_rule = DictRule(
            keys=['name'],
            validators=[StrValidator(allowed_values=WINDOW_NAMES,
                                     ignore_case=True, normalize=True)])
        hours_rule = DictRule(keys=['hours_utc'],
                              validators=[
                                  ListSizeValidator(min_size=1, max_size=24),
                                  ListValueValidator(min_value=0, max_value=23,
                                                     allowed_values=None)])
        priority_rule = DictRule(
            keys=['priority'],
            validators=[IntFloatValidator(min_value=0, max_value=9,
                                          allowed_values=None)])
        per_window_values_validator = DictForEachValidator(
            rules=[name_rule, hours_rule, priority_rule])
        # ``ListForEachValidator`` accepts any ``MemberValidator`` as
        # an element validator. Here we pass two of them: first the
        # dict-keys check, then the per-key value check. This mirrors
        # the order used by every dict example so far.
        per_window_validator = ListForEachValidator(
            element_validators=[per_window_keys_validator,
                                per_window_values_validator],
            element_type=dict)
        return [MemberValidationStep(member_names=['maintenance_windows'],
                                     validator=outer_size_validator),
                MemberValidationStep(member_names=['maintenance_windows'],
                                     validator=per_window_validator)]


# pylint: disable=duplicate-code
def e13_list_of_dicts_set(set_values: SetValues,
                          config_file: PathOrStr) -> None:
    """Create configuration, apply overrides, and store it.

    Args:
        set_values: Values that should differ from the defaults.
        config_file: Path where to write the configuration file.
    """
    config = ExampleConfig13()
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
def e13_list_of_dicts_print(config_file: PathOrStr) -> None:
    """Read a configuration file and show how the values are used.

    Args:
        config_file: Path to the configuration file to read.
    """
    try:
        config = ExampleConfig13(from_json_filename=config_file)
        print(f'Configuration read from {config_file}')
        print(f'Maintenance windows: {config.maintenance_windows}')
        for index, window in enumerate(config.maintenance_windows):
            name = window['name']
            hours = window['hours_utc']
            print(f'Window {index}: name={name}, hours={hours}')
    except (InvalidConfiguration, InvalidConfigurationValue):
        pass  # Error already printed by the Config object.


# -----------------------------------------------------------------------------
# The rest of this file is the command line handling code.
# This is to be able to run the example from the command line,
# but it could be done in any other way, and is not part of what this example
# is trying to teach.
# -----------------------------------------------------------------------------

INPUT_SPECS = [
    InputSpec(name='maintenance_windows', single=True, value_type=str,
              json_value=True)
]
"""Command line values that the example exposes for ``set``.

At this nesting depth (a list of mixed-type dicts that themselves
contain lists), reinventing more separators on the command line stops
teaching anything. The honest CLI input is JSON, so the option
accepts a single JSON-encoded token via ``json_value=True``.
``value_type`` is unused for this flavour but ``InputSpec`` still
requires a value, so it is set to ``str``.

A two-window override looks like:

``--maintenance-windows '[{"name":"weekend","hours_utc":[10,11,12]},
{"name":"weekday","hours_utc":[8,9],"priority":2}]'``
"""


def main(args: Optional[list[str]] = None) -> None:
    """Run the example command line interface.

    Args:
        args: Optional replacement for ``sys.argv[1:]``, mainly for tests.
    """
    cmd_line_handling(example_name='e13_list_of_dicts',
                      input_specs=INPUT_SPECS,
                      set_command=e13_list_of_dicts_set,
                      print_command=e13_list_of_dicts_print, args=args)


if __name__ == '__main__':
    main()
    sys.exit(0)
