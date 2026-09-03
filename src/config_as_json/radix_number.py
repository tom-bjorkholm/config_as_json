#! /usr/local/bin/python3
"""A configuration value that should format as a number in one notation."""

# Copyright (c) 2026 Tom Björkholm
# MIT License

from typing import ClassVar, Generic, NamedTuple, NoReturn, Optional, \
    TextIO, TypeVar
import sys
from enum import Enum
from config_as_json.config import Config
from config_as_json.config_auto_change_hook import ConfigAutoChangeHook
from config_as_json.config_nesting import ConfigFactory
from config_as_json.commontypes import PathOrStr
from config_as_json.member_path import member_path
from config_as_json._deprecated_support import use_member_name
from config_as_json.validator import InvalidConfiguration, ValidationPlan, \
    WholeConfigValidationStep, MemberValidationStep, WholeConfigValidator, \
    MemberValidator
from config_as_json.type_validators import InvalidConfigurationType


class RadixSpec(NamedTuple):
    """Describe one notation that a number is written in.

    The specification holds everything that is the same for every value of
    one notation. The prefix and the digit count differ from value to value
    and are held by the value itself.

    Attributes:
        radix: The base that the digits are read with, such as 16 for the
            hexadecimal notation and 8 for the octal notation.
        digit_chars: Every character accepted in the digit part of a written
            value, in both letter cases where they differ.
        format_letter: The presentation letter of the Python format
            specification writing this notation, such as ``'x'`` or ``'o'``.
        member_name: The name of the public member that holds the written
            value of a :class:`RadixNumber`.
        adjective: The name of the notation in lower case, as it is used in
            diagnostics, such as ``'hexadecimal'``.
        article: The indefinite article of ``adjective``, ``'a'`` or
            ``'an'``, as it is used in diagnostics.
    """

    radix: int
    digit_chars: str
    format_letter: str
    member_name: str
    adjective: str
    article: str


PrefixT = TypeVar('PrefixT', bound=Enum)
"""The enum describing the prefixes of one notation."""


def _checked_digits(digits: int) -> int:
    """Return one checked smallest number of digits."""
    if digits < 0:
        raise ValueError(f'digits must not be negative, got {digits}')
    return digits


def _invalid_value(message: str, stderr_file: Optional[TextIO],
                   error: type[InvalidConfiguration] = InvalidConfiguration
                   ) -> NoReturn:
    """Report one invalid value and raise.

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


def _checked_int(value: int, member_name: str,
                 stderr_file: Optional[TextIO]) -> int:
    """Return one integer accepted as a written value.

    Booleans are rejected although Python counts them as integers, because a
    JSON ``true`` is a mistake here and not the value one.

    Raises:
        InvalidConfiguration: The value is a bool or is negative.
    """
    if isinstance(value, bool):
        msg = f'Value for {member_name} is a bool, not a number.'
        _invalid_value(msg, stderr_file)
    if value < 0:
        msg = f'Value for {member_name} is negative: {value}.'
        _invalid_value(msg, stderr_file)
    return value


def _is_removed_prefix(marker: str, spec: RadixSpec) -> bool:
    """Tell if one prefix is removed before the digits are read.

    A prefix that is made of digits of the notation, such as the leading
    zero of the file mode ``'0755'``, is kept. It cannot be told from the
    padding zeros of a written value, and the value reads as the same
    number whether the prefix is removed or not.
    """
    if not marker:
        return False
    return not all(char in spec.digit_chars for char in marker)


def _strip_prefix(text: str, prefixes: type[Enum], spec: RadixSpec) -> str:
    """Return one written value with any recognized prefix removed.

    Args:
        text: The written value to strip.
        prefixes: The enum describing the prefixes of the notation.
        spec: The notation that the value is written in.

    Returns:
        The written value without the prefix, unchanged when it has no
        prefix that is removed before the digits are read.
    """
    for prefix in prefixes:
        marker = str(prefix.value)
        if not _is_removed_prefix(marker, spec):
            continue
        if text[:len(marker)].lower() == marker:
            return text[len(marker):]
    return text


class _Notation(Generic[PrefixT]):
    """The way that one configuration value is written as a number.

    The prefix, the digit count, and the specification of the notation are
    together everything needed to write one integer as text and to read one
    written value back as an integer.
    """

    def __init__(self, prefix: PrefixT, digits: int, spec: RadixSpec) -> None:
        """Initialize the notation of one value.

        Args:
            prefix: The prefix that written values are formatted with.
            digits: The smallest number of digits to write.
            spec: The notation that the digits are written in.

        Raises:
            ValueError: ``digits`` is negative.
        """
        self.prefix: PrefixT = prefix
        self.digits: int = _checked_digits(digits)
        self.spec: RadixSpec = spec

    def write(self, number: int) -> str:
        """Return one non-negative integer written in this notation.

        The number has to be one that :func:`_checked_int` accepted, as text
        without a sign cannot hold a negative number.
        """
        digits = f'{number:0{self.digits}{self.spec.format_letter}}'
        return f'{self.prefix.value}{digits}'

    def read(self, value: object, member_name: str,
             stderr_file: Optional[TextIO]) -> int:
        """Return the integer that one configured value holds.

        A string holds it in this notation, and an integer holds it
        directly, which is what a configuration file that stored a plain
        number before it stored written text has in it.

        Args:
            value: The configured value to read.
            member_name: The reported dotted and indexed path of the
                member, used in diagnostics.
            stderr_file: Stream used for user-facing diagnostics, ``None``
                to raise without reporting.

        Raises:
            InvalidConfigurationType: The value is neither a string nor an
                integer.
            InvalidConfiguration: The value is negative, or is a string that
                does not hold a number in this notation.
        """
        if isinstance(value, str):
            return self._read_text(value, member_name, stderr_file)
        if isinstance(value, int):
            return _checked_int(value, member_name, stderr_file)
        msg = f'Value for {member_name} is not {self.spec.article} '
        msg += f'{self.spec.adjective} string or a number, but '
        msg += f'{type(value).__name__}.'
        _invalid_value(msg, stderr_file, InvalidConfigurationType)

    def _read_text(self, text: str, member_name: str,
                   stderr_file: Optional[TextIO]) -> int:
        """Return the integer that one written value holds.

        Surrounding whitespace and any recognized prefix are removed before
        the remaining digits are read.

        Raises:
            InvalidConfiguration: The string holds no digits, or holds
                something that is not a digit of the notation.
        """
        spec = self.spec
        told = f'{spec.adjective.capitalize()} string for {member_name} '
        digits = _strip_prefix(text.strip(), type(self.prefix), spec)
        if not digits:
            _invalid_value(told + 'is empty.', stderr_file)
        if not all(char in spec.digit_chars for char in digits):
            msg = told + f'has characters that are not {spec.adjective} '
            msg += f'digits: {text!r}'
            _invalid_value(msg, stderr_file)
        return int(digits, spec.radix)


class RadixValidator(MemberValidator, Generic[PrefixT]):
    """A validator for a configuration value written as a number.

    The member value must be a string holding the digits of the notation,
    optionally preceded by any of the prefixes that the notation describes,
    and optionally surrounded by whitespace. A non-negative integer is
    accepted as well, which is what a configuration file that stored a plain
    number before it stored written text has in it. The validated value is
    returned written with the configured prefix and padded with leading
    zeros to the configured number of digits, so that a file written by hand
    is normalized to the notation that the application declared.

    A derived class says the notation by setting the class member ``_SPEC``
    to one :class:`RadixSpec`, and derives from this class with the prefix
    enum of that notation as its type argument.
    :class:`HexadecimalStringValidator` and :class:`OctalStringValidator`
    are the two notations that this package predefines.

    The validator is used by :class:`RadixNumber`, and it validates any
    plain string member of any Config class just as well.
    """

    _SPEC: ClassVar[RadixSpec]
    """The notation that validated values are written in."""

    def __init__(self, prefix: PrefixT, digits: int = 0) -> None:
        """Initialize the validator.

        Args:
            prefix: The prefix that validated values are written with.
            digits: The smallest number of digits to write. The digits are
                padded with leading zeros up to this count. Zero, the
                default, writes as few digits as the value needs.

        Raises:
            ValueError: ``digits`` is negative.
        """
        super().__init__()
        self._notation: _Notation[PrefixT] = _Notation(prefix, digits,
                                                       self._SPEC)

    @property
    def prefix(self) -> PrefixT:
        """Return the prefix that validated values are written with."""
        return self._notation.prefix

    @property
    def digits(self) -> int:
        """Return the smallest number of digits written."""
        return self._notation.digits

    def validate_member(self, config: 'Config', member_name: str,
                        member_value: object,
                        stderr_file: TextIO = sys.stderr) -> Optional[object]:
        """Validate that the member value is written in the notation.

        Args:
            config: The complete Config object (might be needed if the
                validator needs to access other members of the Config
                object).
            member_name: The reported dotted and indexed path of the
                member to validate.
            member_value: The value of the member to validate.
            stderr_file: The file to write error messages to.

        Returns:
            The value written with the configured prefix and padded to the
            configured number of digits.

        Raises:
            InvalidConfigurationType: The member value is neither a string
                nor an integer.
            InvalidConfiguration: The member value is negative, or is a
                string that does not hold a number in the notation.
        """
        _ = config
        number = self._notation.read(member_value, member_name, stderr_file)
        return self._notation.write(number)


class RadixNumber(Config, Generic[PrefixT]):
    """A configuration value that should format as a number.

    The value is used as an integer, but when serialized to JSON it is
    formatted as text with an optional leading prefix and with leading zeros
    up to a declared minimum number of digits. Reading and editing keep that
    notation, because that is the notation the user of the configuration
    file expects to see and to type. :class:`HexadecimalNumber` and
    :class:`OctalNumber` are the two notations that this package
    predefines.

    A derived class says its notation by setting three class members:
    ``_SPEC`` is the :class:`RadixSpec` describing the notation,
    ``_no_prefix`` is the member of its prefix enum that writes no prefix,
    and ``_validator_class`` is its :class:`RadixValidator` class. The class
    also declares the public member named by ``_SPEC.member_name``, which
    holds the written value and is the only member written to and read from
    JSON.

    The integer is cached, because an application reads a configured value
    far more often than it reads or writes a configuration file. :meth:`get`
    rebuilds the cache whenever the written member was assigned since the
    cache was built, so assigning to that member directly stays correct.

    The prefix and the digit count describe how the application wants the
    value written, and they are not stored in the JSON file. The base class
    rebuilds a nested Config member from its own constructor whenever JSON
    is parsed, so a declaration that says nothing about the format would be
    rebuilt with the default format. Say the format either by deriving a
    subclass that supplies it, or by giving :meth:`factory` to
    ``ConfigNesting(factory_function=...)``.
    """

    _SPEC: ClassVar[RadixSpec]
    """The notation that this value is written in."""

    _no_prefix: PrefixT
    """The member of the prefix enum that writes no prefix at all."""

    _validator_class: type[RadixValidator[PrefixT]]
    """The validator class validating the written member of this value."""

    # pylint: disable-next=too-many-arguments
    def __init__(self, from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 auto_ch_hook: Optional[ConfigAutoChangeHook] = None,
                 stderr_file: TextIO = sys.stderr, *,
                 value: Optional[int | str] = None,
                 prefix: Optional[PrefixT] = None, digits: int = 0,
                 member_name: Optional[str] = None) -> None:
        """Initialize the written number configuration value.

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
                string written in the notation of this class. The value zero
                is used when this is ``None``. If both ``value`` and JSON
                data are provided, the JSON data takes precedence.
            prefix: The prefix to use when formatting the number. ``None``,
                the default, writes no prefix at all.
            digits: The smallest number of digits to write. The digits are
                padded with leading zeros up to this count. Zero, the
                default, writes as few digits as the value needs.
            member_name: Dotted and indexed path for reaching this value by
                traversing nested attributes from the top level of the
                complete construction, such as ``limits[cpu].mask``. ``None``
                means that this value is the top level and not a member of
                anything.

        Raises:
            InvalidConfiguration: ``value`` is negative, or is a string that
                does not hold a number in the notation of this class.
            InvalidConfigurationType: ``value`` is neither an integer nor a
                string.
            ValueError: ``digits`` is negative, or both JSON text and a JSON
                file were supplied.
            KeyError: Parsed data is missing required keys or contains
                unexpected keys.
            ConfigBadJson: The supplied JSON could not be decoded or
                converted into the expected configuration structure.
        """
        used = self._no_prefix if prefix is None else prefix
        self._notation: _Notation[PrefixT] = _Notation(used, digits,
                                                       self._SPEC)
        self._write_text(self._notation.write(0))
        self._int_value: int = 0
        self._cached_text: object = self._read_text()
        if value is not None:
            self.set(value)
        super().__init__(from_json_data_text, from_json_filename, auto_ch_hook,
                         stderr_file, member_name=member_name)

    def _write_text(self, text: str) -> None:
        """Store one written number in the public member of this value."""
        setattr(self, self._SPEC.member_name, text)

    def _read_text(self) -> object:
        """Return what the public member of this value holds.

        The member is public, so the application may have assigned anything
        to it since it was written here.
        """
        return getattr(self, self._SPEC.member_name)

    @classmethod
    def written_member_name(cls) -> str:
        """Return the name of the public member holding the written value."""
        return cls._SPEC.member_name

    @property
    def prefix(self) -> PrefixT:
        """Return the prefix that this value is written with."""
        return self._notation.prefix

    @property
    def digits(self) -> int:
        """Return the smallest number of digits written."""
        return self._notation.digits

    def set(self, value: int | str) -> None:
        """Set the value from an integer or from a written number.

        The stored written member is always formatted with the prefix and
        the digit count of this object, whatever notation the argument used.

        Args:
            value: A non-negative integer, or a string holding the digits of
                the notation with an optional prefix and optional
                surrounding whitespace.

        Raises:
            InvalidConfiguration: The value is negative, or is a string that
                does not hold a number in the notation of this class.
            InvalidConfigurationType: The value is neither an integer nor a
                string.
        """
        number = self._notation.read(value, self._SPEC.member_name, None)
        self._write_text(self._notation.write(number))
        self._cache(number)

    def get(self) -> int:
        """Return the value as an integer.

        The integer is taken from the cache, which is rebuilt first if the
        written member was assigned since the cache was built.

        Raises:
            InvalidConfiguration: The written member was assigned a string
                that does not hold a number in the notation of this class.
            InvalidConfigurationType: The written member was assigned
                something that is neither an integer nor a string.
        """
        self._rebuild_cache(self._SPEC.member_name, None)
        return self._int_value

    def _rebuild_cache(self, reported_name: str,
                       stderr_file: Optional[TextIO]) -> None:
        """Rebuild the cached integer when the written member was assigned.

        Args:
            reported_name: The name that a diagnostic about the written
                member calls it. A validation names the whole path for
                reaching the member, and a read of the value outside a
                validation only knows the local member name.
            stderr_file: Stream used for user-facing diagnostics, ``None``
                to raise without reporting.

        Raises:
            InvalidConfiguration: The written member was assigned a string
                that does not hold a number in the notation of this class.
            InvalidConfigurationType: The written member was assigned
                something that is neither an integer nor a string.
        """
        text = self._read_text()
        if self._cached_text != text:
            self._cache(self._notation.read(text, reported_name, stderr_file))

    def _cache(self, number: int) -> None:
        """Remember the integer that the current written member holds."""
        self._int_value = number
        self._cached_text = self._read_text()

    @classmethod
    def factory(cls, prefix: PrefixT, digits: int = 0,
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
            prefix: The prefix that constructed values are written with.
            digits: The smallest number of digits to write.
            value: The value of a constructed object when no JSON is given.

        Returns:
            A :class:`ConfigFactory` constructing one object of the class
            this is called on.

        Raises:
            InvalidConfiguration: ``value`` is negative, or is a string that
                does not hold a number in the notation of this class.
            InvalidConfigurationType: ``value`` is neither an integer nor a
                string.
            ValueError: ``digits`` is negative.
        """
        return _RadixFactory(cls, prefix, digits, value)

    @classmethod
    def strip_prefix(cls, value: str) -> str:
        """Strip the prefix from one written number.

        Any of the prefixes that the prefix enum of this class describes is
        removed, ignoring case, whichever prefix an object writes with. A
        prefix that is itself a digit of the notation, such as the leading
        zero of the file mode ``'0755'``, is kept, as it cannot be told from
        the padding zeros of a written value.

        Args:
            value: The written number to strip.

        Returns:
            The written number without the prefix, unchanged when it has no
            prefix that is removed before the digits are read.
        """
        return _strip_prefix(value, type(cls._no_prefix), cls._SPEC)

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
        written = MemberValidationStep(
            member_names=[self._SPEC.member_name],
            validator=self._validator_class(prefix=self._notation.prefix,
                                            digits=self._notation.digits))
        cached = WholeConfigValidationStep(validator=_RadixCacheBuilder())
        return [written, cached]


# pylint: disable-next=too-few-public-methods
class _RadixFactory(Generic[PrefixT]):
    """Construct one written number with one declared format.

    The object is what :meth:`RadixNumber.factory` returns, and it is one
    :class:`ConfigFactory`. It constructs the declared default when it is
    called without arguments, and it constructs the parsed value with the
    same format on every later parse.
    """

    def __init__(self, config_type: type['RadixNumber[PrefixT]'],
                 prefix: PrefixT, digits: int,
                 value: Optional[int | str]) -> None:
        """Remember the class and the format to construct with.

        Args:
            config_type: The class that constructed values have.
            prefix: The prefix that constructed values are written with.
            digits: The smallest number of digits to write.
            value: The value of a constructed object when no JSON is given.

        Raises:
            ValueError: ``digits`` is negative.
        """
        self._config_type = config_type
        self._prefix = prefix
        self._digits = _checked_digits(digits)
        self._value = value

    def __call__(self, *, from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 stderr_file: TextIO = sys.stderr,
                 member_name: Optional[str] = None) -> 'RadixNumber[PrefixT]':
        """Construct one written number with the declared format.

        Args:
            from_json_data_text: Optional JSON text to parse directly.
            from_json_filename: Optional path to a JSON file to read.
            stderr_file: Stream used for user-facing diagnostics.
            member_name: Dotted and indexed path for reaching the constructed
                value by traversing nested attributes from the top level of
                the complete construction, such as ``limits[cpu].mask``.
                ``None`` means that the constructed value is the top level
                and not a member of anything.

        Returns:
            The constructed value.
        """
        if use_member_name(self._config_type, stacklevel=2):
            return self._config_type(from_json_data_text, from_json_filename,
                                     None, stderr_file, value=self._value,
                                     prefix=self._prefix, digits=self._digits,
                                     member_name=member_name)
        return self._config_type(from_json_data_text, from_json_filename, None,
                                 stderr_file, value=self._value,
                                 prefix=self._prefix, digits=self._digits)


# pylint: disable-next=too-few-public-methods
class _RadixCacheBuilder(WholeConfigValidator):
    """A normalizer for a RadixNumber configuration value.

    The normalizer makes sure the cached integer matches the written member.
    It is the last step of the validation plan, so that the value a parse or
    an earlier step produced is cached at once instead of on the first read
    of the value.
    """

    def validate(self, config: Config, stderr_file: TextIO = sys.stderr, *,
                 member_name: Optional[str] = None) -> None:
        """Rebuild the cached integer of the RadixNumber.

        Args:
            config: The RadixNumber object to normalize.
            stderr_file: The file to write error messages to.
            member_name: Dotted and indexed path for reaching ``config``
                by traversing nested attributes from the top level of the
                complete ``validate()`` operation, such as
                ``outputs[1].section``. ``None`` means that ``config`` is the
                top level and not a member of anything.

        Raises:
            InvalidConfiguration: The written member does not hold a number
                in the notation of the value.
        """
        assert isinstance(config, RadixNumber)
        written = member_path(member_name, config.written_member_name())
        # pylint: disable-next=protected-access
        config._rebuild_cache(written, stderr_file)
