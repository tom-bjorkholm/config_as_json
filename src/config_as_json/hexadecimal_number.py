#! /usr/local/bin/python3
"""A configuration value that should format as a hexadecimal number."""

# Copyright (c) 2026 Tom Björkholm
# MIT License

from enum import Enum
from config_as_json.radix_number import RadixNumber, RadixSpec, RadixValidator


_HEX_SPEC = RadixSpec(radix=16, digit_chars='0123456789abcdefABCDEF',
                      format_letter='x', member_name='hex_str',
                      adjective='hexadecimal', article='a')
"""The notation that a hexadecimal number is written in."""


class HexadecimalStringValidator(RadixValidator['HexadecimalNumber.Prefix']):
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
    plain string member of any Config class just as well. See
    :class:`RadixValidator` for the constructor and the validation method.
    """

    _SPEC = _HEX_SPEC


class HexadecimalNumber(RadixNumber['HexadecimalNumber.Prefix']):
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
    only member written to and read from JSON. See :class:`RadixNumber` for
    the constructor, for :meth:`RadixNumber.set` and
    :meth:`RadixNumber.get`, and for the two ways of declaring the format of
    a nested member.
    """

    hex_str: str
    """The hexadecimal string, and the only member stored in JSON."""

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

    _SPEC = _HEX_SPEC
    _no_prefix = Prefix.NONE
    _validator_class = HexadecimalStringValidator
