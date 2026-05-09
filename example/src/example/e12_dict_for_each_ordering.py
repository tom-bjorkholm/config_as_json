#! /usr/local/bin/python3
"""Show why the order of ``DictRule`` entries matters.

This example builds on ``e11_dict_for_each.py``. It uses one dict
member ``team_tags`` and runs several ``DictRule`` entries on it. The
key teaching point is that ``DictForEachValidator`` runs the rules in
order, and that each validator sees the value returned by the previous
validator. This is the dict analogue of ``e08_combined_list_validators``,
which teaches the same lesson for a list member.

Three rules are used so that the rule-major iteration shape is visible:

1. Rule A applies to all three keys. It uses ``StrValidator`` with
   ``ignore_case=True`` and ``normalize=True`` to accept user-entered
   spellings like ``'eu'`` or ``'PRODUCTION'`` and rewrite them to the
   canonical spelling stored in ``allowed_values``.
2. Rule B applies to a *subset* of the keys (``region`` and
   ``environment``). It uses a stricter ``StrValidator`` with a smaller
   ``allowed_values`` list. Because Rule A already normalized the case,
   Rule B can safely run with ``ignore_case=False``.
3. Rule C applies to the remaining key (``team``). It enforces a
   different narrower allowed-values list, again on the canonical
   spelling produced by Rule A.

If the rules were rearranged, the configuration would mean something
different. For example, running Rule B before Rule A would reject the
input ``'eu'`` because Rule B alone is case-sensitive.
"""

# Copyright (c) 2026 Tom Björkholm
# MIT License

from typing import Optional, TextIO
import sys
from config_as_json import Config, PathOrStr, ValidationPlan, \
    MemberValidationStep, DictKeysValidator, DictRule, \
    DictForEachValidator, StrValidator, InvalidConfiguration, \
    InvalidConfigurationValue
from .cmd_line_handling import InputSpec, SetValues, cmd_line_handling


CANONICAL_TAG_VALUES = ['Eu', 'Us', 'As',
                        'Production', 'Staging', 'Test',
                        'Engineering', 'Marketing', 'Support']
"""Every canonical tag value accepted by the team-tag schema."""


class ExampleConfig12(Config):
    """Configuration that combines several DictRules on one dict member."""

    def __init__(self, from_json_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 stderr_file: TextIO = sys.stderr) -> None:
        """Initialize the configuration.

        Args:
            from_json_text: Optional JSON text to parse directly.
            from_json_filename: Optional path to a JSON file to read.
            stderr_file: Stream used for user-facing diagnostics.
        """
        # ``team_tags`` carries log-tag values for one running service.
        # Every key holds a string; the values are deliberately stored
        # in their canonical spelling so the default config validates
        # without any normalization happening on the default values
        # themselves.
        self._unchecked_dicts: list[str] = ['team_tags']
        self.team_tags: dict[str, str] = {
            'region': 'Eu',
            'environment': 'Production',
            'team': 'Engineering'
        }
        super().__init__(from_json_data_text=from_json_text,
                         from_json_filename=from_json_filename,
                         stderr_file=stderr_file)

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Build the keys-then-rule-chain plan for ``team_tags``."""
        _ = stderr_file
        # Step 1: gate on the key set, just as in ``e11_dict_for_each``.
        tag_keys_validator = DictKeysValidator(
            mandatory_keys=['region', 'environment', 'team'],
            allowed_keys=None)
        # Step 2: run all three rules in order.
        #
        # Rule A normalizes case for every key. After this rule runs,
        # the value at every key is the canonical spelling stored in
        # ``CANONICAL_TAG_VALUES``.
        rule_a = DictRule(keys=['region', 'environment', 'team'],
                          validators=[
                              StrValidator(allowed_values=CANONICAL_TAG_VALUES,
                                           ignore_case=True, normalize=True)])
        # Rule B applies a narrower allowed-values list to the region
        # and environment keys. ``ignore_case=False`` is safe here
        # because Rule A already normalized the case for every value.
        # If Rule B ran *before* Rule A, the user input ``'eu'`` would
        # be rejected: that is the order-matters lesson, made visible.
        rule_b = DictRule(keys=['region', 'environment'],
                          validators=[
                              StrValidator(allowed_values=[
                                  'Eu', 'Us', 'Production', 'Staging'
                              ], ignore_case=False)])
        # Rule C applies a different narrower allowed-values list to
        # the team key.
        rule_c = DictRule(keys=['team'],
                          validators=[
                              StrValidator(allowed_values=[
                                  'Engineering', 'Marketing', 'Support'
                              ], ignore_case=False)])
        # The iteration shape inside ``DictForEachValidator`` is
        # rule-major, then key-within-rule, then validator-within-rule.
        # That means Rule A runs for all three keys before Rule B runs
        # for any key, which is what makes the threading work.
        values_validator = DictForEachValidator(rules=[rule_a, rule_b, rule_c])
        return [
            MemberValidationStep(member_names=['team_tags'],
                                 validator=tag_keys_validator),
            MemberValidationStep(member_names=['team_tags'],
                                 validator=values_validator)
        ]


# pylint: disable=duplicate-code
def e12_dict_for_each_ordering_set(set_values: SetValues,
                                   config_file: PathOrStr) -> None:
    """Create configuration, apply overrides, and store it.

    Args:
        set_values: Values that should differ from the defaults.
        config_file: Path where to write the configuration file.
    """
    config = ExampleConfig12()
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
def e12_dict_for_each_ordering_print(config_file: PathOrStr) -> None:
    """Read a configuration file and show how the values are used.

    Args:
        config_file: Path to the configuration file to read.
    """
    try:
        config = ExampleConfig12(from_json_filename=config_file)
        print(f'Configuration read from {config_file}')
        print(f'Team tags: {config.team_tags}')
        # Showing the canonical values one by one makes it obvious that
        # any normalization performed during validation has already
        # been applied to the stored configuration.
        print(f"Region: {config.team_tags['region']}")
        print(f"Environment: {config.team_tags['environment']}")
        print(f"Team: {config.team_tags['team']}")
    except (InvalidConfiguration, InvalidConfigurationValue):
        pass  # Error already printed by the Config object.


# -----------------------------------------------------------------------------
# The rest of this file is the command line handling code.
# This is to be able to run the example from the command line,
# but it could be done in any other way, and is not part of what this example
# is trying to teach.
# -----------------------------------------------------------------------------

INPUT_SPECS = [
    InputSpec(name='team_tags', single=False, value_type=str, dict_kv=True)
]
"""Command line values that the example exposes for ``set``.

All ``team_tags`` values are strings, so ``key=value`` tokens are a
natural fit. A full override looks like:

``--team-tags region=eu environment=production team=engineering``

Even though those tokens are written in lowercase, the configuration
file will end up containing the canonical spelling
(``Eu``, ``Production``, ``Engineering``). That is the
normalization-through-threading effect produced by Rule A.
"""


def main(args: Optional[list[str]] = None) -> None:
    """Run the example command line interface.

    Args:
        args: Optional replacement for ``sys.argv[1:]``, mainly for tests.
    """
    cmd_line_handling(example_name='e12_dict_for_each_ordering',
                      input_specs=INPUT_SPECS,
                      set_command=e12_dict_for_each_ordering_set,
                      print_command=e12_dict_for_each_ordering_print,
                      args=args)


if __name__ == '__main__':
    main()
    sys.exit(0)
