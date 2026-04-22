#! /usr/local/bin/python3
"""Implement the core configuration model for config-as-json.

Applications derive from :class:`Config`, create one instance attribute for
each supported configuration setting, and use those attribute values as the
default configuration. Each such configuration setting can also have a value
type of dict or list, or even a nested dict or list.
The base class then provides JSON serialization, parsing, schema-like key
checks, optional-value filling, backward-compatible key renaming, and a
collection of validation helpers for common patterns.
"""

# Copyright (c) 2024-2026 Tom Björkholm
# MIT License


from copy import deepcopy
import json
import sys
import csv
from collections import Counter
from typing import Any, Optional, Type, TypeVar, Mapping, NamedTuple, \
    Callable, Sequence, TextIO
from enum import Enum, IntEnum
from tempfile import TemporaryFile
from config_as_json.str_to_enum import string_to_enum_best_match
from config_as_json.file_must_exist import file_must_exist
from config_as_json.commontypes import JsonType, PathOrStr
from config_as_json.config_auto_change_hook import ConfigAutoChangeHook
from config_as_json.validator import ValidationPlan


Keya = TypeVar('Keya', str, Enum)

BackwardCompatible = NamedTuple('BackwardCompatible',
                                [('old', str), ('new', str)])
"""Describe a configuration key rename from an old name to a new name."""


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


def over_ride_needed(stri: str) -> Any:
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
    read JSON into the object, write the current values back to JSON, fill in
    optional keys, and apply controlled backward-compatible key renames.
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
                as filled default values or renamed backward-compatible keys.
            stderr_file: Stream used for user-facing diagnostics.

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
                                          func=over_ride_needed,
                                          args={})}

    @staticmethod
    def check_key_match(expected_keys: list[str],
                        j_keys: list[str],
                        ok_to_use_defaults: bool,
                        stderr_file: TextIO) -> None:
        """Validate that parsed keys match the declared configuration keys.

        Args:
            expected_keys: Keys declared by the configuration object.
            j_keys: Keys found in parsed JSON data.
            ok_to_use_defaults: Whether missing declared keys may fall back to
                defaults supplied by the configuration object.
            stderr_file: Stream used for user-facing diagnostics.

        Raises:
            KeyError: The JSON data is missing a required key or contains an
                unexpected key.
        """
        if not ok_to_use_defaults:
            for i in expected_keys:
                if i not in j_keys:
                    errmsg = f'No value for {i} in JSON data'
                    print(errmsg, file=stderr_file)
                    raise KeyError(errmsg)
        for i in j_keys:
            if i not in expected_keys:
                errmsg = f'Unexpected parameter {i} in JSON data'
                print(errmsg, file=stderr_file)
                raise KeyError(errmsg)

    @staticmethod
    def check_dict_parse(self_data: dict[str, Any], json_data: dict[str, Any],  # pylint: disable=too-many-arguments,too-many-positional-arguments # noqa: E501
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
        for key, value in ret.items():
            if key in hookd:
                parse_c = hookd[key]
                if not isinstance(value, parse_c.result_type):
                    ret[key] = parse_c.func(value, **parse_c.args)
        return ret

    def _def_vals_for_optional(self) -> dict[str, JsonType]:
        """Return default values for optional configuration keys.

        Derived classes override this method when some configuration keys are
        optional in input files but should still be present on the in-memory
        object after parsing.

        Returns:
            A mapping from optional key name to the default value that should
            be supplied when the key is absent from JSON input.
        """
        return {}

    def _add_optional_configs(self, json_data: dict[str, JsonType]) -> None:
        """Insert missing optional keys into parsed JSON data.

        Args:
            json_data: Parsed JSON object that will be applied to the
                configuration instance.
        """
        defval = self._def_vals_for_optional()
        for key, value in defval.items():
            if key not in json_data:
                json_data[key] = value
                self._hook_cfg_autochange.default_value_provided(
                    def_val_key=key)

    def _backward_compatible(self) -> list[BackwardCompatible]:
        """Return configuration key renames that remain accepted as input.

        Derived classes override this method to describe legacy key names that
        should be mapped onto their current names during parsing.

        Returns:
            A list of ``BackwardCompatible`` entries describing accepted key
            renames.
        """
        return []

    @staticmethod
    def _bwcompat_single(rename: BackwardCompatible,
                         json_data: dict[str, JsonType],
                         stderr_file: TextIO = sys.stderr) -> bool:
        """Apply one backward-compatible key rename in a nested dictionary.

        Args:
            rename: Legacy-to-current key mapping to apply.
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
                      f'old {rename.old} present.',
                      file=stderr_file)
                print(f'Ignoring old parameter {rename.old}', file=stderr_file)
                del json_data[rename.old]
            else:
                json_data[rename.new] = json_data[rename.old]
                del json_data[rename.old]
                ret = True
        for _, value in json_data.items():
            if isinstance(value, dict):
                assert isinstance(value, dict)
                ret |= Config._bwcompat_single(rename=rename, json_data=value,
                                               stderr_file=stderr_file)
            if isinstance(value, list):
                assert isinstance(value, list)
                ret |= Config._bwcompat_single_lst(rename=rename,
                                                   json_data=value,
                                                   stderr_file=stderr_file)
        return ret

    @staticmethod
    def _bwcompat_single_lst(rename: BackwardCompatible,
                             json_data: list[JsonType],
                             stderr_file: TextIO = sys.stderr) -> bool:
        """Apply one backward-compatible key rename inside nested lists.

        Args:
            rename: Legacy-to-current key mapping to apply.
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
                ret |= Config._bwcompat_single(rename=rename,
                                               json_data=value,
                                               stderr_file=stderr_file)
            if isinstance(value, list):
                assert isinstance(value, list)
                ret |= Config._bwcompat_single_lst(rename=rename,
                                                   json_data=value,
                                                   stderr_file=stderr_file)
        return ret

    def _rename_backward_compatible(self,
                                    json_data: dict[str, JsonType],
                                    stderr_file: TextIO) -> None:
        """Apply all declared backward-compatible key renames in place.

        Args:
            json_data: Parsed JSON object to normalize before validation.
            stderr_file: Stream used for user-facing diagnostics.
        """
        bwcompat = self._backward_compatible()
        for name in bwcompat:
            if self._bwcompat_single(rename=name, json_data=json_data,
                                     stderr_file=stderr_file):
                self._hook_cfg_autochange.old_key_handled(old_key=name.old)

    def parse_json(self, from_json_text: str,
                   ok_to_use_defaults: bool = False,
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
        self._add_optional_configs(data)
        self._rename_backward_compatible(data, stderr_file=stderr_file)
        self._hook_cfg_autochange.all_autochanges_done(stderr_file=stderr_file)
        self_keys = [i for i in vars(self).keys() if not
                     callable(getattr(self, i)) and not i.startswith('_')]
        self.check_key_match(self_keys, data.keys(), ok_to_use_defaults,
                             stderr_file)
        for i in self_keys:
            if i in data.keys():
                self.check_dict_parse(getattr(self, i), data[i], i,
                                      ok_to_use_defaults,
                                      self._unchecked_dicts,
                                      stderr_file)
                setattr(self, i, data[i])

    def as_json_string(self, stderr_file: TextIO) -> str:
        """Serialize the current configuration object to formatted JSON.

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
        for i in self_keys:
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
            self.parse_json(data, ok_to_use_defaults,
                            stderr_file=stderr_file)

    def write(self, to_json_filename: PathOrStr,
              stderr_file: TextIO = sys.stderr) -> None:
        """Write the current configuration to a JSON file.

        Args:
            to_json_filename: Destination file that should receive the
                formatted JSON document.
        """
        text = self.as_json_string(stderr_file=stderr_file)
        with open(file=to_json_filename, mode='w', encoding='UTF-8') as file:
            file.write(text)

    @staticmethod
    def get_csv_dialect(*, name: Optional[str],  # pylint: disable=too-many-arguments, line-too-long, too-many-branches # noqa: E501
                        delimiter: Optional[str],
                        quoting: Optional[str], quotechar: Optional[str],
                        lineterminator: Optional[str],
                        escapechar: Optional[str],
                        stderr_file: TextIO = sys.stderr
                        ) -> csv.Dialect:
        """Build a ``csv.Dialect`` from serialized configuration fields.

        Args:
            name: Name of a standard-library dialect template to start from.
            delimiter: Optional field delimiter override.
            quoting: Optional quoting constant name such as
                ``'csv.quote_all'``.
            quotechar: Optional quoting character override.
            lineterminator: Optional line terminator override.
            escapechar: Optional escape character override.
            stderr_file: Stream used for user-facing diagnostics. Defaults to
                ``sys.stderr``.

        Returns:
            A configured ``csv.Dialect`` instance.

        Raises:
            KeyError: ``name`` or ``quoting`` is not one of the supported
                serialized values.
        """
        ret: Optional[csv.Dialect] = None
        if name is None or name.lower() == 'csv.excel':
            ret = csv.excel()
            ret.lineterminator = '\r\n'
        elif name.lower() == 'csv.excel_tab':
            ret = csv.excel_tab()
            ret.lineterminator = '\r\n'
        elif name.lower() == 'csv.unix_dialect':
            ret = csv.unix_dialect()
            ret.lineterminator = '\n'
        else:
            errmsg = f'Unknown csv dialect: {name}'
            print(errmsg, file=stderr_file)
            raise KeyError(errmsg)
        if delimiter is not None:
            ret.delimiter = delimiter
        if quoting is None:
            ret.quoting = csv.QUOTE_MINIMAL
        elif quoting.lower() == 'csv.quote_all':
            ret.quoting = csv.QUOTE_ALL
        elif quoting.lower() == 'csv.quote_minimal':
            ret.quoting = csv.QUOTE_MINIMAL
        elif quoting.lower() == 'csv.quote_none':
            ret.quoting = csv.QUOTE_NONE
        elif quoting.lower() == 'csv.quote_nonnumeric':
            ret.quoting = csv.QUOTE_NONNUMERIC
        else:
            errmsg = f'Unknown csv quoting: {quoting}'
            print(errmsg, file=stderr_file)
            raise KeyError(errmsg)
        if quotechar is None:
            ret.quotechar = '"'
        else:
            ret.quotechar = quotechar
        if lineterminator is not None:
            ret.lineterminator = lineterminator
        if escapechar is None:
            ret.escapechar = '\\'
        else:
            ret.escapechar = escapechar
        return ret

    @staticmethod
    def check_array_keys(name_of_cfg: str, array: Sequence[Mapping[str, Any]],
                         mandatory_keys: list[str],
                         allowed_keys: Optional[list[str]] = None,
                         stderr_file: TextIO = sys.stderr) -> None:
        """Validate keys in a list of mapping objects.

        Every mapping in ``array`` must contain all keys in
        ``mandatory_keys`` and may only contain those keys plus any keys in
        ``allowed_keys``.

        Args:
            name_of_cfg: Name used in user-facing error messages.
            array: Sequence of mappings to validate.
            mandatory_keys: Keys that must be present in every mapping.
            allowed_keys: Extra optional keys that are accepted in addition to
                the mandatory keys.
            stderr_file: Stream used for user-facing diagnostics. Defaults to
                ``sys.stderr``.
        """
        to_allow = deepcopy(mandatory_keys)
        in_cfg = f' in config of {name_of_cfg}'
        if allowed_keys is not None:
            to_allow += deepcopy(allowed_keys)
        for i in array:
            for used_key in list(i.keys()):
                if used_key not in to_allow:
                    bad_k = f'Found non-allowed key "{used_key}"'
                    print(bad_k + in_cfg, file=stderr_file)
                    sys.exit(1)
            for k in mandatory_keys:
                if k not in list(i.keys()):
                    miss = f'Missing key "{k}"'
                    print(miss + in_cfg, file=stderr_file)
                    sys.exit(1)

    @staticmethod
    def check_lst_dict(paramname: str,  # pylint: disable=too-many-arguments,too-many-positional-arguments # noqa: E501
                       inp: Sequence[Mapping[str, Any]],
                       key: str, key_optional: bool, valtype: type,
                       min_size_list: int,
                       stderr_file: TextIO = sys.stderr) -> None:
        """Validate a list of mappings that carry one typed value per row.

        Args:
            paramname: Configuration parameter name used in diagnostics.
            inp: Sequence that should be a list of dictionaries.
            key: Key whose value type should be checked in each dictionary.
            key_optional: Whether dictionaries may omit ``key``.
            valtype: Expected runtime type for the value stored at ``key``.
            min_size_list: Minimum allowed number of dictionaries in ``inp``.
            stderr_file: Stream used for user-facing diagnostics. Defaults to
                ``sys.stderr``.
        """
        errtxt = f'Error in parameter {paramname}. '
        if not isinstance(inp, list):
            err_txt2 = f'Expected list but found {type(inp).__name__}\n'
            print(errtxt + err_txt2 + str(inp), file=stderr_file)
            sys.exit(1)
        assert isinstance(inp, list)
        if len(inp) < min_size_list:
            sizeerr: str = f'\nMinimum {min_size_list} elements needed ' + \
                           f'in list but only {len(inp)} found.'
            print(errtxt + sizeerr, file=stderr_file)
            sys.exit(1)
        for elem in inp:
            if not isinstance(elem, dict):
                err_txt3 = 'Expected dict in list but found ' + \
                           f'{type(elem).__name__}\n'
                print(errtxt + err_txt3 + str(elem), file=stderr_file)
                sys.exit(1)
            assert isinstance(elem, dict)
            if key not in elem:
                if key_optional:
                    return
                err_txt4 = f'Expected key {key} not in dict in list\n'
                print(errtxt + err_txt4 + str(elem), file=stderr_file)
                sys.exit(1)
            val = elem[key]
            if not isinstance(val, valtype):
                err_txt5 = f'Value for key {key} expected to be of type ' + \
                           f'{valtype.__name__} but is of type ' + \
                           f'{type(val).__name__}\n'
                print(errtxt + err_txt5 + str(val), file=stderr_file)
                sys.exit(1)

    @staticmethod
    def check_lst_dict_lst(paramname: str,  # pylint: disable=too-many-arguments,too-many-positional-arguments # noqa: E501
                           inp: Sequence[Mapping[str, Any]],
                           key: str, key_optional: bool,
                           valtype: type, min_size_outer_list: int,
                           min_size_inner_list: int,
                           stderr_file: TextIO = sys.stderr) -> None:
        """Validate a list of mappings whose checked value is itself a list.

        Args:
            paramname: Configuration parameter name used in diagnostics.
            inp: Sequence that should be a list of dictionaries.
            key: Key whose value should be a list of ``valtype`` items.
            key_optional: Whether dictionaries may omit ``key``.
            valtype: Expected runtime type for each item in the inner list.
            min_size_outer_list: Minimum number of dictionaries in ``inp``.
            min_size_inner_list: Minimum number of items in each checked inner
                list.
            stderr_file: Stream used for user-facing diagnostics. Defaults to
                ``sys.stderr``.
        """
        Config.check_lst_dict(paramname=paramname, inp=inp,
                              key=key, key_optional=key_optional,
                              valtype=list, min_size_list=min_size_outer_list,
                              stderr_file=stderr_file)
        assert isinstance(inp, list)
        errtxt = f'Error in parameter {paramname}.\n'
        for elem in inp:
            assert isinstance(elem, dict)
            if key not in elem and key_optional:
                continue
            assert key in elem
            val = elem[key]
            assert isinstance(val, list)
            if len(val) < min_size_inner_list:
                errtxt2 = f'List for key {key} shall be minimum ' + \
                          f'{min_size_inner_list} elements.\nBut it ' + \
                          f'is {len(val)} elements only.\n'
                print(errtxt + errtxt2 + str(val), file=stderr_file)
                sys.exit(1)
            for item in val:
                if not isinstance(item, valtype):
                    errtxt3 = f'Value for key {key} expected to be ' + \
                              f'list of {valtype.__name__}\n' + \
                              f'But element in list is {type(item).__name__}\n'
                    print(errtxt + errtxt3 + str(val), file=stderr_file)
                    sys.exit(1)

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
    # pylint: disable=too-many-locals
    # pylint: disable=too-many-arguments,too-many-positional-arguments
    def check_array_dicts(name_of_cfg: str,
                          array: list[dict[str, Any]],
                          kind_key: str, kind_type: type,
                          dict_of_templates: Mapping[Keya, Mapping[str, type]],
                          stderr_file: TextIO = sys.stderr
                          ) -> None:
        """Validate a list of dictionaries against type templates.

        Each row in ``array`` selects its expected template through
        ``kind_key``. The selected template then defines which keys must
        exist and which runtime types their values must have.

        Args:
            name_of_cfg: Name used in user-facing error messages.
            array: List of dictionaries to validate.
            kind_key: Key whose value selects the expected template.
            kind_type: Type used to normalize the value at ``kind_key``.
            dict_of_templates: Mapping from kind value to a dictionary of
                expected keys and value types.
            stderr_file: Stream used for user-facing diagnostics. Defaults to
                ``sys.stderr``.
        """
        Msgs = NamedTuple('Msgs', [('in_cfg', str), ('bad_arg', str),
                                   ('bad_templ', str)])
        msgs = Msgs(in_cfg=f' in config of {name_of_cfg} ',
                    bad_arg='argument not list of dicts',
                    bad_templ='Internal error: template not dict of dicts')
        if not isinstance(array, list):
            print(msgs.bad_arg + msgs.in_cfg + '(list_of_dicts)',
                  file=stderr_file)
            sys.exit(1)
        if not isinstance(dict_of_templates, dict):
            print(msgs.bad_templ + msgs.in_cfg + '(dict_of_templates)',
                  file=stderr_file)
            raise KeyError(msgs.bad_templ + msgs.in_cfg +
                           '(dict_of_templates)')
        for key1, template in dict_of_templates.items():
            if not isinstance(template, dict):
                msg = f' in template for {key1.name}'
                print(msgs.bad_templ + msgs.in_cfg + msg, file=stderr_file)
                raise KeyError(msgs.bad_templ + msgs.in_cfg + msg)
        for i, row in enumerate(array):
            litem = f'(list index {i})'
            if not isinstance(row, dict):
                print(msgs.bad_arg + msgs.in_cfg + litem, file=stderr_file)
                sys.exit(1)
            if kind_key not in row:
                msg = f'Key {kind_key} not in dict'
                print(msg + msgs.in_cfg + litem, file=stderr_file)
                sys.exit(1)
            kind = Config.value_of_type(row[kind_key], kind_type)
            for key2, valtype in dict_of_templates[kind].items():
                if key2 not in row:
                    msg = f'Key {key2} not in dict'
                    print(msg + msgs.in_cfg + litem, file=stderr_file)
                    sys.exit(1)
                if not isinstance(row[key2], valtype):
                    msg = f'Value for key {key2} = {row[key2]} '
                    msg += f'is not {valtype.__name__} '
                    msg += f'it is {type(row[key2]).__name__} '
                    print(msg + msgs.in_cfg + litem, file=stderr_file)
                    sys.exit(1)

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

    @staticmethod
    def valid_char_encoding(enc: str) -> bool:
        """Return whether ``enc`` names a valid text encoding.

        Args:
            enc: Encoding name to test.

        Returns:
            ``True`` when Python recognizes ``enc`` as a text encoding,
            otherwise ``False``.
        """
        try:
            with TemporaryFile(mode='w', encoding=enc) as _:
                pass
        except LookupError as exc:
            if 'unknown encoding' in str(exc):
                return False
            raise exc  # pragma: no cover
        return True

    @staticmethod
    def check_char_encoding(enc: str,
                            stderr_file: TextIO = sys.stderr) -> None:
        """Fail fast when a named character encoding is not recognized.

        Args:
            enc: Encoding name to validate.
            stderr_file: Stream used for user-facing diagnostics. Defaults to
                ``sys.stderr``.
        """
        if not Config.valid_char_encoding(enc=enc):
            print(f'{enc} is not a recognized encoding', file=stderr_file)
            sys.exit(1)

    @staticmethod
    def check_no_duplicates(expanded_data: list[str] | list[int],
                            param_name: str,
                            stderr_file: TextIO = sys.stderr) -> None:
        """Fail if a sequence contains duplicate values.

        Args:
            expanded_data: Sequence whose values must be unique.
            param_name: Configuration parameter name used in diagnostics.
            stderr_file: Stream used for user-facing diagnostics. Defaults to
                ``sys.stderr``.
        """
        dup = [str(k) for k, v in Counter(expanded_data).items() if v > 1]
        if len(dup) == 0:
            return
        msg = f'Duplicates not allowed in {param_name}. Duplicate values: '  # noqa: E713, E501
        msg += ','.join(dup)
        print(msg, file=stderr_file)
        sys.exit(1)

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
        validation_plan = self.get_validation_plan(stderr_file=stderr_file)
        for validation_step in validation_plan:
            validation_step.apply(self, stderr_file)
