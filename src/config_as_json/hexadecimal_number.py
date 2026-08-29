#! /usr/local/bin/python3
"""A configuration value that should format as a hexadecimal number."""

# Copyright (c) 2026 Tom Björkholm
# MIT License

from typing import NoReturn, Optional, TextIO
import sys
from enum import Enum
from config_as_json.config import Config
from config_as_json.config_auto_change_hook import ConfigAutoChangeHook
from config_as_json.config_nesting import ConfigFactory
from config_as_json.commontypes import PathOrStr
from config_as_json.validator import InvalidConfiguration, ValidationPlan, \
    WholeConfigValidationStep, MemberValidationStep, WholeConfigValidator, \
    MemberValidator
from config_as_json.type_validators import InvalidConfigurationType


_HEX_DIGITS = '0123456789abcdefABCDEF'
"""The characters allowed in the digit part of a hexadecimal string."""


class HexadecimalNumber(Config):
    """A configuration value that should format as a hexadecimal number.

    The value is used as an integer, but when serialized to JSON it is
    formatted as a hexadecimal string with an optional leading prefix and
    with leading zeros up to a declared minimum number of digits. Display
    colours are the typical use: ``Prefix.HASH`` with six digits gives the
    hash sign followed by six digits that Tk expects, and ``Prefix.ZERO_X``
    gives the ``'0xff'`` notation of C-like languages. Reading and editing
    keep that notation, because that is the notation the user of the
    configuration file expects to see and to type.

    The public member ``hex_str`` holds the hexadecimal string, and it is the
    only member written to and read from JSON. The integer is cached, because
    an application reads a configured value far more often than it reads or
    writes a configuration file. :meth:`get` rebuilds the cache whenever
    ``hex_str`` was assigned since the cache was built, so assigning to
    ``hex_str`` directly stays correct.

    The prefix and the digit count describe how the application wants the
    value written, and they are not stored in the JSON file. The base class
    rebuilds a nested Config member from its own constructor whenever JSON is
    parsed, so a declaration that says nothing about the format would be
    rebuilt with the default format. Say the format either by deriving a
    subclass that supplies it, or by giving :meth:`factory` to
    ``ConfigNesting(factory_function=...)``.
    """

    class Prefix(Enum):
        """The prefix to use when formatting the hexadecimal number.

        The value of each member is the prefix text itself, in lower case.
        Any of them is accepted when a value is read, whichever one this
        object formats with, so a hand-edited file is normalized instead of
        refused.
        """

        NONE = ''
        """No prefix."""

        ZERO_X = '0x'
        """The prefix '0x'."""

        HASH = '#'
        """The prefix '#'."""

    # pylint: disable-next=too-many-arguments
    def __init__(self, from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 auto_ch_hook: Optional[ConfigAutoChangeHook] = None,
                 stderr_file: TextIO = sys.stderr, *,
                 value: Optional[int | str] = None,
                 prefix: Prefix = Prefix.NONE, digits: int = 0) -> None:
        """Initialize the HexadecimalNumber configuration value.

        Args:
            from_json_data_text: Optional JSON text to parse directly.
            from_json_filename: Optional path to a JSON file to read.
            auto_ch_hook: Hook that is notified about automatic changes such
                as filled, renamed, moved, or removed values when reading old
                configuration files. The object is kept by reference, so the
                application can read the recorded changes from its own object
                after parsing. See :class:`ConfigAutoChangeHook` for what
                reusing or sharing one hook instance means.
            stderr_file: Stream used for user-facing diagnostics.
            value: Optional initial value, either a non-negative integer or a
                string formatted as a hexadecimal number. The value zero is
                used when this is ``None``. If both ``value`` and JSON data
                are provided, the JSON data takes precedence.
            prefix: The prefix to use when formatting the hexadecimal number.
            digits: The smallest number of hexadecimal digits to write. The
                digits are padded with leading zeros up to this count. Zero,
                the default, writes as few digits as the value needs.

        Raises:
            InvalidConfiguration: ``value`` is negative, or is a string that
                does not hold a hexadecimal number.
            InvalidConfigurationType: ``value`` is neither an integer nor a
                string.
            ValueError: ``digits`` is negative, or both JSON text and a JSON
                file were supplied.
            KeyError: Parsed data is missing required keys or contains
                unexpected keys.
            ConfigBadJson: The supplied JSON could not be decoded or converted
                into the expected configuration structure.
        """
        self._prefix: HexadecimalNumber.Prefix = prefix
        self._digits: int = _checked_digits(digits)
        self.hex_str: str = _format_hex(0, prefix, self._digits)
        self._int_value: int = 0
        self._cached_hex: str = self.hex_str
        if value is not None:
            self.set(value)
        super().__init__(from_json_data_text, from_json_filename, auto_ch_hook,
                         stderr_file)

    @property
    def prefix(self) -> 'HexadecimalNumber.Prefix':
        """Return the prefix that this value is formatted with."""
        return self._prefix

    @property
    def digits(self) -> int:
        """Return the smallest number of hexadecimal digits written."""
        return self._digits

    def set(self, value: int | str) -> None:
        """Set the value from an integer or from a hexadecimal string.

        The stored ``hex_str`` is always formatted with the prefix and the
        digit count of this object, whatever notation the argument used.

        Args:
            value: A non-negative integer, or a string holding hexadecimal
                digits with an optional prefix and optional surrounding
                whitespace.

        Raises:
            InvalidConfiguration: The value is negative, or is a string that
                does not hold a hexadecimal number.
            InvalidConfigurationType: The value is neither an integer nor a
                string.
        """
        number = _value_to_int(value, 'hex_str', None)
        self.hex_str = _format_hex(number, self._prefix, self._digits)
        self._cache(number)

    def get(self) -> int:
        """Return the value as an integer.

        The integer is taken from the cache, which is rebuilt first if
        ``hex_str`` was assigned since the cache was built.

        Raises:
            InvalidConfiguration: ``hex_str`` was assigned a string that does
                not hold a hexadecimal number.
        """
        if self._cached_hex != self.hex_str:
            self._cache(_hex_to_int(self.hex_str, 'hex_str', None))
        return self._int_value

    def _cache(self, number: int) -> None:
        """Remember the integer that the current ``hex_str`` holds."""
        self._int_value = number
        self._cached_hex = self.hex_str

    @classmethod
    def factory(cls, prefix: Prefix, digits: int = 0,
                value: Optional[int | str] = None) -> ConfigFactory:
        """Return a factory constructing values with one declared format.

        Give the returned callable to ``ConfigNesting(factory_function=...)``
        so that reading a file, and every parse that an editor such as
        edit-cfg-json makes, rebuilds the nested member with this format
        instead of with the default format. Deriving a subclass whose
        ``__init__`` supplies the format says the same thing, and needs no
        factory in the declaration.

        Calling the factory without arguments constructs the declared default
        of the member, so that the same call says the format once for both
        the default and every later parse.

        The class this is called on is the class constructed, so it has to
        be one that accepts ``prefix`` and ``digits``. A subclass that fixes
        its own format instead does not, and needs no factory.

        Args:
            prefix: The prefix that constructed values are formatted with.
            digits: The smallest number of hexadecimal digits to write.
            value: The value of a constructed object when no JSON is given.

        Returns:
            A :class:`ConfigFactory` constructing one object of the class
            this is called on.

        Raises:
            InvalidConfiguration: ``value`` is negative, or is a string that
                does not hold a hexadecimal number.
            InvalidConfigurationType: ``value`` is neither an integer nor a
                string.
            ValueError: ``digits`` is negative.
        """
        checked = _checked_digits(digits)

        def make(*, from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 stderr_file: TextIO = sys.stderr) -> 'HexadecimalNumber':
            """Construct one hexadecimal value with the declared format."""
            return cls(from_json_data_text, from_json_filename, None,
                       stderr_file, value=value, prefix=prefix, digits=checked)
        return make

    @staticmethod
    def strip_prefix(value: str) -> str:
        """Strip the prefix from a hexadecimal string.

        Any of the prefixes that :class:`HexadecimalNumber.Prefix` describes
        is removed, ignoring case, whichever prefix an object formats with.

        Args:
            value: The hexadecimal string to strip.

        Returns:
            The hexadecimal string without the prefix, unchanged when it has
            no recognized prefix.
        """
        for prefix in HexadecimalNumber.Prefix:
            marker = prefix.value
            if marker and value[:len(marker)].lower() == marker:
                return value[len(marker):]
        return value

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Return the validation plan for the Config object.

        The plan first validates the value read from JSON and normalizes it
        to the prefix and the digit count of this object, and then rebuilds
        the cached integer from the normalized text.

        Args:
            stderr_file: Stream used for user-facing diagnostics.

        Returns:
            An ordered list of validation steps describing the validations for
            the Config object. The order of the steps in the list is
            significant as a previous validation may normalize or change a
            configuration value that is used in a later validation.
        """
        _ = stderr_file
        is_hex = MemberValidationStep(
            member_names=['hex_str'],
            validator=HexadecimalStringValidator(prefix=self._prefix,
                                                 digits=self._digits))
        cached = WholeConfigValidationStep(validator=_HexCacheBuilder())
        return [is_hex, cached]


def _checked_digits(digits: int) -> int:
    """Return one checked smallest number of hexadecimal digits."""
    if digits < 0:
        raise ValueError(f'digits must not be negative, got {digits}')
    return digits


def _invalid_hex(message: str, stderr_file: Optional[TextIO],
                 error: type[InvalidConfiguration] = InvalidConfiguration
                 ) -> NoReturn:
    """Report one invalid hexadecimal value and raise.

    Args:
        message: The diagnostic text describing what is invalid.
        stderr_file: Stream used for user-facing diagnostics, ``None`` to
            raise without reporting, which is what a direct call from the
            application does.
        error: The exception class to raise.

    Raises:
        InvalidConfiguration: Always, as the given exception class.
    """
    if stderr_file is not None:
        print(message, file=stderr_file)
    raise error(message)


def _format_hex(value: int, prefix: HexadecimalNumber.Prefix,
                digits: int) -> str:
    """Return one integer as hexadecimal text with prefix and padding.

    The value has to be one that :func:`_checked_int` accepted, as
    hexadecimal text without a sign cannot hold a negative number.
    """
    return f'{prefix.value}{value:0{digits}x}'


def _checked_int(value: int, member_name: str,
                 stderr_file: Optional[TextIO]) -> int:
    """Return one integer accepted as a hexadecimal value.

    Booleans are rejected although Python counts them as integers, because a
    JSON ``true`` is a mistake here and not the value one.

    Raises:
        InvalidConfiguration: The value is a bool or is negative.
    """
    if isinstance(value, bool):
        msg = f'Value for {member_name} is a bool, not a number.'
        _invalid_hex(msg, stderr_file)
    if value < 0:
        msg = f'Value for {member_name} is negative: {value}.'
        _invalid_hex(msg, stderr_file)
    return value


def _hex_to_int(text: str, member_name: str,
                stderr_file: Optional[TextIO]) -> int:
    """Return the integer that one hexadecimal string holds.

    Surrounding whitespace and any recognized prefix are removed before the
    remaining digits are read.

    Raises:
        InvalidConfiguration: The string holds no digits, or holds something
            that is not a hexadecimal digit.
    """
    digits = HexadecimalNumber.strip_prefix(text.strip())
    if not digits:
        msg = f'Hexadecimal string for {member_name} is empty.'
        _invalid_hex(msg, stderr_file)
    if not all(character in _HEX_DIGITS for character in digits):
        msg = f'Hexadecimal string for {member_name} has characters that '
        msg += f'are not hexadecimal digits: {text!r}'
        _invalid_hex(msg, stderr_file)
    return int(digits, 16)


def _value_to_int(value: object, member_name: str,
                  stderr_file: Optional[TextIO]) -> int:
    """Return the integer that one configured hexadecimal value holds.

    A string holds it in hexadecimal notation, and an integer holds it
    directly, which is what a configuration file that stored a plain number
    before it stored hexadecimal text has in it.

    Raises:
        InvalidConfigurationType: The value is neither a string nor an
            integer.
        InvalidConfiguration: The value is negative, or is a string that does
            not hold a hexadecimal number.
    """
    if isinstance(value, str):
        return _hex_to_int(value, member_name, stderr_file)
    if isinstance(value, int):
        return _checked_int(value, member_name, stderr_file)
    msg = f'Value for {member_name} is not a hexadecimal string or a '
    msg += f'number, but {type(value).__name__}.'
    _invalid_hex(msg, stderr_file, InvalidConfigurationType)


# pylint: disable-next=too-few-public-methods
class HexadecimalStringValidator(MemberValidator):
    """A validator for a hexadecimal string configuration value.

    The member value must be a string holding hexadecimal digits, optionally
    preceded by any of the prefixes that
    :class:`HexadecimalNumber.Prefix` describes, and optionally surrounded by
    whitespace. A non-negative integer is accepted as well, which is what a
    configuration file that stored a plain number before it stored
    hexadecimal text has in it. The validated value is returned formatted
    with the configured prefix and padded with leading zeros to the
    configured number of digits, so that a file written by hand is normalized
    to the notation the application declared.

    The validator is used by :class:`HexadecimalNumber`, and it validates any
    plain string member of any Config class just as well.
    """

    def __init__(self, prefix: HexadecimalNumber.Prefix,
                 digits: int = 0) -> None:
        """Initialize the HexadecimalStringValidator.

        Args:
            prefix: The prefix that validated values are formatted with.
            digits: The smallest number of hexadecimal digits to write. The
                digits are padded with leading zeros up to this count. Zero,
                the default, writes as few digits as the value needs.

        Raises:
            ValueError: ``digits`` is negative.
        """
        self.prefix: HexadecimalNumber.Prefix = prefix
        self.digits: int = _checked_digits(digits)

    def validate_member(self, config: 'Config', member_name: str,
                        member_value: object,
                        stderr_file: TextIO = sys.stderr) -> Optional[object]:
        """Validate that the member value is a valid hexadecimal string.

        Args:
            config: The complete Config object (might be needed if the
                validator needs to access other members of the Config
                object).
            member_name: The name of the member to validate.
            member_value: The value of the member to validate.
            stderr_file: The file to write error messages to.

        Returns:
            The value formatted with the configured prefix and padded to the
            configured number of digits.

        Raises:
            InvalidConfigurationType: The member value is neither a string
                nor an integer.
            InvalidConfiguration: The member value is negative, or is a
                string that does not hold a hexadecimal number.
        """
        _ = config
        number = _value_to_int(member_value, member_name, stderr_file)
        return _format_hex(number, self.prefix, self.digits)


# pylint: disable-next=too-few-public-methods
class _HexCacheBuilder(WholeConfigValidator):
    """A normalizer for a HexadecimalNumber configuration value.

    The normalizer makes sure the cached integer matches the ``hex_str``
    value. It is the last step of the validation plan, so that the value a
    parse or an earlier step produced is cached at once instead of on the
    first read of the value.
    """

    def validate(self, config: Config, stderr_file: TextIO = sys.stderr) \
            -> None:
        """Rebuild the cached integer of the HexadecimalNumber.

        Args:
            config: The HexadecimalNumber object to normalize.
            stderr_file: The file to write error messages to.

        Raises:
            InvalidConfiguration: The ``hex_str`` member does not hold a
                hexadecimal number.
        """
        _ = stderr_file
        assert isinstance(config, HexadecimalNumber)
        config.get()
