#! /usr/local/bin/python3
"""Read, write, and validate nested Config declarations.

Every traversal here names one nested member the same way. ``member_name``
is the local name of the member in the object that holds it, with the list
index or the dict key already in square brackets for an element. It is the
name that the automatic-change hook composes its own paths from, one nesting
level at a time. ``parent_path`` is the reported path of the object that
holds the member, so ``member_path(parent_path, member_name)`` is the
reported path of the nested member itself.

While reading, the ``json_path`` of a raised ``ConfigParseError`` is relative
to the JSON data of the Config object whose ``parse_json()`` raised it. A
nested Config is constructed through its own class or factory, which cannot
be handed a tuple path, so the path of the nested object in its parent is
put in front of ``json_path`` when the exception leaves the nested object.
The kept value paths of a nested Config are prefixed the same way.

While reading with ``ok_to_use_defaults`` true, the JSON data decides which
nested objects exist, and defaults only complete them. A nested object that
the JSON data contains is parsed in place into the current nested object at
the same place, when that is of the declared class. Otherwise it is
constructed with the JSON text and ``ok_to_use_defaults`` when its
constructor accepts that, or else constructed from its class defaults and
then parsed. A declaration with a factory function is always constructed by
the factory.
"""

# Copyright (c) 2026 Tom Björkholm
# MIT License

from dataclasses import dataclass
from enum import Enum, IntEnum
import json
from typing import Optional, TextIO, TYPE_CHECKING, TypedDict, cast
from config_as_json.commontypes import JsonPath, JsonType
from config_as_json.config_errors import ConfigKeysNotStrings, \
    ConfigMustBeList, ConfigNotDict, ConfigParseError
from config_as_json.config_auto_change_hook import ConfigAutoChangeHook
from config_as_json.config_nesting import ConfigNesting, ConfigNestingKind
from config_as_json._config_call_wrappers import wrap_as_json_string, \
    wrap_parse_json, wrap_validate
from config_as_json._deprecated_support import accepts_keyword, \
    use_member_name
from config_as_json.member_path import member_path, _indexed_path


if TYPE_CHECKING:
    from config_as_json.config import Config


class _NestedConfigEncoder(json.JSONEncoder):
    """Encode nested configuration JSON data with enum names."""

    def default(self, o: object) -> object:
        """Serialize enum members using their symbolic names."""
        if isinstance(o, (Enum, IntEnum)):
            return str(o.name)
        return super().default(o)


class _InitKeywords(TypedDict, total=False):
    """Optional keyword arguments for constructing a nested Config."""

    member_name: str
    ok_to_use_defaults: bool


@dataclass(frozen=True)
class NestedReadContext:
    """What the reads of the nested Config members of one object share.

    Attributes:
        stderr_file: Stream used for user-facing diagnostics.
        auto_ch_hook: Hook of the object holding the nested data, receiving
            the automatic changes of the nested Config objects.
        ok_to_use_defaults: Whether nested JSON objects may lack the keys
            that strict parsing requires.
        kept_paths: Receives the kept value paths of every nested Config,
            prefixed with its path in the JSON data of the object holding
            it.
        parent_path: Reported path of the object holding the nested data.
    """

    stderr_file: TextIO
    auto_ch_hook: ConfigAutoChangeHook
    ok_to_use_defaults: bool
    kept_paths: list[JsonPath]
    parent_path: Optional[str]


def _constructed_defaults(config_type: 'type[Config]', path: str,
                          stderr_file: TextIO) -> 'Config':
    """Construct one Config instance holding its class defaults.

    Args:
        config_type: Config-derived class to construct.
        path: Dotted and indexed path for reaching the constructed object
            from the top level of the configuration being constructed. It
            is the ``member_name`` of the object that is built.
        stderr_file: Stream used for user-facing diagnostics.

    Returns:
        A new Config instance holding its own default values.
    """
    if use_member_name(config_type, stacklevel=2):
        return config_type(from_json_data_text=None, from_json_filename=None,
                           stderr_file=stderr_file, member_name=path)
    return config_type(from_json_data_text=None, from_json_filename=None,
                       stderr_file=stderr_file)


def _init_keywords(config_type: 'type[Config]', name: str,
                   ok_to_use_defaults: bool) -> _InitKeywords:
    """Return the optional keyword arguments for a nested constructor.

    Args:
        config_type: Config-derived class to construct.
        name: Path text for reaching the nested object. It is passed as
            ``member_name`` when the constructor accepts it.
        ok_to_use_defaults: Whether to pass ``ok_to_use_defaults=True``.
            The caller has checked that the constructor accepts it.

    Returns:
        The keyword arguments that the constructor is to get.
    """
    keywords: _InitKeywords = {}
    if use_member_name(config_type, stacklevel=4):
        keywords['member_name'] = name
    if ok_to_use_defaults:
        keywords['ok_to_use_defaults'] = True
    return keywords


def _parsed_in_place(name: str, json_text: str, nested: 'Config',
                     stderr_file: TextIO) -> 'Config':
    """Parse JSON text into a nested Config, keeping its missing values.

    A parse that fails leaves ``nested`` partly updated, as a failing
    ``parse_json()`` does to any object. The parse clears the
    automatic-change hook of ``nested``, so a hook that ``nested`` shares
    with the object holding it loses what it recorded before.

    Args:
        name: Path text for reaching the nested object.
        json_text: JSON text describing the nested Config.
        nested: Nested Config object to parse the JSON text into.
        stderr_file: Stream used for user-facing diagnostics.

    Returns:
        ``nested``, holding the parsed values.
    """
    wrap_parse_json(nested, json_text, True, stderr_file, member_name=name)
    return nested


def _constructed_by_type(name: str, json_text: str, nesting: ConfigNesting,
                         read: NestedReadContext) -> 'Config':
    """Construct one nested Config object with its declared class.

    When ``read.ok_to_use_defaults`` is true, a class whose constructor
    accepts ``ok_to_use_defaults`` is constructed from the JSON text with
    it. Another class is constructed from its class defaults, which are
    then validated on their own, and the JSON text is parsed into it.

    Args:
        name: Path text for reaching the nested object. It is handed to the
            constructed object as its ``member_name``.
        json_text: JSON text describing the nested Config.
        nesting: Nested Config declaration for the member.
        read: What the reads of the nested members share.

    Returns:
        The nested Config made by the declared type.
    """
    config_type = nesting.config_type
    if read.ok_to_use_defaults and \
            not accepts_keyword(config_type, 'ok_to_use_defaults'):
        nested = _constructed_defaults(config_type, name, read.stderr_file)
        return _parsed_in_place(name, json_text, nested, read.stderr_file)
    keywords = _init_keywords(config_type, name, read.ok_to_use_defaults)
    return config_type(from_json_data_text=json_text, from_json_filename=None,
                       stderr_file=read.stderr_file, **keywords)


def _constructed_by_factory(name: str, json_text: str, nesting: ConfigNesting,
                            stderr_file: TextIO) -> 'Config':
    """Construct one nested Config object with its declared factory.

    Args:
        name: Path text for reaching the nested object. It is handed to the
            constructed object as its ``member_name``.
        json_text: JSON text describing the nested Config.
        nesting: Nested Config declaration for the member.
        stderr_file: Stream used for user-facing diagnostics.

    Returns:
        The nested Config made by the declared factory function.
    """
    factory = nesting.factory_function
    assert factory is not None
    if use_member_name(factory, stacklevel=3):
        return factory(from_json_data_text=json_text, from_json_filename=None,
                       stderr_file=stderr_file, member_name=name)
    return factory(from_json_data_text=json_text, from_json_filename=None,
                   stderr_file=stderr_file)


def _current_of_type(current: object,
                     nesting: ConfigNesting) -> Optional['Config']:
    """Return the current nested object if it is of the declared class.

    Only an object whose class is exactly ``config_type`` is returned. An
    instance of a subclass is not, since it is not what parsing makes.

    Args:
        current: Current value at the place of the nested object.
        nesting: Nested Config declaration for the member.

    Returns:
        ``current``, or ``None`` when it is not of the declared class.
    """
    # pylint: disable-next=unidiomatic-typecheck
    if type(current) is not nesting.config_type:
        return None
    assert isinstance(current, nesting.config_type)
    return current


def _constructed_nested(name: str, json_text: str, current: object,
                        nesting: ConfigNesting,
                        read: NestedReadContext) -> 'Config':
    """Construct one nested Config object, or parse into the current one.

    When ``read.ok_to_use_defaults`` is true and the declaration has no
    factory function, the JSON text is parsed into the current nested
    object in place when it is of the declared class.

    Args:
        name: Path text for reaching the nested object. It is handed to the
            constructed object as its ``member_name``.
        json_text: JSON text describing the nested Config.
        current: Current value at the place of the nested object.
        nesting: Nested Config declaration for the member.
        read: What the reads of the nested members share.

    Returns:
        The nested Config made by the declared type, or by the declared
        factory function when the declaration has one, or ``current``.
    """
    if nesting.factory_function is not None:
        return _constructed_by_factory(name=name, json_text=json_text,
                                       nesting=nesting,
                                       stderr_file=read.stderr_file)
    in_place = _current_of_type(current, nesting) \
        if read.ok_to_use_defaults else None
    if in_place is not None:
        return _parsed_in_place(name, json_text, in_place, read.stderr_file)
    return _constructed_by_type(name=name, json_text=json_text,
                                nesting=nesting, read=read)


# pylint: disable-next=too-many-arguments,too-many-positional-arguments
def _located_nested(name: str, json_path: JsonPath, json_text: str,
                    current: object, nesting: ConfigNesting,
                    read: NestedReadContext) -> 'Config':
    """Construct one nested Config, locating its parse errors in the parent.

    Args:
        name: Path text for reaching the nested object.
        json_path: Tuple path of the nested object in the JSON data of the
            object holding it.
        json_text: JSON text describing the nested Config.
        current: Current value at the place of the nested object.
        nesting: Nested Config declaration for the member.
        read: What the reads of the nested members share.

    Returns:
        The nested Config made by the declared type or factory function, or
        the current one that the JSON text was parsed into.

    Raises:
        ConfigParseError: The nested JSON data is not valid. ``json_path``
            of the exception is prefixed with the given ``json_path``.
    """
    try:
        return _constructed_nested(name=name, json_text=json_text,
                                   current=current, nesting=nesting, read=read)
    except ConfigParseError as exc:
        exc.json_path = json_path + exc.json_path
        raise


# pylint: disable-next=too-many-arguments
def _item_from_json(name: str, json_data: object, current: object,
                    nesting: ConfigNesting, read: NestedReadContext, *,
                    json_path: JsonPath) -> 'Config':
    """Construct one nested Config from one parsed JSON object.

    Additionally the automatic changes that the nested Config recorded about
    its own JSON data are merged into ``read.auto_ch_hook`` using paths in
    the parent, so the application learns about old-file compatibility
    inside nested objects. That merge composes one nesting level at a time,
    which is why it is given the local ``name`` and not the whole reported
    path. The kept value paths of the nested Config are added to
    ``read.kept_paths`` with ``json_path`` in front.

    Args:
        name: Local name of the nested Config in the object that holds it.
        json_data: Parsed JSON object for the nested Config.
        current: Current value at the place of the nested Config.
        nesting: Nested Config declaration for the member.
        read: What the reads of the nested members share.
        json_path: Tuple path of the nested Config in the JSON data of the
            object holding it.

    Returns:
        A new nested Config instance, or ``current`` parsed in place.

    Raises:
        ConfigNotDict: JSON data is not a dict for a nested Config.
        ConfigParseError: The nested JSON data is not valid.
        TypeError: The factory returned the wrong Config type.
    """
    path = member_path(read.parent_path, name)
    if not isinstance(json_data, dict):
        msg = f'Nested Config member {path} must be a JSON object'
        print(msg, file=read.stderr_file)
        raise ConfigNotDict(msg, member_name=path, json_path=json_path)
    json_text = json.dumps(json_data, cls=_NestedConfigEncoder)
    nested_config = _located_nested(name=path, json_path=json_path,
                                    json_text=json_text, current=current,
                                    nesting=nesting, read=read)
    if not isinstance(nested_config, nesting.config_type):
        msg = f'Nested Config factory for {path} must return '
        msg += nesting.config_type.__name__
        print(msg, file=read.stderr_file)
        raise TypeError(msg)
    read.auto_ch_hook.merge_nested(nested=nested_config.auto_change_hook(),
                                   path_prefix=name)
    read.kept_paths.extend(json_path + kept
                           for kept in nested_config.kept_value_paths())
    return nested_config


def _list_from_json(member_name: str, json_data: object,
                    nesting: ConfigNesting,
                    read: NestedReadContext) -> list['Config']:
    """Construct a list of nested Config objects from parsed JSON.

    The list has exactly the elements of the JSON list. An element is never
    parsed into the current element at the same index, since elements have
    no correspondence by index.

    Args:
        member_name: Public parent member receiving the nested list.
        json_data: Parsed JSON value for the member.
        nesting: Nested Config declaration for the list elements.
        read: What the reads of the nested members share.

    Returns:
        A list containing one nested Config for each JSON element.

    Raises:
        ConfigMustBeList: JSON data is not a list.
        ConfigNotDict: A list element is not a dict.
        ConfigParseError: The JSON data of a nested Config is not valid.
    """
    if not isinstance(json_data, list):
        path = member_path(read.parent_path, member_name)
        msg = f'Nested Config member {path} must be a JSON list'
        print(msg, file=read.stderr_file)
        raise ConfigMustBeList(msg, member_name=path, json_path=(member_name,))
    nested_configs: list['Config'] = []
    for index, element_data in enumerate(json_data):
        element_name = _indexed_path(member_name, index)
        nested_configs.append(_item_from_json(name=element_name,
                                              json_data=element_data,
                                              current=None, nesting=nesting,
                                              read=read,
                                              json_path=(member_name, index)))
    return nested_configs


def _current_dict(current: object) -> dict[str, object]:
    """Return the current dict value, or an empty dict for another value."""
    return current if isinstance(current, dict) else {}


def _dict_from_json(member_name: str, json_data: object, current: object,
                    nesting: ConfigNesting,
                    read: NestedReadContext) -> dict[str, 'Config']:
    """Construct a dict of nested Config objects from parsed JSON.

    The dict has exactly the keys of the JSON dict. A value is parsed into
    the current value at the same key when there is one to parse into.

    Args:
        member_name: Public parent member receiving the nested dict.
        json_data: Parsed JSON value for the member.
        current: Current value of the member.
        nesting: Nested Config declaration for the dict values.
        read: What the reads of the nested members share.

    Returns:
        A dict containing one nested Config for each JSON value.

    Raises:
        ConfigNotDict: JSON data or one of its values is not a dict.
        ConfigKeysNotStrings: A key of the JSON data is not a string.
        ConfigParseError: The JSON data of a nested Config is not valid.
    """
    path = member_path(read.parent_path, member_name)
    if not isinstance(json_data, dict):
        msg = f'Nested Config member {path} must be a JSON object'
        print(msg, file=read.stderr_file)
        raise ConfigNotDict(msg, member_name=path, json_path=(member_name,))
    current_dict = _current_dict(current)
    nested_configs: dict[str, 'Config'] = {}
    for key, value_data in json_data.items():
        if not isinstance(key, str):
            msg = f'Nested Config member {path} keys must be strings'
            print(msg, file=read.stderr_file)
            raise ConfigKeysNotStrings(msg, member_name=path,
                                       json_path=(member_name,))
        value_name = _indexed_path(member_name, key)
        nested_configs[key] = _item_from_json(name=value_name,
                                              json_data=value_data,
                                              current=current_dict.get(key),
                                              nesting=nesting, read=read,
                                              json_path=(member_name, key))
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
                           current: object, nestings: list[ConfigNesting],
                           read: NestedReadContext) -> dict[str, object]:
    """Construct selected dict values as nested Config objects.

    The dict has exactly the keys of the JSON dict. A declared value is
    parsed into the current value at the same key when there is one to
    parse into.

    Args:
        member_name: Public parent member receiving the nested dict.
        json_data: Parsed JSON value for the member.
        current: Current value of the member.
        nestings: Nested Config declarations for selected dict keys.
        read: What the reads of the nested members share.

    Returns:
        A dictionary where declared keys contain nested Config objects and
        undeclared keys keep their parsed JSON values.

    Raises:
        ConfigNotDict: JSON data is not a dict, or a declared key does not
            contain a dict.
        ConfigKeysNotStrings: A key of the JSON data is not a string.
        ConfigParseError: The JSON data of a nested Config is not valid.
    """
    path = member_path(read.parent_path, member_name)
    if not isinstance(json_data, dict):
        msg = f'Nested Config member {path} must be a JSON object'
        print(msg, file=read.stderr_file)
        raise ConfigNotDict(msg, member_name=path, json_path=(member_name,))
    nesting_by_key = _nesting_by_key(nestings)
    current_dict = _current_dict(current)
    nested_configs: dict[str, object] = {}
    for key, value_data in json_data.items():
        if not isinstance(key, str):
            msg = f'Nested Config member {path} keys must be strings'
            print(msg, file=read.stderr_file)
            raise ConfigKeysNotStrings(msg, member_name=path,
                                       json_path=(member_name,))
        if key in nesting_by_key:
            value_name = _indexed_path(member_name, key)
            nested_configs[key] = _item_from_json(value_name, value_data,
                                                  current_dict.get(key),
                                                  nesting_by_key[key], read,
                                                  json_path=(member_name,
                                                             key))
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
                             current: object, nestings: list[ConfigNesting],
                             read: NestedReadContext) -> object:
    """Construct nested Config data from parsed JSON data.

    When ``read.ok_to_use_defaults`` is true, each nested object that the
    JSON data contains is completed with the values of the current nested
    object at the same place, parsed in place, or else with the defaults of
    its class. The JSON data decides which nested objects exist: list
    elements, dict keys and JSON ``null`` are exactly those of the JSON
    data.

    Args:
        member_name: Public parent member receiving the nested data.
        json_data: Parsed JSON value for the member.
        current: Current value of the member.
        nestings: Nested Config declarations for the member.
        read: What the reads of the nested members share.

    Returns:
        A nested Config, ``None`` for optional JSON null, a list of nested
        Config objects, or a dict of nested Config objects.
    """
    if _is_dict_value_by_key(nestings):
        return _dict_by_key_from_json(member_name=member_name,
                                      json_data=json_data, current=current,
                                      nestings=nestings, read=read)
    nesting = _single_nesting(nestings)
    if nesting.kind == ConfigNestingKind.LIST_ELEMENT:
        return _list_from_json(member_name=member_name, json_data=json_data,
                               nesting=nesting, read=read)
    if nesting.kind == ConfigNestingKind.DICT_VALUE:
        return _dict_from_json(member_name=member_name, json_data=json_data,
                               current=current, nesting=nesting, read=read)
    if json_data is None and nesting.kind == ConfigNestingKind.OPTIONAL_MEMBER:
        return None
    return _item_from_json(name=member_name, json_data=json_data,
                           current=current, nesting=nesting, read=read,
                           json_path=(member_name,))


def _item_json_data(member_name: str, member_value: object,
                    nesting: ConfigNesting, stderr_file: TextIO, *,
                    parent_path: Optional[str]) -> dict[str, JsonType]:
    """Return JSON data for one nested Config object.

    Args:
        member_name: Local name of the nested Config in the object that
            holds it.
        member_value: Current nested Config value.
        nesting: Nested Config declaration for the member.
        stderr_file: Stream used for user-facing diagnostics.
        parent_path: Reported path of the object holding the nested Config.

    Returns:
        A JSON-compatible dictionary.

    Raises:
        TypeError: The member value is not a valid nested Config object.
    """
    path = member_path(parent_path, member_name)
    if not isinstance(member_value, nesting.config_type):
        msg = f'Nested Config member {path} must be '
        msg += nesting.config_type.__name__
        raise TypeError(msg)
    json_text = wrap_as_json_string(member_value, stderr_file=stderr_file,
                                    member_name=path)
    json_data = json.loads(json_text)
    assert isinstance(json_data, dict)
    return cast(dict[str, JsonType], json_data)


def _list_json_data(member_name: str, member_value: object,
                    nesting: ConfigNesting, stderr_file: TextIO, *,
                    parent_path: Optional[str]) -> list[JsonType]:
    """Return JSON data for a list of nested Config objects.

    Args:
        member_name: Public parent member being serialized.
        member_value: Current nested list value.
        nesting: Nested Config declaration for the list elements.
        stderr_file: Stream used for user-facing diagnostics.
        parent_path: Reported path of the object holding the nested list.

    Returns:
        A JSON-compatible list.

    Raises:
        TypeError: The member value is not a list of nested Config objects.
    """
    if not isinstance(member_value, list):
        msg = 'Nested Config member '
        msg += f'{member_path(parent_path, member_name)} must be a list'
        raise TypeError(msg)
    json_data: list[JsonType] = []
    for index, element_value in enumerate(member_value):
        element_name = _indexed_path(member_name, index)
        element_data = _item_json_data(member_name=element_name,
                                       member_value=element_value,
                                       nesting=nesting,
                                       stderr_file=stderr_file,
                                       parent_path=parent_path)
        json_data.append(element_data)
    return json_data


def _dict_json_data(member_name: str, member_value: object,
                    nesting: ConfigNesting, stderr_file: TextIO, *,
                    parent_path: Optional[str]) -> dict[str, JsonType]:
    """Return JSON data for a dict of nested Config objects.

    Args:
        member_name: Public parent member being serialized.
        member_value: Current nested dict value.
        nesting: Nested Config declaration for the dict values.
        stderr_file: Stream used for user-facing diagnostics.
        parent_path: Reported path of the object holding the nested dict.

    Returns:
        A JSON-compatible dict.

    Raises:
        TypeError: The member value is not a dict of nested Config objects.
    """
    path = member_path(parent_path, member_name)
    if not isinstance(member_value, dict):
        msg = f'Nested Config member {path} must be a dict'
        raise TypeError(msg)
    json_data: dict[str, JsonType] = {}
    for key, value in member_value.items():
        if not isinstance(key, str):
            msg = f'Nested Config member {path} keys must be strings'
            raise TypeError(msg)
        value_name = _indexed_path(member_name, key)
        json_data[key] = _item_json_data(member_name=value_name,
                                         member_value=value, nesting=nesting,
                                         stderr_file=stderr_file,
                                         parent_path=parent_path)
    return json_data


def _is_config_object(value: object) -> bool:
    """Return whether value is a Config object without import-time cycles."""
    return any(cls.__module__ == 'config_as_json.config' and
               cls.__name__ == 'Config' for cls in type(value).mro())


def _dict_by_key_json_data(member_name: str, member_value: object,
                           nestings: list[ConfigNesting], stderr_file: TextIO,
                           *, parent_path: Optional[str]) \
        -> dict[str, JsonType]:
    """Return JSON data for a dict with selected nested Config values.

    Args:
        member_name: Public parent member being serialized.
        member_value: Current nested dict value.
        nestings: Nested Config declarations for selected dict keys.
        stderr_file: Stream used for user-facing diagnostics.
        parent_path: Reported path of the object holding the nested dict.

    Returns:
        A JSON-compatible dict.

    Raises:
        TypeError: The member value is not a dict, a key is not a string, or
            an undeclared key stores a Config object.
    """
    path = member_path(parent_path, member_name)
    if not isinstance(member_value, dict):
        msg = f'Nested Config member {path} must be a dict'
        raise TypeError(msg)
    nesting_by_key = _nesting_by_key(nestings)
    json_data: dict[str, JsonType] = {}
    for key, value in member_value.items():
        if not isinstance(key, str):
            msg = f'Nested Config member {path} keys must be strings'
            raise TypeError(msg)
        if key in nesting_by_key:
            value_name = _indexed_path(member_name, key)
            json_data[key] = _item_json_data(member_name=value_name,
                                             member_value=value,
                                             nesting=nesting_by_key[key],
                                             stderr_file=stderr_file,
                                             parent_path=parent_path)
        elif _is_config_object(value):
            msg = f'Nested Config member {_indexed_path(path, key)} has no '
            msg += 'DICT_VALUE_BY_KEY declaration'
            raise TypeError(msg)
        else:
            json_data[key] = cast(JsonType, value)
    return json_data


def _nested_config_json_data(member_name: str, member_value: object,
                             nestings: list[ConfigNesting],
                             stderr_file: TextIO, *,
                             parent_path: Optional[str]) -> JsonType:
    """Return JSON data for one nested Config declaration.

    Args:
        member_name: Public parent member being serialized.
        member_value: Current value of that member.
        nestings: Nested Config declarations for the member.
        stderr_file: Stream used for user-facing diagnostics.
        parent_path: Reported path of the object holding the nested data.

    Returns:
        JSON-compatible data for the configured nesting kind.
    """
    if _is_dict_value_by_key(nestings):
        return _dict_by_key_json_data(member_name=member_name,
                                      member_value=member_value,
                                      nestings=nestings,
                                      stderr_file=stderr_file,
                                      parent_path=parent_path)
    nesting = _single_nesting(nestings)
    if nesting.kind == ConfigNestingKind.LIST_ELEMENT:
        return _list_json_data(member_name=member_name,
                               member_value=member_value, nesting=nesting,
                               stderr_file=stderr_file,
                               parent_path=parent_path)
    if nesting.kind == ConfigNestingKind.DICT_VALUE:
        return _dict_json_data(member_name=member_name,
                               member_value=member_value, nesting=nesting,
                               stderr_file=stderr_file,
                               parent_path=parent_path)
    if member_value is None and \
            nesting.kind == ConfigNestingKind.OPTIONAL_MEMBER:
        return None
    return _item_json_data(member_name=member_name, member_value=member_value,
                           nesting=nesting, stderr_file=stderr_file,
                           parent_path=parent_path)


def _validate_item(member_name: str, member_value: object,
                   nesting: ConfigNesting, stderr_file: TextIO, *,
                   parent_path: Optional[str]) -> None:
    """Validate one nested Config object.

    Args:
        member_name: Local name of the nested Config in the object that
            holds it.
        member_value: Current nested Config value.
        nesting: Nested Config declaration for the member.
        stderr_file: Stream used for user-facing diagnostics.
        parent_path: Reported path of the object holding the nested Config.

    Raises:
        TypeError: The member value is not a valid nested Config object.
    """
    path = member_path(parent_path, member_name)
    if not isinstance(member_value, nesting.config_type):
        msg = f'Nested Config member {path} must be '
        msg += nesting.config_type.__name__
        print(msg, file=stderr_file)
        raise TypeError(msg)
    wrap_validate(member_value, stderr_file=stderr_file, member_name=path)


def _validate_list(member_name: str, member_value: object,
                   nesting: ConfigNesting, stderr_file: TextIO, *,
                   parent_path: Optional[str]) -> None:
    """Validate a list of nested Config objects.

    Args:
        member_name: Public parent member containing the nested list.
        member_value: Current nested list value.
        nesting: Nested Config declaration for the list elements.
        stderr_file: Stream used for user-facing diagnostics.
        parent_path: Reported path of the object holding the nested list.

    Raises:
        TypeError: The member value is not a list of nested Config objects.
    """
    if not isinstance(member_value, list):
        msg = 'Nested Config member '
        msg += f'{member_path(parent_path, member_name)} must be a list'
        print(msg, file=stderr_file)
        raise TypeError(msg)
    for index, element_value in enumerate(member_value):
        element_name = _indexed_path(member_name, index)
        _validate_item(member_name=element_name, member_value=element_value,
                       nesting=nesting, stderr_file=stderr_file,
                       parent_path=parent_path)


def _validate_dict(member_name: str, member_value: object,
                   nesting: ConfigNesting, stderr_file: TextIO, *,
                   parent_path: Optional[str]) -> None:
    """Validate a dict of nested Config objects.

    Args:
        member_name: Public parent member containing the nested dict.
        member_value: Current nested dict value.
        nesting: Nested Config declaration for the dict values.
        stderr_file: Stream used for user-facing diagnostics.
        parent_path: Reported path of the object holding the nested dict.

    Raises:
        TypeError: The member value is not a dict of nested Config objects.
    """
    path = member_path(parent_path, member_name)
    if not isinstance(member_value, dict):
        msg = f'Nested Config member {path} must be a dict'
        print(msg, file=stderr_file)
        raise TypeError(msg)
    for key, value in member_value.items():
        if not isinstance(key, str):
            msg = f'Nested Config member {path} keys must be strings'
            print(msg, file=stderr_file)
            raise TypeError(msg)
        value_name = _indexed_path(member_name, key)
        _validate_item(member_name=value_name, member_value=value,
                       nesting=nesting, stderr_file=stderr_file,
                       parent_path=parent_path)


def _validate_dict_by_key(member_name: str, member_value: object,
                          nestings: list[ConfigNesting], stderr_file: TextIO,
                          *, parent_path: Optional[str]) -> None:
    """Validate a dict with selected nested Config values.

    Args:
        member_name: Public parent member containing the nested dict.
        member_value: Current nested dict value.
        nestings: Nested Config declarations for selected dict keys.
        stderr_file: Stream used for user-facing diagnostics.
        parent_path: Reported path of the object holding the nested dict.

    Raises:
        TypeError: The member value is not a dict, a key is not a string, an
            undeclared key stores a Config object, or a declared key has the
            wrong nested Config type.
    """
    path = member_path(parent_path, member_name)
    if not isinstance(member_value, dict):
        msg = f'Nested Config member {path} must be a dict'
        print(msg, file=stderr_file)
        raise TypeError(msg)
    nesting_by_key = _nesting_by_key(nestings)
    for key, value in member_value.items():
        if not isinstance(key, str):
            msg = f'Nested Config member {path} keys must be strings'
            print(msg, file=stderr_file)
            raise TypeError(msg)
        value_name = _indexed_path(member_name, key)
        if key in nesting_by_key:
            _validate_item(member_name=value_name, member_value=value,
                           nesting=nesting_by_key[key],
                           stderr_file=stderr_file, parent_path=parent_path)
        elif _is_config_object(value):
            msg = f'Nested Config member {_indexed_path(path, key)} has no '
            msg += 'DICT_VALUE_BY_KEY declaration'
            print(msg, file=stderr_file)
            raise TypeError(msg)


def _validate_nested_config(member_name: str, member_value: object,
                            nestings: list[ConfigNesting], stderr_file: TextIO,
                            *, parent_path: Optional[str]) -> None:
    """Validate one nested Config declaration.

    Args:
        member_name: Public parent member containing the nested data.
        member_value: Current value of that member.
        nestings: Nested Config declarations for the member.
        stderr_file: Stream used for user-facing diagnostics.
        parent_path: Reported path of the object holding the nested data.

    Raises:
        TypeError: The member value does not match the nesting kind.
    """
    if _is_dict_value_by_key(nestings):
        _validate_dict_by_key(member_name=member_name,
                              member_value=member_value, nestings=nestings,
                              stderr_file=stderr_file, parent_path=parent_path)
        return
    nesting = _single_nesting(nestings)
    if nesting.kind == ConfigNestingKind.LIST_ELEMENT:
        _validate_list(member_name=member_name, member_value=member_value,
                       nesting=nesting, stderr_file=stderr_file,
                       parent_path=parent_path)
        return
    if nesting.kind == ConfigNestingKind.DICT_VALUE:
        _validate_dict(member_name=member_name, member_value=member_value,
                       nesting=nesting, stderr_file=stderr_file,
                       parent_path=parent_path)
        return
    if member_value is None and \
            nesting.kind == ConfigNestingKind.OPTIONAL_MEMBER:
        return
    _validate_item(member_name=member_name, member_value=member_value,
                   nesting=nesting, stderr_file=stderr_file,
                   parent_path=parent_path)
