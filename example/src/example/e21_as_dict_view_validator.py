#! /usr/local/bin/python3
"""Teach validation of a dict or object through one dict-shaped view.

Some applications use a small runtime object for one configuration member,
but the same data is naturally written to JSON as a dictionary. Sometimes
application code may also assign the dictionary form directly before writing
the configuration.

``AsDictViewValidator`` lets both representations use one dict-validation
policy. The example stores a retry policy as a ``RetryPolicy`` object at
runtime, accepts the same policy as a dict from the command line and JSON,
and validates both representations through the same dictionary view.

This is one possible shape for configuration member variables, and one of
the shapes where ``AsDictViewValidator`` is handy. It is not presented as
the only recommended shape for configuration members.
"""

# Copyright (c) 2026 Tom Björkholm
# MIT License

from typing import Optional, TextIO
import sys
from config_as_json import AsDictViewValidator, Config, DictKeysValidator, \
    DictRule, IntFloatValidator, InvalidConfiguration, \
    InvalidConfigurationValue, MemberValidationStep, ParseConverter, \
    PathOrStr, StrValidator, ValidationPlan, public_attrs_to_dict
from .cmd_line_handling import InputSpec, SetValues, cmd_line_handling


# pylint: disable-next=too-few-public-methods
class RetryPolicy:
    """Application runtime object for retry settings."""

    def __init__(self, mode: object = None, max_attempts: object = None,
                 backoff_seconds: object = None) -> None:
        """Initialize only the attributes that were supplied."""
        # The attributes are typed as object because values coming from JSON
        # have not yet been validated when the runtime object is created.
        # The validators below own the actual value policy.
        if mode is not None:
            self.mode: object = mode
        if max_attempts is not None:
            self.max_attempts: object = max_attempts
        if backoff_seconds is not None:
            self.backoff_seconds: object = backoff_seconds

    def describe(self) -> str:
        """Return a short human-readable retry policy description."""
        return f'{self.mode}, {self.max_attempts} attempts'


def retry_policy_from_dict(value: object) -> object:
    """Build a ``RetryPolicy`` from a parsed JSON dictionary.

    Args:
        value: Parsed JSON value for the retry policy member.

    Returns:
        A ``RetryPolicy`` when ``value`` is a dict, otherwise ``value``
        unchanged so the validator can report the invalid type.
    """
    # ``parse_converters()`` calls this after JSON parsing. JSON object
    # members arrive as dictionaries, and this example wants application
    # code to see a ``RetryPolicy`` object instead.
    if not isinstance(value, dict):
        # Returning the value unchanged gives ``AsDictViewValidator`` the
        # chance to print the normal "not a dict or RetryPolicy" diagnostic.
        return value
    policy = RetryPolicy()
    for key, item in value.items():
        # JSON object keys are strings. The guard keeps this converter robust
        # if it is called directly with a non-JSON dictionary in a test.
        if isinstance(key, str):
            setattr(policy, key, item)
    return policy


def retry_policy_to_dict(config: Config, policy: RetryPolicy,
                         stderr_file: TextIO) -> dict[str, object]:
    """Return the JSON dictionary form for one retry policy object."""
    # ``public_attrs_to_dict`` is the same simple projection used by the
    # validator. Reusing it keeps "what is the dict view?" consistent.
    view = public_attrs_to_dict(config, 'retry_policy', policy, stderr_file)
    result: dict[str, object] = {}
    for key, value in view.items():
        # The retry policy object uses normal attribute names, so all keys
        # should be strings and can safely become JSON object keys.
        assert isinstance(key, str)
        result[key] = value
    return result


def retry_policy_object(value: object) -> RetryPolicy:
    """Return ``value`` as a retry policy object."""
    # Consumer code in the print command wants one object shape. This helper
    # accepts both forms so the command stays focused on using the config.
    if isinstance(value, RetryPolicy):
        return value
    converted = retry_policy_from_dict(value)
    assert isinstance(converted, RetryPolicy)
    return converted


class ExampleConfig21(Config):
    """Configuration with one member that can be a dict or an object."""

    def __init__(self, from_json_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 stderr_file: TextIO = sys.stderr) -> None:
        """Initialize the configuration.

        Args:
            from_json_text: Optional JSON text to parse directly.
            from_json_filename: Optional path to a JSON file to read.
            stderr_file: Stream used for user-facing diagnostics.
        """
        # The default is deliberately the application runtime object form.
        # The member is typed as object because command-line overrides may
        # assign the dictionary form before ``Config.write()`` validates it.
        self.retry_policy: object = RetryPolicy(
            mode='fixed', max_attempts=3, backoff_seconds=30)
        # ``Config`` reads JSON, applies parse converters, and then runs the
        # validation plan. The default above is therefore validated too.
        super().__init__(from_json_data_text=from_json_text,
                         from_json_filename=from_json_filename,
                         stderr_file=stderr_file)

    def parse_converters(self) -> dict[str, ParseConverter]:
        """Convert parsed retry-policy dictionaries into runtime objects."""
        # This is the read-path half of the example: JSON stores a dict, but
        # application code receives a ``RetryPolicy`` object after parsing.
        return {'retry_policy': ParseConverter(result_type=RetryPolicy,
                                               func=retry_policy_from_dict,
                                               args={})}

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Return the validation plan for the retry policy."""
        _ = stderr_file
        # First validate the shape of the dictionary view. This catches
        # missing or unknown attributes before validating individual values.
        keys_validator = DictKeysValidator(
            mandatory_keys=['mode', 'max_attempts', 'backoff_seconds'])
        # Then define the per-key value policy. ``DictRule`` is the compact
        # shape consumed by ``DictForEachValidator`` inside
        # ``AsDictViewValidator``.
        mode_rule = DictRule(
            keys=['mode'],
            validators=[StrValidator(allowed_values=['fixed', 'exponential'],
                                     ignore_case=True, normalize=True)])
        attempts_rule = DictRule(
            keys=['max_attempts'],
            validators=[IntFloatValidator(min_value=1, max_value=10,
                                          allowed_values=None)])
        backoff_rule = DictRule(
            keys=['backoff_seconds'],
            validators=[IntFloatValidator(min_value=1, max_value=3600,
                                          allowed_values=None)])
        # ``AsDictViewValidator`` accepts either a real dict or a RetryPolicy.
        # RetryPolicy objects are projected with ``public_attrs_to_dict``.
        # The key validator runs first, then the per-key rules.
        retry_validator = AsDictViewValidator(
            non_dict_type=RetryPolicy,
            rules=[mode_rule, attempts_rule, backoff_rule],
            to_dict=public_attrs_to_dict, validators=[keys_validator])
        # A validation plan always names the config member and the validator
        # that owns that member's policy.
        return [MemberValidationStep(member_names=['retry_policy'],
                                     validator=retry_validator)]


def serialize_retry_policy(config: ExampleConfig21,
                           stderr_file: TextIO) -> None:
    """Convert the retry policy object to the dict form before writing."""
    # The validator can validate an object through a dict view, but JSON
    # writing still needs an actual JSON-serializable value.
    if isinstance(config.retry_policy, RetryPolicy):
        config.retry_policy = retry_policy_to_dict(
            config, config.retry_policy, stderr_file)


# pylint: disable=duplicate-code
def e21_as_dict_view_set(set_values: SetValues,
                         config_file: PathOrStr) -> None:
    """Create configuration, apply overrides, and store it.

    Args:
        set_values: Values that should differ from the defaults.
        config_file: Path where to write the configuration file.
    """
    # Start from the object-form default so the write path demonstrates that
    # an application may use objects internally.
    config = ExampleConfig21()
    for key, value in set_values.items():
        # Command-line parsing may provide the retry policy as a dict. That
        # is accepted because ``AsDictViewValidator`` supports both forms.
        if hasattr(config, key):
            setattr(config, key, value)
        else:
            raise ValueError(f'Invalid key: {key}')
    # Convert any remaining object-form policy to a JSON dictionary before
    # asking ``Config`` to write the file.
    serialize_retry_policy(config, sys.stderr)
    try:
        # ``write`` validates the current member value, so invalid command
        # line values are rejected before anything is stored.
        config.write(to_json_filename=config_file)
        print(f'Configuration written to {config_file}')
    except (InvalidConfiguration, InvalidConfigurationValue):
        pass  # Error already printed by the Config object.


def e21_as_dict_view_print(config_file: PathOrStr) -> None:
    """Read a configuration file and show how the values are used.

    Args:
        config_file: Path to the configuration file to read.
    """
    try:
        # On read, the JSON dict is converted by ``parse_converters()`` before
        # validation. Validation then projects the object back to a dict view.
        config = ExampleConfig21(from_json_filename=config_file)
        # The rest of the application can now use the runtime object shape.
        policy = retry_policy_object(config.retry_policy)
        print(f'Configuration read from {config_file}')
        print(f'Retry mode: {policy.mode}')
        print(f'Max attempts: {policy.max_attempts}')
        print(f'Backoff seconds: {policy.backoff_seconds}')
        print(f'Runtime policy object: {policy.describe()}')
    except (InvalidConfiguration, InvalidConfigurationValue):
        pass  # Error already printed by the Config object.


INPUT_SPECS = [
    # ``json_value=True`` lets the command-line helper parse one shell string
    # into the mixed-type dictionary used by the retry policy.
    InputSpec(name='retry_policy', single=True, value_type=str,
              json_value=True)]
"""Command line values that the example exposes for ``set``.

The retry policy is a mixed-type dictionary in JSON, so the command line
accepts it as one JSON value:

``--retry-policy '{"mode": "EXPONENTIAL", "max_attempts": 5,
"backoff_seconds": 60}'``
"""


def main(args: Optional[list[str]] = None) -> None:
    """Run the example command line interface.

    Args:
        args: Optional replacement for ``sys.argv[1:]``, mainly for tests.
    """
    # The common example command-line helper supplies the same "set" and
    # "print" workflow as the earlier teaching examples.
    cmd_line_handling(example_name='e21_as_dict_view_validator',
                      input_specs=INPUT_SPECS,
                      set_command=e21_as_dict_view_set,
                      print_command=e21_as_dict_view_print, args=args)


if __name__ == '__main__':
    main()
    sys.exit(0)
