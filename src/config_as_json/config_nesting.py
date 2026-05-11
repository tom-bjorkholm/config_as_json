#! /usr/local/bin/python3
"""Describe nested Config declarations."""

# Copyright (c) 2026 Tom Björkholm
# MIT License

import sys
from enum import Enum, auto
from typing import Optional, Protocol, TextIO, TYPE_CHECKING, Type, NamedTuple
from config_as_json.commontypes import PathOrStr


if TYPE_CHECKING:
    from config_as_json.config import Config


class ConfigNestingKind(Enum):
    """Describe where a nested Config object is stored.

    ``MEMBER`` describes a mandatory public member containing one nested
    Config object. ``OPTIONAL_MEMBER`` describes a public member that may be
    ``None`` or one nested Config object. ``LIST_ELEMENT`` describes a public
    member that stores a list where every element is a nested Config object.
    ``DICT_VALUE`` describes a public member that stores a dict where every
    value is a nested Config object and every key must be a string.
    ``DICT_VALUE_BY_KEY`` is reserved for future discriminated dictionary
    value support and raises ``NotImplementedError`` in this increment.
    """

    MEMBER = auto()
    OPTIONAL_MEMBER = auto()
    LIST_ELEMENT = auto()
    DICT_VALUE = auto()
    # Reserved for future discriminated dictionary-value nesting support.
    DICT_VALUE_BY_KEY = auto()


# pylint: disable-next=too-few-public-methods
class ConfigFactory(Protocol):
    """Construct one nested Config object from JSON input."""

    def __call__(self, *, from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 stderr_file: TextIO = sys.stderr) -> 'Config':
        """Construct one nested Config object.

        Args:
            from_json_data_text: Optional JSON text to parse directly.
            from_json_filename: Optional path to a JSON file to read.
            stderr_file: Stream used for user-facing diagnostics.

        Returns:
            The constructed nested Config object.
        """
        raise NotImplementedError


class ConfigNesting(NamedTuple):
    """Describe one nested Config declaration.

    The nested class must derive from :class:`Config` and must be
    constructible with keyword arguments ``from_json_data_text``,
    ``from_json_filename``, and ``stderr_file``. This is the constructor
    shape used by the base class when it reads a nested JSON object. If
    ``factory_function`` is set, that callable is used instead of the
    ``config_type`` constructor. The factory must accept the same keyword
    arguments and must return an instance of ``config_type`` or a subclass.

    Attributes:
        kind: Where the nested configuration object is stored.
        config_type: Config-derived type expected for this member.
        discriminator_key: Reserved for future ``DICT_VALUE_BY_KEY`` support.
        factory_function: Optional callable used to construct JSON objects.
    """

    kind: ConfigNestingKind
    config_type: Type['Config']
    discriminator_key: Optional[str] = None
    factory_function: Optional[ConfigFactory] = None
