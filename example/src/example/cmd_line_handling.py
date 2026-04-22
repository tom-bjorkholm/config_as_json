#! /usr/local/bin/python3
"""Create a minimal command line interface for example programs.

The examples in this repository are meant to teach configuration handling,
not command line parsing. This module therefore hides most ``argparse``
details behind a small helper that builds the same two subcommands for each
example:

- ``set`` writes a configuration file, optionally overriding defaults.
- ``print`` reads a configuration file and shows how values can be used.
"""

# Copyright (c) 2026 Tom Björkholm
# MIT License

import argparse
from enum import Enum
from typing import Callable, NamedTuple, Optional, cast
from config_as_json import PathOrStr, string_to_enum_best_match

type SingleValue = int | float | str | bool | Enum
type CfgValue = SingleValue | list[SingleValue]

type SetValues = dict[str, CfgValue]
""" Values to set in the configuration file.

    These are values for named members to change
    compared to the default configuration values
"""

type SetCommand = Callable[[SetValues, PathOrStr], None]
"""Command that writes configuration with selected values to a file.

Args:
    set_values: Values to change compared to the default configuration.
    config_file: Path to the file that should receive the configuration.
"""


type PrintCommand = Callable[[PathOrStr], None]
"""Command that prints values from a configuration file.

The configuration is read from a file, validated, and then shown to the
user.

Args:
    config_file: Path to the configuration file to read.
"""

type SingleValueTypes = type[int] | type[float] | type[str] | \
    type[bool] | type[Enum]


class InputSpec(NamedTuple):
    """Describe one configuration value exposed on the command line."""

    name: str
    """Name of the config member and also the flag name."""

    single: bool
    """True for a single value, False for a list of values."""

    value_type: SingleValueTypes
    """Python type that the command line text should be converted to."""


def _bool_from_text(text: str) -> bool:
    """Convert a case-insensitive boolean word to ``bool``.

    Args:
        text: Command line text for one boolean value.

    Returns:
        ``True`` or ``False``.

    Raises:
        argparse.ArgumentTypeError: The text is not ``true`` or ``false``.
    """
    lowered = text.lower()
    if lowered == 'true':
        return True
    if lowered == 'false':
        return False
    msg = "Expected 'true' or 'false'."
    raise argparse.ArgumentTypeError(msg)


def _enum_from_text(text: str, enum_type: type[Enum]) -> Enum:
    """Convert text to the best-matching enum member.

    Args:
        text: Command line text for one enum value.
        enum_type: Enum class that should be searched.

    Returns:
        The matching enum member.

    Raises:
        argparse.ArgumentTypeError: No enum member matched the text.
    """
    try:
        return string_to_enum_best_match(text, enum_type)
    except KeyError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc


def _value_parser(
        value_type: SingleValueTypes) -> Callable[[str], SingleValue]:
    """Return the text-to-value converter for one input specification.

    Args:
        value_type: Declared value type for one command line option.

    Returns:
        Function that converts one command line token to a Python value.
    """
    if value_type is str:
        return lambda text: text
    if value_type is int:
        return int
    if value_type is float:
        return float
    if value_type is bool:
        return _bool_from_text
    return lambda text: _enum_from_text(text, cast(type[Enum], value_type))


def _add_set_arguments(
        parser: argparse.ArgumentParser,
        input_specs: list[InputSpec]) -> None:
    """Add one ``--name`` style option for each configurable value.

    Args:
        parser: Parser for the ``set`` subcommand.
        input_specs: Values that should be accepted from the command line.
    """
    for input_spec in input_specs:
        argument_name = f'--{input_spec.name.replace("_", "-")}'
        if not input_spec.single:
            parser.add_argument(
                argument_name,
                dest=input_spec.name,
                type=_value_parser(input_spec.value_type),
                default=None,
                nargs='+',
                help=f'Set configuration value {input_spec.name}.'
            )
            continue
        parser.add_argument(
            argument_name,
            dest=input_spec.name,
            type=_value_parser(input_spec.value_type),
            default=None,
            help=f'Set configuration value {input_spec.name}.'
        )


def _set_values_from_args(parsed_args: argparse.Namespace,
                          input_specs: list[InputSpec]) -> SetValues:
    """Collect only the values that were explicitly set on the command line.

    Args:
        parsed_args: Parsed command line namespace.
        input_specs: Definitions of accepted value arguments.

    Returns:
        Dictionary with only the values that the user supplied.
    """
    set_values: SetValues = {}
    for input_spec in input_specs:
        value = getattr(parsed_args, input_spec.name)
        if value is None:
            continue
        set_values[input_spec.name] = cast(CfgValue, value)
    return set_values


def _create_argument_parser(
        example_name: str,
        input_specs: list[InputSpec]) -> argparse.ArgumentParser:
    """Build the command line parser for one example program.

    Args:
        example_name: Name shown in help output.
        input_specs: Value arguments accepted by the ``set`` subcommand.

    Returns:
        Configured top-level argument parser.
    """
    parser = argparse.ArgumentParser(prog=example_name)
    subparsers = parser.add_subparsers(dest='command')
    subparsers.required = True
    print_parser = subparsers.add_parser(
        'print',
        help='Read a configuration file and print the values.'
    )
    print_parser.add_argument(
        '-i',
        '--input',
        required=True,
        help='Configuration file to read.'
    )
    set_parser = subparsers.add_parser(
        'set',
        help='Write a configuration file, optionally overriding defaults.'
    )
    set_parser.add_argument(
        '-o',
        '--output',
        required=True,
        help='Configuration file to write.'
    )
    _add_set_arguments(set_parser, input_specs)
    return parser


def cmd_line_handling(example_name: str, input_specs: list[InputSpec],
                      set_command: SetCommand,
                      print_command: PrintCommand,
                      args: Optional[list[str]] = None) -> None:
    """Handle command line arguments for one example program.

    The helper converts command line text to the same Python types that the
    configuration class uses. That keeps each example focused on
    configuration values instead of on parser mechanics.

    Args:
        example_name: Name of the example program for help text.
        input_specs: Specifications of accepted ``set`` values.
        set_command: Command that writes configuration values to a file.
        print_command: Command that prints the values in a configuration file.
        args: Optional replacement for ``sys.argv[1:]``, mainly for tests.
    """
    parser = _create_argument_parser(example_name, input_specs)
    parsed_args = parser.parse_args(args)
    if parsed_args.command == 'print':
        print_command(parsed_args.input)
        return
    set_values = _set_values_from_args(parsed_args, input_specs)
    set_command(set_values, parsed_args.output)
