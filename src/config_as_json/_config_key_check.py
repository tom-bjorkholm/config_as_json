#! /usr/local/bin/python3
"""Check parsed JSON keys against the keys a configuration declares.

This private module implements the bodies of the public static methods
``Config.check_key_match`` and ``Config.check_dict_parse``. Those methods
keep their signatures and docstrings and delegate here. The recursion of
the dict check calls the functions of this module directly, as it always
called the ``Config`` methods by class name and never an override.
"""

# Copyright (c) 2024-2026 Tom Björkholm
# MIT License

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
