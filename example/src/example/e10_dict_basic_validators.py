#! /usr/local/bin/python3
"""Show the most basic dict validator: ``DictKeysValidator``.

This example is the first teaching example that uses dict-valued
configuration members. It keeps the lesson deliberately small by showing
only the validator that checks the key set of a dict, and by keeping
the values inside the dicts so simple that no value validation is
needed.

The example introduces 2 modes of ``DictKeysValidator``, applied to 2
independent dict members so that the reader can see them side by side:

- ``feature_flags`` shows the *mandatory + optional* shape: some keys
  must be present and a few additional keys are accepted.
- ``port_assignments`` shows the *exact-shape* form: only the listed
  keys are accepted, and they are all mandatory.

Readers who want the general introduction to ``ValidationPlan`` should
first read ``e03_scalar_validators.py``. This example only repeats the
parts that are important for understanding dict validators.
"""

# Copyright (c) 2026 Tom Björkholm
# MIT License

from typing import Optional, TextIO
import sys
from config_as_json import Config, PathOrStr, ValidationPlan, \
    MemberValidationStep, DictKeysValidator, InvalidConfiguration, \
    InvalidConfigurationValue
from .cmd_line_handling import InputSpec, SetValues, cmd_line_handling


class ExampleConfig10(Config):
    """Configuration that introduces the most basic dict validator."""

    def __init__(self, from_json_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 stderr_file: TextIO = sys.stderr) -> None:
        """Initialize the configuration.

        Args:
            from_json_text: Optional JSON text to parse directly.
            from_json_filename: Optional path to a JSON file to read.
            stderr_file: Stream used for user-facing diagnostics.
        """
        # The new thing here is that ordinary Python dicts are allowed as
        # configuration members. There are 2 of them, one for each mode
        # of ``DictKeysValidator`` we want to teach.
        #
        # The ``Config`` base class already checks dict members against the
        # default value's key set (saving you validators for many closed
        # dict shapes). You only list names in ``_unchecked_dicts`` when
        # you need a richer policy: optional keys, a different key rule
        # than the default, or to pair with per-value rules.
        # Here we opt out for both members so ``DictKeysValidator`` is
        # the only place that describes allowed keys. That is required for
        # ``feature_flags`` so optional ``debug``/``profiling`` keys that
        # are absent from the default are still valid JSON. For
        # ``port_assignments`` the base class's exact key match would
        # already have matched the plan; the opt-out is still used so
        # this example has one place (the ``ValidationPlan``) that
        # documents the two ``DictKeysValidator`` modes, not a split
        # between implicit base-class checking and a validator.
        self._unchecked_dicts: list[str] = ['feature_flags',
                                            'port_assignments']
        # ``feature_flags`` will be checked with mandatory + optional
        # keys: 'logging' and 'metrics' must be present, and a few
        # additional keys are also accepted.
        self.feature_flags: dict[str, bool] = {
            'logging': True,
            'metrics': True
        }
        # ``port_assignments`` will be checked with exact-shape keys:
        # only 'http' and 'https' are accepted, and both are mandatory.
        self.port_assignments: dict[str, int] = {
            'http': 80,
            'https': 443
        }
        super().__init__(from_json_data_text=from_json_text,
                         from_json_filename=from_json_filename,
                         stderr_file=stderr_file)

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Return the validation steps for this dict example."""
        _ = stderr_file
        # ``DictKeysValidator`` only inspects the *keys* of the dict.
        # It never looks at the values, so it pairs naturally with the
        # JSON shape: here the values are already ``bool`` and ``int``
        # by the time JSON parsing has finished, and that is good enough
        # for this example.
        #
        # First mode: mandatory keys plus a few optional ones.
        # ``allowed_keys`` lists the *additional* keys that are allowed
        # but not required. The total set of permitted keys is the
        # union of ``mandatory_keys`` and ``allowed_keys``.
        feature_flags_validator = DictKeysValidator(
            mandatory_keys=['logging', 'metrics'],
            allowed_keys=['debug', 'profiling']
        )
        # Second mode: only mandatory keys, exact shape.
        # Passing ``allowed_keys=None`` means "no optional keys", so the
        # dict must contain exactly the mandatory keys and nothing else.
        port_assignments_validator = DictKeysValidator(
            mandatory_keys=['http', 'https'],
            allowed_keys=None
        )
        return [MemberValidationStep(
                    member_names=['feature_flags'],
                    validator=feature_flags_validator),
                MemberValidationStep(
                    member_names=['port_assignments'],
                    validator=port_assignments_validator)]


def e10_dict_basic_validators_set(  # pylint: disable=duplicate-code
        set_values: SetValues, config_file: PathOrStr) -> None:
    """Create configuration, apply overrides, and store it.

    Args:
        set_values: Values that should differ from the defaults.
        config_file: Path where to write the configuration file.
    """
    config = ExampleConfig10()
    # The set command follows the same pattern as earlier examples:
    # start with defaults, apply only the requested overrides, and let
    # ``Config.write()`` validate everything before JSON is written.
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


def e10_dict_basic_validators_print(  # pylint: disable=duplicate-code
        config_file: PathOrStr) -> None:
    """Read a configuration file and show how the values are used.

    Args:
        config_file: Path to the configuration file to read.
    """
    try:
        config = ExampleConfig10(from_json_filename=config_file)
        print(f'Configuration read from {config_file}')
        print(f'Feature flags: {config.feature_flags}')
        print(f'Port assignments: {config.port_assignments}')
    except (InvalidConfiguration, InvalidConfigurationValue):
        pass  # Error already printed by the Config object.


# -----------------------------------------------------------------------------
# The rest of this file is the command line handling code.
# This is to be able to run the example from the command line,
# but it could be done in any other way, and is not part of what this example
# is trying to teach.
# -----------------------------------------------------------------------------

INPUT_SPECS = [
    InputSpec(name='feature_flags', single=False, value_type=bool,
              dict_kv=True),
    InputSpec(name='port_assignments', single=False, value_type=int,
              dict_kv=True)
]
"""Command line values that the example exposes for ``set``.

The ``dict_kv=True`` flag tells the shared command line helper that
each CLI token is a ``key=value`` pair. The value side is converted
using ``value_type``, and the whole option produces a flat dict, e.g.
``--feature-flags logging=true metrics=false debug=true``.
"""


def main(args: Optional[list[str]] = None) -> None:
    """Run the example command line interface.

    Args:
        args: Optional replacement for ``sys.argv[1:]``, mainly for tests.
    """
    cmd_line_handling(example_name='e10_dict_basic_validators',
                      input_specs=INPUT_SPECS,
                      set_command=e10_dict_basic_validators_set,
                      print_command=e10_dict_basic_validators_print,
                      args=args)


if __name__ == '__main__':
    main()
    sys.exit(0)
