#! /usr/local/bin/python3
"""Teach predicate-based ``DictRule`` keys and dynamic numeric values.

Earlier dict examples use fixed key lists: a rule says exactly which keys
it applies to. That is a good fit for closed dict shapes, but many
applications also have open dictionaries whose keys are chosen by users,
plugins, or data files.

This example has 2 open dict members:

- ``cache_tunables`` may contain arbitrary keys. Keys ending in
  ``_seconds`` must contain integer seconds, and keys ending in ``_slots``
  must contain one of the allowed slot counts. Other keys are kept as
  application metadata and are not validated by these rules.
- ``pool_sizes`` is a simpler dict where every key is user-defined but
  every value must be one of the allowed pool sizes.

The important new ideas are:

- A ``DictRule`` can receive a key predicate instead of a fixed key list.
  The predicate is called for each present dict key, and normal Python
  truthiness decides whether the rule applies.
- ``accept_all_keys`` is the convenience predicate for rules that should
  apply to every present key.
- ``IntFloatValidator`` can receive a callable for ``allowed_values``.
  The callable is used when validation runs, so applications can calculate
  the allowed values from their own runtime state.
"""

# Copyright (c) 2026 Tom Björkholm
# MIT License

import sys
from collections.abc import Hashable
from typing import Optional, Sequence, TextIO
from config_as_json import Config, PathOrStr, ValidationPlan, \
    MemberValidationStep, DictRule, DictForEachValidator, IntFloatValidator, \
    InvalidConfiguration, InvalidConfigurationValue, accept_all_keys
from .cmd_line_handling import InputSpec, SetValues, cmd_line_handling


def is_seconds_tunable(key: Hashable) -> bool:
    """Return ``True`` for tunable keys that store seconds."""
    return isinstance(key, str) and key.endswith('_seconds')


def is_slots_tunable(key: Hashable) -> bool:
    """Return ``True`` for tunable keys that store slot counts."""
    return isinstance(key, str) and key.endswith('_slots')


class ExampleConfig20(Config):
    """Configuration that validates open dictionaries by key predicate."""

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
        # Both members are open dictionaries. Their key sets are not known
        # from the defaults, so we opt out of the base class dict-key check
        # and let ``DictForEachValidator`` validate values for the keys that
        # match each rule.
        self._unchecked_dicts: list[str] = ['cache_tunables', 'pool_sizes']
        self.cache_tunables: dict[str, object] = {
            'frontend_seconds': 60,
            'backend_seconds': 120,
            'image_slots': 4,
            'note': 'development defaults'
        }
        self.pool_sizes: dict[str, object] = {
            'default': 2,
            'analytics': 4
        }
        super().__init__(from_json_data_text=from_json_text,
                         from_json_filename=from_json_filename,
                         stderr_file=stderr_file, member_name=member_name)

    def allowed_pool_sizes(self) -> Sequence[int]:
        """Return pool-size values currently allowed by the application."""
        # A real application could calculate this from enabled plugins,
        # license level, or hardware. The validator sees whatever this method
        # returns when validation runs.
        return [1, 2, 4, 8]

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Build the validation plan for the open dict members."""
        _ = stderr_file
        seconds_rule = DictRule(
            keys=is_seconds_tunable,
            validators=[IntFloatValidator(min_value=1, max_value=3600,
                                          allowed_values=None)])
        slots_rule = DictRule(keys=is_slots_tunable,
                              validators=[IntFloatValidator(
                                  min_value=None, max_value=None,
                                  allowed_values=self.allowed_pool_sizes)])
        cache_tunables_validator = DictForEachValidator(
            rules=[seconds_rule, slots_rule])
        pool_sizes_validator = DictForEachValidator(
            rules=[DictRule(keys=accept_all_keys,
                            validators=[IntFloatValidator(
                                min_value=None, max_value=None,
                                allowed_values=self.allowed_pool_sizes)])])
        return [MemberValidationStep(member_names=['cache_tunables'],
                                     validator=cache_tunables_validator),
                MemberValidationStep(member_names=['pool_sizes'],
                                     validator=pool_sizes_validator)]


# pylint: disable=duplicate-code
def e20_dynamic_dict_rules_set(set_values: SetValues,
                               config_file: PathOrStr) -> None:
    """Create configuration, apply overrides, and store it.

    Args:
        set_values: Values that should differ from the defaults.
        config_file: Path where to write the configuration file.
    """
    config = ExampleConfig20()
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
def e20_dynamic_dict_rules_print(config_file: PathOrStr) -> None:
    """Read a configuration file and show how the values are used.

    Args:
        config_file: Path to the configuration file to read.
    """
    try:
        config = ExampleConfig20(from_json_filename=config_file)
        print(f'Configuration read from {config_file}')
        print(f'Cache tunables: {config.cache_tunables}')
        print(f'Pool sizes: {config.pool_sizes}')
        print('Frontend seconds: '
              f'{config.cache_tunables.get("frontend_seconds")}')
        print(f'Default pool size: {config.pool_sizes.get("default")}')
    except (InvalidConfiguration, InvalidConfigurationValue):
        pass  # Error already printed by the Config object.


# -----------------------------------------------------------------------------
# The rest of this file is the command line handling code.
# This is to be able to run the example from the command line,
# but it could be done in any other way, and is not part of what this example
# is trying to teach.
# -----------------------------------------------------------------------------

INPUT_SPECS = [
    InputSpec(name='cache_tunables', single=True, value_type=str,
              json_value=True),
    InputSpec(name='pool_sizes', single=True, value_type=str, json_value=True)
]
"""Command line values that the example exposes for ``set``.

Both members are open dicts, and ``cache_tunables`` deliberately mixes
integers and strings, so the command line accepts each member as one JSON
value.

A full override looks like:

``--cache-tunables '{"frontend_seconds": 30, "image_slots": 8,
"note": "fast"}' --pool-sizes '{"default": 4, "analytics": 8}'``
"""


def main(args: Optional[list[str]] = None) -> None:
    """Run the example command line interface.

    Args:
        args: Optional replacement for ``sys.argv[1:]``, mainly for tests.
    """
    cmd_line_handling(example_name='e20_dynamic_dict_rules',
                      input_specs=INPUT_SPECS,
                      set_command=e20_dynamic_dict_rules_set,
                      print_command=e20_dynamic_dict_rules_print, args=args)


if __name__ == '__main__':
    main()
    sys.exit(0)
