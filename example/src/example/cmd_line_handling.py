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
import json
from enum import Enum
from typing import Callable, Mapping, NamedTuple, Optional, Sequence, cast
from config_as_json import JsonType, PathOrStr, string_to_enum_best_match

type SingleValue = int | float | str | bool | Enum
type CfgValue = SingleValue | Sequence[SingleValue] | \
    Sequence[Sequence[SingleValue]] | \
    Mapping[str, SingleValue] | JsonType
""" One value that a command line option can produce.

    A value is either one scalar, a sequence of scalars, a sequence of
    sequences of scalars (for ``nested=True``), a flat mapping from str
    to scalar (for ``dict_kv=True``), or any JSON-shaped value (for
    ``json_value=True``). The list arms use ``Sequence`` (rather than
    ``list``) so that dict literals such as ``{'k': [1, 2, 3]}`` can be
    assigned to ``SetValues`` without triggering invariant-generic
    errors.
"""

type SetValues = dict[str, CfgValue]
""" Values to set in the configuration file.

    These are values for named members to change
    compared to the default configuration values.
    A value may be a single scalar, a sequence of scalars, a sequence of
    sequences of scalars (for ``nested`` command line inputs), a flat
    mapping from str to scalar (for ``dict_kv`` command line inputs),
    or any JSON-shaped value (for ``json_value`` command line inputs).
"""

NESTED_LIST_SEPARATOR = ','
"""Separator used between scalar values inside one nested CLI token."""

DICT_KV_SEPARATOR = '='
"""Separator between key and value inside one ``dict_kv`` CLI token."""

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

    nested: bool = False
    """True if each list element is itself a list of ``value_type`` values.

    When ``nested`` is True the ``single`` field must be False. Each
    command line token is then parsed as a list of values separated by
    ``NESTED_LIST_SEPARATOR``, so the whole option produces a list of
    lists of ``value_type`` values.
    """

    dict_kv: bool = False
    """True if the option accepts ``key=value`` tokens for a flat dict.

    When ``dict_kv`` is True the ``single`` and ``nested`` fields must
    be False. Each command line token is then parsed as ``key=value``,
    where ``value`` is converted using ``value_type``. The whole option
    produces a ``dict[str, value_type]``. This is the dict-valued
    counterpart of the plain list option.
    """

    json_value: bool = False
    """True if the option accepts one JSON-encoded token.

    When ``json_value`` is True the ``single`` field must be True and
    the ``nested`` and ``dict_kv`` fields must be False. The single
    command line token is then parsed with ``json.loads``. This is used
    for deeply nested configuration members where reinventing more
    separators stops teaching anything; the honest CLI input at that
    nesting level is JSON. ``value_type`` is ignored for this flavour.
    """


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


def _nested_value_parser(value_type: SingleValueTypes,
                         separator: str = NESTED_LIST_SEPARATOR
                         ) -> Callable[[str], list[SingleValue]]:
    """Return a converter that turns one CLI token into a list of values.

    The returned converter splits the token on ``separator`` and converts
    each part using the scalar converter for ``value_type``. It is used
    when ``InputSpec.nested`` is True to let one command line option
    accept a list of lists: every CLI token becomes one inner list.

    Args:
        value_type: Declared value type for the inner list elements.
        separator: Character used to split one CLI token into elements.

    Returns:
        Function that converts one command line token to a list of values.
    """
    inner = _value_parser(value_type)

    def parse_nested_token(text: str) -> list[SingleValue]:
        """Split one CLI token and convert each part to ``value_type``."""
        return [inner(part) for part in text.split(separator)]

    return parse_nested_token


def _dict_kv_token_parser(value_type: SingleValueTypes,
                          separator: str = DICT_KV_SEPARATOR
                          ) -> Callable[[str], tuple[str, SingleValue]]:
    """Return a converter that turns one ``key=value`` token into a pair.

    The returned converter splits the token on the first occurrence of
    ``separator`` and converts the value part using the scalar converter
    for ``value_type``. The key part is always returned as a ``str``.

    Args:
        value_type: Declared value type for the dict values.
        separator: Character used to split one CLI token into key and
            value.

    Returns:
        Function that converts one command line token to a ``(key, value)``
        pair. The full dict is assembled from these pairs by
        ``_set_values_from_args``.

    Raises:
        argparse.ArgumentTypeError: The token does not contain
            ``separator``.
    """
    inner = _value_parser(value_type)

    def parse_kv_token(text: str) -> tuple[str, SingleValue]:
        """Split one CLI token into key and converted value."""
        if separator not in text:
            msg = f"Expected '<key>{separator}<value>'."
            raise argparse.ArgumentTypeError(msg)
        key, value_text = text.split(separator, 1)
        return key, inner(value_text)

    return parse_kv_token


def _json_token_parser() -> Callable[[str], JsonType]:
    """Return a converter that parses one CLI token as JSON.

    Returns:
        Function that converts one command line token to the matching
        Python value via :func:`json.loads`.

    Raises:
        argparse.ArgumentTypeError: The token is not valid JSON.
    """

    def parse_json_token(text: str) -> JsonType:
        """Parse one CLI token as a JSON document."""
        try:
            return cast(JsonType, json.loads(text))
        except json.JSONDecodeError as exc:
            raise argparse.ArgumentTypeError(str(exc)) from exc

    return parse_json_token


def _check_input_spec_flag_combination(input_spec: InputSpec) -> None:
    """Validate the combination of boolean flags on one input spec.

    Raises:
        ValueError: If ``nested``, ``dict_kv``, or ``json_value`` are
            combined in an unsupported way with each other or with
            ``single``.
    """
    flags = (input_spec.nested, input_spec.dict_kv, input_spec.json_value)
    if sum(1 for f in flags if f) > 1:
        msg = 'InputSpec flags nested, dict_kv, and json_value are '
        msg += 'mutually exclusive.'
        raise ValueError(msg)
    if input_spec.nested and input_spec.single:
        msg = 'InputSpec.nested requires InputSpec.single to be False.'
        raise ValueError(msg)
    if input_spec.dict_kv and input_spec.single:
        msg = 'InputSpec.dict_kv requires InputSpec.single to be False.'
        raise ValueError(msg)
    if input_spec.json_value and not input_spec.single:
        msg = 'InputSpec.json_value requires InputSpec.single to be True.'
        raise ValueError(msg)


def _token_parser(input_spec: InputSpec) -> Callable[[str], object]:
    """Return the argparse ``type`` callable for one input specification.

    Args:
        input_spec: Specification of one command line value.

    Returns:
        Function that converts one command line token to the configured
        Python value. For a nested list spec the callable returns one
        inner list, for a ``dict_kv`` spec one ``(key, value)`` pair, for
        a ``json_value`` spec the parsed JSON value, and otherwise one
        scalar value.

    Raises:
        ValueError: If the specification combines ``single``, ``nested``,
            ``dict_kv``, or ``json_value`` in an unsupported way.
    """
    _check_input_spec_flag_combination(input_spec)
    if input_spec.nested:
        return _nested_value_parser(input_spec.value_type)
    if input_spec.dict_kv:
        return _dict_kv_token_parser(input_spec.value_type)
    if input_spec.json_value:
        return _json_token_parser()
    return _value_parser(input_spec.value_type)


def _add_set_arguments(parser: argparse.ArgumentParser,
                       input_specs: list[InputSpec]) -> None:
    """Add one ``--name`` style option for each configurable value.

    Args:
        parser: Parser for the ``set`` subcommand.
        input_specs: Values that should be accepted from the command line.
    """
    for input_spec in input_specs:
        argument_name = f'--{input_spec.name.replace("_", "-")}'
        token_parser = _token_parser(input_spec)
        if not input_spec.single:
            parser.add_argument(
                argument_name, dest=input_spec.name, type=token_parser,
                default=None, nargs='+',
                help=f'Set configuration value {input_spec.name}.')
            continue
        parser.add_argument(argument_name, dest=input_spec.name,
                            type=token_parser, default=None,
                            help=f'Set configuration value {input_spec.name}.')


def _coerce_input_value(input_spec: InputSpec, value: object) -> CfgValue:
    """Reshape one parsed argparse value into its final ``CfgValue`` form.

    For a ``dict_kv`` spec argparse has produced a list of ``(key, value)``
    pairs (one per CLI token). The pairs are assembled into a dict here.
    For all other spec flavours the value is already in its final shape
    and is only re-typed for the ``SetValues`` dictionary.

    Args:
        input_spec: Specification of one command line value.
        value: The raw value as produced by argparse.

    Returns:
        The value in the shape expected by the example's ``set`` helper.
    """
    if input_spec.dict_kv:
        pairs = cast(list[tuple[str, SingleValue]], value)
        return dict(pairs)
    return cast(CfgValue, value)


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
        set_values[input_spec.name] = _coerce_input_value(input_spec, value)
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
        'print', help='Read a configuration file and print the values.')
    print_parser.add_argument('-i', '--input', required=True,
                              help='Configuration file to read.')
    set_parser = subparsers.add_parser(
        'set',
        help='Write a configuration file, optionally overriding defaults.')
    set_parser.add_argument('-o', '--output', required=True,
                            help='Configuration file to write.')
    _add_set_arguments(set_parser, input_specs)
    return parser


def cmd_line_handling(example_name: str, input_specs: list[InputSpec],
                      set_command: SetCommand, print_command: PrintCommand,
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
