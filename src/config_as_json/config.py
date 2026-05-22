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
from typing import Optional, Type, NamedTuple, Callable, TextIO, TypeVar
from enum import Enum
from config_as_json.str_to_enum import string_to_enum_best_match
from config_as_json.file_must_exist import file_must_exist
from config_as_json.commontypes import ConfigPath, PathOrStr
from config_as_json.config_auto_change_hook import ConfigAutoChangeHook
from config_as_json.config_nesting import ConfigNesting, ConfigNestingKind, \
    NestedConfigs
from config_as_json._config_nesting_io import _nested_config_from_json, \
    _nested_config_json_data, _validate_nested_config
from config_as_json.json_write_hooks import SerializeConverters, \
    apply_serialize_converters
from config_as_json.read_old_configuration import ReadOldConfiguration
from config_as_json.validator import ValidationPlan


class ConfigBadJson(json.JSONDecodeError):
    """Report JSON input that could not be interpreted as configuration."""


def _over_ride_needed(value: object) -> int:
    """Act as a placeholder conversion function for incomplete subclasses.

    The base :meth:`Config.parse_converters` implementation uses this helper
    to make missing converter customization obvious. Subclasses that need to
    coerce parsed JSON values should override ``parse_converters`` and return
    real conversion recipes.

    Args:
        value: Parsed JSON value that needs conversion.

    Returns:
        A sentinel value only in the degenerate case where no conversion was
        actually needed.

    Raises:
        NotImplementedError: A subclass relied on the placeholder converter
            for a real conversion.
    """
    if value is not None:
        msg = 'Override of Config.parse_converters needed.'
        raise NotImplementedError(msg)
    return 42


ParseConverter = NamedTuple('ParseConverter', [('result_type', type),
                                               ('func',
                                                Callable[..., object]),
                                               ('args',
                                                dict[str, object])])
"""Describe how one parsed JSON value should be converted after loading."""


_T = TypeVar('_T', int, str, bool, float)


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

    A derived class can also declare nested configuration sections by
    overriding :meth:`nested_configs`. ``MEMBER`` and ``OPTIONAL_MEMBER``
    describe direct members, ``LIST_ELEMENT`` describes a list whose elements
    are nested Config objects, ``DICT_VALUE`` describes a dict whose values
    are nested Config objects, and ``DICT_VALUE_BY_KEY`` describes selected
    keys inside a dict whose values are nested Config objects. Use a direct
    ``ConfigNesting`` value for one declaration. Use a list only when every
    list element has kind ``DICT_VALUE_BY_KEY`` and the entries describe
    selected keys inside the same dict member.
    Nested config classes must accept the constructor keyword arguments
    ``from_json_data_text``,
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
                as filled, renamed, moved, or removed values when reading old
                configuration files.
            stderr_file: Stream used for user-facing diagnostics.

        Dict-valued members are checked against the default key set by the
        base class unless listed in ``_unchecked_dicts``; see the class
        docstring.

        Raises:
            AttributeError: The derived class did not declare any public
                configuration attributes before calling ``super().__init__``.
            TypeError: ``_unchecked_dicts`` exists but is not a list, or
                ``nested_configs`` returns invalid declarations.
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
        if '_nested_configs' in vars(self):
            # Remove this transition check after the API migration.
            raise TypeError('_nested_configs is no longer supported')
        self_keys = [i for i in vars(self).keys() if not
                     callable(getattr(self, i)) and not i.startswith('_')]
        if not self_keys:
            msg = 'No object variables in object of class derived from '
            msg += 'Config. (Create object variables in __init__ before '
            msg += 'calling super().__init__().)'
            raise AttributeError(msg)
        self._checked_omit_none_from_json(self_keys)
        self._nested_config_decls: dict[str, list[ConfigNesting]] = \
            self._checked_nested_configs(self_keys)
        self._check_nested_config_members(self_keys, self._nested_config_decls)
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
        else:
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

    def serialize_converters(self) -> SerializeConverters:
        """Return write-side conversion rules for rich Python values.

        Derived classes override this method when some configuration values
        need explicit conversion into JSON-compatible data before
        ``json.dumps()`` is called. The motivating case is ``IntEnum``,
        which Python's JSON encoder treats as ``int`` and never offers to
        ``default()``; an explicit converter sidesteps that problem.

        The returned dictionary maps selectors to converters. A selector
        may be either a recursive key-name string (matches every
        dictionary member with that name in data owned by this object) or
        an absolute ``ConfigPath`` (matches one specific path). Path
        selectors use the same rules as ROCF paths.

        Converters apply only to data owned by this object. Declared
        nested ``Config`` objects serialize themselves and apply their own
        converters; the parent's converters never reach into those
        subtrees.

        Explicit converters override built-in fallback conversions. The
        initial built-in fallbacks are limited to ``Enum`` and ``IntEnum``
        members, which are converted to their member names.

        Returning the same key with both a recursive key selector and a
        path selector that ends in or passes through that key is a
        declaration error; ``apply_serialize_converters`` raises
        ``SerializeSelectorError`` in that case.

        Returns:
            Write-side conversion rules. The base class returns an empty
            dictionary; override and return non-empty rules when explicit
            conversions are needed.
        """
        return {}

    def nested_configs(self) -> NestedConfigs:
        """Return nested Config declarations for this configuration.

        Override this for public members that contain nested :class:`Config`
        objects. Return :class:`NestedConfigs` mapping member names to
        :class:`ConfigNesting` declarations. Use ``@override`` so static type
        checkers can catch a misspelled method name.

        The override should only return stable declarative metadata: no
        parsing, validation, mutation, diagnostics, or other side effects.
        Values should be constant from the time ``super().__init__`` is
        called. Every nested Config object needs a declaration.
        """
        return {}

    def _get_read_old_configuration(self) -> ReadOldConfiguration:
        """Return the object that normalizes old configuration data.

        Derived classes override this method when they need to accept old
        configuration file shapes. The default object leaves parsed data
        unchanged.
        """
        return ReadOldConfiguration()

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
    def check_dict_parse(self_data: object, json_data: object, key: str,
                         ok_to_use_defaults: bool, unchecked_dicts: list[str],
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
        assert isinstance(self_data, dict)
        assert isinstance(json_data, dict)
        Config.check_key_match(list(self_data.keys()), list(json_data.keys()),
                               ok_to_use_defaults, stderr_file)
        for i in self_data.keys():
            if i in json_data:
                Config.check_dict_parse(self_data[i], json_data[i], i,
                                        ok_to_use_defaults, unchecked_dicts,
                                        stderr_file)

    def _json_parse_obj_hook(self, indict: dict[str, object]) \
            -> dict[str, object]:
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
        absent from JSON input. In strict reads, absent listed members become
        ``None``; when ``ok_to_use_defaults`` is true, absent members keep
        their constructor defaults. Explicit JSON ``null`` is read as
        ``None``, and writing the configuration omits listed members while
        their value is still ``None``.

        Returns:
            A list of public member names that use omit-when-None behavior.
        """
        return []

    def _checked_omit_none_from_json(self, self_keys: list[str]) -> list[str]:
        """Return validated omit-when-None member names.

        Args:
            self_keys: Public configuration member names on this object.

        Returns:
            The keys returned by :meth:`_omit_none_from_json`.

        Raises:
            TypeError: The hook returned a value with the wrong type.
            KeyError: The hook listed an unknown public member.
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
        """
        if not isinstance(nesting.kind, ConfigNestingKind):
            msg = f'nested_configs()[{key}].kind must be ConfigNestingKind'
            raise TypeError(msg)
        if not isinstance(nesting.config_type, type):
            msg = f'nested_configs()[{key}].config_type must be a type'
            raise TypeError(msg)
        if not issubclass(nesting.config_type, Config):
            msg = 'nested_configs()'
            msg += f'[{key}].config_type must derive from Config'
            raise TypeError(msg)
        if nesting.factory_function is not None and \
                not callable(nesting.factory_function):
            msg = f'nested_configs()[{key}].factory_function must be callable'
            raise TypeError(msg)
        discriminator = nesting.discriminator_key
        if discriminator is not None and not isinstance(discriminator, str):
            msg = 'nested_configs()'
            msg += f'[{key}].discriminator_key must be a string'
            raise TypeError(msg)
        if discriminator is not None and \
                nesting.kind != ConfigNestingKind.DICT_VALUE_BY_KEY:
            msg = 'nested_configs() discriminator_key is reserved for '
            msg += 'DICT_VALUE_BY_KEY'
            raise ValueError(msg)

    @staticmethod
    def _checked_config_nesting_list(key: str, nesting_raw: object) \
            -> list[ConfigNesting]:
        """Return the checked declaration list for one nested member.

        Args:
            key: Public member name described by the declarations.
            nesting_raw: Raw value from :meth:`nested_configs`.

        Returns:
            One or more checked ``ConfigNesting`` declarations.

        Raises:
            TypeError: The raw value or a list entry has the wrong type.
            ValueError: The list shape is not valid for the declared kinds.
        """
        if isinstance(nesting_raw, ConfigNesting):
            nestings = [nesting_raw]
        elif isinstance(nesting_raw, list):
            if not nesting_raw:
                msg = f'nested_configs()[{key}] list must not be empty'
                raise ValueError(msg)
            nestings = []
            for nesting in nesting_raw:
                if not isinstance(nesting, ConfigNesting):
                    msg = f'nested_configs()[{key}] list entries must be '
                    msg += 'ConfigNesting'
                    raise TypeError(msg)
                nestings.append(nesting)
        else:
            msg = f'nested_configs()[{key}] must be ConfigNesting or list'
            raise TypeError(msg)
        for nesting in nestings:
            Config._check_config_nesting(key=key, nesting=nesting)
        list_form = isinstance(nesting_raw, list)
        Config._check_config_nesting_kinds(key=key, nestings=nestings,
                                           list_form=list_form)
        return nestings

    @staticmethod
    def _check_config_nesting_kinds(key: str, nestings: list[ConfigNesting],
                                    list_form: bool) -> None:
        """Validate combinations of nested Config declaration kinds.

        Args:
            key: Public member name described by the declarations.
            nestings: Checked declarations for one public member.
            list_form: Whether the declarations used list syntax.

        Raises:
            ValueError: The declarations combine incompatible nesting kinds.
        """
        by_key_kind = ConfigNestingKind.DICT_VALUE_BY_KEY
        by_key_nestings = [
            nesting for nesting in nestings if nesting.kind == by_key_kind]
        if list_form and len(by_key_nestings) != len(nestings):
            msg = f'nested_configs()[{key}] list '
            msg += 'may only contain DICT_VALUE_BY_KEY declarations'
            raise ValueError(msg)
        if not by_key_nestings:
            return
        used_keys: set[str] = set()
        for nesting in by_key_nestings:
            discriminator = nesting.discriminator_key
            if discriminator is None:
                msg = f'nested_configs()[{key}] DICT_VALUE_BY_KEY '
                msg += 'requires discriminator_key'
                raise ValueError(msg)
            if discriminator in used_keys:
                msg = f'nested_configs()[{key}] duplicate '
                msg += f'discriminator_key {discriminator}'
                raise ValueError(msg)
            used_keys.add(discriminator)

    def _checked_nested_configs(self, self_keys: list[str]) \
            -> dict[str, list[ConfigNesting]]:
        """Return validated and normalized nested Config declarations."""
        nested_raw: object = self.nested_configs()
        if not isinstance(nested_raw, dict):
            msg = 'nested_configs() must return a dict'
            raise TypeError(msg)
        nested_configs: dict[str, list[ConfigNesting]] = {}
        for key, nesting_raw in nested_raw.items():
            if not isinstance(key, str):
                msg = 'nested_configs() keys must be strings'
                raise TypeError(msg)
            if key not in self_keys:
                msg = f'nested_configs() returned unknown key {key}'
                raise KeyError(msg)
            nestings = self._checked_config_nesting_list(
                key=key, nesting_raw=nesting_raw)
            nested_configs[key] = nestings
        return nested_configs

    @staticmethod
    def _value_has_config(value: object) -> bool:
        """Return whether a default value visibly contains a Config object."""
        if isinstance(value, Config):
            return True
        if isinstance(value, list):
            return any(isinstance(item, Config) for item in value)
        if isinstance(value, dict):
            return any(isinstance(item, Config) for item in value.values())
        return False

    def _check_nested_config_members(
            self, self_keys: list[str],
            nested_configs: dict[str, list[ConfigNesting]]) -> None:
        """Validate that visible nested Config defaults are declared."""
        for key in self_keys:
            if key in nested_configs:
                continue
            if self._value_has_config(getattr(self, key)):
                msg = f'Nested Config member {key} is not returned from '
                msg += 'nested_configs()'
                raise TypeError(msg)

    def _validate_nested_configs(self, stderr_file: TextIO) -> None:
        """Validate all direct nested Config members before this object.

        Args:
            stderr_file: Stream used for user-facing diagnostics.
        """
        nested_configs = self._nested_config_decls
        for member_name, nesting in nested_configs.items():
            member_value = getattr(self, member_name)
            _validate_nested_config(
                member_name=member_name, member_value=member_value,
                nestings=nesting, stderr_file=stderr_file)

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
        data: Optional[dict[str, object]] = None
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
        if data is None or not isinstance(data, dict):
            msg = 'Configuration JSON root must be a JSON object.'
            print(msg, file=stderr_file)
            raise ConfigBadJson(msg=msg, doc=from_json_text, pos=0)
        assert data is not None  # runtime checked above, tell mypy it's ok
        assert isinstance(data, dict)  # tell mypy it's ok
        rocf = self._get_read_old_configuration()
        data_obj = rocf.process_json(json_data=data,
                                     auto_ch_hook=self._hook_cfg_autochange,
                                     stderr_file=stderr_file)
        self._hook_cfg_autochange.all_autochanges_done(stderr_file=stderr_file)
        assert data_obj is not None
        assert isinstance(data_obj, dict)
        data = data_obj
        self_keys = [i for i in vars(self).keys() if not
                     callable(getattr(self, i)) and not i.startswith('_')]
        omit_none_keys = self._checked_omit_none_from_json(self_keys)
        nested_configs = self._nested_config_decls
        self.check_key_match(self_keys, list(data.keys()), ok_to_use_defaults,
                             stderr_file, omit_none_keys)
        if not ok_to_use_defaults:
            for i in omit_none_keys:
                if i not in data:
                    setattr(self, i, None)
        for i in self_keys:
            if i in data.keys():
                if i in nested_configs:
                    nested_value = _nested_config_from_json(
                        member_name=i, json_data=data[i],
                        nestings=nested_configs[i], stderr_file=stderr_file)
                    setattr(self, i, nested_value)
                else:
                    self.check_dict_parse(getattr(self, i), data[i], i,
                                          ok_to_use_defaults,
                                          self._unchecked_dicts, stderr_file)
                    setattr(self, i, data[i])
        self.validate(stderr_file=stderr_file)

    def _child_owned_paths(self) -> list[ConfigPath]:
        """Return paths to nested ``Config`` subtrees owned by children.

        Used by :meth:`as_json_string` to tell
        :func:`apply_serialize_converters` which parts of the assembled
        JSON data have already been produced by a child ``Config``'s own
        ``as_json_string()`` and must not be touched by this object's
        write-side converters.

        The literal ``'['`` step in a returned path means "every list
        element or every dictionary value at this position", which lets
        ``LIST_ELEMENT`` and ``DICT_VALUE`` declarations share the same
        notation.
        """
        nested_configs = self._nested_config_decls
        child_owned: list[ConfigPath] = []
        for member, nestings in nested_configs.items():
            first = nestings[0]
            if first.kind == ConfigNestingKind.LIST_ELEMENT:
                child_owned.append((member, '['))
                continue
            if first.kind == ConfigNestingKind.DICT_VALUE:
                child_owned.append((member, '['))
                continue
            if first.kind == ConfigNestingKind.DICT_VALUE_BY_KEY:
                for nesting in nestings:
                    discriminator = nesting.discriminator_key
                    assert discriminator is not None
                    child_owned.append((member, discriminator))
                continue
            child_owned.append((member,))
        return child_owned

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
        data: dict[str, object] = {}
        self_keys = [i for i in vars(self).keys() if not
                     callable(getattr(self, i)) and not i.startswith('_')]
        omit_none_keys = self._checked_omit_none_from_json(self_keys)
        nested_configs = self._nested_config_decls
        for i in self_keys:
            if i in omit_none_keys and getattr(self, i) is None:
                continue
            if i in nested_configs:
                data[i] = _nested_config_json_data(
                    member_name=i, member_value=getattr(self, i),
                    nestings=nested_configs[i], stderr_file=stderr_file)
            else:
                data[i] = getattr(self, i)
        converters = self.serialize_converters()
        converted = apply_serialize_converters(
            data=data, converters=converters, stderr_file=stderr_file,
            child_owned_paths=self._child_owned_paths())
        return json.dumps(converted, sort_keys=True, indent=4)

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
    def value_of_type[_T](input_value: object, to_type: type[_T]) -> _T:  # noqa: D102,E501
        """Return ``input_value`` as an instance of ``to_type``.

        Args:
            input_value: Value to normalize.
            to_type: Target runtime type.

        Returns:
            ``input_value`` unchanged when it already has the expected type,
            otherwise the result of calling ``to_type(input_value)``.
        """
        assert isinstance(to_type, type)
        assert issubclass(to_type, (int, str, bool, float))
        if isinstance(input_value, to_type):
            assert isinstance(input_value, to_type)
            return input_value
        assert isinstance(input_value, (int, str, bool, float))
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
