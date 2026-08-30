#! /usr/local/bin/python3
"""Show how to validate a relation between two list-like values.

``ListRelationValidator`` validates that two sequence values have a selected
relation. The values may come directly from configuration members, or one or
both sides may be projected from the whole configuration.

This example has two stored members:

- ``declared_routes`` lists the routes that the application should expose.
- ``route_handlers`` maps route names to handler names.

The important rule is that the route names on both sides must match as sets:
every declared route needs one handler, and every handler key must correspond
to a declared route.

The second side is projected from the dictionary keys of ``route_handlers``.
The projector returns a tuple to show that relation validation accepts
sequence values other than ``list`` objects. Text and binary values such as
``str``, ``bytes``, and ``bytearray`` are rejected because comparing them as
character or byte sequences would usually be a programming error.
"""

# Copyright (c) 2026 Tom Björkholm
# MIT License

import sys
from typing import Optional, TextIO, cast
from config_as_json import Config, DictKeyValueTypesValidator, \
    InvalidConfiguration, InvalidConfigurationValue, ListIsOrderedValidator, \
    ListRelationKind, ListRelationValidator, MemberValidationStep, PathOrStr, \
    ValidationPlan, WholeConfigValidationStep
from .cmd_line_handling import InputSpec, SetValues, cmd_line_handling


def project_handler_routes(config: Config, stderr_file: TextIO) -> object:
    """Return route names that have configured handlers.

    Args:
        config: The complete Config object to project from.
        stderr_file: Diagnostic stream. It is not needed here because
            ``ListRelationValidator`` owns the relation diagnostic.

    Returns:
        A tuple containing the keys from ``route_handlers``.
    """
    _ = stderr_file
    route_config = cast(ExampleConfig24, config)
    return tuple(route_config.route_handlers.keys())


class ExampleConfig24(Config):
    """Configuration using a list relation validator."""

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
        # Route handler keys are application data, not a closed schema from
        # the default keys. The validator owns the key/value policy.
        self._unchecked_dicts: list[str] = ['route_handlers']
        self.declared_routes: list[str] = ['api', 'admin']
        self.route_handlers: dict[str, str] = {
            'api': 'api_handler',
            'admin': 'admin_handler'}
        super().__init__(from_json_data_text=from_json_text,
                         from_json_filename=from_json_filename,
                         stderr_file=stderr_file, member_name=member_name)

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Return the ordered validation steps for this example."""
        _ = stderr_file
        # The relation below intentionally ignores duplicates, because
        # SET_EQUAL is about distinct values. Keep the duplicate rule explicit
        # with the normal list validator, where the diagnostic can point to
        # the duplicate index.
        declared_routes_validator = ListIsOrderedValidator(str,
                                                           is_ordered=False,
                                                           unique_values=True)
        # The dictionary is open-ended, but it is still uniform: every key and
        # every value must be a string.
        handlers_validator = DictKeyValueTypesValidator(key_type=str,
                                                        value_type=str)
        # The stored list is compared with a projected tuple of dictionary
        # keys. The pseudo-member name is used only in diagnostics.
        relation_validator = ListRelationValidator(
            kind=ListRelationKind.SET_EQUAL, member_a_name='declared_routes',
            member_b_name='route_handler_names',
            b_projector=project_handler_routes)
        return [
            MemberValidationStep(member_names=['declared_routes'],
                                 validator=declared_routes_validator),
            MemberValidationStep(member_names=['route_handlers'],
                                 validator=handlers_validator),
            WholeConfigValidationStep(validator=relation_validator)
        ]


# pylint: disable=duplicate-code
def e24_list_relation_set(set_values: SetValues,
                          config_file: PathOrStr) -> None:
    """Create configuration, apply overrides, and store it.

    Args:
        set_values: Values that should differ from the defaults.
        config_file: Path where to write the configuration file.
    """
    config = ExampleConfig24()
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
def e24_list_relation_print(config_file: PathOrStr) -> None:
    """Read a configuration file and show how the values are used.

    Args:
        config_file: Path to the configuration file to read.
    """
    try:
        config = ExampleConfig24(from_json_filename=config_file)
        print(f'Configuration read from {config_file}')
        print(f'Declared routes: {config.declared_routes}')
        print(f'Route handlers: {config.route_handlers}')
        handler_routes = project_handler_routes(config, sys.stderr)
        print(f'Projected handler routes: {handler_routes}')
    except (InvalidConfiguration, InvalidConfigurationValue):
        pass  # Error already printed by the Config object.


INPUT_SPECS = [
    InputSpec(name='declared_routes', single=False, value_type=str),
    InputSpec(name='route_handlers', single=False, value_type=str,
              dict_kv=True)
]
"""Command line values that the example exposes for ``set``.

``declared_routes`` accepts a list of route names:

``--declared-routes api admin``

``route_handlers`` accepts key/value tokens:

``--route-handlers api=api_handler admin=admin_handler``
"""


def main(args: Optional[list[str]] = None) -> None:
    """Run the example command line interface.

    Args:
        args: Optional replacement for ``sys.argv[1:]``, mainly for tests.
    """
    cmd_line_handling(example_name='e24_list_relation_validator',
                      input_specs=INPUT_SPECS,
                      set_command=e24_list_relation_set,
                      print_command=e24_list_relation_print, args=args)


if __name__ == '__main__':
    main()
    sys.exit(0)
