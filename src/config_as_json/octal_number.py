#! /usr/local/bin/python3
"""A configuration value that should format as an octal number."""

# Copyright (c) 2026 Tom Björkholm
# MIT License

from enum import Enum
from config_as_json.radix_number import RadixNumber, RadixSpec, RadixValidator


_OCT_SPEC = RadixSpec(radix=8, digit_chars='01234567', format_letter='o',
                      member_name='oct_str', adjective='octal', article='an')
"""The notation that an octal number is written in."""


class OctalStringValidator(RadixValidator['OctalNumber.Prefix']):
    """A validator for an octal string configuration value.

    The member value must be a string holding octal digits, optionally
    preceded by any of the prefixes that :class:`OctalNumber.Prefix`
    describes, and optionally surrounded by whitespace. A non-negative
    integer is accepted as well, which is what a configuration file that
    stored a plain number before it stored octal text has in it. The
    validated value is returned formatted with the configured prefix and
    padded with leading zeros to the configured number of digits, so that a
    file written by hand is normalized to the notation the application
    declared.

    The validator is used by :class:`OctalNumber`, and it validates any
    plain string member of any Config class just as well. See
    :class:`RadixValidator` for the constructor and the validation method.
    """

    _SPEC = _OCT_SPEC


class OctalNumber(RadixNumber['OctalNumber.Prefix']):
    """A configuration value that should format as an octal number.

    The value is used as an integer, but when serialized to JSON it is
    formatted as an octal string with an optional leading prefix and with
    leading zeros up to a declared minimum number of digits. File modes are
    the typical use: ``Prefix.ZERO`` with three digits gives the ``'0755'``
    notation that the chmod documentation uses, and ``Prefix.ZERO_O`` gives
    the ``'0o755'`` notation of Python. Reading and editing keep that
    notation, because that is the notation the user of the configuration
    file expects to see and to type.

    The public member ``oct_str`` holds the octal string, and it is the only
    member written to and read from JSON. See :class:`RadixNumber` for the
    constructor, for :meth:`RadixNumber.set` and :meth:`RadixNumber.get`,
    and for the two ways of declaring the format of a nested member.

    Declare at least as many digits as the file mode has when writing with
    ``Prefix.ZERO``, as the prefix is written whatever the value is. The
    default of no digits then writes the value zero as ``'00'``.
    """

    oct_str: str
    """The octal string, and the only member stored in JSON."""

    class Prefix(Enum):
        """The prefix to use when formatting the octal number.

        The value of each member is the prefix text itself, in lower case.
        Any of them is accepted when a value is read, whichever one this
        object formats with, so a hand-edited file is normalized instead of
        refused. The leading zero of ``ZERO`` is kept when a value is read,
        as it cannot be told from the padding zeros of a written value, and
        the value reads as the same number either way.
        """

        NONE = ''
        """No prefix."""

        ZERO_O = '0o'
        """The prefix '0o', the notation of Python."""

        ZERO = '0'
        """The leading zero of the traditional file mode notation."""

    _SPEC = _OCT_SPEC
    _no_prefix = Prefix.NONE
    _validator_class = OctalStringValidator
