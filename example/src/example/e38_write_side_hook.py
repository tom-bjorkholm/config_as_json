#! /usr/local/bin/python3
"""Teach the write-side JSON conversion hook (``serialize_converters``).

The motivating problem
======================

Python's :mod:`json` encoder calls a custom encoder's ``default`` method
only for values that the encoder does not already know how to serialize.
A plain :class:`enum.Enum` is unknown to ``json.dumps`` and would reach
``default``, but :class:`enum.IntEnum` is a subclass of :class:`int`, and
``json.dumps`` therefore treats it as an integer before any custom code
ever sees it. There is no clean way to convert an ``IntEnum`` to its name
during ``json.dumps`` itself.

The library solves this problem with a *pre-serialization* hook. The
configuration object first assembles a plain Python data tree, the hook
walks that tree and replaces selected values with JSON-compatible ones,
and only then ``json.dumps`` runs.

This example shows two useful patterns:

1. Convert an ``IntEnum`` member to its symbolic name so the output stays
   human-friendly and the file remains stable across renumbering.
2. Convert a richer scalar (``pathlib.Path``) into a portable string.

When you write a config that uses these, also override
``parse_converters`` so the value can be read back into its original
Python type. The two hooks are designed to be used together.

Two kinds of selectors are demonstrated:

- A *recursive key selector* (a plain string such as ``'priority'``)
  matches every dictionary member with that exact name in data owned by
  this Config object. Use this when the same converter should apply
  wherever the key appears.
- An *absolute path selector* (a ``ConfigPath`` tuple such as
  ``('output_file',)``) targets one specific location in the tree. Use
  this when only one place should be converted. Path selectors also
  support a literal ``'['`` step to mean "every list element" or "every
  dictionary value" at that point, which is the right tool when the data
  contains lists of rich Python values.

The opposite of the write-side hook
===================================

The library also ships a *read-side* hook called ``parse_converters``.
It turns parsed JSON values into rich Python values when the
configuration is loaded. Together the two hooks let an application
treat configuration as native Python objects in memory while the file
on disk stays plain JSON.
"""

# Copyright (c) 2026 Tom Björkholm
# MIT License

# pylint: disable=duplicate-code

import sys
from enum import Enum, IntEnum
from pathlib import Path
from typing import Optional, TextIO, override
from config_as_json import Config, JsonType, PathOrStr, ValidationPlan, \
    ParseConverter, SerializeConverter, SerializeConverters
from .cmd_line_handling import InputSpec, SetValues, cmd_line_handling


class Priority(IntEnum):
    """Task priority modeled as an ``IntEnum``.

    ``IntEnum`` is a subclass of ``int``, which means ``json.dumps``
    treats it as an integer. This is precisely the case the write-side
    hook is designed to handle.
    """

    LOW = 1
    MEDIUM = 5
    HIGH = 9


class ReviewState(Enum):
    """Review state modeled as a plain ``Enum``.

    A plain ``Enum`` is not a subclass of ``int`` or ``str``, so the
    library's built-in fallback (Enum/IntEnum -> ``.name``) already
    works without an explicit converter. This member is included to
    contrast plain ``Enum`` with ``IntEnum``.
    """

    DRAFT = 'draft'
    READY = 'ready'
    PUBLISHED = 'published'


def _priority_to_name(value: object, *, path_text: str, stderr_file: TextIO,
                      **_extra: object) -> JsonType:
    """Convert a :class:`Priority` member to its symbolic name.

    A converter function receives the matched Python value plus three
    keyword arguments: ``path_text`` for diagnostics, ``stderr_file`` for
    user-facing messages, and any extra keyword arguments declared in the
    ``args`` field of the :class:`SerializeConverter`. Returning a
    JSON-compatible value (``str``, ``int``, ``float``, ``bool``,
    ``None``, ``list``, or ``dict``) is the converter's contract.

    The ``Optional[None]`` case never reaches a converter; ``None``
    always passes through unchanged so omit-when-None handling stays
    consistent.
    """
    _ = path_text, stderr_file
    assert isinstance(value, Priority), (
        f'Priority converter received a {type(value).__name__}; expected '
        'Priority')
    return value.name


def _path_to_posix(value: object, *, path_text: str, stderr_file: TextIO,
                   **_extra: object) -> JsonType:
    """Convert a :class:`pathlib.Path` into a portable POSIX string.

    Filesystem paths render differently on Windows and POSIX, so writing
    the POSIX form keeps the JSON portable. The matching parse converter
    turns the string back into a :class:`Path` on read.
    """
    _ = path_text, stderr_file
    assert isinstance(value, Path), (
        f'Path converter received a {type(value).__name__}; expected Path')
    return value.as_posix()


def _path_from_text(value: object) -> object:
    """Parse-side converter that turns a string back into a :class:`Path`."""
    assert isinstance(value, str)
    return Path(value)


class TaskConfig(Config):
    """Configuration that exercises the write-side conversion hook.

    The configuration models a small task tracker:

    - ``project`` is a plain string.
    - ``output_file`` is a :class:`pathlib.Path` and needs a converter
      because :class:`Path` is not a JSON-native type.
    - ``review_state`` is a plain ``Enum``. The library's built-in
      fallback for Enum/IntEnum members converts it to its symbolic
      ``.name`` automatically, so no explicit converter is needed.
    - ``priority`` is an ``IntEnum``. This is the motivating case for
      the hook: ``json.dumps`` would otherwise treat it as a plain
      integer because ``IntEnum`` is a subclass of ``int``.
    """

    def __init__(self, from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 stderr_file: TextIO = sys.stderr) -> None:
        """Initialize the example configuration with rich Python defaults."""
        self.project: str = 'config-as-json'
        self.output_file: Path = Path('reports/tasks.json')
        self.review_state: ReviewState = ReviewState.DRAFT
        self.priority: Priority = Priority.MEDIUM
        super().__init__(from_json_data_text=from_json_data_text,
                         from_json_filename=from_json_filename,
                         stderr_file=stderr_file)

    @override
    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Skip extra validation; the example is focused on serialization."""
        _ = stderr_file
        return []

    @override
    def serialize_converters(self) -> SerializeConverters:
        """Return the write-side conversion rules.

        Two kinds of selectors are used:

        - ``'priority'`` (plain string) is a recursive key selector that
          matches every dictionary member named ``priority`` inside data
          owned by this Config object. Here that is just the one member
          on the root, but the same selector would also match a nested
          dictionary that happens to contain a ``priority`` key.

        - ``('output_file',)`` is an absolute path selector that targets
          one specific location, namely the root-level ``output_file``
          key. Path selectors are the right tool when only one place
          should be converted.

        Returning the same key as both a recursive key selector and a
        path selector that ends in that key is a declaration error; the
        hook raises ``SerializeSelectorError`` in that case.
        """
        rules: SerializeConverters = {
            # Use ``value_type`` to enforce a Python type check before
            # the converter runs. The check raises
            # ``JsonWriteHookError`` with the actual path of the
            # offending value, which is much more helpful than a
            # ``TypeError`` from inside the converter.
            'priority': SerializeConverter(
                value_type=Priority, func=_priority_to_name, args={}),
            ('output_file',): SerializeConverter(
                value_type=Path, func=_path_to_posix, args={}),
        }
        return rules

    @override
    def parse_converters(self) -> dict[str, ParseConverter]:
        """Convert JSON values back into the rich Python types on read.

        The library helper ``self.get_converter_dict(EnumType)`` builds
        a ready-made converter that parses the symbolic name back into
        an enum member. For :class:`Path` we declare a small explicit
        converter.

        Parse converters apply per top-level key. They expect a scalar
        JSON value (string, int, bool, ...) and do not auto-recurse
        into lists or dicts. If your configuration stores a list of
        ``Enum`` values, the typical pattern is to wrap each element in
        a small nested ``Config`` (see ``e34_list_nested_configs``);
        each nested element then declares its own
        ``serialize_converters`` and ``parse_converters``.
        """
        return {
            'output_file': ParseConverter(
                result_type=Path, func=_path_from_text, args={}),
            'review_state': self.get_converter_dict(ReviewState),
            'priority': self.get_converter_dict(Priority),
        }


def e38_write_side_hook_set(set_values: SetValues,
                            config_file: PathOrStr) -> None:
    """Apply CLI overrides to defaults and write the configuration.

    The command line helper produces ready-made Python values: a
    :class:`Priority` ``IntEnum`` for ``priority``, a list of
    ``Priority`` members for ``priorities``, and so on. The set command
    just assigns them; the write-side hook does the conversion from
    Python ``IntEnum`` to JSON ``str`` later.

    Args:
        set_values: Values that should differ from the defaults.
        config_file: Path where to write the configuration file.
    """
    config = TaskConfig()
    for key, value in set_values.items():
        if key == 'project':
            assert isinstance(value, str)
            config.project = value
        elif key == 'output_file':
            assert isinstance(value, str)
            config.output_file = Path(value)
        elif key == 'review_state':
            assert isinstance(value, ReviewState)
            config.review_state = value
        elif key == 'priority':
            assert isinstance(value, Priority)
            config.priority = value
        else:
            raise ValueError(f'Invalid key: {key}')
    config.write(to_json_filename=config_file)
    print(f'Configuration written to {config_file}')


def e38_write_side_hook_print(config_file: PathOrStr) -> None:
    """Read a configuration file and print the rich Python values.

    Args:
        config_file: Path to the configuration file to read.
    """
    config = TaskConfig(from_json_filename=config_file)
    print(f'Configuration read from {config_file}')
    print(f'Project: {config.project}')
    print(f'Output file: {config.output_file}')
    print(f'Review state: {config.review_state.name}')
    # The numeric value of an IntEnum is still accessible after read.
    # That is what makes IntEnum awkward for json.dumps in the first place.
    print(f'Priority: {config.priority.name} '
          f'(numeric value {int(config.priority)})')


INPUT_SPECS = [
    InputSpec(name='project', single=True, value_type=str),
    InputSpec(name='output_file', single=True, value_type=str),
    InputSpec(name='review_state', single=True, value_type=ReviewState),
    InputSpec(name='priority', single=True, value_type=Priority),
]
"""Command line values that the example exposes for ``set``."""


def main(args: Optional[list[str]] = None) -> None:
    """Run the example command line interface."""
    cmd_line_handling(example_name='e38_write_side_hook',
                      input_specs=INPUT_SPECS,
                      set_command=e38_write_side_hook_set,
                      print_command=e38_write_side_hook_print, args=args)


if __name__ == '__main__':
    main()
    sys.exit(0)


# A direct usage hint: the converted JSON for the default configuration
# above looks like:
#
# {
#     "output_file": "reports/tasks.json",
#     "priority": "MEDIUM",
#     "project": "config-as-json",
#     "review_state": "DRAFT"
# }
#
# Without the write-side hook the ``priority`` value would render as an
# integer (``5``), and ``output_file`` would raise a ``TypeError`` from
# inside ``json.dumps`` because ``Path`` is not JSON-native.
