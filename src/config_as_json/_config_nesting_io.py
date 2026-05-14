#! /usr/local/bin/python3
"""Read, write, and validate nested Config declarations."""

# Copyright (c) 2026 Tom Björkholm
# MIT License

from enum import Enum, IntEnum
import json
from typing import TextIO, TYPE_CHECKING, cast
from config_as_json.commontypes import JsonType
from config_as_json.config_nesting import ConfigNesting, ConfigNestingKind


if TYPE_CHECKING:
    from config_as_json.config import Config


class _NestedConfigEncoder(json.JSONEncoder):
    """Encode nested configuration JSON data with enum names."""

    def default(self, o: object) -> object:
        """Serialize enum members using their symbolic names."""
        if isinstance(o, (Enum, IntEnum)):
            return str(o.name)
        return super().default(o)


def _item_from_json(name: str, json_data: object, nesting: ConfigNesting,
                    stderr_file: TextIO) -> 'Config':
    """Construct one nested Config from one parsed JSON object.

    Args:
        name: Diagnostic name for the nested Config.
        json_data: Parsed JSON object for the nested Config.
        nesting: Nested Config declaration for the member.
        stderr_file: Stream used for user-facing diagnostics.

    Returns:
        A new nested Config instance.

    Raises:
        KeyError: JSON data is not a dictionary for a nested Config.
        TypeError: The factory returned the wrong Config type.
    """
    if not isinstance(json_data, dict):
        msg = f'Nested Config member {name} must be a JSON object'
        print(msg, file=stderr_file)
        raise KeyError(msg)
    json_text = json.dumps(json_data, cls=_NestedConfigEncoder)
    if nesting.factory_function is None:
        nested_config = nesting.config_type(
            from_json_data_text=json_text, from_json_filename=None,
            stderr_file=stderr_file)
    else:
        nested_config = nesting.factory_function(
            from_json_data_text=json_text, from_json_filename=None,
            stderr_file=stderr_file)
    if not isinstance(nested_config, nesting.config_type):
        msg = f'Nested Config factory for {name} must return '
        msg += nesting.config_type.__name__
        print(msg, file=stderr_file)
        raise TypeError(msg)
    return nested_config


def _list_from_json(member_name: str, json_data: object,
                    nesting: ConfigNesting,
                    stderr_file: TextIO) -> list['Config']:
    """Construct a list of nested Config objects from parsed JSON.

    Args:
        member_name: Public parent member receiving the nested list.
        json_data: Parsed JSON value for the member.
        nesting: Nested Config declaration for the list elements.
        stderr_file: Stream used for user-facing diagnostics.

    Returns:
        A list containing one nested Config for each JSON element.

    Raises:
        KeyError: JSON data is not a list of dictionaries.
    """
    if not isinstance(json_data, list):
        msg = f'Nested Config member {member_name} must be a JSON list'
        print(msg, file=stderr_file)
        raise KeyError(msg)
    nested_configs: list['Config'] = []
    for index, element_data in enumerate(json_data):
        element_name = f'{member_name}[{index}]'
        nested_configs.append(_item_from_json(
            name=element_name, json_data=element_data, nesting=nesting,
            stderr_file=stderr_file))
    return nested_configs


def _dict_from_json(member_name: str, json_data: object,
                    nesting: ConfigNesting,
                    stderr_file: TextIO) -> dict[str, 'Config']:
    """Construct a dict of nested Config objects from parsed JSON.

    Args:
        member_name: Public parent member receiving the nested dict.
        json_data: Parsed JSON value for the member.
        nesting: Nested Config declaration for the dict values.
        stderr_file: Stream used for user-facing diagnostics.

    Returns:
        A dict containing one nested Config for each JSON value.

    Raises:
        KeyError: JSON data is not a dict of dictionaries.
    """
    if not isinstance(json_data, dict):
        msg = f'Nested Config member {member_name} must be a JSON object'
        print(msg, file=stderr_file)
        raise KeyError(msg)
    nested_configs: dict[str, 'Config'] = {}
    for key, value_data in json_data.items():
        if not isinstance(key, str):
            msg = f'Nested Config member {member_name} keys must be strings'
            print(msg, file=stderr_file)
            raise KeyError(msg)
        value_name = f'{member_name}[{key}]'
        nested_configs[key] = _item_from_json(
            name=value_name, json_data=value_data, nesting=nesting,
            stderr_file=stderr_file)
    return nested_configs


def _nesting_by_key(nestings: list[ConfigNesting]) \
        -> dict[str, ConfigNesting]:
    """Return DICT_VALUE_BY_KEY declarations keyed by discriminator_key."""
    nesting_by_key: dict[str, ConfigNesting] = {}
    for nesting in nestings:
        key = nesting.discriminator_key
        assert key is not None
        nesting_by_key[key] = nesting
    return nesting_by_key


def _dict_by_key_from_json(member_name: str, json_data: object,
                           nestings: list[ConfigNesting],
                           stderr_file: TextIO) -> dict[str, object]:
    """Construct selected dict values as nested Config objects.

    Args:
        member_name: Public parent member receiving the nested dict.
        json_data: Parsed JSON value for the member.
        nestings: Nested Config declarations for selected dict keys.
        stderr_file: Stream used for user-facing diagnostics.

    Returns:
        A dictionary where declared keys contain nested Config objects and
        undeclared keys keep their parsed JSON values.

    Raises:
        KeyError: JSON data is not a dictionary or a declared key does not
            contain a JSON object.
    """
    if not isinstance(json_data, dict):
        msg = f'Nested Config member {member_name} must be a JSON object'
        print(msg, file=stderr_file)
        raise KeyError(msg)
    nesting_by_key = _nesting_by_key(nestings)
    nested_configs: dict[str, object] = {}
    for key, value_data in json_data.items():
        if not isinstance(key, str):
            msg = f'Nested Config member {member_name} keys must be strings'
            print(msg, file=stderr_file)
            raise KeyError(msg)
        if key in nesting_by_key:
            value_name = f'{member_name}[{key}]'
            nested_configs[key] = _item_from_json(
                name=value_name, json_data=value_data,
                nesting=nesting_by_key[key], stderr_file=stderr_file)
        else:
            nested_configs[key] = value_data
    return nested_configs


def _is_dict_value_by_key(nestings: list[ConfigNesting]) -> bool:
    """Return whether the declarations describe keyed dict values."""
    return nestings[0].kind == ConfigNestingKind.DICT_VALUE_BY_KEY


def _single_nesting(nestings: list[ConfigNesting]) -> ConfigNesting:
    """Return the single declaration for non-keyed nesting kinds."""
    assert len(nestings) == 1
    return nestings[0]


def _nested_config_from_json(member_name: str, json_data: object,
                             nestings: list[ConfigNesting],
                             stderr_file: TextIO) -> object:
    """Construct nested Config data from parsed JSON data.

    Args:
        member_name: Public parent member receiving the nested data.
        json_data: Parsed JSON value for the member.
        nestings: Nested Config declarations for the member.
        stderr_file: Stream used for user-facing diagnostics.

    Returns:
        A nested Config, ``None`` for optional JSON null, a list of nested
        Config objects, or a dict of nested Config objects.
    """
    if _is_dict_value_by_key(nestings):
        return _dict_by_key_from_json(
            member_name=member_name, json_data=json_data, nestings=nestings,
            stderr_file=stderr_file)
    nesting = _single_nesting(nestings)
    if nesting.kind == ConfigNestingKind.LIST_ELEMENT:
        return _list_from_json(member_name=member_name, json_data=json_data,
                               nesting=nesting, stderr_file=stderr_file)
    if nesting.kind == ConfigNestingKind.DICT_VALUE:
        return _dict_from_json(member_name=member_name, json_data=json_data,
                               nesting=nesting, stderr_file=stderr_file)
    if json_data is None and nesting.kind == ConfigNestingKind.OPTIONAL_MEMBER:
        return None
    return _item_from_json(name=member_name, json_data=json_data,
                           nesting=nesting, stderr_file=stderr_file)


def _item_json_data(member_name: str, member_value: object,
                    nesting: ConfigNesting,
                    stderr_file: TextIO) -> dict[str, JsonType]:
    """Return JSON data for one nested Config object.

    Args:
        member_name: Diagnostic name for the nested Config.
        member_value: Current nested Config value.
        nesting: Nested Config declaration for the member.
        stderr_file: Stream used for user-facing diagnostics.

    Returns:
        A JSON-compatible dictionary.

    Raises:
        TypeError: The member value is not a valid nested Config object.
    """
    if not isinstance(member_value, nesting.config_type):
        msg = f'Nested Config member {member_name} must be '
        msg += nesting.config_type.__name__
        raise TypeError(msg)
    json_data = json.loads(member_value.as_json_string(
        stderr_file=stderr_file))
    assert isinstance(json_data, dict)
    return cast(dict[str, JsonType], json_data)


def _list_json_data(member_name: str, member_value: object,
                    nesting: ConfigNesting,
                    stderr_file: TextIO) -> list[JsonType]:
    """Return JSON data for a list of nested Config objects.

    Args:
        member_name: Public parent member being serialized.
        member_value: Current nested list value.
        nesting: Nested Config declaration for the list elements.
        stderr_file: Stream used for user-facing diagnostics.

    Returns:
        A JSON-compatible list.

    Raises:
        TypeError: The member value is not a list of nested Config objects.
    """
    if not isinstance(member_value, list):
        msg = f'Nested Config member {member_name} must be a list'
        raise TypeError(msg)
    json_data: list[JsonType] = []
    for index, element_value in enumerate(member_value):
        element_name = f'{member_name}[{index}]'
        element_data = _item_json_data(
            member_name=element_name, member_value=element_value,
            nesting=nesting, stderr_file=stderr_file)
        json_data.append(element_data)
    return json_data


def _dict_json_data(member_name: str, member_value: object,
                    nesting: ConfigNesting,
                    stderr_file: TextIO) -> dict[str, JsonType]:
    """Return JSON data for a dict of nested Config objects.

    Args:
        member_name: Public parent member being serialized.
        member_value: Current nested dict value.
        nesting: Nested Config declaration for the dict values.
        stderr_file: Stream used for user-facing diagnostics.

    Returns:
        A JSON-compatible dict.

    Raises:
        TypeError: The member value is not a dict of nested Config objects.
    """
    if not isinstance(member_value, dict):
        msg = f'Nested Config member {member_name} must be a dict'
        raise TypeError(msg)
    json_data: dict[str, JsonType] = {}
    for key, value in member_value.items():
        if not isinstance(key, str):
            msg = f'Nested Config member {member_name} keys must be strings'
            raise TypeError(msg)
        value_name = f'{member_name}[{key}]'
        json_data[key] = _item_json_data(
            member_name=value_name, member_value=value, nesting=nesting,
            stderr_file=stderr_file)
    return json_data


def _is_config_object(value: object) -> bool:
    """Return whether value is a Config object without import-time cycles."""
    return any(cls.__module__ == 'config_as_json.config' and
               cls.__name__ == 'Config' for cls in type(value).mro())


def _dict_by_key_json_data(member_name: str, member_value: object,
                           nestings: list[ConfigNesting],
                           stderr_file: TextIO) -> dict[str, JsonType]:
    """Return JSON data for a dict with selected nested Config values.

    Args:
        member_name: Public parent member being serialized.
        member_value: Current nested dict value.
        nestings: Nested Config declarations for selected dict keys.
        stderr_file: Stream used for user-facing diagnostics.

    Returns:
        A JSON-compatible dict.

    Raises:
        TypeError: The member value is not a dict, a key is not a string, or
            an undeclared key stores a Config object.
    """
    if not isinstance(member_value, dict):
        msg = f'Nested Config member {member_name} must be a dict'
        raise TypeError(msg)
    nesting_by_key = _nesting_by_key(nestings)
    json_data: dict[str, JsonType] = {}
    for key, value in member_value.items():
        if not isinstance(key, str):
            msg = f'Nested Config member {member_name} keys must be strings'
            raise TypeError(msg)
        if key in nesting_by_key:
            value_name = f'{member_name}[{key}]'
            json_data[key] = _item_json_data(
                member_name=value_name, member_value=value,
                nesting=nesting_by_key[key], stderr_file=stderr_file)
        elif _is_config_object(value):
            msg = f'Nested Config member {member_name}[{key}] has no '
            msg += 'DICT_VALUE_BY_KEY declaration'
            raise TypeError(msg)
        else:
            json_data[key] = cast(JsonType, value)
    return json_data


def _nested_config_json_data(member_name: str, member_value: object,
                             nestings: list[ConfigNesting],
                             stderr_file: TextIO) -> JsonType:
    """Return JSON data for one nested Config declaration.

    Args:
        member_name: Public parent member being serialized.
        member_value: Current value of that member.
        nestings: Nested Config declarations for the member.
        stderr_file: Stream used for user-facing diagnostics.

    Returns:
        JSON-compatible data for the configured nesting kind.
    """
    if _is_dict_value_by_key(nestings):
        return _dict_by_key_json_data(
            member_name=member_name, member_value=member_value,
            nestings=nestings, stderr_file=stderr_file)
    nesting = _single_nesting(nestings)
    if nesting.kind == ConfigNestingKind.LIST_ELEMENT:
        return _list_json_data(member_name=member_name,
                               member_value=member_value, nesting=nesting,
                               stderr_file=stderr_file)
    if nesting.kind == ConfigNestingKind.DICT_VALUE:
        return _dict_json_data(member_name=member_name,
                               member_value=member_value, nesting=nesting,
                               stderr_file=stderr_file)
    if member_value is None and \
            nesting.kind == ConfigNestingKind.OPTIONAL_MEMBER:
        return None
    return _item_json_data(member_name=member_name, member_value=member_value,
                           nesting=nesting, stderr_file=stderr_file)


def _validate_item(member_name: str, member_value: object,
                   nesting: ConfigNesting, stderr_file: TextIO) -> None:
    """Validate one nested Config object.

    Args:
        member_name: Diagnostic name for the nested Config.
        member_value: Current nested Config value.
        nesting: Nested Config declaration for the member.
        stderr_file: Stream used for user-facing diagnostics.

    Raises:
        TypeError: The member value is not a valid nested Config object.
    """
    if not isinstance(member_value, nesting.config_type):
        msg = f'Nested Config member {member_name} must be '
        msg += nesting.config_type.__name__
        print(msg, file=stderr_file)
        raise TypeError(msg)
    member_value.validate(stderr_file=stderr_file)


def _validate_list(member_name: str, member_value: object,
                   nesting: ConfigNesting, stderr_file: TextIO) -> None:
    """Validate a list of nested Config objects.

    Args:
        member_name: Public parent member containing the nested list.
        member_value: Current nested list value.
        nesting: Nested Config declaration for the list elements.
        stderr_file: Stream used for user-facing diagnostics.

    Raises:
        TypeError: The member value is not a list of nested Config objects.
    """
    if not isinstance(member_value, list):
        msg = f'Nested Config member {member_name} must be a list'
        print(msg, file=stderr_file)
        raise TypeError(msg)
    for index, element_value in enumerate(member_value):
        element_name = f'{member_name}[{index}]'
        _validate_item(member_name=element_name, member_value=element_value,
                       nesting=nesting, stderr_file=stderr_file)


def _validate_dict(member_name: str, member_value: object,
                   nesting: ConfigNesting, stderr_file: TextIO) -> None:
    """Validate a dict of nested Config objects.

    Args:
        member_name: Public parent member containing the nested dict.
        member_value: Current nested dict value.
        nesting: Nested Config declaration for the dict values.
        stderr_file: Stream used for user-facing diagnostics.

    Raises:
        TypeError: The member value is not a dict of nested Config objects.
    """
    if not isinstance(member_value, dict):
        msg = f'Nested Config member {member_name} must be a dict'
        print(msg, file=stderr_file)
        raise TypeError(msg)
    for key, value in member_value.items():
        if not isinstance(key, str):
            msg = f'Nested Config member {member_name} keys must be strings'
            print(msg, file=stderr_file)
            raise TypeError(msg)
        value_name = f'{member_name}[{key}]'
        _validate_item(member_name=value_name, member_value=value,
                       nesting=nesting, stderr_file=stderr_file)


def _validate_dict_by_key(member_name: str, member_value: object,
                          nestings: list[ConfigNesting],
                          stderr_file: TextIO) -> None:
    """Validate a dict with selected nested Config values.

    Args:
        member_name: Public parent member containing the nested dict.
        member_value: Current nested dict value.
        nestings: Nested Config declarations for selected dict keys.
        stderr_file: Stream used for user-facing diagnostics.

    Raises:
        TypeError: The member value is not a dict, a key is not a string, an
            undeclared key stores a Config object, or a declared key has the
            wrong nested Config type.
    """
    if not isinstance(member_value, dict):
        msg = f'Nested Config member {member_name} must be a dict'
        print(msg, file=stderr_file)
        raise TypeError(msg)
    nesting_by_key = _nesting_by_key(nestings)
    for key, value in member_value.items():
        if not isinstance(key, str):
            msg = f'Nested Config member {member_name} keys must be strings'
            print(msg, file=stderr_file)
            raise TypeError(msg)
        value_name = f'{member_name}[{key}]'
        if key in nesting_by_key:
            _validate_item(member_name=value_name, member_value=value,
                           nesting=nesting_by_key[key],
                           stderr_file=stderr_file)
        elif _is_config_object(value):
            msg = f'Nested Config member {value_name} has no '
            msg += 'DICT_VALUE_BY_KEY declaration'
            print(msg, file=stderr_file)
            raise TypeError(msg)


def _validate_nested_config(member_name: str, member_value: object,
                            nestings: list[ConfigNesting],
                            stderr_file: TextIO) -> None:
    """Validate one nested Config declaration.

    Args:
        member_name: Public parent member containing the nested data.
        member_value: Current value of that member.
        nestings: Nested Config declarations for the member.
        stderr_file: Stream used for user-facing diagnostics.

    Raises:
        TypeError: The member value does not match the nesting kind.
    """
    if _is_dict_value_by_key(nestings):
        _validate_dict_by_key(
            member_name=member_name, member_value=member_value,
            nestings=nestings, stderr_file=stderr_file)
        return
    nesting = _single_nesting(nestings)
    if nesting.kind == ConfigNestingKind.LIST_ELEMENT:
        _validate_list(member_name=member_name, member_value=member_value,
                       nesting=nesting, stderr_file=stderr_file)
        return
    if nesting.kind == ConfigNestingKind.DICT_VALUE:
        _validate_dict(member_name=member_name, member_value=member_value,
                       nesting=nesting, stderr_file=stderr_file)
        return
    if member_value is None and \
            nesting.kind == ConfigNestingKind.OPTIONAL_MEMBER:
        return
    _validate_item(member_name=member_name, member_value=member_value,
                   nesting=nesting, stderr_file=stderr_file)
