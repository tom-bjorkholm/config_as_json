#! /usr/local/bin/python3
"""Implement the core configuration model for config-as-json.

Applications derive from :class:`Config`, create one instance attribute for
each supported configuration setting, and use those attribute values as the
default configuration. Each such configuration setting can also have a value
type of dict or list, or even a nested dict or list.
The base class then provides JSON serialization, parsing, schema-like key
checks, omit-when-None handling, old-file migration helpers, and validation
plan integration.
"""

# Copyright (c) 2024-2026 Tom Björkholm
# MIT License

from copy import deepcopy
import json
import sys
from typing import Any, Optional, Type, NamedTuple, Callable, TextIO
from enum import Enum, IntEnum
from config_as_json.str_to_enum import string_to_enum_best_match
from config_as_json.file_must_exist import file_must_exist
from config_as_json.commontypes import JsonType, PathOrStr
from config_as_json.config_auto_change_hook import ConfigAutoChangeHook
from config_as_json.config_nesting import ConfigFactory, ConfigNesting, \
    ConfigNestingKind
from config_as_json.validator import ValidationPlan


__all__ = ['Config', 'ConfigBadJson', 'ConfigFactory', 'ConfigNesting',
           'ConfigNestingKind', 'ParseConverter', 'RocfKeyRename']


RocfKeyRename = NamedTuple('RocfKeyRename', [('old', str), ('new', str)])
"""Describe a configuration key rename from an old name to a new name.

    Renaming rule for Reading Old Configuration File (ROCF).
    Used by derived classes to describe key names in old configuration files
    that should be mapped onto their current names during parsing of an old
    configuration file.
    """


class _ConfigEncoder(json.JSONEncoder):
    """Encode configuration objects with enum values stored as names."""

    def default(self, o: object) -> object:
        """Serialize enum members using their symbolic names.

        Args:
            o: Object supplied by ``json.dumps`` for custom encoding.

        Returns:
            The JSON-serializable representation of ``o``.

        Raises:
            TypeError: The object cannot be serialized by this encoder or its
                base implementation.
        """
        if isinstance(o, (Enum, IntEnum)):
            return str(o.name)
        return super().default(o)


class ConfigBadJson(json.JSONDecodeError):
    """Report JSON input that could not be interpreted as configuration."""


def _over_ride_needed(stri: str) -> Any:
    """Act as a placeholder conversion function for incomplete subclasses.

    The base :meth:`Config.parse_converters` implementation uses this helper
    to make missing converter customization obvious. Subclasses that need to
    coerce parsed JSON values should override ``parse_converters`` and return
    real conversion recipes.

    Args:
        stri: Parsed JSON value that needs conversion.

    Returns:
        A sentinel value only in the degenerate case where no conversion was
        actually needed.

    Raises:
        NotImplementedError: A subclass relied on the placeholder converter
            for a real conversion.
    """
    if stri is not None:
        msg = 'Override of Config.parse_converters needed.'
        raise NotImplementedError(msg)
    return 42


ParseConverter = NamedTuple('ParseConverter', [('result_type', type),
                                               ('func', Callable[..., Any]),
                                               ('args', dict[str, Any])])
"""Describe how one parsed JSON value should be converted after loading."""


class Config():
    """Base class for application-specific JSON-backed configuration models.

    A derived class declares the supported configuration schema by assigning
    instance attributes before calling ``super().__init__``. Those initial
    attribute values form the default configuration. The base class can then
    read JSON into the object, write the current values back to JSON, omit
    selected ``None`` values, and apply controlled old-file migration helpers.

    For each configuration attribute that holds a ``dict``, the base class
    recursively checks parsed JSON against the default: unknown keys in the
    file are rejected, and (depending on the load path) required keys from the
    default may need to be present. That built-in check covers many fixed dict
    shapes and avoids extra application code. List a dict member's name in
    ``_unchecked_dicts`` to skip that check for that member and let validators
    such as ``DictKeysValidator`` and ``DictForEachValidator`` define more
    flexible or more complex key and value policy instead. See
    ``DictKeysValidator`` in ``dict_validators`` for how that interacts with
    this check.

    A derived class can also declare direct nested configuration sections in
    ``_nested_configs``. The first increment supports direct ``MEMBER`` and
    ``OPTIONAL_MEMBER`` entries; other declared nesting kinds are reserved for
    later use and fail visibly. Nested config classes must accept the
    constructor keyword arguments ``from_json_data_text``,
    ``from_json_filename``, and ``stderr_file`` because those are used when
    nested JSON objects are parsed. As an alternative construction path, a
    ``ConfigNesting`` declaration may provide ``factory_function`` with the
    same keyword-argument contract. The returned object must be an instance of
    the declared ``config_type``.
    """

    def __init__(self, from_json_data_text: Optional[str],
                 from_json_filename: Optional[PathOrStr],
                 auto_ch_hook: Optional[ConfigAutoChangeHook] = None,
                 stderr_file: TextIO = sys.stderr) -> None:
        """Initialize a derived configuration object.

        A derived ``__init__`` is expected to assign every supported
        configuration attribute before calling this constructor. If neither
        JSON source argument is supplied, those attribute values remain in
        place as the default configuration. If a JSON source is supplied, the
        parsed data is applied to the same attributes instead.

        Args:
            from_json_data_text: Optional JSON text to parse directly.
            from_json_filename: Optional path to a JSON file to read.
            auto_ch_hook: Hook that is notified about automatic changes such
                as filled values or renamed keys when reading old
                configuration files.
            stderr_file: Stream used for user-facing diagnostics.

        Dict-valued members are checked against the default key set by the
        base class unless listed in ``_unchecked_dicts``; see the class
        docstring.

        Raises:
            AttributeError: The derived class did not declare any public
                configuration attributes before calling ``super().__init__``.
            TypeError: ``_unchecked_dicts`` exists but is not a list.
            ValueError: Both JSON text and a JSON file were supplied.
            KeyError: Parsed data is missing required keys or contains
                unexpected keys.
            ConfigBadJson: The supplied JSON could not be decoded or converted
                into the expected configuration structure.
            NotImplementedError: The derived class did not implement
                ``get_validation_plan``.
        """
        if auto_ch_hook is None:
            auto_ch_hook = ConfigAutoChangeHook()
        self._hook_cfg_autochange: ConfigAutoChangeHook = \
            deepcopy(auto_ch_hook)
        self_keys = [i for i in vars(self).keys() if not
                     callable(getattr(self, i)) and not i.startswith('_')]
        if not self_keys:
            msg = 'No object variables in object of class derived from '
            msg += 'Config. (Create object variables in __init__ before '
            msg += 'calling super().__init__().)'
            raise AttributeError(msg)
        self._checked_omit_none_from_json(self_keys, check_default_values=True)
        self._checked_nested_configs(self_keys)
        unchecked = getattr(self, '_unchecked_dicts', None)
        if unchecked is None:
            self._unchecked_dicts: list[str] = []
        elif not isinstance(unchecked, list):
            msg = '_unchecked_dicts must be a list'
            raise TypeError(msg)
        self._hook_dict = self.parse_converters()
        if from_json_data_text is not None and from_json_filename is not None:
            msg = 'Either JSON text or JSON file can be provided, but not '
            msg += 'both.'
            raise ValueError(msg)
        if from_json_data_text is not None:
            self.parse_json(from_json_data_text, stderr_file=stderr_file)
        elif from_json_filename is not None:
            self.read(from_json_filename, stderr_file=stderr_file)
        self.validate(stderr_file=stderr_file)

    def parse_converters(self) -> Optional[dict[str, ParseConverter]]:
        """Return post-load conversion rules for parsed JSON values.

        Derived classes override this method when some keys should accept a
        JSON representation that needs conversion into a richer Python type,
        for example turning enum names into enum members.

        Returns:
            A mapping from JSON key name to a :class:`ParseConverter`
            describing the expected parsed type, the conversion callable, and
            keyword arguments passed to that callable.
        """
        return {'in_type': ParseConverter(result_type=int,
                                          func=_over_ride_needed, args={})}

    @staticmethod
    def check_key_match(
            expected_keys: list[str], j_keys: list[str],
            ok_to_use_defaults: bool, stderr_file: TextIO,
            allowed_missing_keys: Optional[list[str]] = None) -> None:
        """Validate that parsed keys match the declared configuration keys.

        Args:
            expected_keys: Keys declared by the configuration object.
            j_keys: Keys found in parsed JSON data.
            ok_to_use_defaults: Whether missing declared keys may fall back to
                defaults supplied by the configuration object.
            stderr_file: Stream used for user-facing diagnostics.
            allowed_missing_keys: Keys that may be omitted even when
                ``ok_to_use_defaults`` is false.

        Raises:
            KeyError: The JSON data is missing a required key or contains an
                unexpected key.
        """
        if allowed_missing_keys is None:
            allowed_missing_keys = []
        if not ok_to_use_defaults:
            for i in expected_keys:
                if i not in j_keys and i not in allowed_missing_keys:
                    errmsg = f'No value for {i} in JSON data'
                    print(errmsg, file=stderr_file)
                    raise KeyError(errmsg)
        for i in j_keys:
            if i not in expected_keys:
                errmsg = f'Unexpected parameter {i} in JSON data'
                print(errmsg, file=stderr_file)
                raise KeyError(errmsg)

    @staticmethod
    # pylint: disable-next=too-many-arguments,too-many-positional-arguments
    def check_dict_parse(self_data: dict[str, Any], json_data: dict[str, Any],
                         key: str, ok_to_use_defaults: bool,
                         unchecked_dicts: list[str],
                         stderr_file: TextIO) -> None:
        """Recursively validate nested dictionaries against default values.

        Args:
            self_data: Default value currently stored on the configuration
                object.
            json_data: Parsed JSON value for the same key.
            key: Name of the configuration key being checked.
            ok_to_use_defaults: Whether missing nested keys may use defaults.
            unchecked_dicts: Keys whose nested dictionary contents should not
                be validated recursively.
            stderr_file: Stream used for user-facing diagnostics.

        Raises:
            KeyError: The JSON structure for the key does not match the
                expected dictionary shape.
        """
        if not isinstance(self_data, dict) and \
                not isinstance(json_data, dict):
            return
        if isinstance(self_data, dict):
            if not isinstance(json_data, dict):
                errmsg = f'Not dictionary for {key} in JSON data'
                print(errmsg, file=stderr_file)
                raise KeyError(errmsg)
        if not isinstance(self_data, dict):
            errmsg = f'Unexpected dictionary for {key} in JSON data'
            print(errmsg, file=stderr_file)
            raise KeyError(errmsg)
        if key in unchecked_dicts:
            return
        Config.check_key_match(list(self_data.keys()), list(json_data.keys()),
                               ok_to_use_defaults, stderr_file)
        for i in self_data.keys():
            if i in json_data:
                Config.check_dict_parse(self_data[i], json_data[i], i,
                                        ok_to_use_defaults, unchecked_dicts,
                                        stderr_file)

    def _json_parse_obj_hook(self, indict: dict[str, Any]) -> dict[str, Any]:
        """Apply configured post-load conversions to one decoded JSON object.

        Args:
            indict: Dictionary produced by ``json.loads``.

        Returns:
            A copy of ``indict`` where configured keys have been converted to
            their intended Python representation.
        """
        hookd = self._hook_dict
        if hookd is None:
            return indict  # pragma: no cover
        ret = deepcopy(indict)
        omit_none_keys = self._omit_none_from_json()
        for key, value in ret.items():
            if key in hookd:
                parse_c = hookd[key]
                if value is None and key in omit_none_keys:
                    continue
                if not isinstance(value, parse_c.result_type):
                    ret[key] = parse_c.func(value, **parse_c.args)
        return ret

    def _omit_none_from_json(self) -> list[str]:
        """Return keys omitted from JSON when their value is ``None``.

        Derived classes override this method when a top-level public
        configuration member is intentionally optional. Such members may be
        absent from JSON input. They keep their constructor value of ``None``
        when absent, explicit JSON ``null`` is read as ``None``, and writing
        the configuration omits them while their value is still ``None``.

        Returns:
            A list of public member names that use omit-when-None behavior.
        """
        return []

    def _checked_omit_none_from_json(self, self_keys: list[str],
                                     check_default_values: bool) -> list[str]:
        """Return validated omit-when-None member names.

        Args:
            self_keys: Public configuration member names on this object.
            check_default_values: Whether listed members must currently have
                the value ``None``.

        Returns:
            The keys returned by :meth:`_omit_none_from_json`.

        Raises:
            TypeError: The hook returned a value with the wrong type.
            KeyError: The hook listed an unknown public member.
            ValueError: A listed member did not default to ``None``.
        """
        omit_none_keys = self._omit_none_from_json()
        if not isinstance(omit_none_keys, list):
            msg = '_omit_none_from_json() must return a list'
            raise TypeError(msg)
        for key in omit_none_keys:
            if not isinstance(key, str):
                msg = '_omit_none_from_json() must return a list of strings'
                raise TypeError(msg)
            if key not in self_keys:
                msg = f'_omit_none_from_json() returned unknown key {key}'
                raise KeyError(msg)
            if check_default_values and getattr(self, key) is not None:
                msg = f'_omit_none_from_json() key {key} must default to None'
                raise ValueError(msg)
        return omit_none_keys

    @staticmethod
    def _check_config_nesting(key: str, nesting: ConfigNesting) -> None:
        """Validate one nested Config declaration.

        Args:
            key: Public member name described by ``nesting``.
            nesting: Nested configuration declaration to validate.

        Raises:
            TypeError: The declaration has the wrong runtime type.
            ValueError: ``discriminator_key`` is used with the wrong kind.
            NotImplementedError: The declaration uses a future nesting kind.
        """
        if not isinstance(nesting.kind, ConfigNestingKind):
            msg = f'_nested_configs[{key}].kind must be ConfigNestingKind'
            raise TypeError(msg)
        if not isinstance(nesting.config_type, type):
            msg = f'_nested_configs[{key}].config_type must be a type'
            raise TypeError(msg)
        if not issubclass(nesting.config_type, Config):
            msg = f'_nested_configs[{key}].config_type must derive from Config'
            raise TypeError(msg)
        if nesting.factory_function is not None and \
                not callable(nesting.factory_function):
            msg = f'_nested_configs[{key}].factory_function must be callable'
            raise TypeError(msg)
        discriminator = nesting.discriminator_key
        if discriminator is not None and not isinstance(discriminator, str):
            msg = f'_nested_configs[{key}].discriminator_key must be a string'
            raise TypeError(msg)
        if discriminator is not None and \
                nesting.kind != ConfigNestingKind.DICT_VALUE_BY_KEY:
            msg = '_nested_configs discriminator_key is reserved for '
            msg += 'DICT_VALUE_BY_KEY'
            raise ValueError(msg)
        if nesting.kind in (ConfigNestingKind.LIST_ELEMENT,
                            ConfigNestingKind.DICT_VALUE,
                            ConfigNestingKind.DICT_VALUE_BY_KEY):
            msg = f'_nested_configs[{key}] uses unsupported nesting kind '
            msg += f'{nesting.kind.name}'
            raise NotImplementedError(msg)

    def _checked_nested_configs(self, self_keys: list[str]) \
            -> dict[str, ConfigNesting]:
        """Return validated nested Config declarations.

        Args:
            self_keys: Public configuration member names on this object.

        Returns:
            The declarations stored in ``_nested_configs``, or an empty dict.

        Raises:
            TypeError: ``_nested_configs`` or one of its entries has the wrong
                runtime type.
            KeyError: A declaration names an unknown public member.
            ValueError: A future-only discriminator is used with the wrong
                kind.
            NotImplementedError: A declaration uses a future nesting kind.
        """
        nested_raw: object = getattr(self, '_nested_configs', None)
        if nested_raw is None:
            self._nested_configs: dict[str, ConfigNesting] = {}
            return {}
        if not isinstance(nested_raw, dict):
            msg = '_nested_configs must be a dict'
            raise TypeError(msg)
        nested_configs: dict[str, ConfigNesting] = {}
        for key, nesting in nested_raw.items():
            if not isinstance(key, str):
                msg = '_nested_configs keys must be strings'
                raise TypeError(msg)
            if key not in self_keys:
                msg = f'_nested_configs returned unknown key {key}'
                raise KeyError(msg)
            if not isinstance(nesting, ConfigNesting):
                msg = f'_nested_configs[{key}] must be ConfigNesting'
                raise TypeError(msg)
            self._check_config_nesting(key=key, nesting=nesting)
            nested_configs[key] = nesting
        self._nested_configs = nested_configs
        return nested_configs

    def _rocf_get_keys_to_remove(self) -> list[str]:
        """Return old JSON keys to remove while reading old files.

        When Reading an Old Configuration File (ROCF), the old configuration
        version in the file might have keys that no longer exist in the
        current configuration. This method returns those old key names.
        Derived classes should override this method as needed.

        Returns:
            A list of old keys that should be removed from the JSON input.
        """
        return []

    @staticmethod
    def _rocf_remove_json_key_in_dict(key: str,
                                      json_data: dict[str, JsonType]) \
            -> bool:
        """Remove one ROCF key from a nested dictionary.

        Args:
            key: Old JSON key to remove.
            json_data: Parsed JSON dictionary to update in place.

        Returns:
            ``True`` if the key was found and removed anywhere in
            ``json_data``, otherwise ``False``.
        """
        assert key is not None
        ret = key in json_data
        if ret:
            del json_data[key]
        for value in json_data.values():
            if isinstance(value, dict):
                assert isinstance(value, dict)
                ret |= Config._rocf_remove_json_key_in_dict(key=key,
                                                            json_data=value)
            if isinstance(value, list):
                assert isinstance(value, list)
                ret |= Config._rocf_remove_json_key_in_list(key=key,
                                                            json_data=value)
        return ret

    @staticmethod
    def _rocf_remove_json_key_in_list(key: str, json_data: list[JsonType]) \
            -> bool:
        """Remove one ROCF key inside nested lists.

        Args:
            key: Old JSON key to remove.
            json_data: Parsed JSON list to walk recursively.

        Returns:
            ``True`` if the key was found and removed anywhere in
            ``json_data``, otherwise ``False``.
        """
        assert key is not None
        ret = False
        for value in json_data:
            if isinstance(value, dict):
                assert isinstance(value, dict)
                ret |= Config._rocf_remove_json_key_in_dict(key=key,
                                                            json_data=value)
            if isinstance(value, list):
                assert isinstance(value, list)
                ret |= Config._rocf_remove_json_key_in_list(key=key,
                                                            json_data=value)
        return ret

    def _rocf_remove_json_keys(self, json_data: dict[str, JsonType]) -> None:
        """Apply all declared ROCF key removals in place.

        When Reading an Old Configuration File (ROCF), some key names in the
        JSON input from the old configuration file may no longer exist in the
        current configuration. This method removes all declared old keys
        before normal schema checks are applied.

        Args:
            json_data: Parsed JSON object to normalize before validation.
        """
        for key in self._rocf_get_keys_to_remove():
            if self._rocf_remove_json_key_in_dict(key=key,
                                                  json_data=json_data):
                self._hook_cfg_autochange.old_key_handled(old_key=key)

    def _rocf_values_for_missing_json_keys(self) -> dict[str, JsonType]:
        """Return values for missing JSON keys.

        When Reading an Old Configuration File (ROCF), some now existing
        and mandatory keys may be missing in the JSON input from the
        old configuration file. This method returns the values that should
        be supplied for these missing keys.
        Derived classes should override this method as needed.

        Returns:
            A mapping from missing key name to the value that should
            be supplied when the key is absent from JSON input.
        """
        return {}

    def _rocf_apply_missing_values(self,
                                   json_data: dict[str, JsonType]) -> None:
        """Apply values for missing JSON keys to the configuration object.

        When Reading an Old Configuration File (ROCF), some now existing
        and mandatory keys may be missing in the JSON input from the
        old configuration file. This method applies the values that should
        be supplied for these missing keys to the configuration object.

        Args:
            json_data: Parsed JSON object that will be applied to the
                configuration instance.
        """
        rocfval = self._rocf_values_for_missing_json_keys()
        for key, value in rocfval.items():
            if key not in json_data:
                json_data[key] = value
                self._hook_cfg_autochange.rocf_missing_value_provided(
                    rocf_val_key=key)

    def _rocf_get_json_key_renames(self) -> list[RocfKeyRename]:
        """Return configuration key renames for Reading Old Configuration File.

        Derived classes override this method to describe key names
        in old configuration files that should be mapped onto their current
        names during parsing of an old configuration file.

        Returns:
            A list of ``RocfKeyRename`` entries describing accepted key
            renames.
        """
        return []

    @staticmethod
    def _rocf_rename_json_key_in_dict(rename: RocfKeyRename,
                                      json_data: dict[str, JsonType],
                                      stderr_file: TextIO = sys.stderr) \
            -> bool:
        """Apply one ROCF key rename in a nested dictionary.

        Args:
            rename: ROCT old to new key mapping to apply.
            json_data: Parsed JSON dictionary to update in place.
            stderr_file: Stream used for user-facing diagnostics.

        Returns:
            ``True`` if the old key name was found and replaced anywhere in
            ``json_data``, otherwise ``False``.
        """
        assert rename.old is not None
        assert rename.new is not None
        assert rename.old != rename.new
        ret: bool = False
        if rename.old in json_data:
            if rename.new in json_data:
                print('Inconsistent configuration:', file=stderr_file)
                print(f'Both new config parameter {rename.new} and '
                      f'old {rename.old} present.', file=stderr_file)
                print(f'Ignoring old parameter {rename.old}', file=stderr_file)
                del json_data[rename.old]
            else:
                json_data[rename.new] = json_data[rename.old]
                del json_data[rename.old]
                ret = True
        for _, value in json_data.items():
            if isinstance(value, dict):
                assert isinstance(value, dict)
                ret |= Config._rocf_rename_json_key_in_dict(
                    rename=rename, json_data=value, stderr_file=stderr_file)
            if isinstance(value, list):
                assert isinstance(value, list)
                ret |= Config._rocf_rename_json_key_in_list(
                    rename=rename, json_data=value, stderr_file=stderr_file)
        return ret

    @staticmethod
    def _rocf_rename_json_key_in_list(rename: RocfKeyRename,
                                      json_data: list[JsonType],
                                      stderr_file: TextIO = sys.stderr) \
            -> bool:
        """Apply one ROCF key rename inside nested lists.

        Args:
            rename: ROCF old to new key mapping to apply.
            json_data: Parsed JSON list to walk recursively.
            stderr_file: Stream used for user-facing diagnostics.

        Returns:
            ``True`` if the old key name was found and replaced anywhere in
            ``json_data``, otherwise ``False``.
        """
        ret: bool = False
        for value in json_data:
            if isinstance(value, dict):
                assert isinstance(value, dict)
                ret |= Config._rocf_rename_json_key_in_dict(
                    rename=rename, json_data=value, stderr_file=stderr_file)
            if isinstance(value, list):
                assert isinstance(value, list)
                ret |= Config._rocf_rename_json_key_in_list(
                    rename=rename, json_data=value, stderr_file=stderr_file)
        return ret

    def _rocf_rename_json_keys(self, json_data: dict[str, JsonType],
                               stderr_file: TextIO) -> None:
        """Apply all declared ROCF key renames in place.

        When Reading an Old Configuration File (ROCF), some key names in the
        JSON input from the old configuration file may need to be mapped onto
        their current names during parsing of an old configuration file.
        This method applies all declared ROCF key renames in place.

        Args:
            json_data: Parsed JSON object to normalize before validation.
            stderr_file: Stream used for user-facing diagnostics.
        """
        bwcompat = self._rocf_get_json_key_renames()
        for name in bwcompat:
            if self._rocf_rename_json_key_in_dict(rename=name,
                                                  json_data=json_data,
                                                  stderr_file=stderr_file):
                self._hook_cfg_autochange.old_key_handled(old_key=name.old)

    @staticmethod
    def _nested_config_from_json(member_name: str, json_data: object,
                                 nesting: ConfigNesting,
                                 stderr_file: TextIO) -> Optional['Config']:
        """Construct one direct nested Config from parsed JSON data.

        Args:
            member_name: Public parent member receiving the nested Config.
            json_data: Parsed JSON value for the member.
            nesting: Nested Config declaration for the member.
            stderr_file: Stream used for user-facing diagnostics.

        Returns:
            A new nested Config instance, or ``None`` for optional JSON null.

        Raises:
            KeyError: JSON data is not a dictionary for a nested Config.
        """
        if json_data is None and \
                nesting.kind == ConfigNestingKind.OPTIONAL_MEMBER:
            return None
        if not isinstance(json_data, dict):
            msg = f'Nested Config member {member_name} must be a JSON object'
            print(msg, file=stderr_file)
            raise KeyError(msg)
        json_text = json.dumps(json_data, cls=_ConfigEncoder)
        if nesting.factory_function is None:
            nested_config = nesting.config_type(
                from_json_data_text=json_text, from_json_filename=None,
                stderr_file=stderr_file)
        else:
            nested_config = nesting.factory_function(
                from_json_data_text=json_text, from_json_filename=None,
                stderr_file=stderr_file)
        if not isinstance(nested_config, nesting.config_type):
            msg = f'Nested Config factory for {member_name} must return '
            msg += nesting.config_type.__name__
            print(msg, file=stderr_file)
            raise TypeError(msg)
        return nested_config

    @staticmethod
    def _nested_config_json_data(member_name: str, member_value: object,
                                 nesting: ConfigNesting, stderr_file: TextIO) \
            -> Optional[dict[str, JsonType]]:
        """Return JSON data for one direct nested Config member.

        Args:
            member_name: Public parent member being serialized.
            member_value: Current value of that member.
            nesting: Nested Config declaration for the member.
            stderr_file: Stream used for user-facing diagnostics.

        Returns:
            A JSON-compatible dictionary, or ``None`` for optional members.

        Raises:
            TypeError: The member value is not a valid nested Config object.
        """
        if member_value is None and \
                nesting.kind == ConfigNestingKind.OPTIONAL_MEMBER:
            return None
        if not isinstance(member_value, nesting.config_type):
            msg = f'Nested Config member {member_name} must be '
            msg += nesting.config_type.__name__
            raise TypeError(msg)
        json_data = json.loads(member_value.as_json_string(
            stderr_file=stderr_file))
        assert isinstance(json_data, dict)
        return json_data

    @staticmethod
    def _validate_nested_config_member(member_name: str, member_value: object,
                                       nesting: ConfigNesting,
                                       stderr_file: TextIO) -> None:
        """Validate one direct nested Config member.

        Args:
            member_name: Public parent member containing the nested Config.
            member_value: Current value of that member.
            nesting: Nested Config declaration for the member.
            stderr_file: Stream used for user-facing diagnostics.

        Raises:
            TypeError: The member value is not a valid nested Config object.
        """
        if member_value is None and \
                nesting.kind == ConfigNestingKind.OPTIONAL_MEMBER:
            return
        if not isinstance(member_value, nesting.config_type):
            msg = f'Nested Config member {member_name} must be '
            msg += nesting.config_type.__name__
            print(msg, file=stderr_file)
            raise TypeError(msg)
        member_value.validate(stderr_file=stderr_file)

    def _validate_nested_configs(self, stderr_file: TextIO) -> None:
        """Validate all direct nested Config members before this object.

        Args:
            stderr_file: Stream used for user-facing diagnostics.
        """
        self_keys = [i for i in vars(self).keys() if not
                     callable(getattr(self, i)) and not i.startswith('_')]
        nested_configs = self._checked_nested_configs(self_keys)
        for member_name, nesting in nested_configs.items():
            member_value = getattr(self, member_name)
            self._validate_nested_config_member(
                member_name=member_name, member_value=member_value,
                nesting=nesting, stderr_file=stderr_file)

    def parse_json(self, from_json_text: str, ok_to_use_defaults: bool = False,
                   stderr_file: TextIO = sys.stderr) -> None:
        """Parse JSON text and apply it to the configuration object.

        Args:
            from_json_text: JSON document describing configuration values.
            ok_to_use_defaults: Whether missing declared keys may remain at
                their already assigned default values.
            stderr_file: Stream used for user-facing diagnostics. Defaults to
                ``sys.stderr``.

        Raises:
            ConfigBadJson: The text is not valid configuration JSON.
            KeyError: The parsed configuration does not match the declared
                keys or nested dictionary structure.
            NotImplementedError: A required custom converter was not supplied
                by a derived class.
        """
        self._hook_dict = self.parse_converters()
        hook = self._json_parse_obj_hook if self._hook_dict is not None \
            else None
        data = None
        try:
            data = json.loads(from_json_text, object_hook=hook)
        except Exception as exc:
            if isinstance(exc, NotImplementedError):
                raise exc
            msg = 'Config.parse_json failed to load JSON from string/file.\n'
            msg += 'Probably incorrectly edited configuration,\n'
            msg += 'or using wrong file (not config file) as configuration.\n'
            msg += str(exc)
            print(msg, file=stderr_file)
            if isinstance(exc, json.JSONDecodeError):
                raise ConfigBadJson(msg=msg, doc=exc.doc, pos=exc.pos) from exc
            raise ConfigBadJson(msg=msg, doc='', pos=0) from exc
        self._rocf_remove_json_keys(data)
        self._rocf_apply_missing_values(data)
        self._rocf_rename_json_keys(data, stderr_file=stderr_file)
        self._hook_cfg_autochange.all_autochanges_done(stderr_file=stderr_file)
        self_keys = [i for i in vars(self).keys() if not
                     callable(getattr(self, i)) and not i.startswith('_')]
        omit_none_keys = self._checked_omit_none_from_json(
            self_keys, check_default_values=False)
        nested_configs = self._checked_nested_configs(self_keys)
        self.check_key_match(self_keys, data.keys(), ok_to_use_defaults,
                             stderr_file, omit_none_keys)
        for i in self_keys:
            if i in data.keys():
                if i in nested_configs:
                    nested_value = self._nested_config_from_json(
                        member_name=i, json_data=data[i],
                        nesting=nested_configs[i], stderr_file=stderr_file)
                    setattr(self, i, nested_value)
                else:
                    self.check_dict_parse(getattr(self, i), data[i], i,
                                          ok_to_use_defaults,
                                          self._unchecked_dicts, stderr_file)
                    setattr(self, i, data[i])

    def as_json_string(self, stderr_file: TextIO) -> str:
        """Serialize the current configuration object to formatted JSON.

        Args:
            stderr_file: Stream used for user-facing diagnostics during
                validation.

        Returns:
            A JSON document containing every public, non-callable instance
            attribute on the configuration object.
        """
        # We validate the configuration before writing it to JSON,
        # to make sure that the configuration is valid so it can be read back
        self.validate(stderr_file=stderr_file)
        data = {}
        self_keys = [i for i in vars(self).keys() if not
                     callable(getattr(self, i)) and not i.startswith('_')]
        omit_none_keys = self._checked_omit_none_from_json(
            self_keys, check_default_values=False)
        nested_configs = self._checked_nested_configs(self_keys)
        for i in self_keys:
            if i in omit_none_keys and getattr(self, i) is None:
                continue
            if i in nested_configs:
                data[i] = self._nested_config_json_data(
                    member_name=i, member_value=getattr(self, i),
                    nesting=nested_configs[i], stderr_file=stderr_file)
            else:
                data[i] = getattr(self, i)
        return json.dumps(data, sort_keys=True, indent=4, cls=_ConfigEncoder)

    def read(self, from_json_filename: PathOrStr,
             ok_to_use_defaults: bool = False,
             stderr_file: TextIO = sys.stderr) -> None:
        """Read configuration JSON from a file and apply it to the object.

        Args:
            from_json_filename: File containing configuration JSON.
            ok_to_use_defaults: Whether missing declared keys may remain at
                their already assigned default values.
            stderr_file: Stream used for user-facing diagnostics. Defaults to
                ``sys.stderr``.
        """
        file_must_exist(filename=from_json_filename,
                        with_content_txt='configuration JSON input',
                        stderr_file=stderr_file)
        with open(file=from_json_filename, mode='r', encoding='UTF-8') as file:
            data = file.read()
            self.parse_json(data, ok_to_use_defaults, stderr_file=stderr_file)

    def write(self, to_json_filename: PathOrStr,
              stderr_file: TextIO = sys.stderr) -> None:
        """Write the current configuration to a JSON file.

        Args:
            to_json_filename: Destination file that should receive the
                formatted JSON document.
            stderr_file: Stream used for user-facing diagnostics during
                validation.
        """
        text = self.as_json_string(stderr_file=stderr_file)
        with open(file=to_json_filename, mode='w', encoding='UTF-8') as file:
            file.write(text)

    @staticmethod
    def value_of_type(input_value: Any, to_type: Any) -> Any:
        """Return ``input_value`` as an instance of ``to_type``.

        Args:
            input_value: Value to normalize.
            to_type: Target runtime type or constructor.

        Returns:
            ``input_value`` unchanged when it already has the expected type,
            otherwise the result of calling ``to_type(input_value)``.
        """
        if isinstance(input_value, to_type):
            return input_value
        return to_type(input_value)

    @staticmethod
    def get_converter_dict(enum_type: Type[Enum]) -> ParseConverter:
        """Build a converter recipe for enum-valued configuration fields.

        Args:
            enum_type: Enum class that should be reconstructed from text.

        Returns:
            A ``ParseConverter`` that parses strings with
            :func:`string_to_enum_best_match`.
        """
        return ParseConverter(result_type=enum_type,
                              func=string_to_enum_best_match,
                              args={'num_type': enum_type})

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Return the validation plan for the Config object.

        The validation plan is used to validate the Config object after it has
        been parsed from JSON, and it is also used to validate the Config
        object after it has been default constructed.

        The derived class shall override this method to return a list of
        validation steps describing the validations for the Config object.
        This is mandatory even for derived classes that do not currently use
        validation and only want to return an empty list.

        Args:
            stderr_file: Stream used for user-facing diagnostics.

        Returns:
            An ordered list of validation steps describing the validations for
            the Config object. The order of the steps in the list is
            significant as a previous validation may normalize or change a
            configuration value that is used in a later validation.
        """
        msg = 'Config.get_validation_plan() must be implemented in a ' + \
            'derived class.'
        print(msg, file=stderr_file)
        raise NotImplementedError(msg)
        return []  # pylint: disable=unreachable

    def validate(self, stderr_file: TextIO) -> None:
        """Validate the Config object.

        The validation is performed by the validation plan returned by
        ``get_validation_plan``. The validation plan is applied in the order
        of the validation steps in the list. A previous validation may
        normalize or change a configuration value that is used in a later
        validation.
        A member validator returns the value that shall be stored back into the
        member, even if that returned value is ``None``.
        A whole-config validator may instead mutate the Config object
        directly.

        Raises:
            InvalidConfiguration: The Config object is not valid.
            InvalidConfigurationValue: The value of a member of the Config
                                       object is not valid.
            NotImplementedError: The derived class did not override
                                 ``get_validation_plan`` or one of the
                                 required validation methods.
            AttributeError: A member name in the validation plan is not a
                            valid member name of the Config object.

        Args:
            stderr_file: Stream used for user-facing diagnostics.
        """
        self._validate_nested_configs(stderr_file=stderr_file)
        validation_plan = self.get_validation_plan(stderr_file=stderr_file)
        for validation_step in validation_plan:
            validation_step.apply(self, stderr_file)
