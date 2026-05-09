#! /usr/local/bin/python3
"""Show validator replacements for old Config check helper patterns.

Older code sometimes used Config methods that directly checked common
list-of-dicts shapes. This example shows the validator-based form of the
same ideas. The important point is that no special helper is needed:
``ListForEachValidator`` reaches into each list element, and ordinary dict
validators describe what must be present and what values must look like.

The configuration has three members:

- ``column_mappings`` replaces the old "list of dicts with one typed key"
  pattern. Every row must contain ``column`` as a string, and extra keys are
  accepted.
- ``merge_rules`` replaces the old "list of dicts where one key contains a
  list of typed values" pattern. Every row must contain a non-empty
  ``columns`` list of strings.
- ``rewrite_rules`` replaces the old "list of dicts selected by kind"
  pattern. Each row has a ``kind`` key, and the selected kind decides which
  other keys are mandatory and how their values are validated.
"""

# Copyright (c) 2026 Tom Björkholm
# MIT License

import sys
from typing import Optional, TextIO
from config_as_json import Config, PathOrStr, ValidationPlan, \
    MemberValidationStep, DictKeysValidator, DictRule, DictForEachValidator, \
    DictVariant, DiscriminatedDictValidator, InvalidConfiguration, \
    InvalidConfigurationValue, ListForEachValidator, ListSizeValidator, \
    ListValueTypeValidator, StrValidator, ValueTypeValidator
from .cmd_line_handling import InputSpec, SetValues, cmd_line_handling

REWRITE_KINDS = ['strip', 'remove_chars', 'replace']
"""Allowed normalized rewrite rule kinds."""


def column_mapping_validator() -> ListForEachValidator:
    """Build a validator for a list of dicts with one required typed key."""
    # Each element in ``column_mappings`` is a dict. We validate that dict
    # in two independent steps: first the keys, then the value stored at the
    # key that this example cares about.
    #
    # Extra keys are allowed because a real mapping row may contain metadata
    # such as a source column name, a label, or display-order information.
    # Those keys are application data, so this validator leaves them alone.
    keys_validator = DictKeysValidator(mandatory_keys=['column'],
                                       allow_extra_dict_keys=True)
    values_validator = DictForEachValidator(rules=[
        DictRule(keys=['column'], validators=[ValueTypeValidator(str)])])
    return ListForEachValidator(
        element_validators=[keys_validator, values_validator],
        element_type=dict)


def merge_rule_validator() -> ListForEachValidator:
    """Build a validator for dicts whose checked value is a typed list."""
    # A merge rule is still just one dict inside an outer list, but one of
    # its values is itself a list. The outer ``ListForEachValidator`` reaches
    # each dict. ``DictKeysValidator`` then requires the keys that every merge
    # row needs.
    #
    # ``DictForEachValidator`` validates values at selected keys. For
    # ``columns`` we chain two list validators: one for the list size and one
    # for the element type. For ``separator`` a plain type validator is enough.
    keys_validator = DictKeysValidator(mandatory_keys=['columns', 'separator'],
                                       allow_extra_dict_keys=True)
    values_validator = DictForEachValidator(rules=[
        DictRule(keys=['columns'],
                 validators=[
                     ListSizeValidator(1, sys.maxsize),
                     ListValueTypeValidator(str)
                 ]),
        DictRule(keys=['separator'], validators=[ValueTypeValidator(str)])])
    return ListForEachValidator(
        element_validators=[keys_validator, values_validator],
        element_type=dict)


def rewrite_rule_validator() -> ListForEachValidator:
    """Build a validator for list elements selected by a kind key."""
    # Rewrite rows do not all have the same shape. The ``kind`` value decides
    # which keys are required and how the values should be checked. A
    # ``DiscriminatedDictValidator`` models that "kind selects shape" rule for
    # one dict.
    #
    # The discriminator value is ordinary configuration data, so it can use a
    # normal string validator. Here it accepts user-friendly spelling such as
    # ``REMOVE_CHARS`` and stores the normalized value ``remove_chars``.
    kind_validator = StrValidator(allowed_values=REWRITE_KINDS,
                                  ignore_case=True, normalize=True)
    # Each ``DictVariant`` describes one shape selected by ``kind``. Variants
    # keep their mandatory keys and value rules close together, which is much
    # easier to read than one large collection of cross-cutting conditions.
    strip_variant = DictVariant(mandatory_keys=['column', 'chars'],
                                rules=[
                                    DictRule(
                                        keys=['column', 'chars'],
                                        validators=[ValueTypeValidator(str)])
                                ], allow_extra_dict_keys=True)
    remove_chars_variant = DictVariant(
        mandatory_keys=['column', 'chars'],
        rules=[
            DictRule(keys=['column'], validators=[ValueTypeValidator(str)]),
            DictRule(keys=['chars'], validators=[ListValueTypeValidator(str)])
        ], allow_extra_dict_keys=True)
    replace_variant = DictVariant(mandatory_keys=['column', 'from', 'to'],
                                  rules=[
                                      DictRule(
                                          keys=['column', 'from', 'to'],
                                          validators=[ValueTypeValidator(str)])
                                  ], allow_extra_dict_keys=True)
    one_rule_validator = DiscriminatedDictValidator(
        discriminator_key='kind',
        variants={
            'strip': strip_variant,
            'remove_chars': remove_chars_variant,
            'replace': replace_variant
        }, discriminator_validator=kind_validator)
    # Finally, wrap the one-row validator in ``ListForEachValidator`` so the
    # same kind-selected validation is applied to every row in the list.
    return ListForEachValidator(element_validators=[one_rule_validator],
                                element_type=dict)


class ExampleConfig18(Config):
    """Configuration with nested list-of-dicts validator composition."""

    def __init__(self, from_json_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 stderr_file: TextIO = sys.stderr) -> None:
        """Initialize the configuration.

        Args:
            from_json_text: Optional JSON text to parse directly.
            from_json_filename: Optional path to a JSON file to read.
            stderr_file: Stream used for user-facing diagnostics.
        """
        self.column_mappings: list[dict[str, object]] = [{
            'column': 'first_name',
            'source': 'First Name'
        }]
        self.merge_rules: list[dict[str, object]] = [{
            'columns': ['first_name', 'last_name'],
            'separator':
            ' '
        }]
        self.rewrite_rules: list[dict[str, object]] = [{
            'kind': 'strip',
            'column': 'phone',
            'chars': ' '
        }]
        super().__init__(from_json_data_text=from_json_text,
                         from_json_filename=from_json_filename,
                         stderr_file=stderr_file)

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Return the ordered validation steps for this example."""
        _ = stderr_file
        return [
            MemberValidationStep(member_names=['column_mappings'],
                                 validator=ListSizeValidator(1, sys.maxsize)),
            MemberValidationStep(member_names=['column_mappings'],
                                 validator=column_mapping_validator()),
            MemberValidationStep(member_names=['merge_rules'],
                                 validator=ListSizeValidator(1, sys.maxsize)),
            MemberValidationStep(member_names=['merge_rules'],
                                 validator=merge_rule_validator()),
            MemberValidationStep(member_names=['rewrite_rules'],
                                 validator=rewrite_rule_validator())
        ]


def e18_replacing_check_helpers_set(set_values: SetValues,
                                    config_file: PathOrStr) -> None:
    """Create configuration, apply overrides, and store it.

    Args:
        set_values: Values that should differ from the defaults.
        config_file: Path where to write the configuration file.
    """
    config = ExampleConfig18()
    unknown_keys = [key for key in set_values if not hasattr(config, key)]
    if unknown_keys:
        raise ValueError(f'Invalid key: {unknown_keys[0]}')
    for key, value in set_values.items():
        setattr(config, key, value)
    try:
        config.write(to_json_filename=config_file)
    except (InvalidConfiguration, InvalidConfigurationValue):
        return  # Error already printed by the Config object.
    print(f'Configuration written to {config_file}')


def e18_replacing_config_check_helpers_print(config_file: PathOrStr) -> None:
    """Read a configuration file and show how the values are used.

    Args:
        config_file: Path to the configuration file to read.
    """
    try:
        config = ExampleConfig18(from_json_filename=config_file)
        print(f'Configuration read from {config_file}')
        print(f'Column mappings: {config.column_mappings}')
        print(f'Merge rules: {config.merge_rules}')
        print(f'Rewrite rules: {config.rewrite_rules}')
    except (InvalidConfiguration, InvalidConfigurationValue):
        pass  # Error already printed by the Config object.


INPUT_SPECS = [
    InputSpec(name='column_mappings', single=True, value_type=str,
              json_value=True),
    InputSpec(name='merge_rules', single=True, value_type=str,
              json_value=True),
    InputSpec(name='rewrite_rules', single=True, value_type=str,
              json_value=True)
]
"""Command line values that the example exposes for ``set``."""


def main(args: Optional[list[str]] = None) -> None:
    """Run the example command line interface.

    Args:
        args: Optional replacement for ``sys.argv[1:]``, mainly for tests.
    """
    cmd_line_handling(example_name='e18_replacing_config_check_helpers',
                      input_specs=INPUT_SPECS,
                      set_command=e18_replacing_check_helpers_set,
                      print_command=e18_replacing_config_check_helpers_print,
                      args=args)


if __name__ == '__main__':
    main()
    sys.exit(0)
