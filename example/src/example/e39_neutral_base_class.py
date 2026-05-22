#! /usr/local/bin/python3
"""Teach configuration that bridges a framework-neutral data class.

The teaching story
==================

Some applications already work with a framework-neutral data class that
defines a configuration shape. The data class is intentionally not tied
to ``config_as_json``; it could equally well be consumed by a different
serialization library or by application code that has no serialization
at all. The motivating use is a bridge: keep the neutral data class as
the source of defaults and use it for in-memory passing, while a small
bridge class adds the ``Config`` lifecycle (JSON reading and writing,
validation, and nested-config plumbing).

The example uses three neutral classes:

- ``NSubA`` is a leaf section with no constructor arguments.
- ``NSubB`` is a leaf section with optional argument-driven defaults.
- ``NConfigEager`` is the top-level neutral class. Its constructor takes
  required arguments. It eagerly creates non-``None`` nested neutral
  defaults for ``suba`` and ``subb``.

For each neutral class there is a 1:1 bridge subclass that inherits both
from the neutral class and from :class:`config_as_json.Config`:
``MySubA``, ``MySubB``, and ``MyConfigEager``. The leaf bridges use the
familiar multiple-inheritance pattern (``e04_third_party_class`` shows
the same pattern for a flat third-party class). The top-level bridge
demonstrates the case where the neutral constructor requires arguments
that the bridge does not duplicate.

Two library mechanisms drive the bridge
=======================================

1. ``Config.copy_initial_data(source, target)`` copies public attributes
   from a neutral source (plain object, dataclass, or mapping) onto a
   ``Config`` target. The bridge calls this in its ``__init__`` to seed
   the bridge's schema from a supplied neutral instance.

2. The library automatically auto-wraps nested member defaults inside
   ``Config.__init__``. When a member is declared as a nested config and
   the default value is a neutral instance (not yet the declared bridge
   type), the library constructs a fresh bridge object and copies the
   neutral's public attributes onto it. This is what turns the eager
   non-``None`` defaults of ``NConfigEager`` into ``MySubA`` /
   ``MySubB`` instances in the bridge's memory.

The auto-wrap pass is recursive: a nested bridge that contains its own
nested neutrals is wrapped at every level. The pass leaves already-wrapped
values, ``None`` (for ``OPTIONAL_MEMBER``), and unrelated scalar members
unchanged.

The two flow variants the example exercises
===========================================

The ``set`` command builds an ``NConfigEager`` instance from the command
line, hands it to ``MyConfigEager`` via the ``neutral`` keyword, and
writes the configuration to a file. Because the neutral instance owns
the defaults, the bridge stays small.

The ``print`` command reads the configuration file back into
``MyConfigEager`` using the bridge's hard-coded default neutral instance
to establish the schema, and then prints the values.
"""

# Copyright (c) 2026 Tom Björkholm
# MIT License

# pylint: disable=duplicate-code

import sys
from typing import Optional, TextIO, cast, override
from config_as_json import Config, ConfigNesting, ConfigNestingKind, \
    NestedConfigs, PathOrStr, ValidationPlan
from .cmd_line_handling import InputSpec, SetValues, cmd_line_handling


# ----------------------------------------------------------------------------
# The neutral data classes. Imagine that these come from a framework-neutral
# library that the application also uses for non-config purposes.
# ----------------------------------------------------------------------------


class NSubA:  # pylint: disable=too-few-public-methods
    """Framework-neutral section A.

    The constructor takes no required arguments, so the bridge can call
    ``NSubA.__init__(self)`` directly in the simple multiple-inheritance
    pattern that ``MySubA`` uses below.
    """

    def __init__(self) -> None:
        """Initialize section A with neutral defaults."""
        # Each instance attribute is one public configuration value. The
        # bridge inherits these names verbatim, so the bridge's schema is
        # exactly the neutral's schema.
        self.a1param: str = 'aa'
        self.a2param: int = 4
        self.a3param: Optional[str] = None


class NSubB:  # pylint: disable=too-few-public-methods
    """Framework-neutral section B with argument-driven defaults.

    Even when a neutral class accepts arguments, the bridge can still use
    the multiple-inheritance pattern as long as every argument has a
    default value. ``NSubB`` keeps that contract; ``MySubB`` therefore
    looks just like ``MySubA``.
    """

    def __init__(self, b1param: bool = False, b3param: int = 1) -> None:
        """Initialize section B with optional argument-driven defaults."""
        self.b1param: bool = b1param
        self.b2param: Optional[str] = 'bbb'
        self.b3param: int = b3param


class NConfigEager:  # pylint: disable=too-few-public-methods
    """Framework-neutral top-level config with eager nested defaults.

    Two properties of this class make the simple multiple-inheritance
    pattern awkward at the top level:

    - The constructor requires arguments (``c1``, ``b1p``, ``b3p``) that
      callers must always supply. The bridge cannot call
      ``NConfigEager.__init__(self)`` with no arguments to establish the
      schema.
    - The nested members default to real instances of the neutral leaf
      classes, not to ``None``. The library's auto-wrap pass is what
      converts those instances to the matching bridge types.

    The bridge therefore uses ``Config.copy_initial_data`` to seed the
    schema from a supplied neutral instance and leaves the nested-type
    conversion to the auto-wrap pass.
    """

    def __init__(self, c1: str, b1p: bool, b3p: int) -> None:
        """Initialize the neutral top-level config from required args."""
        # The required arguments determine the eager nested instances
        # that the application wants to write to the configuration file.
        self.c1: str = c1
        self.suba: Optional[NSubA] = NSubA()
        self.subb: Optional[NSubB] = NSubB(b1param=b1p, b3param=b3p)


# ----------------------------------------------------------------------------
# The bridge classes. Each one combines a neutral class with Config.
# ----------------------------------------------------------------------------


class MySubA(NSubA, Config):
    """Bridge for ``NSubA``: same shape, plus the ``Config`` lifecycle.

    This is the same multiple-inheritance pattern as ``e04`` uses for a
    flat third-party class. The neutral ``__init__`` is called first to
    create the public attributes, and ``Config.__init__`` then runs the
    usual schema check, validation, and JSON reading.
    """

    def __init__(self, from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 stderr_file: TextIO = sys.stderr) -> None:
        """Construct the bridge for section A."""
        # The neutral base class creates the public attributes that make
        # up the configuration schema for this bridge.
        NSubA.__init__(self)
        # Config.__init__ inspects ``vars(self)`` to learn the schema,
        # reads JSON if any was supplied, validates, and so on.
        Config.__init__(self, from_json_data_text=from_json_data_text,
                        from_json_filename=from_json_filename,
                        stderr_file=stderr_file)

    @override
    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Return an empty validation plan for this teaching bridge."""
        _ = stderr_file
        return []


class MySubB(NSubB, Config):
    """Bridge for ``NSubB``: same pattern as ``MySubA``."""

    def __init__(self, from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 stderr_file: TextIO = sys.stderr) -> None:
        """Construct the bridge for section B using neutral defaults."""
        # The neutral arguments have defaults, so the bridge does not
        # need to duplicate them and can still call ``NSubB.__init__``
        # without arguments.
        NSubB.__init__(self)
        Config.__init__(self, from_json_data_text=from_json_data_text,
                        from_json_filename=from_json_filename,
                        stderr_file=stderr_file)

    @override
    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Return an empty validation plan for this teaching bridge."""
        _ = stderr_file
        return []


class MyConfigEager(NConfigEager, Config):
    """Bridge for ``NConfigEager`` that seeds defaults from a neutral.

    The application owns the construction of the neutral instance.
    Application code typically writes something like::

        neutral = NConfigEager('hello', True, 4)
        cfg = MyConfigEager(neutral=neutral)
        cfg.write('example.cfg')

    The bridge does not call ``NConfigEager.__init__`` because that
    constructor requires arguments the bridge does not duplicate.
    ``Config.copy_initial_data`` is the small library helper that copies
    every public attribute from the neutral instance onto ``self`` so
    that ``Config.__init__`` then sees the right schema.
    """

    # pylint: disable-next=super-init-not-called
    def __init__(self, *, neutral: Optional[NConfigEager] = None,
                 from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 stderr_file: TextIO = sys.stderr) -> None:
        """Construct the bridge from a supplied or default neutral.

        ``NConfigEager.__init__`` is intentionally not invoked here
        because that constructor requires arguments the bridge does not
        duplicate. ``Config.copy_initial_data`` establishes the schema
        instead, using the supplied neutral instance.
        """
        # When no neutral instance is supplied the bridge falls back to
        # its own hard-coded defaults. That keeps reading from a file
        # work without forcing every caller to build a neutral first.
        if neutral is None:
            neutral = NConfigEager(c1='example', b1p=False, b3p=1)
        # ``copy_initial_data`` copies the neutral's public attributes
        # onto ``self``. Nested members come across as their neutral
        # types (NSubA, NSubB); the auto-wrap pass inside
        # ``Config.__init__`` turns them into MySubA / MySubB.
        Config.copy_initial_data(neutral, self)
        Config.__init__(self, from_json_data_text=from_json_data_text,
                        from_json_filename=from_json_filename,
                        stderr_file=stderr_file)

    @override
    def nested_configs(self) -> NestedConfigs:
        """Return nested Config declarations for the eager bridge.

        The two nested members come from ``NConfigEager``. The bridge
        declares each one as an ``OPTIONAL_MEMBER`` so that explicit
        JSON ``null`` and absence both map to ``None`` on read.
        """
        return {
            'suba': ConfigNesting(kind=ConfigNestingKind.OPTIONAL_MEMBER,
                                  config_type=MySubA),
            'subb': ConfigNesting(kind=ConfigNestingKind.OPTIONAL_MEMBER,
                                  config_type=MySubB)
        }

    @override
    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Return an empty validation plan for this teaching bridge."""
        _ = stderr_file
        return []


# ----------------------------------------------------------------------------
# The set and print commands. These are intentionally short; the example is
# focused on the bridge pattern, not on command-line ergonomics.
# ----------------------------------------------------------------------------


def _neutral_from_set_values(set_values: SetValues) -> NConfigEager:
    """Build the application's neutral instance from CLI overrides.

    Args:
        set_values: Values supplied on the command line.

    Returns:
        One ``NConfigEager`` whose constructor arguments come from the
        overrides, falling back to ``c1='example'``, ``b1p=False``,
        ``b3p=1`` when nothing was supplied.
    """
    c1_value = set_values.get('c1', 'example')
    b1p_value = set_values.get('b1p', False)
    b3p_value = set_values.get('b3p', 1)
    assert isinstance(c1_value, str)
    assert isinstance(b1p_value, bool)
    assert isinstance(b3p_value, int)
    return NConfigEager(c1=c1_value, b1p=b1p_value, b3p=b3p_value)


def e39_neutral_base_class_set(set_values: SetValues,
                               config_file: PathOrStr) -> None:
    """Build a neutral instance and write the bridge configuration.

    Args:
        set_values: Values supplied on the command line.
        config_file: Destination file for the configuration JSON.
    """
    # The application owns the neutral instance, the bridge just adapts
    # it to JSON. The auto-wrap pass turns ``suba`` and ``subb`` into
    # the bridge types behind the scenes.
    neutral = _neutral_from_set_values(set_values)
    config = MyConfigEager(neutral=neutral)
    config.write(to_json_filename=config_file)
    print(f'Configuration written to {config_file}')


def _print_section_a(suba: Optional[MySubA]) -> None:
    """Print one optional section A member."""
    if suba is None:
        print('suba: not configured')
        return
    print(f'suba.a1param: {suba.a1param}')
    print(f'suba.a2param: {suba.a2param}')
    print(f'suba.a3param: {suba.a3param}')


def _print_section_b(subb: Optional[MySubB]) -> None:
    """Print one optional section B member."""
    if subb is None:
        print('subb: not configured')
        return
    print(f'subb.b1param: {subb.b1param}')
    print(f'subb.b2param: {subb.b2param}')
    print(f'subb.b3param: {subb.b3param}')


def e39_neutral_base_class_print(config_file: PathOrStr) -> None:
    """Read the configuration file and print the bridge values.

    Args:
        config_file: Source file for the configuration JSON.
    """
    config = MyConfigEager(from_json_filename=config_file)
    print(f'Configuration read from {config_file}')
    print(f'c1: {config.c1}')
    # The static type of the inherited nested members is the neutral
    # type (Optional[NSubA]), but at runtime the auto-wrap pass has
    # replaced them with the declared bridge type. The cast lines up
    # the static type with the documented runtime type so the print
    # helpers can use the bridge attributes directly.
    _print_section_a(cast(Optional[MySubA], config.suba))
    _print_section_b(cast(Optional[MySubB], config.subb))


INPUT_SPECS = [
    InputSpec(name='c1', single=True, value_type=str),
    InputSpec(name='b1p', single=True, value_type=bool),
    InputSpec(name='b3p', single=True, value_type=int)
]
"""Command-line overrides for the neutral constructor arguments."""


def main(args: Optional[list[str]] = None) -> None:
    """Run the example command line interface.

    Args:
        args: Optional replacement for ``sys.argv[1:]``, mainly for tests.
    """
    cmd_line_handling(example_name='e39_neutral_base_class',
                      input_specs=INPUT_SPECS,
                      set_command=e39_neutral_base_class_set,
                      print_command=e39_neutral_base_class_print, args=args)


if __name__ == '__main__':
    main()
    sys.exit(0)
