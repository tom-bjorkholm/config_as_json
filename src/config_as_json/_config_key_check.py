#! /usr/local/bin/python3
"""Check parsed JSON keys against the keys a configuration declares.

This private module implements the bodies of the public static methods
``Config.check_key_match`` and ``Config.check_dict_parse``. Those methods
keep their signatures and docstrings and delegate here. The recursion of
the dict check calls the functions of this module directly, as it always
called the ``Config`` methods by class name and never an override. The
module also fills the missing keys of checked dicts when defaults may be
used.
"""

# Copyright (c) 2024-2026 Tom Björkholm
# MIT License

from copy import deepcopy
from typing import Optional, TextIO
from config_as_json.commontypes import JsonPath
from config_as_json.config_errors import ConfigMissingKey, ConfigNotDict, \
    ConfigUnexpectedDict, ConfigUnknownKey
from config_as_json.member_path import member_path, _indexed_path


# pylint: disable-next=too-many-arguments
def check_key_match_impl(expected_keys: list[str], j_keys: list[str],
                         ok_to_use_defaults: bool, stderr_file: TextIO,
                         allowed_missing_keys: Optional[list[str]] = None, *,
                         member_name: Optional[str] = None,
                         dict_keys: bool = False,
                         json_path: JsonPath = ()) -> None:
    """Validate that parsed keys match the declared configuration keys.

    See :meth:`Config.check_key_match` for the meaning of the arguments.

    Raises:
        ConfigMissingKey: The JSON data is missing a required key.
        ConfigUnknownKey: The JSON data contains an unexpected key.
    """
    key_path = _indexed_path if dict_keys else member_path
    if allowed_missing_keys is None:
        allowed_missing_keys = []
    if not ok_to_use_defaults:
        for i in expected_keys:
            if i not in j_keys and i not in allowed_missing_keys:
                path = key_path(member_name, i)
                errmsg = f'No value for {path} in JSON data'
                print(errmsg, file=stderr_file)
                raise ConfigMissingKey(errmsg, missing_key=i, member_name=path,
                                       json_path=json_path + (i,))
    for i in j_keys:
        if i not in expected_keys:
            path = key_path(member_name, i)
            errmsg = f'Unexpected parameter {path} in JSON data'
            print(errmsg, file=stderr_file)
            raise ConfigUnknownKey(errmsg, unknown_key=i, member_name=path,
                                   json_path=json_path + (i,))


# pylint: disable-next=too-many-arguments,too-many-positional-arguments
def check_dict_parse_impl(self_data: object, json_data: object, key: str,
                          ok_to_use_defaults: bool, unchecked_dicts: list[str],
                          stderr_file: TextIO, *,
                          member_name: Optional[str] = None,
                          json_path: Optional[JsonPath] = None) -> None:
    """Recursively validate nested dictionaries against default values.

    See :meth:`Config.check_dict_parse` for the meaning of the arguments.

    Raises:
        ConfigNotDict: The default is a dict but the JSON value is not.
        ConfigUnexpectedDict: The JSON value is a dict but the default is
            not.
        ConfigMissingKey: A nested dictionary misses a required key.
        ConfigUnknownKey: A nested dictionary has an unexpected key.
    """
    value_name = key if member_name is None else member_name
    checked_path = (key,) if json_path is None else json_path
    if not isinstance(self_data, dict) and \
            not isinstance(json_data, dict):
        return
    if isinstance(self_data, dict):
        if not isinstance(json_data, dict):
            errmsg = f'Not dictionary for {value_name} in JSON data'
            print(errmsg, file=stderr_file)
            raise ConfigNotDict(errmsg, member_name=value_name,
                                json_path=checked_path)
    if not isinstance(self_data, dict):
        errmsg = f'Unexpected dictionary for {value_name} in JSON data'
        print(errmsg, file=stderr_file)
        raise ConfigUnexpectedDict(errmsg, member_name=value_name,
                                   json_path=checked_path)
    if key in unchecked_dicts:
        return
    assert isinstance(self_data, dict)
    assert isinstance(json_data, dict)
    check_key_match_impl(list(self_data.keys()), list(json_data.keys()),
                         ok_to_use_defaults, stderr_file,
                         member_name=member_name, dict_keys=True,
                         json_path=checked_path)
    for i in self_data.keys():
        if i in json_data:
            value_path = _indexed_path(member_name, i)
            check_dict_parse_impl(self_data[i], json_data[i], i,
                                  ok_to_use_defaults, unchecked_dicts,
                                  stderr_file, member_name=value_path,
                                  json_path=checked_path + (i,))


def fill_missing_keys(self_data: object, json_data: object, key: str,
                      unchecked_dicts: list[str], json_path: JsonPath) \
        -> tuple[object, list[JsonPath]]:
    """Return the JSON value with the missing keys of checked dicts filled.

    The value is expected to have passed ``check_dict_parse_impl`` with
    ``ok_to_use_defaults`` true, so a checked dict in the JSON value has no
    unknown keys. The same name-based rule decides which dicts are checked:
    a dict whose key name is in ``unchecked_dicts`` is not filled, at any
    depth. A missing key gets a deep copy of the current value, so that the
    parsed value never shares data with the current value, which may be a
    default dict assigned by reference. The JSON keys keep their order, and
    the filled keys follow in the order of the current dict.

    Args:
        self_data: Current value of the key, before the parse.
        json_data: Parsed JSON value for the same key.
        key: Name of the key, used for the ``unchecked_dicts`` rule.
        unchecked_dicts: Key names whose dicts are not checked.
        json_path: Tuple path of the value from the root of the JSON data.

    Returns:
        The filled value, a new dict when the value is a checked dict, and the
        ``JsonPath`` of every filled key. A filled key whose value is a dict
        is one path; the keys inside it are not listed.
    """
    if not isinstance(self_data, dict) or not isinstance(json_data, dict) \
            or key in unchecked_dicts:
        return json_data, []
    filled: dict[str, object] = {}
    paths: list[JsonPath] = []
    for i, value in json_data.items():
        filled[i], inner_paths = fill_missing_keys(self_data.get(i), value, i,
                                                   unchecked_dicts,
                                                   json_path + (i,))
        paths.extend(inner_paths)
    for i in [i for i in self_data if i not in json_data]:
        filled[i] = deepcopy(self_data[i])
        paths.append(json_path + (i,))
    return filled, paths
