#! /usr/local/bin/python3
"""Show how to validate dict variants selected by one discriminator key.

This example builds on the dict validator examples ``e10`` through
``e13``. Those examples validate dicts with one fixed shape. This example
handles a common next step: one dict member can have several allowed
shapes, and one key in the dict tells us which shape applies.

The configuration has one member ``export_target``. It is always a dict
with a ``kind`` key:

- if ``kind`` is ``'file'``, the dict must contain ``filename`` and may
  contain ``format``
- if ``kind`` is ``'queue'``, the dict must contain ``queue`` and may
  contain ``batch_size``

``DiscriminatedDictValidator`` owns that whole decision. It first
validates and normalizes ``kind`` with a normal ``StrValidator``. Then it
selects the matching ``DictVariant``. The selected variant defines the
mandatory keys, the optional keys, and the per-key validators that apply
only to that variant.

This keeps the validation plan small: one member validation step describes
the whole discriminated dict, while the two ``DictVariant`` objects keep the
variant-specific details close to their names.
"""

# Copyright (c) 2026 Tom Björkholm
# MIT License

from typing import Optional, TextIO
import sys
from config_as_json import Config, PathOrStr, ValidationPlan, \
    MemberValidationStep, DictRule, DictVariant, \
    DiscriminatedDictValidator, IntFloatValidator, StrValidator, \
    InvalidConfiguration, InvalidConfigurationValue
from .cmd_line_handling import InputSpec, SetValues, cmd_line_handling

EXPORT_KINDS = ['file', 'queue']
"""Allowed normalized export target kinds."""


class ExampleConfig14(Config):
    """Configuration with one discriminated dictionary member."""

    def __init__(self, from_json_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 stderr_file: TextIO = sys.stderr) -> None:
        """Initialize the configuration.

        Args:
            from_json_text: Optional JSON text to parse directly.
            from_json_filename: Optional path to a JSON file to read.
            stderr_file: Stream used for user-facing diagnostics.
        """
        # ``export_target`` is a dict member, but it does not have one fixed
        # key set. We opt out of the Config base class dict-shape check so
        # ``DiscriminatedDictValidator`` can decide which shape is valid
        # after it has inspected ``kind``.
        self._unchecked_dicts: list[str] = ['export_target']
        self.export_target: dict[str, object] = {
            'kind': 'file',
            'filename': 'report.json',
            'format': 'json'
        }
        super().__init__(from_json_data_text=from_json_text,
                         from_json_filename=from_json_filename,
                         stderr_file=stderr_file)

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Return the ordered validation steps for this example."""
        _ = stderr_file
        # The discriminator is ordinary data, so a normal string validator
        # can validate and normalize it before variant lookup.
        kind_validator = StrValidator(allowed_values=EXPORT_KINDS,
                                      ignore_case=True, normalize=True)
        # The file variant accepts only file-related keys. The ``format`` key
        # is optional, so a file target may be just ``kind`` + ``filename``.
        file_variant = DictVariant(
            mandatory_keys=['filename'], allowed_keys=['format'],
            rules=[
                DictRule(keys=['filename'],
                         validators=[
                             StrValidator(
                                 allowed_values=['report.json', 'report.csv'],
                                 ignore_case=False)
                         ]),
                DictRule(keys=['format'],
                         validators=[
                             StrValidator(allowed_values=['json', 'csv'],
                                          ignore_case=True, normalize=True)])])
        # The queue variant has different mandatory and optional keys.
        # ``batch_size`` is validated only when this variant is selected.
        queue_variant = DictVariant(
            mandatory_keys=['queue'], allowed_keys=['batch_size'],
            rules=[
                DictRule(keys=['queue'],
                         validators=[
                             StrValidator(allowed_values=['reports', 'alerts'],
                                          ignore_case=True, normalize=True)
                         ]),
                DictRule(keys=['batch_size'],
                         validators=[
                             IntFloatValidator(min_value=1, max_value=1000,
                                               allowed_values=None)])])
        target_validator = DiscriminatedDictValidator(
            discriminator_key='kind',
            variants={
                'file': file_variant,
                'queue': queue_variant
            }, discriminator_validator=kind_validator)
        return [
            MemberValidationStep(member_names=['export_target'],
                                 validator=target_validator)
        ]


def e14_discriminated_dict_set(set_values: SetValues,
                               config_file: PathOrStr) -> None:
    """Create configuration, apply overrides, and store it.

    Args:
        set_values: Values that should differ from the defaults.
        config_file: Path where to write the configuration file.
    """
    config = ExampleConfig14()
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


def e14_discriminated_dict_validator_print(config_file: PathOrStr) -> None:
    """Read a configuration file and show how the values are used.

    Args:
        config_file: Path to the configuration file to read.
    """
    try:
        config = ExampleConfig14(from_json_filename=config_file)
        print(f'Configuration read from {config_file}')
        target = config.export_target
        print(f'Export target: {target}')
        print(f"Export kind: {target['kind']}")
        if target['kind'] == 'file':
            print(f"Filename: {target['filename']}")
        if target['kind'] == 'queue':
            print(f"Queue: {target['queue']}")
    except (InvalidConfiguration, InvalidConfigurationValue):
        pass  # Error already printed by the Config object.


# -----------------------------------------------------------------------------
# The rest of this file is the command line handling code.
# This is to be able to run the example from the command line,
# but it could be done in any other way, and is not part of what this example
# is trying to teach.
# -----------------------------------------------------------------------------

INPUT_SPECS = [
    InputSpec(name='export_target', single=True, value_type=str,
              json_value=True)
]
"""Command line values that the example exposes for ``set``.

``export_target`` is a mixed-type dict whose allowed keys depend on another
key in the same dict. A JSON token is therefore the clearest command-line
form. A queue target override looks like:

``--export-target '{"kind":"QUEUE","queue":"ALERTS","batch_size":50}'``

The stored configuration will contain the normalized values
``'queue'`` and ``'alerts'``.
"""


def main(args: Optional[list[str]] = None) -> None:
    """Run the example command line interface.

    Args:
        args: Optional replacement for ``sys.argv[1:]``, mainly for tests.
    """
    cmd_line_handling(example_name='e14_discriminated_dict_validator',
                      input_specs=INPUT_SPECS,
                      set_command=e14_discriminated_dict_set,
                      print_command=e14_discriminated_dict_validator_print,
                      args=args)


if __name__ == '__main__':
    main()
    sys.exit(0)
