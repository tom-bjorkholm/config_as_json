#! /usr/local/bin/python3
"""Show per-key value validation with ``DictForEachValidator``.

This example builds on ``e10_dict_basic_validators.py``. It keeps the
key-set check from ``DictKeysValidator`` and adds the natural next
step: validating the *values* at each key with a per-key chain of
inner validators.

Two new pieces are introduced:

- ``DictRule`` ties a list of dict keys to a list of inner validators
  that should be applied to the value at each of those keys.
- ``DictForEachValidator`` runs all the rules in order, applying their
  inner validator chains to the matching dict values.

The example uses one dict member ``cache_settings`` with all four keys
mandatory and validated, so the reader can see the typical pairing of
two validation steps on the same member:

1. ``DictKeysValidator`` rejects unknown keys and missing keys.
2. ``DictForEachValidator`` runs per-key value rules, including a rule
   that groups two keys that share the same validator chain.

The inner validators are the same ``IntFloatValidator`` and
``StrValidator`` that ``e03_scalar_validators.py`` already introduced;
this example only shows that they can also be reused inside a dict
rule. ``MemberValidator`` is the lingua franca of composition.
"""

# Copyright (c) 2026 Tom Björkholm
# MIT License

from typing import Optional, TextIO
import sys
from config_as_json import Config, PathOrStr, ValidationPlan, \
    MemberValidationStep, DictKeysValidator, DictRule, \
    DictForEachValidator, IntFloatValidator, StrValidator, \
    InvalidConfiguration, InvalidConfigurationValue
from .cmd_line_handling import InputSpec, SetValues, cmd_line_handling


class ExampleConfig11(Config):
    """Configuration that uses per-key dict value validation."""

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
        # ``cache_settings`` is a dict whose keys are validated by
        # ``DictKeysValidator`` and whose values are validated by
        # ``DictForEachValidator``. The values are deliberately of mixed
        # types (3 ints and 1 string) to make the per-key rules
        # interesting: each key gets the validator that matches its
        # type.
        #
        # As in ``e10_dict_basic_validators.py``, we opt out of the
        # ``Config`` base class's own dict-shape check so the dict
        # validators below become the single source of truth.
        self._unchecked_dicts: list[str] = ['cache_settings']
        self.cache_settings: dict[str, object] = {
            'ttl_seconds': 300,
            'refresh_seconds': 60,
            'max_entries': 1000,
            'eviction_policy': 'lru'
        }
        super().__init__(from_json_data_text=from_json_text,
                         from_json_filename=from_json_filename,
                         stderr_file=stderr_file, member_name=member_name)

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Build the keys-then-values plan for ``cache_settings``."""
        _ = stderr_file
        # Step 1: gate on the key set.
        # ``DictKeysValidator`` enforces that every mandatory key is
        # present and that no unknown key is present. It never inspects
        # values, so it pairs naturally with the per-key value rules
        # below.
        keys_validator = DictKeysValidator(
            mandatory_keys=['ttl_seconds', 'refresh_seconds',
                            'max_entries', 'eviction_policy'],
            allowed_keys=None)
        # Step 2: per-key value rules.
        #
        # A ``DictRule`` ties a list of keys to a list of inner
        # validators. The first rule below shows *why* ``DictRule``
        # exists at all: ``ttl_seconds`` and ``refresh_seconds`` share
        # the same range rule, so we list them together in one rule
        # with one validator chain. Without that grouping we would
        # have had to repeat the same ``IntFloatValidator`` twice.
        seconds_range_validator = IntFloatValidator(min_value=1,
                                                    max_value=86400,
                                                    allowed_values=None)
        seconds_rule = DictRule(keys=['ttl_seconds', 'refresh_seconds'],
                                validators=[seconds_range_validator])
        # The next two rules each apply a different validator to a
        # single key. Splitting them into separate rules keeps each
        # rule's intent obvious.
        max_entries_rule = DictRule(
            keys=['max_entries'],
            validators=[IntFloatValidator(min_value=1, max_value=10000,
                                          allowed_values=None)])
        eviction_policy_rule = DictRule(
            keys=['eviction_policy'],
            validators=[StrValidator(allowed_values=['lru', 'lfu', 'fifo'],
                                     ignore_case=False)])
        values_validator = DictForEachValidator(
            rules=[seconds_rule, max_entries_rule, eviction_policy_rule])
        # Note that ``DictForEachValidator`` silently skips a rule key
        # that is not present in the dict. Enforcing that mandatory
        # keys are present is the job of ``DictKeysValidator`` in
        # step 1, so the two validators stay strictly orthogonal.
        return [MemberValidationStep(member_names=['cache_settings'],
                                     validator=keys_validator),
                MemberValidationStep(member_names=['cache_settings'],
                                     validator=values_validator)]


# pylint: disable=duplicate-code
def e11_dict_for_each_set(set_values: SetValues,
                          config_file: PathOrStr) -> None:
    """Create configuration, apply overrides, and store it.

    Args:
        set_values: Values that should differ from the defaults.
        config_file: Path where to write the configuration file.
    """
    config = ExampleConfig11()
    # Same explicit set pattern as the earlier examples so the reader
    # can focus on the validation plan rather than on helper functions.
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
def e11_dict_for_each_print(config_file: PathOrStr) -> None:
    """Read a configuration file and show how the values are used.

    Args:
        config_file: Path to the configuration file to read.
    """
    try:
        config = ExampleConfig11(from_json_filename=config_file)
        print(f'Configuration read from {config_file}')
        print(f'Cache settings: {config.cache_settings}')
        # Unpack the dict to show that the application can use each
        # validated value directly without any further checking.
        ttl_seconds = config.cache_settings['ttl_seconds']
        eviction_policy = config.cache_settings['eviction_policy']
        print(f'Time-to-live: {ttl_seconds} seconds')
        print(f'Eviction policy: {eviction_policy}')
    except (InvalidConfiguration, InvalidConfigurationValue):
        pass  # Error already printed by the Config object.


# -----------------------------------------------------------------------------
# The rest of this file is the command line handling code.
# This is to be able to run the example from the command line,
# but it could be done in any other way, and is not part of what this example
# is trying to teach.
# -----------------------------------------------------------------------------

INPUT_SPECS = [
    InputSpec(name='cache_settings', single=True, value_type=str,
              json_value=True)
]
"""Command line values that the example exposes for ``set``.

The ``cache_settings`` member contains a mix of int and str values, so
``key=value`` tokens are not enough to express it on the command line:
each token would need its own type. We therefore accept the whole dict
as one JSON-encoded token via ``json_value=True``. ``value_type`` is
ignored for this flavour but ``InputSpec`` still requires a value, so
we set it to ``str``.

A full override looks like:

``--cache-settings '{"ttl_seconds": 60, "refresh_seconds": 30,
"max_entries": 100, "eviction_policy": "fifo"}'``
"""


def main(args: Optional[list[str]] = None) -> None:
    """Run the example command line interface.

    Args:
        args: Optional replacement for ``sys.argv[1:]``, mainly for tests.
    """
    cmd_line_handling(example_name='e11_dict_for_each',
                      input_specs=INPUT_SPECS,
                      set_command=e11_dict_for_each_set,
                      print_command=e11_dict_for_each_print, args=args)


if __name__ == '__main__':
    main()
    sys.exit(0)
