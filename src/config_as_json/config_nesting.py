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
    ``DICT_VALUE_BY_KEY`` describes one configured key inside a public dict
    member. The value stored at ``discriminator_key`` is a nested Config
    object. Other keys in the same public dict keep their ordinary JSON
    values unless they are declared by another ``DICT_VALUE_BY_KEY`` entry.
    """

    MEMBER = auto()
    OPTIONAL_MEMBER = auto()
    LIST_ELEMENT = auto()
    DICT_VALUE = auto()
    DICT_VALUE_BY_KEY = auto()


# pylint: disable-next=too-few-public-methods
class ConfigFactory(Protocol):
    """Construct one nested Config object from JSON input."""

    def __call__(self, *, from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 stderr_file: TextIO = sys.stderr,
                 member_name: Optional[str] = None,
                 ok_to_use_defaults: bool = False) -> 'Config':
        """Construct one nested Config object.

        A factory is expected to pass every argument on to the constructor
        of the class that it chooses, so that class has to accept
        ``ok_to_use_defaults`` as well.

        The library calls the factory for every nested object that the JSON
        data contains, also when the object being parsed already holds a
        nested object at the same place. A factory chooses the class from
        the JSON data, so the library never parses the JSON data into the
        current nested object. With ``ok_to_use_defaults`` true, the keys
        that the JSON data lacks therefore keep the default values of the
        class that the factory constructs, not the values of the current
        nested object.

        Args:
            from_json_data_text: Optional JSON text to parse directly.
            from_json_filename: Optional path to a JSON file to read.
            stderr_file: Stream used for user-facing diagnostics.
            member_name: Dotted and indexed path for reaching the constructed
                object by traversing nested attributes from the top level of
                the complete construction, such as ``outputs[1].section``.
                ``None`` means that the constructed object is the top level
                and not a member of anything.
            ok_to_use_defaults: Whether the JSON data may lack required
                keys, which then keep the default values of the constructed
                class. See :meth:`Config.parse_json` and
                :meth:`Config.kept_value_paths`.

        Returns:
            The constructed nested Config object.
        """
        raise NotImplementedError


class ConfigNesting(NamedTuple):
    """Describe one nested Config declaration.

    The nested class must derive from :class:`Config` and must be
    constructible with keyword arguments ``from_json_data_text``,
    ``from_json_filename``, and ``stderr_file``, and should accept
    ``member_name`` as well. This is the constructor shape used by the base
    class when it reads a nested JSON object. A class or a factory that does
    not accept ``member_name`` is called without it and warns that it should
    be changed. If ``factory_function`` is set, that callable is used instead
    of the ``config_type`` constructor. The factory must accept the same
    keyword arguments, should accept ``ok_to_use_defaults`` as well, see
    :class:`ConfigFactory`, and must return an instance of ``config_type`` or
    a subclass.

    When the parent is parsed with ``ok_to_use_defaults`` true, a nested
    class is constructed with ``ok_to_use_defaults=True`` if its constructor
    accepts it. Another class is constructed from its class defaults, which
    are then validated on their own, and the JSON data is then parsed into
    it. Only a class whose defaults are not valid on their own needs to
    accept ``ok_to_use_defaults`` and pass it on to ``super().__init__``. A
    factory is called with ``ok_to_use_defaults=True`` if it accepts it. A
    factory that does not accept it is called without it, so it parses
    strictly, and warns that it should be changed.

    A member declared with ``factory_function`` is never parsed into its
    current nested object, since the factory chooses the class from the
    JSON data. With ``ok_to_use_defaults`` true, its missing keys keep the
    default values of the class that the factory constructs, not the values
    of the current nested object. Without a factory, a nested object of
    exactly ``config_type`` that is a ``MEMBER``, an ``OPTIONAL_MEMBER`` or a
    dict value is parsed into in place, and keeps its values. See
    :meth:`Config.kept_value_paths`.

    Attributes:
        kind: Where the nested configuration object is stored.
        config_type: Config-derived type expected for this member.
        discriminator_key: Dict key used by ``DICT_VALUE_BY_KEY``.
        factory_function: Optional callable used to construct JSON objects.
    """

    kind: ConfigNestingKind
    config_type: Type['Config']
    discriminator_key: Optional[str] = None
    factory_function: Optional[ConfigFactory] = None


type NestedConfigs = dict[str, ConfigNesting | list[ConfigNesting]]
"""Return type of :meth:`Config.nested_configs` declarations.

Use a direct :class:`ConfigNesting` value for one nested declaration. Use
the list form only when every list element has kind
``ConfigNestingKind.DICT_VALUE_BY_KEY`` and the entries describe selected
keys inside the same Config member variable of dict type.
"""
