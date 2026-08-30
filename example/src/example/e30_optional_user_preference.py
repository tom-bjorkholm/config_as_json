#! /usr/local/bin/python3
"""Show how to let runtime defaults stand until a user has an opinion.

Most configuration members have a concrete default value. When those members
are written to JSON, the default value is written too. Sometimes that is not
what the application wants. A missing value may instead mean "the user has no
opinion; let this version of the application decide".

This example has two such members:

- ``author_note`` is an optional string. If it is ``None``, the report has no
  note.
- ``palette`` is an optional enum. If it is ``None``, the application chooses
  the palette it currently considers best.

The important method is ``_omit_none_from_json``. It tells ``Config`` that
these top-level members may be absent from input JSON, and that they should be
omitted from output JSON while their value is ``None``.
"""

# Copyright (c) 2026 Tom Björkholm
# MIT License

from enum import Enum, auto
from typing import Optional, TextIO, override
import sys
from config_as_json import Config, PathOrStr, ValidationPlan, \
    ParseConverter
from .cmd_line_handling import InputSpec, SetValues, cmd_line_handling


class DeliveryFormat(Enum):
    """Select the report file format."""

    HTML = auto()
    TEXT = auto()


class Palette(Enum):
    """Select a color palette for generated reports."""

    ACCESSIBLE = auto()
    PRINT = auto()
    VIVID = auto()


class ExampleConfig30(Config):
    """Configuration with optional user preference members."""

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
        # These two members are ordinary configuration values. They always
        # have a value, so they are always written to JSON.
        self.report_name: str = 'daily-status'
        self.delivery_format: DeliveryFormat = DeliveryFormat.HTML
        # These two members are intentionally optional. Their default value is
        # None, and _omit_none_from_json() below tells Config to keep them out
        # of JSON until the user explicitly selects a value.
        self.author_note: Optional[str] = None
        self.palette: Optional[Palette] = None
        super().__init__(from_json_data_text=from_json_text,
                         from_json_filename=from_json_filename,
                         stderr_file=stderr_file, member_name=member_name)

    @override
    def _omit_none_from_json(self) -> list[str]:
        """Return members omitted from JSON while their value is None."""
        return ['author_note', 'palette']

    def selected_palette(self) -> Palette:
        """Return the palette the application should use.

        Returns:
            The user-selected palette, or the current automatic choice when
            no palette has been configured.
        """
        if self.palette is None:
            return Palette.ACCESSIBLE
        return self.palette

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Return extra validation steps for this example configuration."""
        _ = stderr_file
        return []

    def parse_converters(self) -> dict[str, ParseConverter]:
        """Return conversions needed when reading enum values from JSON."""
        return {'delivery_format': self.get_converter_dict(DeliveryFormat),
                'palette': self.get_converter_dict(Palette)}


def e30_optional_user_preference_set(set_values: SetValues,
                                     config_file: PathOrStr) -> None:
    """Create configuration, apply overrides, and store it.

    Args:
        set_values: Values that should differ from the defaults.
        config_file: Path where to write the configuration file.
    """
    config = ExampleConfig30()
    for key, value in set_values.items():
        if key == 'report_name':
            assert isinstance(value, str)
            config.report_name = value
        elif key == 'delivery_format':
            assert isinstance(value, DeliveryFormat)
            config.delivery_format = value
        elif key == 'author_note':
            assert isinstance(value, str)
            config.author_note = value
        elif key == 'palette':
            assert isinstance(value, Palette)
            config.palette = value
        else:
            raise ValueError(f'Invalid key: {key}')
    config.write(to_json_filename=config_file)
    print(f'Configuration written to {config_file}')


def e30_optional_user_preference_print(config_file: PathOrStr) -> None:
    """Read a configuration file and show how the values are used.

    Args:
        config_file: Path to the configuration file to read.
    """
    config = ExampleConfig30(from_json_filename=config_file)
    if config.author_note is None:
        author_note = 'not configured'
    else:
        author_note = config.author_note
    if config.palette is None:
        palette_setting = 'automatic'
    else:
        palette_setting = config.palette.name
    print(f'Configuration read from {config_file}')
    print(f'Report name: {config.report_name}')
    print(f'Delivery format: {config.delivery_format.name}')
    print(f'Author note: {author_note}')
    print(f'Palette setting: {palette_setting}')
    print(f'Selected palette: {config.selected_palette().name}')


# -----------------------------------------------------------------------------
# The rest of this file is the command line handling code.
# This is to be able to run the example from the command line,
# but it could be done in any other way, and is not part of what this example
# is trying to teach.
# -----------------------------------------------------------------------------

INPUT_SPECS = [
    InputSpec(name='report_name', single=True, value_type=str),
    InputSpec(name='delivery_format', single=True, value_type=DeliveryFormat),
    InputSpec(name='author_note', single=True, value_type=str),
    InputSpec(name='palette', single=True, value_type=Palette)
]
"""Command line values that the example exposes for ``set``."""


def main(args: Optional[list[str]] = None) -> None:
    """Run the example command line interface.

    Args:
        args: Optional replacement for ``sys.argv[1:]``, mainly for tests.
    """
    cmd_line_handling(example_name='e30_optional_user_preference',
                      input_specs=INPUT_SPECS,
                      set_command=e30_optional_user_preference_set,
                      print_command=e30_optional_user_preference_print,
                      args=args)


if __name__ == '__main__':
    main()
    sys.exit(0)
