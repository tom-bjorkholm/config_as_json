#! /usr/local/bin/python3
"""Teach hexadecimal and octal configuration values.

Some configuration values are integers to the application, but the user of
the configuration file never thinks of them as decimal numbers:

- a file mode is ``0644``, and not the integer 420
- a umask is ``0o022``, and not the integer 18
- a Tk colour is ``#204060``, and not the integer 2113632
- a bit mask is ``0x0000000f``, and not the integer 15

``OctalNumber`` and ``HexadecimalNumber`` store such a value as text in the
notation the user expects, and hand the application the integer. The value
is a small nested ``Config`` object with one single public member, which is
the written text. That is what makes the notation survive a write, a read,
and every parse that an editor such as edit-cfg-json-tk makes: the editor
shows the member ``oct_str`` or ``hex_str``, so the user edits ``0644`` and
never sees the integer 420.

The example also shows the two ways of declaring the format of such a
value, because the format is deliberately not stored in the JSON file:

- derive a subclass whose ``__init__`` supplies the format (``FileMode``
  and ``TkColour`` below)
- call ``factory()`` and give the result to
  ``ConfigNesting(factory_function=...)`` (``umask`` and ``feature_bits``
  below)
"""

# Copyright (c) 2026 Tom Björkholm
# MIT License

from typing import Optional, TextIO, override
import sys
from config_as_json import Config, ConfigNesting, ConfigNestingKind, \
    HexadecimalNumber, InvalidConfiguration, InvalidConfigurationValue, \
    NestedConfigs, OctalNumber, PathOrStr, ValidationPlan
from .cmd_line_handling import InputSpec, SetValues, cmd_line_handling


class FileMode(OctalNumber):
    """One file mode, written the way the chmod documentation writes one.

    This is the first of the two ways of declaring the format. The subclass
    supplies the prefix and the digit count to ``OctalNumber``, so every
    ``FileMode`` object is written the same way. The base class constructs a
    new nested object every time JSON is parsed, and because that new object
    is a ``FileMode``, the format comes back with it.
    """

    def __init__(self, from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 stderr_file: TextIO = sys.stderr, *,
                 value: Optional[int | str] = None) -> None:
        """Initialize one file mode.

        Args:
            from_json_data_text: Optional JSON text to parse directly.
            from_json_filename: Optional path to a JSON file to read.
            stderr_file: Stream used for user-facing diagnostics.
            value: Optional initial value, an integer or a written value.
        """
        # Prefix.ZERO writes the leading zero of '0644'. Three digits is the
        # smallest number of digits written, so '0006' is written for a mode
        # that only has the read bit for others set. Declare at least three
        # digits with this prefix, because the prefix is always written, and
        # a value of zero would otherwise be written as the odd looking '00'.
        super().__init__(from_json_data_text, from_json_filename, None,
                         stderr_file, value=value,
                         prefix=OctalNumber.Prefix.ZERO, digits=3)


class TkColour(HexadecimalNumber):
    """One colour, written the way Tk expects to be given one.

    The same first way of declaring the format, for the hexadecimal
    notation. Tk wants a hash sign and exactly six digits, which is what
    ``Prefix.HASH`` and six digits give.
    """

    def __init__(self, from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 stderr_file: TextIO = sys.stderr, *,
                 value: Optional[int | str] = None) -> None:
        """Initialize one colour.

        Args:
            from_json_data_text: Optional JSON text to parse directly.
            from_json_filename: Optional path to a JSON file to read.
            stderr_file: Stream used for user-facing diagnostics.
            value: Optional initial value, an integer or a written value.
        """
        super().__init__(from_json_data_text, from_json_filename, None,
                         stderr_file, value=value,
                         prefix=HexadecimalNumber.Prefix.HASH, digits=6)


# This is the second way of declaring the format. One call says the prefix,
# the digit count, and the default value once, and the same object is used
# both for the default value of the member and for every later parse.
UMASK_FACTORY = OctalNumber.factory(OctalNumber.Prefix.ZERO_O, 3, 0o022)
"""Construct one umask value written as '0o022'."""

FEATURE_FACTORY = HexadecimalNumber.factory(HexadecimalNumber.Prefix.ZERO_X, 8,
                                            0x0000000f)
"""Construct one feature bit mask written as '0x0000000f'."""


def _new_umask() -> OctalNumber:
    """Return one umask value constructed by the shared factory."""
    # A factory promises to construct some Config object, because that is
    # what ConfigNesting needs from it. The assert tells the type checker,
    # and checks while the example runs, what this factory really returns.
    made = UMASK_FACTORY()
    assert isinstance(made, OctalNumber)
    return made


def _new_features() -> HexadecimalNumber:
    """Return one feature bit mask constructed by the shared factory."""
    made = FEATURE_FACTORY()
    assert isinstance(made, HexadecimalNumber)
    return made


class ExampleConfig41(Config):
    """Configuration with octal and hexadecimal configuration values."""

    def __init__(self, from_json_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 stderr_file: TextIO = sys.stderr) -> None:
        """Initialize the configuration.

        Args:
            from_json_text: Optional JSON text to parse directly.
            from_json_filename: Optional path to a JSON file to read.
            stderr_file: Stream used for user-facing diagnostics.
        """
        # Every one of these four members is a nested Config object holding
        # one written number. The JSON file therefore looks like this:
        #   "file_mode": {"oct_str": "0644"},
        #   "umask": {"oct_str": "0o022"},
        #   "window_colour": {"hex_str": "#204060"},
        #   "feature_bits": {"hex_str": "0x0000000f"}
        # The written member is the only thing stored. The prefix and the
        # digit count are not in the file, because they are a decision of
        # the application and not of the user.
        self.report_name: str = 'monthly-report'
        self.file_mode: OctalNumber = FileMode(value=0o644)
        self.umask: OctalNumber = _new_umask()
        self.window_colour: HexadecimalNumber = TkColour(value=0x204060)
        self.feature_bits: HexadecimalNumber = _new_features()
        super().__init__(from_json_data_text=from_json_text,
                         from_json_filename=from_json_filename,
                         stderr_file=stderr_file)

    @override
    def nested_configs(self) -> NestedConfigs:
        """Return nested Config declarations for the written numbers."""
        # Every nested Config member is declared here. The two members that
        # have a class of their own name that class as the config_type, and
        # nothing more is needed. The two members that are declared by a
        # factory name the library class as the config_type, and give the
        # factory that supplies the format to the object the library builds
        # while it parses.
        return {
            'file_mode': ConfigNesting(kind=ConfigNestingKind.MEMBER,
                                       config_type=FileMode),
            'umask': ConfigNesting(kind=ConfigNestingKind.MEMBER,
                                   config_type=OctalNumber,
                                   factory_function=UMASK_FACTORY),
            'window_colour': ConfigNesting(kind=ConfigNestingKind.MEMBER,
                                           config_type=TkColour),
            'feature_bits': ConfigNesting(kind=ConfigNestingKind.MEMBER,
                                          config_type=HexadecimalNumber,
                                          factory_function=FEATURE_FACTORY)
        }

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Return the validation steps of the top-level configuration."""
        # The written numbers need no step here. Each nested value brings
        # its own validation plan, which refuses a value that is not written
        # in its notation, and normalizes an accepted value to the declared
        # prefix and digit count.
        _ = stderr_file
        return []

    def owner_may_write(self) -> bool:
        """Tell if the file mode gives the owner the right to write."""
        # This is what the application does with the value: it asks for the
        # integer with get(), and uses it as an ordinary integer. The
        # integer is cached, so asking for it often is cheap.
        return bool(self.file_mode.get() & 0o200)


def _apply_set_value(config: ExampleConfig41, key: str, value: object) -> None:
    """Apply one command-line value to the matching configuration value.

    Args:
        config: Configuration object to update.
        key: Command-line key being applied.
        value: Command-line value.

    Raises:
        ValueError: The command-line helper supplied an unknown key.
    """
    assert isinstance(value, str)
    if key == 'report_name':
        config.report_name = value
        return
    # The written numbers are nested Config objects, so a new value is given
    # to the object with set(). Assigning the text to the member itself
    # would replace the nested object with a plain string, and the declared
    # notation would be lost with it. set() accepts any of the notations of
    # its class, so '0o644', '0644', and '644' all set the same file mode,
    # and all three are stored as '0644'.
    if key == 'file_mode':
        config.file_mode.set(value)
        return
    if key == 'umask':
        config.umask.set(value)
        return
    if key == 'window_colour':
        config.window_colour.set(value)
        return
    if key == 'feature_bits':
        config.feature_bits.set(value)
        return
    raise ValueError(f'Invalid key: {key}')


def e41_hex_and_octal_set(set_values: SetValues,
                          config_file: PathOrStr) -> None:
    """Create configuration, apply overrides, and store it.

    Args:
        set_values: Values that should differ from the defaults.
        config_file: Path where to write the configuration file.
    """
    # The writing of the file, and the reading of it in the print command
    # below, are the same in every example, so pylint sees the shared lines
    # as duplicated code here.
    # pylint: disable=duplicate-code
    config = ExampleConfig41()
    for key, value in set_values.items():
        _apply_set_value(config, key, value)
    try:
        config.write(to_json_filename=config_file)
        print(f'Configuration written to {config_file}')
    except (InvalidConfiguration, InvalidConfigurationValue):
        pass  # Error already printed by the Config object.


def e41_hex_and_octal_print(config_file: PathOrStr) -> None:
    """Read a configuration file and show how the values are used.

    Args:
        config_file: Path to the configuration file to read.
    """
    # pylint: disable=duplicate-code
    try:
        config = ExampleConfig41(from_json_filename=config_file)
        print(f'Configuration read from {config_file}')
        print(f'Report name: {config.report_name}')
        # Each value is shown twice: as the text that the file holds and
        # that the user edits, and as the integer that the application uses.
        mode = config.file_mode
        print(f'File mode: {mode.oct_str} = {mode.get()} as an integer')
        umask = config.umask
        print(f'Umask: {umask.oct_str} = {umask.get()} as an integer')
        colour = config.window_colour
        print(f'Window colour: {colour.hex_str} = {colour.get()} '
              'as an integer')
        bits = config.feature_bits
        print(f'Feature bits: {bits.hex_str} = {bits.get()} as an integer')
        answer = 'yes' if config.owner_may_write() else 'no'
        print(f'The owner may write the file: {answer}')
    except (InvalidConfiguration, InvalidConfigurationValue):
        pass  # Error already printed by the Config object.


INPUT_SPECS = [
    InputSpec(name='report_name', single=True, value_type=str),
    InputSpec(name='file_mode', single=True, value_type=str),
    InputSpec(name='umask', single=True, value_type=str),
    InputSpec(name='window_colour', single=True, value_type=str),
    InputSpec(name='feature_bits', single=True, value_type=str)
]
"""Command line values that the example exposes for ``set``.

The four written numbers are given as text, in any of the notations that
their class accepts, which is exactly what the user writes in the file.
"""


def main(args: Optional[list[str]] = None) -> None:
    """Run the example command line interface.

    Args:
        args: Optional replacement for ``sys.argv[1:]``, mainly for tests.
    """
    cmd_line_handling(example_name='e41_hex_and_octal',
                      input_specs=INPUT_SPECS,
                      set_command=e41_hex_and_octal_set,
                      print_command=e41_hex_and_octal_print, args=args)


if __name__ == '__main__':
    main()
    sys.exit(0)
