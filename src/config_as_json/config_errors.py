#! /usr/local/bin/python3
"""Define the exceptions for problems found in configuration JSON data.

Every problem that :meth:`Config.parse_json` finds in the JSON data it is
given is raised as a :class:`ConfigParseError`, so an application, such as a
helpful editor of the configuration file, can tell the problems apart by
their type, and find where in the data the problem is from data members,
without parsing the message text.

Each specific exception also derives from the exception type that was raised
for the same problem before these types existed, ``KeyError`` or
:class:`ConfigBadJson`, so existing ``except`` clauses keep working.

Two data members tell where the problem is. ``member_name`` is the reported
path text, such as ``outputs[1].section.kind``, written for a person to read
(see :mod:`config_as_json.member_path`). ``json_path`` is the same location as
a :data:`JsonPath` tuple, such as ``('outputs', 1, 'section', 'kind')``, for a
program to follow into the JSON data without parsing text.

``json_path`` is relative to the JSON data of the outermost ``parse_json()``
operation, which is the data read from the configuration file. It addresses
that data after the rules for reading an old configuration file have been
applied, so a key that such a rule moved or renamed is addressed where the
rule put it.
"""

# Copyright (c) 2026 Tom Björkholm
# MIT License

import json
from typing import Optional
from config_as_json.commontypes import JsonPath


class ConfigParseError(Exception):
    """Base of every problem found in configuration JSON data.

    ``str()`` of the exception is the message exactly as it was printed to
    the diagnostics stream. The quotation marks that ``KeyError`` would
    otherwise put around it are not added.

    Attributes:
        member_name: Reported path of the value that the problem is about,
            such as ``outputs[1].section.kind``. ``None`` means the root of
            the JSON data of the configuration object that was parsed.
        json_path: Path of the same value as a tuple of dict keys (``str``)
            and list indices (``int``) from the root of the JSON data of the
            outermost ``parse_json()`` operation. The empty tuple means that
            root itself.
    """

    def __init__(self, *args: object, member_name: Optional[str],
                 json_path: JsonPath) -> None:
        """Initialize the exception.

        Args:
            args: Arguments for the next exception class in the method
                resolution order, normally the message only.
            member_name: Reported path of the value the problem is about.
            json_path: Tuple path of the same value.
        """
        super().__init__(*args)
        self.member_name: Optional[str] = member_name
        self.json_path: JsonPath = json_path

    def __str__(self) -> str:
        """Return the message without quotation marks added."""
        return BaseException.__str__(self)


class ConfigMissingKey(ConfigParseError, KeyError):
    """The JSON data has no value for a key the configuration requires.

    ``member_name`` and ``json_path`` address the missing key itself, as if
    it were present.

    Attributes:
        missing_key: Local name of the missing key in the object or the dict
            that should contain it.
    """

    def __init__(self, message: str, *, missing_key: str, member_name: str,
                 json_path: JsonPath) -> None:
        """Initialize the exception.

        Args:
            message: Message for the user.
            missing_key: Local name of the missing key.
            member_name: Reported path of the missing key.
            json_path: Tuple path of the missing key.
        """
        super().__init__(message, member_name=member_name, json_path=json_path)
        self.missing_key: str = missing_key


class ConfigUnknownKey(ConfigParseError, KeyError):
    """The JSON data has a key that the configuration does not declare.

    ``member_name`` and ``json_path`` address the unexpected key itself.

    Attributes:
        unknown_key: Local name of the unexpected key in the object or the
            dict that contains it.
    """

    def __init__(self, message: str, *, unknown_key: str, member_name: str,
                 json_path: JsonPath) -> None:
        """Initialize the exception.

        Args:
            message: Message for the user.
            unknown_key: Local name of the unexpected key.
            member_name: Reported path of the unexpected key.
            json_path: Tuple path of the unexpected key.
        """
        super().__init__(message, member_name=member_name, json_path=json_path)
        self.unknown_key: str = unknown_key


class ConfigWrongShape(ConfigParseError, KeyError):
    """A value in the JSON data has the wrong JSON shape.

    ``member_name`` and ``json_path`` address the value with the wrong shape.
    """


class ConfigMustBeList(ConfigWrongShape):
    """A value is not a list where a list is required."""


class ConfigNotDict(ConfigWrongShape):
    """A value is not a dict where a dict is required."""


class ConfigUnexpectedDict(ConfigWrongShape):
    """A value is a dict where another shape is required."""


class ConfigKeysNotStrings(ConfigWrongShape):
    """A dict in the data has keys that are not strings.

    ``member_name`` and ``json_path`` address the dict.
    """


class ConfigBadJson(ConfigParseError, json.JSONDecodeError):
    """Report JSON input that could not be interpreted as configuration.

    The data members ``msg``, ``doc``, ``pos``, ``lineno`` and ``colno`` are
    those of ``json.JSONDecodeError``. Only for :class:`ConfigMustBeJson` do
    they locate the problem in the JSON text; otherwise ``pos`` is ``0``.
    """

    # pylint: disable-next=too-many-arguments
    def __init__(self, msg: str, doc: str, pos: int, *,
                 member_name: Optional[str] = None,
                 json_path: JsonPath = ()) -> None:
        """Initialize the exception.

        Args:
            msg: Message for the user.
            doc: JSON text that was being parsed, or ``''``.
            pos: Index in ``doc`` where the problem was found.
            member_name: Reported path of the configuration object whose
                JSON text it is, ``None`` for the top level.
            json_path: Tuple path of the same configuration object.
        """
        super().__init__(msg, doc, pos, member_name=member_name,
                         json_path=json_path)


class ConfigMustBeJson(ConfigBadJson):
    """The text is not JSON, or failed to parse as JSON.

    ``pos``, ``lineno`` and ``colno`` locate the problem in ``doc``.
    """


class ConfigRootNotDict(ConfigBadJson):
    """The root of the JSON text is not a dict."""


class ConfigConversionFailed(ConfigBadJson):
    """A parse converter refused the value of a key in the JSON data.

    The exception that the converter raised is the ``__cause__``.

    The converters run while the text is decoded, at a point where the
    position of the value is not known. ``member_name`` and ``json_path``
    therefore address the configuration object whose converter failed, and
    ``converted_key`` names the key. The key is usually a direct member of
    that object, but a converter applies to its key in every dict in the
    text of that configuration object.

    Attributes:
        converted_key: Key whose value the converter refused.
    """

    # pylint: disable-next=too-many-arguments
    def __init__(self, msg: str, doc: str, pos: int, *, converted_key: str,
                 member_name: Optional[str] = None,
                 json_path: JsonPath = ()) -> None:
        """Initialize the exception.

        Args:
            msg: Message for the user.
            doc: JSON text that was being parsed, or ``''``.
            pos: Index in ``doc`` where the problem was found.
            converted_key: Key whose value the converter refused.
            member_name: Reported path of the configuration object.
            json_path: Tuple path of the configuration object.
        """
        super().__init__(msg, doc, pos, member_name=member_name,
                         json_path=json_path)
        self.converted_key: str = converted_key
