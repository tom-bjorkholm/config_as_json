#! /usr/local/bin/python3
"""Apply decoded configuration JSON data to the members of a Config object.

``Config.parse_json`` decodes the JSON text and lets the read-old processor
normalize it, then calls the functions here: one checks the keys of the
data against the public members, and one assigns the data to the members.

The private state of the ``Config`` object that these functions need is
passed in as arguments, so that this module uses only the public interface
of ``Config``.
"""

# Copyright (c) 2024-2026 Tom Björkholm
# MIT License

from typing import Optional, TextIO, TYPE_CHECKING
from config_as_json.config_auto_change_hook import ConfigAutoChangeHook
from config_as_json.config_nesting import ConfigNesting
from config_as_json._config_key_check import fill_missing_keys
from config_as_json._config_nesting_io import _nested_config_from_json
from config_as_json.member_path import member_path


if TYPE_CHECKING:
    from config_as_json.config import Config


def public_member_names(config: 'Config') -> list[str]:
    """Return the names of the public configuration members of ``config``.

    A public configuration member is an instance attribute whose name does
    not start with ``_`` and whose value is not callable.
    """
    return [i for i in vars(config).keys() if not
            callable(getattr(config, i)) and not i.startswith('_')]


# pylint: disable-next=too-many-arguments,too-many-positional-arguments
def check_parsed_keys(config: 'Config', data: dict[str, object],
                      self_keys: list[str], omit_none_keys: list[str],
                      ok_to_use_defaults: bool, stderr_file: TextIO, *,
                      member_name: Optional[str]) -> None:
    """Check the keys of the data against the public members.

    In strict parsing, an omit-when-None member that the data lacks is set
    to ``None``.

    Args:
        config: Configuration object that the data is parsed into.
        data: Decoded JSON data, after the read-old processor.
        self_keys: Public configuration member names of ``config``.
        omit_none_keys: Members that the data may lack in strict parsing.
        ok_to_use_defaults: Whether missing members keep their values.
        stderr_file: Stream used for user-facing diagnostics.
        member_name: Dotted and indexed path for reaching ``config`` from
            the top level of the complete ``parse_json()`` operation, or
            ``None`` when ``config`` is that top level.

    Raises:
        ConfigMissingKey: The data has no value for a required member.
        ConfigUnknownKey: The data has a key that is not a member.
    """
    config.check_key_match(self_keys, list(data.keys()), ok_to_use_defaults,
                           stderr_file, omit_none_keys,
                           member_name=member_name)
    if not ok_to_use_defaults:
        for i in omit_none_keys:
            if i not in data:
                setattr(config, i, None)


# pylint: disable-next=too-many-arguments
def assign_parsed_members(config: 'Config', data: dict[str, object],
                          self_keys: list[str], ok_to_use_defaults: bool,
                          stderr_file: TextIO, *, member_name: Optional[str],
                          nested_decls: dict[str, list[ConfigNesting]],
                          unchecked_dicts: list[str],
                          auto_ch_hook: ConfigAutoChangeHook) -> None:
    """Assign the values of the data to the public members of ``config``.

    Members are assigned in the order of ``self_keys``. A member that the
    data lacks is left unchanged.

    Args:
        config: Configuration object that the data is parsed into.
        data: Decoded JSON data, after the read-old processor and the key
            check.
        self_keys: Public configuration member names of ``config``.
        ok_to_use_defaults: Whether missing dict keys may keep defaults.
        stderr_file: Stream used for user-facing diagnostics.
        member_name: Dotted and indexed path for reaching ``config`` from
            the top level of the complete ``parse_json()`` operation, or
            ``None`` when ``config`` is that top level.
        nested_decls: Validated nested Config declarations of ``config``.
        unchecked_dicts: Dict members whose keys are not checked.
        auto_ch_hook: Hook of ``config`` receiving the automatic changes of
            nested Config objects.

    Raises:
        ConfigParseError: A value does not fit its member.
    """
    for key in self_keys:
        if key not in data:
            continue
        if key in nested_decls:
            value = _nested_config_from_json(member_name=key,
                                             json_data=data[key],
                                             nestings=nested_decls[key],
                                             stderr_file=stderr_file,
                                             auto_ch_hook=auto_ch_hook,
                                             parent_path=member_name)
        else:
            value = _checked_plain_value(config, key, data[key],
                                         ok_to_use_defaults, unchecked_dicts,
                                         stderr_file, member_name=member_name)
        setattr(config, key, value)


# pylint: disable-next=too-many-arguments,too-many-positional-arguments
def _checked_plain_value(config: 'Config', key: str, json_value: object,
                         ok_to_use_defaults: bool, unchecked_dicts: list[str],
                         stderr_file: TextIO, *,
                         member_name: Optional[str]) -> object:
    """Return the JSON value of a member that is not a nested Config.

    The value is checked against the current value of the member with
    ``Config.check_dict_parse`` first. When ``ok_to_use_defaults`` is true,
    the missing keys of checked dicts are then filled with deep copies of
    the current values.

    Args:
        config: Configuration object that holds the member.
        key: Name of the member.
        json_value: Decoded JSON value for the member.
        ok_to_use_defaults: Whether missing dict keys may keep defaults.
        unchecked_dicts: Dict members whose keys are not checked.
        stderr_file: Stream used for user-facing diagnostics.
        member_name: Dotted and indexed path for reaching ``config`` from
            the top level of the complete ``parse_json()`` operation, or
            ``None`` when ``config`` is that top level.

    Returns:
        The value to assign to the member.
    """
    config.check_dict_parse(getattr(config, key), json_value, key,
                            ok_to_use_defaults, unchecked_dicts, stderr_file,
                            member_name=member_path(member_name, key),
                            json_path=(key,))
    if not ok_to_use_defaults:
        return json_value
    value, _ = fill_missing_keys(getattr(config, key), json_value, key,
                                 unchecked_dicts, (key,))
    return value
