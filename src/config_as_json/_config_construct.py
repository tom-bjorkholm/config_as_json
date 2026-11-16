#! /usr/local/bin/python3
"""Construct a Config object of a known class on behalf of the library.

The library constructs a Config class itself for a nested Config declared
by type, in ``config_factory_from_json``, and in the factory returned by
``RadixNumber.factory()``. Each of them passes its own other arguments, so
each hands over a :class:`ConfigMaker` that calls the constructor, and this
module decides about the keyword arguments that came later in the API:

- ``member_name`` is passed when the constructor accepts it, and a
  constructor that does not accept it warns that it should be changed.
- ``ok_to_use_defaults`` is only considered when the flag is true. A
  constructor that accepts it is called with it. Another one is constructed
  from its class defaults, which are validated on their own, and the JSON
  data is then read into it with ``ok_to_use_defaults`` true. So no derived
  class has to accept the keyword unless its defaults are not valid on
  their own.
"""

# Copyright (c) 2026 Tom Björkholm
# MIT License

from typing import Callable, Optional, Protocol, TextIO, TYPE_CHECKING, \
    TypedDict, TypeVar, Unpack
from config_as_json.commontypes import PathOrStr
from config_as_json._config_call_wrappers import wrap_parse_json, wrap_read
from config_as_json._deprecated_support import accepts_keyword, \
    use_member_name


if TYPE_CHECKING:
    from config_as_json.config import Config


ConfigT_co = TypeVar('ConfigT_co', bound='Config', covariant=True)
"""The class of the Config object that a :class:`ConfigMaker` constructs."""


class InitKeywords(TypedDict, total=False):
    """Optional keyword arguments for constructing a Config object."""

    member_name: Optional[str]
    ok_to_use_defaults: bool


# pylint: disable-next=too-few-public-methods
class ConfigMaker(Protocol[ConfigT_co]):
    """Call the constructor of one Config class with its JSON source."""

    def __call__(self, json_text: Optional[str],
                 json_filename: Optional[PathOrStr], /,
                 **keywords: Unpack[InitKeywords]) -> ConfigT_co:
        """Construct one Config object.

        Args:
            json_text: Optional JSON text, for ``from_json_data_text``.
            json_filename: Optional JSON file, for ``from_json_filename``.
            keywords: The optional keyword arguments to pass on.

        Returns:
            The constructed Config object.
        """
        raise NotImplementedError


def member_name_keywords(func: Callable[..., object],
                         member_name: Optional[str],
                         stacklevel: int) -> InitKeywords:
    """Return ``member_name`` as keyword arguments, if a callable takes it.

    Args:
        func: Class or factory function that the library is about to call.
        member_name: Dotted and indexed path for reaching the constructed
            object from the top level of the complete construction.
        stacklevel: Stack level that a warning is attributed to, counted
            from the caller of this function.

    Returns:
        The keyword arguments holding ``member_name``, or none.
    """
    if use_member_name(func, stacklevel=stacklevel + 1):
        return {'member_name': member_name}
    return {}


def _one_source(json_text: Optional[str],
                json_filename: Optional[PathOrStr]) -> bool:
    """Return whether exactly one JSON source is given."""
    return (json_text is None) != (json_filename is None)


def _read_into(config: 'Config', json_text: Optional[str],
               json_filename: Optional[PathOrStr], stderr_file: TextIO,
               member_name: Optional[str]) -> None:
    """Read the one given JSON source into a Config, keeping its values."""
    if json_text is not None:
        wrap_parse_json(config, json_text, True, stderr_file,
                        member_name=member_name)
        return
    assert json_filename is not None
    wrap_read(config, json_filename, True, stderr_file,
              member_name=member_name)


# pylint: disable-next=too-many-arguments
def construct_config(make: ConfigMaker[ConfigT_co],
                     config_type: type['Config'], json_text: Optional[str],
                     json_filename: Optional[PathOrStr],
                     ok_to_use_defaults: bool, *, stderr_file: TextIO,
                     member_name: Optional[str],
                     stacklevel: int) -> ConfigT_co:
    """Construct one Config object, keeping defaults when asked to.

    With ``ok_to_use_defaults`` false the constructor is called exactly as
    without the flag, and its signature is not checked for it. The flag
    is also not passed on without exactly one JSON source, since then it
    has no effect, and two sources are left to the constructor to reject.

    Args:
        make: Calls the constructor of ``config_type``.
        config_type: The class that ``make`` constructs.
        json_text: Optional JSON text to construct from.
        json_filename: Optional JSON file to construct from.
        ok_to_use_defaults: Whether the JSON data may lack required keys,
            which then keep the default values of the class.
        stderr_file: Stream used for user-facing diagnostics.
        member_name: Dotted and indexed path for reaching the constructed
            object from the top level of the complete construction. ``None``
            means that the constructed object is the top level.
        stacklevel: Stack level that a warning is attributed to, counted
            from the caller of this function.

    Returns:
        The constructed Config object.
    """
    keywords = member_name_keywords(config_type, member_name, stacklevel + 1)
    if ok_to_use_defaults and _one_source(json_text, json_filename):
        if not accepts_keyword(config_type, 'ok_to_use_defaults'):
            config = make(None, None, **keywords)
            _read_into(config, json_text, json_filename, stderr_file,
                       member_name)
            return config
        keywords['ok_to_use_defaults'] = True
    return make(json_text, json_filename, **keywords)
