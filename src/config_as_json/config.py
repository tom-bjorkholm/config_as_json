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
from config_as_json._config_nesting_decl import _checked_nested_configs, \
    _check_nested_config_members
from config_as_json._config_initial_data import copy_initial_data_impl, \
    auto_wrap_nested_defaults_impl
from config_as_json._deprecated_support import DeprecatedHook, \
    use_deprecated_hook, \
    warn_deprecated_hook
from config_as_json.json_write_hooks import SerializeConverters, \
    apply_serialize_converters
from config_as_json.member_path import member_path, _indexed_path
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


_READ_OLD_CONFIG_HOOK = DeprecatedHook(owner_name='Config',
                                       old_name='_get_read_old_configuration',
                                       new_name='_get_read_old_config')


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
    ``from_json_data_text``, ``from_json_filename``, ``stderr_file``, and
    ``member_name`` because those are used when nested JSON objects are
    parsed. As an alternative construction path, a ``ConfigNesting``
    declaration may provide ``factory_function`` with the same
    keyword-argument contract. The returned object must be an instance of
    the declared ``config_type``.
    """

    def __init__(self, from_json_data_text: Optional[str],
                 from_json_filename: Optional[PathOrStr],
                 auto_ch_hook: Optional[ConfigAutoChangeHook] = None,
                 stderr_file: TextIO = sys.stderr, *,
                 member_name: Optional[str]) -> None:
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
                configuration files. The object is kept by reference, so the
                application can read the recorded changes from its own object
                after parsing. See :class:`ConfigAutoChangeHook` for what
                reusing or sharing one hook instance means.
            stderr_file: Stream used for user-facing diagnostics.
            member_name: Dotted and indexed path for reaching this object by
                traversing nested attributes from the top level of the
                complete construction, such as ``outputs[1].section``.
                ``None`` means that this object is the top level and not a
                member of anything.

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
        self._hook_cfg_autochange: ConfigAutoChangeHook = auto_ch_hook
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
            _checked_nested_configs(nested_raw=self.nested_configs(),
                                    self_keys=self_keys, config_base=Config)
        self._auto_wrap_nested_defaults(stderr_file=stderr_file,
                                        member_name=member_name)
        _check_nested_config_members(config=self, self_keys=self_keys,
                                     nested_configs=self._nested_config_decls,
                                     config_base=Config)
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
            self._wrap_parse_json(from_json_data_text, stderr_file=stderr_file,
                                  member_name=member_name)
        elif from_json_filename is not None:
            self.read(from_json_filename, stderr_file=stderr_file,
                      member_name=member_name)
        else:
            self._wrap_validate(stderr_file=stderr_file,
                                member_name=member_name)

    def auto_change_hook(self) -> ConfigAutoChangeHook:
        """Return the hook that recorded automatic changes for this object.

        This is the hook supplied to the constructor, or the default hook
        created there when the application supplied none. It holds the
        automatic changes of the most recent parse, including changes inside
        declared nested ``Config`` objects.

        Returns:
            The automatic-change hook used by this configuration object.
        """
        return self._hook_cfg_autochange

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

    def _get_active_rocf(self) -> ReadOldConfiguration:
        """Return the read-old processor from the active hook."""
        if use_deprecated_hook(self, Config, _READ_OLD_CONFIG_HOOK,
                               stacklevel=4):
            return self._get_read_old_configuration()
        return self._get_read_old_config()

    def _get_read_old_config(self) -> ReadOldConfiguration:
        """Return the object that normalizes old configuration data.

        Derived classes override this method when they need to accept old
        configuration file shapes. The default object leaves parsed data
        unchanged.

        Returns:
            Read-old processor that should normalize old configuration data.
        """
        return ReadOldConfiguration()

    def _get_read_old_configuration(self) -> ReadOldConfiguration:
        """Return the object that normalizes old configuration data.

        .. deprecated:: 1.1.2
           Use :meth:`_get_read_old_config` instead. The deprecated name is
           kept during an API migration period so old subclasses continue to
           work when they override it.

        Returns:
            Read-old processor that should normalize old configuration data.
        """
        warn_deprecated_hook(_READ_OLD_CONFIG_HOOK, stacklevel=2)
        return self._get_read_old_config()

    @staticmethod
    # pylint: disable-next=too-many-arguments
    def check_key_match(expected_keys: list[str], j_keys: list[str],
                        ok_to_use_defaults: bool, stderr_file: TextIO,
                        allowed_missing_keys: Optional[list[str]] = None, *,
                        member_name: Optional[str],
                        dict_keys: bool = False) -> None:
        """Validate that parsed keys match the declared configuration keys.

        Args:
            expected_keys: Keys declared by the configuration object.
            j_keys: Keys found in parsed JSON data.
            ok_to_use_defaults: Whether missing declared keys may fall back to
                defaults supplied by the configuration object.
            stderr_file: Stream used for user-facing diagnostics.
            allowed_missing_keys: Keys that may be omitted even when
                ``ok_to_use_defaults`` is false.
            member_name: Dotted and indexed path for reaching the object or
                the dictionary that ``expected_keys`` are the keys of, by
                traversing nested attributes from the top level of the
                complete ``parse_json()`` operation, such as
                ``outputs[1].section``. ``None`` means that the keys are the
                keys of the top level and not of a member of anything.
            dict_keys: Whether the keys are keys of a plain dictionary rather
                than attribute names of a configuration object. Keys of a
                dictionary are reported in square brackets, and attribute
                names are reported after a dot.

        Raises:
            KeyError: The JSON data is missing a required key or contains an
                unexpected key.
        """
        key_path = _indexed_path if dict_keys else member_path
        if allowed_missing_keys is None:
            allowed_missing_keys = []
        if not ok_to_use_defaults:
            for i in expected_keys:
                if i not in j_keys and i not in allowed_missing_keys:
                    errmsg = f'No value for {key_path(member_name, i)} '
                    errmsg += 'in JSON data'
                    print(errmsg, file=stderr_file)
                    raise KeyError(errmsg)
        for i in j_keys:
            if i not in expected_keys:
                errmsg = 'Unexpected parameter '
                errmsg += f'{key_path(member_name, i)} in JSON data'
                print(errmsg, file=stderr_file)
                raise KeyError(errmsg)

    @staticmethod
    # pylint: disable-next=too-many-arguments,too-many-positional-arguments
    def check_dict_parse(self_data: object, json_data: object, key: str,
                         ok_to_use_defaults: bool, unchecked_dicts: list[str],
                         stderr_file: TextIO, *,
                         member_name: Optional[str]) -> None:
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
            member_name: Dotted and indexed path for reaching the checked
                value itself, by traversing nested attributes from the top
                level of the complete ``parse_json()`` operation, such as
                ``outputs[1].limits``. Values of a checked dictionary are
                reached by appending the key in square brackets. ``None``
                means that the checked value is the top level and not a
                member of anything.

        Raises:
            KeyError: The JSON structure for the key does not match the
                expected dictionary shape.
        """
        value_name = key if member_name is None else member_name
        if not isinstance(self_data, dict) and \
                not isinstance(json_data, dict):
            return
        if isinstance(self_data, dict):
            if not isinstance(json_data, dict):
                errmsg = f'Not dictionary for {value_name} in JSON data'
                print(errmsg, file=stderr_file)
                raise KeyError(errmsg)
        if not isinstance(self_data, dict):
            errmsg = f'Unexpected dictionary for {value_name} in JSON data'
            print(errmsg, file=stderr_file)
            raise KeyError(errmsg)
        if key in unchecked_dicts:
            return
        assert isinstance(self_data, dict)
        assert isinstance(json_data, dict)
        Config.check_key_match(list(self_data.keys()), list(json_data.keys()),
                               ok_to_use_defaults, stderr_file,
                               member_name=member_name, dict_keys=True)
        for i in self_data.keys():
            if i in json_data:
                value_path = _indexed_path(member_name, i)
                Config.check_dict_parse(self_data[i], json_data[i], i,
                                        ok_to_use_defaults, unchecked_dicts,
                                        stderr_file, member_name=value_path)

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

    def _validate_nested_configs(self, stderr_file: TextIO, *,
                                 member_name: Optional[str]) -> None:
        """Validate all direct nested Config members before this object.

        Args:
            stderr_file: Stream used for user-facing diagnostics.
            member_name: Dotted and indexed path for reaching this object by
                traversing nested attributes from the top level of the
                complete ``validate()`` operation, such as
                ``outputs[1].section``. ``None`` means that this object is
                the top level and not a member of anything.
        """
        nested_configs = self._nested_config_decls
        for local_name, nesting in nested_configs.items():
            member_value = getattr(self, local_name)
            _validate_nested_config(member_name=local_name,
                                    member_value=member_value,
                                    nestings=nesting, stderr_file=stderr_file,
                                    parent_path=member_name)

    @staticmethod
    def copy_initial_data(source: object, target: 'Config') -> None:
        """Copy public attributes from ``source`` onto a Config ``target``.

        Use this helper from a derived Config constructor when the
        configuration defaults come from a separate framework-neutral data
        class that the derived class wants to bridge to. The neutral data
        class can be a plain object, a dataclass instance, or a
        ``Mapping`` such as a ``dict``. Private names (those starting with
        ``_``) and bound method-like callables are not copied.

        When ``target`` already exposes at least one public attribute, the
        helper enforces that every public attribute in ``source`` is also
        declared on ``target``; an unexpected attribute on ``source``
        therefore raises immediately with a clear diagnostic message. This
        covers two practical cases: the common multiple-inheritance
        pattern where the neutral base class constructor on ``target`` has
        already established the schema, and the internal wrap path used
        when nested neutral defaults are turned into bridge instances.

        When ``target`` has not yet had its schema established, the helper
        simply copies every public attribute from ``source`` onto
        ``target`` and the source's set of names becomes the bridge's
        schema. This covers the pattern used when the neutral class
        constructor takes required arguments that the bridge does not
        duplicate; the application constructs the neutral instance and
        hands it to the bridge.

        Args:
            source: Object, dataclass instance, or mapping whose public
                attributes describe the desired initial values.
            target: Config instance whose attributes should be assigned.

        Raises:
            TypeError: ``source`` cannot be read, a mapping key is not a
                string, or ``target`` has a declared public schema and
                ``source`` exposes a public attribute that ``target`` does
                not declare.
        """
        copy_initial_data_impl(source=source, target=target)

    def _auto_wrap_nested_defaults(self, stderr_file: TextIO, *,
                                   member_name: Optional[str]) -> None:
        """Wrap nested member defaults that are not yet bridge-typed.

        Scans the validated nested-config declarations and replaces any
        default value that is not already an instance of the declared
        ``config_type`` with a freshly constructed bridge instance whose
        public attributes were copied from the original neutral value.
        Already-wrapped values are left untouched, and ``None`` is left
        in place for ``OPTIONAL_MEMBER`` declarations.

        Args:
            stderr_file: Stream used for user-facing diagnostics.
            member_name: Dotted and indexed path for reaching this object by
                traversing nested attributes from the top level of the
                complete construction, such as ``outputs[1].section``.
                ``None`` means that this object is the top level and not a
                member of anything. A diagnostic about one wrapped member
                names the whole path of that member.
        """
        auto_wrap_nested_defaults_impl(target=self,
                                       nested_decls=self._nested_config_decls,
                                       stderr_file=stderr_file,
                                       parent_path=member_name)

    def _decoded_json_object(self, from_json_text: str, stderr_file: TextIO, *,
                             member_name: Optional[str]) \
            -> dict[str, object]:
        """Decode configuration JSON text into a JSON object.

        The conversions declared by :meth:`parse_converters` are applied by
        the object hook while the text is decoded.

        Args:
            from_json_text: JSON document describing configuration values.
            stderr_file: Stream used for user-facing diagnostics.
            member_name: Dotted and indexed path for reaching this object by
                traversing nested attributes from the top level of the
                complete ``parse_json()`` operation, such as
                ``outputs[1].section``. ``None`` means that this object is
                the top level and not a member of anything, and then the
                diagnostics name no member.

        Returns:
            The decoded JSON object.

        Raises:
            ConfigBadJson: The text is not valid JSON, or its root is not a
                JSON object.
            NotImplementedError: A required custom converter was not supplied
                by a derived class.
        """
        where = '' if member_name is None else f' for {member_name}'
        hook = self._json_parse_obj_hook if self._hook_dict is not None \
            else None
        data: Optional[dict[str, object]] = None
        try:
            data = json.loads(from_json_text, object_hook=hook)
        except Exception as exc:
            if isinstance(exc, NotImplementedError):
                raise exc
            msg = f'Config.parse_json{where} failed to load JSON from '
            msg += 'string/file.\n'
            msg += 'Probably incorrectly edited configuration,\n'
            msg += 'or using wrong file (not config file) as configuration.\n'
            msg += str(exc)
            print(msg, file=stderr_file)
            if isinstance(exc, json.JSONDecodeError):
                raise ConfigBadJson(msg=msg, doc=exc.doc, pos=exc.pos) from exc
            raise ConfigBadJson(msg=msg, doc='', pos=0) from exc
        if data is None or not isinstance(data, dict):
            msg = f'Configuration JSON root{where} must be a JSON object.'
            print(msg, file=stderr_file)
            raise ConfigBadJson(msg=msg, doc=from_json_text, pos=0)
        return data

    def parse_json(self, from_json_text: str, ok_to_use_defaults: bool = False,
                   stderr_file: TextIO = sys.stderr, *,
                   member_name: Optional[str]) -> None:
        """Parse JSON text and apply it to the configuration object.

        The automatic-change hook is cleared before parsing starts, and it is
        notified once after every declared nested ``Config`` object has been
        parsed, so the report covers old-file compatibility in nested objects
        too. Nothing is reported when parsing fails before that point.

        Args:
            from_json_text: JSON document describing configuration values.
            ok_to_use_defaults: Whether missing declared keys may remain at
                their already assigned default values.
            stderr_file: Stream used for user-facing diagnostics. Defaults to
                ``sys.stderr``.
            member_name: Dotted and indexed path for reaching this object by
                traversing nested attributes from the top level of the
                complete ``parse_json()`` operation, such as
                ``outputs[1].section``. ``None`` means that this object is
                the top level and not a member of anything.

        Raises:
            ConfigBadJson: The text is not valid configuration JSON.
            KeyError: The parsed configuration does not match the declared
                keys or nested dictionary structure.
            NotImplementedError: A required custom converter was not supplied
                by a derived class.
        """
        self._hook_dict = self.parse_converters()
        self._hook_cfg_autochange.clear()
        data = self._decoded_json_object(from_json_text=from_json_text,
                                         stderr_file=stderr_file,
                                         member_name=member_name)
        rocf = self._get_active_rocf()
        data_obj = rocf.process_json(json_data=data,
                                     auto_ch_hook=self._hook_cfg_autochange,
                                     stderr_file=stderr_file)
        assert data_obj is not None
        assert isinstance(data_obj, dict)
        data = data_obj
        self_keys = [i for i in vars(self).keys() if not
                     callable(getattr(self, i)) and not i.startswith('_')]
        omit_none_keys = self._checked_omit_none_from_json(self_keys)
        nested_configs = self._nested_config_decls
        self.check_key_match(self_keys, list(data.keys()), ok_to_use_defaults,
                             stderr_file, omit_none_keys,
                             member_name=member_name)
        if not ok_to_use_defaults:
            for i in omit_none_keys:
                if i not in data:
                    setattr(self, i, None)
        for i in self_keys:
            if i in data.keys():
                if i in nested_configs:
                    nested_value = _nested_config_from_json(
                        member_name=i, json_data=data[i],
                        nestings=nested_configs[i], stderr_file=stderr_file,
                        auto_ch_hook=self._hook_cfg_autochange,
                        parent_path=member_name)
                    setattr(self, i, nested_value)
                else:
                    item_path = member_path(member_name, i)
                    self.check_dict_parse(getattr(self, i), data[i], i,
                                          ok_to_use_defaults,
                                          self._unchecked_dicts, stderr_file,
                                          member_name=item_path)
                    setattr(self, i, data[i])
        self._hook_cfg_autochange.all_autochanges_done(stderr_file=stderr_file)
        self._wrap_validate(stderr_file=stderr_file, member_name=member_name)

    def _wrap_parse_json(self, from_json_text: str,
                         ok_to_use_defaults: bool = False,
                         stderr_file: TextIO = sys.stderr, *,
                         member_name: Optional[str]) -> None:
        """Call :meth:`parse_json` on behalf of the library itself.

        Every call the library makes to ``parse_json`` on a Config object
        goes through this wrapper, so that support for derived classes that
        do not accept every argument has a single place to live. An
        application calls :meth:`parse_json` directly instead.

        Args:
            from_json_text: JSON document describing configuration values.
            ok_to_use_defaults: Whether missing declared keys may remain at
                their already assigned default values.
            stderr_file: Stream used for user-facing diagnostics. Defaults to
                ``sys.stderr``.
            member_name: Dotted and indexed path for reaching this object by
                traversing nested attributes from the top level of the
                complete ``parse_json()`` operation, such as
                ``outputs[1].section``. ``None`` means that this object is
                the top level and not a member of anything.
        """
        self.parse_json(from_json_text, ok_to_use_defaults,
                        stderr_file=stderr_file, member_name=member_name)

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

    def as_json_string(self, stderr_file: TextIO, *,
                       member_name: Optional[str]) -> str:
        """Serialize the current configuration object to formatted JSON.

        Args:
            stderr_file: Stream used for user-facing diagnostics during
                validation.
            member_name: Dotted and indexed path for reaching this object by
                traversing nested attributes from the top level of the
                complete ``as_json_string()`` operation, such as
                ``outputs[1].section``. ``None`` means that this object is
                the top level and not a member of anything.

        Returns:
            A JSON document containing every public, non-callable instance
            attribute on the configuration object.
        """
        # We validate the configuration before writing it to JSON,
        # to make sure that the configuration is valid so it can be read back
        self._wrap_validate(stderr_file=stderr_file, member_name=member_name)
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
                    nestings=nested_configs[i], stderr_file=stderr_file,
                    parent_path=member_name)
            else:
                data[i] = getattr(self, i)
        converters = self.serialize_converters()
        converted = apply_serialize_converters(
            data=data, converters=converters, stderr_file=stderr_file,
            child_owned_paths=self._child_owned_paths(),
            member_name=member_name)
        return json.dumps(converted, sort_keys=True, indent=4)

    def read(self, from_json_filename: PathOrStr,
             ok_to_use_defaults: bool = False,
             stderr_file: TextIO = sys.stderr, *,
             member_name: Optional[str]) -> None:
        """Read configuration JSON from a file and apply it to the object.

        Args:
            from_json_filename: File containing configuration JSON.
            ok_to_use_defaults: Whether missing declared keys may remain at
                their already assigned default values.
            stderr_file: Stream used for user-facing diagnostics. Defaults to
                ``sys.stderr``.
            member_name: Dotted and indexed path for reaching this object by
                traversing nested attributes from the top level of the
                complete ``read()`` operation, such as
                ``outputs[1].section``. ``None`` means that this object is
                the top level and not a member of anything.
        """
        file_must_exist(filename=from_json_filename,
                        with_content_txt='configuration JSON input',
                        stderr_file=stderr_file)
        with open(file=from_json_filename, mode='r', encoding='UTF-8') as file:
            data = file.read()
            self._wrap_parse_json(data, ok_to_use_defaults,
                                  stderr_file=stderr_file,
                                  member_name=member_name)

    def write(self, to_json_filename: PathOrStr,
              stderr_file: TextIO = sys.stderr) -> None:
        """Write the current configuration to a JSON file.

        Args:
            to_json_filename: Destination file that should receive the
                formatted JSON document.
            stderr_file: Stream used for user-facing diagnostics during
                validation.
        """
        text = self.as_json_string(stderr_file=stderr_file, member_name=None)
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

    def validate(self, stderr_file: TextIO, *,
                 member_name: Optional[str]) -> None:
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
            member_name: Dotted and indexed path for reaching this object by
                traversing nested attributes from the top level of the
                complete ``validate()`` operation, such as
                ``outputs[1].section``. ``None`` means that this object is
                the top level and not a member of anything.
        """
        self._validate_nested_configs(stderr_file=stderr_file,
                                      member_name=member_name)
        validation_plan = self.get_validation_plan(stderr_file=stderr_file)
        for validation_step in validation_plan:
            validation_step.apply(self, stderr_file, member_name=member_name)

    def _wrap_validate(self, stderr_file: TextIO, *,
                       member_name: Optional[str]) -> None:
        """Call :meth:`validate` on behalf of the library itself.

        Every call the library makes to ``validate`` on a Config object goes
        through this wrapper, so that support for derived classes that do not
        accept every argument has a single place to live. An application
        calls :meth:`validate` directly instead.

        Args:
            stderr_file: Stream used for user-facing diagnostics.
            member_name: Dotted and indexed path for reaching this object by
                traversing nested attributes from the top level of the
                complete ``validate()`` operation, such as
                ``outputs[1].section``. ``None`` means that this object is
                the top level and not a member of anything.
        """
        self.validate(stderr_file=stderr_file, member_name=member_name)
