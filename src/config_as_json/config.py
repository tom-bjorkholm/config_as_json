#! /usr/local/bin/python3
"""Base class to read and write configurations."""

# Copyright (c) 2024-2026 Tom Björkholm
# MIT License


from copy import deepcopy
import json
import sys
import csv
import sys
from collections import Counter
from typing import Any, Optional, Type, TypeVar, Mapping, NamedTuple, \
    Callable, Sequence, TextIO
from enum import Enum, IntEnum
from tempfile import TemporaryFile
from config_as_json.str_to_enum import string_to_enum_best_match
from config_as_json.config_enums import RewriteKind
from config_as_json.file_must_exist import file_must_exist
from config_as_json.commontypes import JsonType, PathOrStr
from config_as_json.config_auto_change_hook import ConfigAutoChangeHook


Keya = TypeVar('Keya', str, Enum, RewriteKind)

BackwardCompatible = NamedTuple('BackwardCompatible',
                                [('old', str), ('new', str)])


class ConfigEncoder(json.JSONEncoder):
    """Encoder for enumerations in config."""

    def default(self, o: object) -> object:
        """Define default encoding of enumerations."""
        if isinstance(o, (Enum, IntEnum)):
            return str(o.name)
        return super().default(o)


class ConfigBadJson(json.JSONDecodeError):
    """Exception class for bad JSON in configuration."""


def over_ride_needed(stri: str) -> Any:
    """Tell programmer override is needed."""
    if stri is not None:
        msg = 'Override of Config.parse_converters needed.'
        raise NotImplementedError(msg)
    return 42


ParseConverter = NamedTuple('ParseConverter', [('result_type', type),
                                               ('func', Callable[..., Any]),
                                               ('args', dict[str, Any])])


class Config():
    """Base class for classes that read and write configurations.

    Derive from this class to and have the configuration parameters
    as instance member variables of the derived class.
    """

    def __init__(self, from_json_data_text: Optional[str],
                 from_json_filename: Optional[PathOrStr],
                 auto_ch_hook: ConfigAutoChangeHook =
                 ConfigAutoChangeHook(),
                 stderr_file: TextIO = sys.stderr) -> None:
        """Construct configuration base class.

        Derived class __init__ must create all object variables
        before calling super().__init__()
        Derived class __init__ usually does checking after
        call to super().__init__()
        """
        self._stderr_file: TextIO = stderr_file
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
        if from_json_data_text is not None:
            self.parse_json(from_json_data_text)
        elif from_json_filename is not None:
            self.read(from_json_filename)

    def parse_converters(self) -> dict[str, ParseConverter]:
        """Get converters for use when parsing JSON.

        Override in derived class.
        Return None if no conversions.
        Return dict of dict for use in json decoder hook.
        Structure of return value shall be:
        {key: {'result type': res_type, 'func': function,
        'args': {arg_name: arg_value}}}.
        """
        return {'in_type': ParseConverter(result_type=int,
                                          func=over_ride_needed,
                                          args={})}

    @staticmethod
    def check_key_match(expected_keys: list[str],
                        j_keys: list[str],
                        ok_to_use_defaults: bool,
                        stderr_file: TextIO) -> None:
        """Check if keys in imported JSON match exptected keys."""
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
    def check_dict_parse(self_data: dict[str, Any], json_data: dict[str, Any],
                         key: str, ok_to_use_defaults: bool,
                         unchecked_dicts: list[str],
                         stderr_file: TextIO) -> None:
        """Check and parse dictionary."""
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
        """Convert str to correct type."""
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
        """Get default values for optional config parameters.

        Derived class shall override this method if it has
        optional config parameters.
        """
        return {}

    def _add_optional_configs(self, json_data: dict[str, JsonType]) -> None:
        """Add optional config parameters to json data as needed."""
        defval = self._def_vals_for_optional()
        for key, value in defval.items():
            if key not in json_data:
                json_data[key] = value
                self._hook_cfg_autochange.default_value_provided(
                    def_val_key=key)

    def _backward_compatible(self) -> list[BackwardCompatible]:
        """Get names of backward compatible config parameters.

        Derived class shall override this method if it has
        backward compatible config parameter names.
        """
        return []

    @staticmethod
    def _bwcompat_single(rename: BackwardCompatible,
                         json_data: dict[str, JsonType],
                         stderr_file: TextIO) -> bool:
        """Find and rename a single backward compatible in JSON data."""
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
                             stderr_file: TextIO) -> bool:
        """Find and rename a single backward compatible in JSON data."""
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
                                    json_data: dict[str, JsonType]) -> None:
        """Rename any backward compatible config parameter to new name."""
        bwcompat = self._backward_compatible()
        for name in bwcompat:
            if self._bwcompat_single(rename=name, json_data=json_data,
                                     stderr_file=self._stderr_file):
                self._hook_cfg_autochange.old_key_handled(old_key=name.old)

    def parse_json(self, from_json_text: str,
                   ok_to_use_defaults: bool = False) -> None:
        """Parse a string of JSON data and set self to that."""
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
            print(msg, file=self._stderr_file)
            if isinstance(exc, json.JSONDecodeError):
                raise ConfigBadJson(msg=msg, doc=exc.doc, pos=exc.pos) from exc
            raise ConfigBadJson(msg=msg, doc='', pos=0) from exc
        self._add_optional_configs(data)
        self._rename_backward_compatible(data)
        self._hook_cfg_autochange.all_autochanges_done()
        self_keys = [i for i in vars(self).keys() if not
                     callable(getattr(self, i)) and not i.startswith('_')]
        self.check_key_match(self_keys, data.keys(), ok_to_use_defaults,
                             self._stderr_file)
        for i in self_keys:
            if i in data.keys():
                self.check_dict_parse(getattr(self, i), data[i], i,
                                      ok_to_use_defaults,
                                      self._unchecked_dicts,
                                      self._stderr_file)
                setattr(self, i, data[i])

    def as_json_string(self) -> str:
        """Return string with this configuration as JSON data."""
        data = {}
        self_keys = [i for i in vars(self).keys() if not
                     callable(getattr(self, i)) and not i.startswith('_')]
        for i in self_keys:
            data[i] = getattr(self, i)
        return json.dumps(data, sort_keys=True, indent=4, cls=ConfigEncoder)

    def read(self, from_json_filename: PathOrStr,
             ok_to_use_defaults: bool = False) -> None:
        """Read configuration JSON from named file."""
        file_must_exist(filename=from_json_filename,
                        with_content_txt='with configuration JSON input')
        with open(from_json_filename, "r", encoding='UTF-8') as file:
            data = file.read()
            self.parse_json(data, ok_to_use_defaults)

    def write(self, to_json_filename: str) -> None:
        """Create named file with configuration as JSON."""
        with open(to_json_filename, "w", encoding='UTF-8') as file:
            text = self.as_json_string()
            file.write(text)

    @staticmethod
    def get_csv_dialect(*, name: Optional[str],  # pylint: disable=too-many-arguments, line-too-long, too-many-branches # noqa: E501
                        delimiter: Optional[str],
                        quoting: Optional[str], quotechar: Optional[str],
                        lineterminator: Optional[str],
                        escapechar: Optional[str]
                        ) -> type[csv.Dialect]:
        """Get CSV dialect object matching arguments."""
        ret: Optional[type[csv.Dialect]] = None
        if name is None or name.lower() == 'csv.excel':
            ret = csv.excel
            ret.lineterminator = '\r\n'
        elif name.lower() == 'csv.excel_tab':
            ret = csv.excel_tab
            ret.lineterminator = '\r\n'
        elif name.lower() == 'csv.unix_dialect':
            ret = csv.unix_dialect
            ret.lineterminator = '\n'
        else:
            errmsg = f'Unknown csv dialect: {name}'
            print(errmsg, file=sys.stderr)
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
            print(errmsg, file=sys.stderr)
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
                         allowed_keys: Optional[list[str]] = None) -> None:
        """Check an array of dicts that all keys match allowed/mandatory.

        Check that all keys of the list of dict are allowed.
        A key is allowed if listed in mandatory_keys of allowed_keys.
        Check that all mandatory keys exist in all dicts in the list.
        @param nam_of_cfg The name of the configuration used in error message.
        @param array The array of dicts to check.
        @param mandatory_keys An array of the mandatory keys.
        @param allowed_keys An array of allowed keys excluding madatory keys.
        """
        to_allow = deepcopy(mandatory_keys)
        in_cfg = f' in config of {name_of_cfg}'
        if allowed_keys is not None:
            to_allow += deepcopy(allowed_keys)
        for i in array:
            for used_key in list(i.keys()):
                if used_key not in to_allow:
                    bad_k = f'Found non-allowed key "{used_key}"'
                    print(bad_k + in_cfg, file=sys.stderr)
                    sys.exit(1)
            for k in mandatory_keys:
                if k not in list(i.keys()):
                    miss = f'Missing key "{k}"'
                    print(miss + in_cfg, file=sys.stderr)
                    sys.exit(1)

    @staticmethod
    def check_lst_dict(paramname: str,  # pylint: disable=too-many-arguments,too-many-positional-arguments # noqa: E501
                       inp: Sequence[Mapping[str, Any]],
                       key: str, key_optional: bool, valtype: type,
                       min_size_list: int) -> None:
        """Check that input is a list of dicts of str to list of valtype.

        @param paramname The configuration parameter name (for err msg)
        @param inp    The input to check. Expect to be list[dict[str, valtype]
        @param key    The key to check value of in each dict in list
        @param key_optional Is it OK that key is missing in dict?
        @param valtype The type that is in value for key
        @param min_size_list Minimum number of elements in list
        """
        errtxt = f'Error in parameter {paramname}. '
        if not isinstance(inp, list):
            err_txt2 = f'Expected list but found {type(inp).__name__}\n'
            print(errtxt + err_txt2 + str(inp), file=sys.stderr)
            sys.exit(1)
        assert isinstance(inp, list)
        if len(inp) < min_size_list:
            sizeerr: str = f'\nMinimum {min_size_list} elements needed ' + \
                           f'in list but only {len(inp)} found.'
            print(errtxt + sizeerr, file=sys.stderr)
            sys.exit(1)
        for elem in inp:
            if not isinstance(elem, dict):
                err_txt3 = 'Expected dict in list but found ' + \
                           f'{type(elem).__name__}\n'
                print(errtxt + err_txt3 + str(elem), file=sys.stderr)
                sys.exit(1)
            assert isinstance(elem, dict)
            if key not in elem:
                if key_optional:
                    return
                err_txt4 = f'Expected key {key} not in dict in list\n'
                print(errtxt + err_txt4 + str(elem), file=sys.stderr)
                sys.exit(1)
            val = elem[key]
            if not isinstance(val, valtype):
                err_txt5 = f'Value for key {key} expected to be of type ' + \
                           f'{valtype.__name__} but is of type ' + \
                           f'{type(val).__name__}\n'
                print(errtxt + err_txt5 + str(val), file=sys.stderr)
                sys.exit(1)

    @staticmethod
    def check_lst_dict_lst(paramname: str,  # pylint: disable=too-many-arguments,too-many-positional-arguments # noqa: E501
                           inp: Sequence[Mapping[str, Any]],
                           key: str, key_optional: bool,
                           valtype: type, min_size_outer_list: int,
                           min_size_inner_list: int) -> None:
        """Check that input is a list of dicts of str to list of valtype.

        @param paramname The configuration parameter name (for err msg)
        @param inp    The input to check. Expect to be list[dict[str, list[]]
        @param key    The key to check value of in each dict in list
        @param key_optional Is it OK that key is missing in dict?
        @param valtype The type that is in list that is value for key
        @param min_size_outer_list Minimum number of elements in outer list
        @param min_size_inner_list Minimum number of elements in inner list
        """
        Config.check_lst_dict(paramname=paramname, inp=inp,
                              key=key, key_optional=key_optional,
                              valtype=list, min_size_list=min_size_outer_list)
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
                print(errtxt + errtxt2 + str(val), file=sys.stderr)
                sys.exit(1)
            for item in val:
                if not isinstance(item, valtype):
                    errtxt3 = f'Value for key {key} expected to be ' + \
                              f'list of {valtype.__name__}\n' + \
                              f'But element in list is {type(item).__name__}\n'
                    print(errtxt + errtxt3 + str(val), file=sys.stderr)
                    sys.exit(1)

    @staticmethod
    def value_of_type(input_value: Any, to_type: Any) -> Any:
        """Convert input to given type."""
        if isinstance(input_value, to_type):
            return input_value
        return to_type(input_value)

    @staticmethod
    def check_array_dicts(name_of_cfg: str,  # pylint: disable=too-many-locals
                          array: list[dict[str, Any]],
                          kind_key: str, kind_type: type,
                          dict_of_templates: Mapping[Keya, Mapping[str, type]]
                          ) -> None:
        """Check a list of dicts that all dicts matches a template.

        Check that all dicts in list of dicts matches one of the
        templates. The templates are each a dict and all keys must
        match one of the template dicts. For each key in matching
        template the value must be of the template value type.
        @param nam_of_cfg The name of the configuration used in error message.
        @param array The array of dicts to check.
        @param kind_key The key of the kind enum that determines template.
        @param kind_type The type of enum that is used as kind enum.
        @param dict_of_templates  The dict of template dicts.
        """
        Msgs = NamedTuple('Msgs', [('in_cfg', str), ('bad_arg', str),
                                   ('bad_templ', str)])
        msgs = Msgs(in_cfg=f' in config of {name_of_cfg} ',
                    bad_arg='argument not list of dicts',
                    bad_templ='Internal error: template not dict of dicts')
        if not isinstance(array, list):
            print(msgs.bad_arg + msgs.in_cfg + '(list_of_dicts)',
                  file=sys.stderr)
            sys.exit(1)
        if not isinstance(dict_of_templates, dict):
            print(msgs.bad_templ + msgs.in_cfg + '(dict_of_templates)',
                  file=sys.stderr)
            raise KeyError(msgs.bad_templ + msgs.in_cfg +
                           '(dict_of_templates)')
        for key1, template in dict_of_templates.items():
            if not isinstance(template, dict):
                msg = f' in template for {key1.name}'
                print(msgs.bad_templ + msgs.in_cfg + msg, file=sys.stderr)
                raise KeyError(msgs.bad_templ + msgs.in_cfg + msg)
        for i, row in enumerate(array):
            litem = f'(list index {i})'
            if not isinstance(row, dict):
                print(msgs.bad_arg + msgs.in_cfg + litem, file=sys.stderr)
                sys.exit(1)
            if kind_key not in row:
                msg = f'Key {kind_key} not in dict'
                print(msg + msgs.in_cfg + litem, file=sys.stderr)
                sys.exit(1)
            kind = Config.value_of_type(row[kind_key], kind_type)
            for key2, valtype in dict_of_templates[kind].items():
                if key2 not in row:
                    msg = f'Key {key2} not in dict'
                    print(msg + msgs.in_cfg + litem, file=sys.stderr)
                    sys.exit(1)
                if not isinstance(row[key2], valtype):
                    msg = f'Value for key {key2} = {row[key2]} '
                    msg += f'is not {valtype.__name__} '
                    msg += f'it is {type(row[key2]).__name__} '
                    print(msg + msgs.in_cfg + litem, file=sys.stderr)
                    sys.exit(1)

    @staticmethod
    def get_converter_dict(enum_type: Type[Enum]) -> ParseConverter:
        """Get dict for converting to given enum_type."""
        return ParseConverter(result_type=enum_type,
                              func=string_to_enum_best_match,
                              args={'num_type': enum_type})

    @staticmethod
    def valid_char_encoding(enc: str) -> bool:
        """Check if character encoding is valid."""
        try:
            with TemporaryFile(mode='w', encoding=enc) as _:
                pass
        except LookupError as exc:
            if 'unknown encoding' in str(exc):
                return False
            raise exc  # pragma: no cover
        return True

    @staticmethod
    def check_char_encoding(enc: str) -> None:
        """Report error and exit if character encoding is not valid."""
        if not Config.valid_char_encoding(enc=enc):
            print(f'{enc} is not a recognized encoding', file=sys.stderr)
            sys.exit(1)

    @staticmethod
    def check_no_duplicates(expanded_data: list[str] | list[int],
                            param_name: str) -> None:
        """Error report duplicate data."""
        dup = [str(k) for k, v in Counter(expanded_data).items() if v > 1]
        if len(dup) == 0:
            return
        msg = f'Duplicates not allowed in {param_name}. Duplicate values: '  # noqa: E713, E501
        msg += ','.join(dup)
        print(msg, file=sys.stderr)
        sys.exit(1)
