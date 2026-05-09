#! /usr/local/bin/python3
# mypy: disable-error-code="no-untyped-def,no-untyped-call"
"""Test the Config class (part 2 of tests)."""

# Copyright (c) 2024-2026 Tom Björkholm
# MIT License

from copy import deepcopy
from enum import Enum, auto
import json
import sys
from typing import Any, Optional, cast, TextIO
import pytest
from config_as_json.config import Config, RocfKeyRename, ParseConverter
from config_as_json.config_auto_change_hook import ConfigAutoChangeHook
from config_as_json.commontypes import JsonType
from config_as_json.validator import ValidationPlan


class AbcConfig(Config):
    """Class to test defualt values."""

    def __init__(self, from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[str] = None,
                 stderr_file: TextIO = sys.stderr) -> None:
        """Construct test config object."""
        self.ab = 'a1b2'
        self.cd = 'c3d4'
        self.ef = 'e5f6'
        super().__init__(from_json_data_text=from_json_data_text,
                         from_json_filename=from_json_filename,
                         stderr_file=stderr_file)

    def _rocf_values_for_missing_json_keys(self) -> dict[str, JsonType]:
        """Return default values for optional parameters."""
        return {'cd': 'cd99', 'ef': 'ef99'}

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Get validation plan for use when validating the Config object."""
        return []


class OptionalOutputMode(Enum):
    """Output modes used by omit-None tests."""

    FAST = auto()
    CAREFUL = auto()


class OmitNoneConfig(Config):
    """Class to test omit-when-None configuration values."""

    def __init__(self, from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[str] = None,
                 stderr_file: TextIO = sys.stderr) -> None:
        """Construct a config object with true optional members."""
        self.required_name = 'default'
        self.optional_text: Optional[str] = None
        self.optional_mode: Optional[OptionalOutputMode] = None
        super().__init__(from_json_data_text=from_json_data_text,
                         from_json_filename=from_json_filename,
                         stderr_file=stderr_file)

    def _omit_none_from_json(self) -> list[str]:
        """Return the keys omitted while their value is None."""
        return ['optional_text', 'optional_mode']

    def parse_converters(self) -> dict[str, ParseConverter]:
        """Return converters for enum-valued test members."""
        return {'optional_mode': self.get_converter_dict(OptionalOutputMode)}

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Get validation plan for use when validating the Config object."""
        _ = stderr_file
        return []


class OmitNoneUnknownMemberConfig(OmitNoneConfig):
    """Class with an invalid omit-None member name."""

    def _omit_none_from_json(self) -> list[str]:
        """Return an invalid omit-None member name."""
        return ['missing_member']


class OmitNoneNonNoneDefaultConfig(Config):
    """Class with an invalid omit-None default value."""

    def __init__(self, stderr_file: TextIO = sys.stderr) -> None:
        """Construct an invalid config object for omit-None tests."""
        self.required_name = 'default'
        self.optional_text: Optional[str] = 'must fail'
        super().__init__(from_json_data_text=None, from_json_filename=None,
                         stderr_file=stderr_file)

    def _omit_none_from_json(self) -> list[str]:
        """Return a key whose constructor default is not None."""
        return ['optional_text']

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Get validation plan for use when validating the Config object."""
        _ = stderr_file
        return []


class OmitNoneBadReturnConfig(OmitNoneConfig):
    """Class with an invalid omit-None hook return value."""

    def __init__(self, omitted_keys: object,
                 stderr_file: TextIO = sys.stderr) -> None:
        """Construct an invalid config object for omit-None hook tests."""
        self._omitted_keys = omitted_keys
        super().__init__(stderr_file=stderr_file)

    def _omit_none_from_json(self) -> list[str]:
        """Return the configured invalid omit-None hook value."""
        return cast(list[str], self._omitted_keys)


class RocfRemoveAutoChangeHook(ConfigAutoChangeHook):
    """Verify the automatic-change notification from ROCF removal tests."""

    def __init__(self, old_keys_ver: list[str],
                 rocf_val_keys_ver: list[str]) -> None:
        """Construct a hook with expected automatic changes."""
        self._old_keys_ver = old_keys_ver
        self._rocf_val_keys_ver = rocf_val_keys_ver
        super().__init__()

    def auto_changed(self, old_keys_handled: list[str],
                     rocf_vals_handled: list[str],
                     stderr_file: TextIO) -> None:
        """Verify that the parser reported the expected changes."""
        _ = stderr_file
        assert self._old_keys_ver == old_keys_handled
        assert self._rocf_val_keys_ver == rocf_vals_handled


class RocfRemoveConfig(Config):
    """Class to test removed old JSON keys during ROCF parsing."""

    def __init__(self, from_json_data_text: Optional[str] = None,
                 auto_ch_hook: Optional[ConfigAutoChangeHook] = None,
                 stderr_file: TextIO = sys.stderr) -> None:
        """Construct a config object with removed-key compatibility."""
        self.version = 2
        self.name = 'current'
        self.count = 0
        self.details: dict[str, JsonType] = {
            'mode': 'normal',
            'limits': {
                'high': 10
            }
        }
        self.entries: list[JsonType] = []
        super().__init__(from_json_data_text=from_json_data_text,
                         from_json_filename=None, auto_ch_hook=auto_ch_hook,
                         stderr_file=stderr_file)

    def _rocf_get_keys_to_remove(self) -> list[str]:
        """Return old keys that should be dropped from JSON input."""
        return ['obsolete_top', 'obsolete_nested']

    def _rocf_values_for_missing_json_keys(self) -> dict[str, JsonType]:
        """Return current values for keys missing from old files."""
        return {'version': 2}

    def _rocf_get_json_key_renames(self) -> list[RocfKeyRename]:
        """Return old key names that should be mapped to current names."""
        return [RocfKeyRename(old='title', new='name')]

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Get validation plan for use when validating the Config object."""
        _ = stderr_file
        return []


def test_cfg_abc_dump_ok(capsys):
    """Test dump of default constructed AbcConfig."""
    abc = AbcConfig(stderr_file=sys.stderr)
    jstext = abc.as_json_string(stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert '' == out
    assert '' == err
    jstext = jstext.replace('\n', ' ')
    for _ in range(10):
        jstext = jstext.replace('  ', ' ')
    assert jstext == '{ "ab": "a1b2", "cd": "c3d4", "ef": "e5f6" }'


def test_omit_none_config_omits_default_none_values(capsys):
    """Test that default None members are omitted from JSON."""
    cfg = OmitNoneConfig(stderr_file=sys.stderr)
    json_data = json.loads(cfg.as_json_string(stderr_file=sys.stderr))
    out, err = capsys.readouterr()
    assert '' == out
    assert '' == err
    assert json_data == {'required_name': 'default'}


def test_omit_none_config_accepts_missing_values(capsys):
    """Test that missing omit-None members remain None."""
    cfg = OmitNoneConfig(from_json_data_text='{"required_name": "read"}',
                         stderr_file=sys.stderr)
    json_data = json.loads(cfg.as_json_string(stderr_file=sys.stderr))
    out, err = capsys.readouterr()
    assert '' == out
    assert '' == err
    assert cfg.required_name == 'read'
    assert cfg.optional_text is None
    assert cfg.optional_mode is None
    assert json_data == {'required_name': 'read'}


def test_omit_none_config_accepts_explicit_null(capsys):
    """Test that explicit JSON null is treated like a missing value."""
    cfg = OmitNoneConfig(from_json_data_text='{"required_name": "read", '
                         '"optional_text": null, '
                         '"optional_mode": null}', stderr_file=sys.stderr)
    json_data = json.loads(cfg.as_json_string(stderr_file=sys.stderr))
    out, err = capsys.readouterr()
    assert '' == out
    assert '' == err
    assert cfg.optional_text is None
    assert cfg.optional_mode is None
    assert json_data == {'required_name': 'read'}


def test_omit_none_config_keeps_explicit_values(capsys):
    """Test that explicit optional values are read, converted, and written."""
    cfg = OmitNoneConfig(from_json_data_text='{"required_name": "read", '
                         '"optional_text": "note", '
                         '"optional_mode": "FAST"}', stderr_file=sys.stderr)
    json_data = json.loads(cfg.as_json_string(stderr_file=sys.stderr))
    out, err = capsys.readouterr()
    assert '' == out
    assert '' == err
    assert cfg.optional_text == 'note'
    assert cfg.optional_mode == OptionalOutputMode.FAST
    assert json_data == {
        'optional_mode': 'FAST',
        'optional_text': 'note',
        'required_name': 'read'
    }


def test_omit_none_config_still_requires_normal_members(capsys):
    """Test that omit-None handling does not hide missing required keys."""
    with pytest.raises(KeyError):
        _ = OmitNoneConfig(from_json_data_text='{"optional_text": "note"}',
                           stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert '' == out
    assert 'No value for required_name in JSON data' in err


def test_omit_none_config_rejects_unknown_member(capsys):
    """Test that omit-None member names must exist."""
    with pytest.raises(KeyError) as exc:
        _ = OmitNoneUnknownMemberConfig(stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert '' == out
    assert '' == err
    assert '_omit_none_from_json() returned unknown key missing_member' in \
        str(exc.value)


def test_omit_none_config_rejects_non_none_default(capsys):
    """Test that omit-None members must default to None."""
    with pytest.raises(ValueError) as exc:
        _ = OmitNoneNonNoneDefaultConfig(stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert '' == out
    assert '' == err
    assert '_omit_none_from_json() key optional_text must default to None' in \
        str(exc.value)


@pytest.mark.parametrize(
    'omitted_keys, message',
    [('optional_text', '_omit_none_from_json() must return a list'),
     (['optional_text', 7
       ], '_omit_none_from_json() must return a list of strings')])
def test_omit_none_rejects_bad_hook(capsys, omitted_keys, message):
    """Test that omit-None hook return values are type checked."""
    with pytest.raises(TypeError) as exc:
        _ = OmitNoneBadReturnConfig(omitted_keys, stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert '' == out
    assert '' == err
    assert message in str(exc.value)


@pytest.mark.parametrize(
    'jstext, aval, cval, fval',
    [('{ "ab": "a1b2", "cd": "c3d4", "ef": "e5f6" }', 'a1b2', 'c3d4', 'e5f6'),
     ('{ "ab": "donald", "cd": "duck", "ef": "mouse" }', 'donald', 'duck',
      'mouse'), ('{ "ab": "aaa", "cd": "mickey" }', 'aaa', 'mickey', 'ef99'),
     ('{ "ab": "donald", "ef": "duck" }', 'donald', 'cd99', 'duck'),
     ('{ "ab": "duck"}', 'duck', 'cd99', 'ef99')])
def test_cfg_rocf_val_json_ok(capsys, jstext, aval, cval, fval):
    """Test construction of cfg from json with default values."""
    abc = AbcConfig(from_json_data_text=jstext, from_json_filename=None)
    out, err = capsys.readouterr()
    assert '' == out
    assert '' == err
    assert abc.ab == aval
    assert abc.cd == cval
    assert abc.ef == fval


@pytest.mark.parametrize('jstext', [
    '{ "cd": "c3d4", "ef": "e5f6" }', '{ "cd": "duck", "ef": "mouse" }',
    '{ "cd": "mickey" }', '{ "ef": "duck" }', '{}'])
def test_cfg_rocf_val_json_nok(capsys, jstext):
    """Test construction of cfg from json with default values."""
    with pytest.raises(KeyError):
        _ = AbcConfig(from_json_data_text=jstext, from_json_filename=None,
                      stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert '' == out
    assert 'No value for ab in' in err


def remove_json_key_in_dict(key: str, json_data: dict[str, JsonType]) -> bool:
    """Remove one ROCF key from a dictionary in tests."""
    # pylint: disable-next=protected-access
    return Config._rocf_remove_json_key_in_dict(key=key, json_data=json_data)


def remove_json_key_in_list(key: str, json_data: list[JsonType]) -> bool:
    """Remove one ROCF key from a list in tests."""
    # pylint: disable-next=protected-access
    return Config._rocf_remove_json_key_in_list(key=key, json_data=json_data)


def rename_json_key_in_dict(rename: RocfKeyRename, json_data: dict[str,
                                                                   JsonType],
                            stderr_file: TextIO) -> bool:
    """Rename one ROCF key in a dictionary in tests."""
    # pylint: disable-next=protected-access
    return Config._rocf_rename_json_key_in_dict(rename=rename,
                                                json_data=json_data,
                                                stderr_file=stderr_file)


def rename_json_key_in_list(rename: RocfKeyRename, json_data: list[JsonType],
                            stderr_file: TextIO) -> bool:
    """Rename one ROCF key in a list in tests."""
    # pylint: disable-next=protected-access
    return Config._rocf_rename_json_key_in_list(rename=rename,
                                                json_data=json_data,
                                                stderr_file=stderr_file)


def rename_json_keys(config: Config, json_data: dict[str, JsonType],
                     stderr_file: TextIO) -> None:
    """Rename all configured ROCF keys in tests."""
    # pylint: disable-next=protected-access
    config._rocf_rename_json_keys(json_data=json_data, stderr_file=stderr_file)


@pytest.mark.parametrize('ind,outd,key,changed',
                         [({
                             'keep': 1
                         }, {
                             'keep': 1
                         }, 'obsolete', False),
                          ({
                              'obsolete': 1,
                              'keep': 2
                          }, {
                              'keep': 2
                          }, 'obsolete', True),
                          ({
                              'outer': {
                                  'obsolete': 'old',
                                  'keep': {
                                      'value': 3
                                  }
                              }
                          }, {
                              'outer': {
                                  'keep': {
                                      'value': 3
                                  }
                              }
                          }, 'obsolete', True),
                          ({
                              'items': [{
                                  'obsolete': 1,
                                  'keep': 2
                              }, [{
                                  'obsolete': 3
                              }]],
                              'obsolete': 4
                          }, {
                              'items': [{
                                  'keep': 2
                              }, [{}]]
                          }, 'obsolete', True)])
def test_rocf_remove_json_key_in_dict(capsys, ind, outd, key, changed):
    """Test removing one ROCF key from nested dictionaries."""
    data = deepcopy(ind)
    assert remove_json_key_in_dict(key=key, json_data=data) == changed
    out, err = capsys.readouterr()
    assert '' == out
    assert '' == err
    assert data == outd


@pytest.mark.parametrize('ind,outd,key,changed',
                         [([], [], 'obsolete', False),
                          ([{
                              'obsolete': 1,
                              'keep': 2
                          }, [{
                              'obsolete': 3,
                              'keep': 4
                          }]], [{
                              'keep': 2
                          }, [{
                              'keep': 4
                          }]], 'obsolete', True)])
def test_rocf_remove_json_key_in_list(capsys, ind, outd, key, changed):
    """Test removing one ROCF key from nested lists."""
    data = deepcopy(ind)
    assert remove_json_key_in_list(key=key, json_data=data) == changed
    out, err = capsys.readouterr()
    assert '' == out
    assert '' == err
    assert data == outd


@pytest.mark.parametrize('json_data', [{'a': 'b'}, [{'a': 'b'}]])
def test_rocf_remove_json_key_rejects_none_key(capsys, json_data):
    """Test that removing a None key fails like invalid ROCF rename rules."""
    with pytest.raises(AssertionError):
        if isinstance(json_data, dict):
            remove_json_key_in_dict(key=cast(Any, None), json_data=json_data)
        else:
            remove_json_key_in_list(key=cast(Any, None), json_data=json_data)
    out, _ = capsys.readouterr()
    assert '' == out


def test_rocf_removed_keys_are_accepted_and_reported(capsys):
    """Test parsing old JSON with removed, renamed and missing keys."""
    jstext = json.dumps({
        'title':
        'legacy report',
        'count':
        3,
        'details': {
            'mode': 'careful',
            'obsolete_nested': 'drop',
            'limits': {
                'high': 20,
                'obsolete_nested': 'drop'
            }
        },
        'entries': [{
            'name': 'first',
            'obsolete_nested': 'drop'
        }, [{
            'obsolete_nested': 'drop'
        }]],
        'obsolete_top': {
            'ignored': True
        }
    })
    hook = RocfRemoveAutoChangeHook(
        old_keys_ver=['obsolete_top', 'obsolete_nested', 'title'],
        rocf_val_keys_ver=['version'])
    cfg = RocfRemoveConfig(from_json_data_text=jstext, auto_ch_hook=hook,
                           stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert '' == out
    assert '' == err
    assert cfg.version == 2
    assert cfg.name == 'legacy report'
    assert cfg.count == 3
    assert cfg.details == {'mode': 'careful', 'limits': {'high': 20}}
    assert cfg.entries == [{'name': 'first'}, [{}]]


def test_rocf_removed_keys_absent_does_not_report_change(capsys):
    """Test current JSON parsing when no removed old keys are present."""
    jstext = json.dumps({
        'version': 2,
        'name': 'current report',
        'count': 4,
        'details': {
            'mode': 'normal',
            'limits': {
                'high': 9
            }
        },
        'entries': []
    })
    cfg = RocfRemoveConfig(from_json_data_text=jstext,
                           auto_ch_hook=RocfRemoveAutoChangeHook(
                               old_keys_ver=[], rocf_val_keys_ver=[]),
                           stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert '' == out
    assert '' == err
    assert cfg.version == 2
    assert cfg.name == 'current report'
    assert cfg.count == 4
    assert cfg.details == {'mode': 'normal', 'limits': {'high': 9}}
    assert not cfg.entries


@pytest.mark.parametrize(
    'ind, outd, ren, errtxt',
    [({
        'foo': 12,
        'bar': 'data'
    }, {
        'foo': 12,
        'bar': 'data'
    }, RocfKeyRename(old='star', new='sun'), ''),
     ({
         'foo': 12,
         'bar': 'data'
     }, {
         'sun': 12,
         'bar': 'data'
     }, RocfKeyRename(old='foo', new='sun'), ''),
     ({
         'foo': 12,
         'bar': 'data'
     }, {
         'foo': 12,
         'sun': 'data'
     }, RocfKeyRename(old='bar', new='sun'), ''),
     ({
         'foo': 12,
         'bar': 'data'
     }, {
         'foo': 12
     }, RocfKeyRename(old='bar', new='foo'), 'Inconsistent configuration:\n' +
      'Both new config parameter foo and old bar ' +
      'present.\nIgnoring old parameter bar\n'),
     ({
         'foo': {
             'a': 'b',
             'bar': 'c'
         },
         'bar': 'data'
     }, {
         'foo': {
             'a': 'b',
             'sun': 'c'
         },
         'sun': 'data'
     }, RocfKeyRename(old='bar', new='sun'), ''),
     ({
         'foo': {
             'a': 'b',
             'foo': 'c'
         },
         'bar': 'data'
     }, {
         'sun': {
             'a': 'b',
             'sun': 'c'
         },
         'bar': 'data'
     }, RocfKeyRename(old='foo', new='sun'), ''),
     ({
         'foo': {
             'foo': 'b',
             'bar': 'c'
         },
         'bar': 'data'
     }, {
         'sun': {
             'sun': 'b',
             'bar': 'c'
         },
         'bar': 'data'
     }, RocfKeyRename(old='foo', new='sun'), ''),
     ({
         'a': [{
             'a': 1,
             'b': 2
         }, {
             'a': 3,
             'b': 4
         }],
         'b': 5
     }, {
         'c': [{
             'c': 1,
             'b': 2
         }, {
             'c': 3,
             'b': 4
         }],
         'b': 5
     }, RocfKeyRename(old='a', new='c'), '')])
def test_bw_compat_single1(capsys, ind, outd, ren, errtxt):
    """Test Config._bwcompat_single for case 1."""
    data = deepcopy(ind)
    rename_json_key_in_dict(rename=ren, json_data=data, stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert '' == out
    assert err == errtxt
    assert data == outd


@pytest.mark.parametrize('ren', [
    RocfKeyRename(old=cast(Any, None), new='sun'),
    RocfKeyRename(old='foo', new=cast(Any, None)),
    RocfKeyRename(old='foo', new='foo')])
def test_bw_compat_single2(capsys, ren):
    """Test Config._bwcompat_single for not OK case."""
    with pytest.raises(AssertionError):
        rename_json_key_in_dict(rename=ren, json_data={'a': 'b'},
                                stderr_file=sys.stderr)
    out, _ = capsys.readouterr()
    assert '' == out


@pytest.mark.parametrize(
    'ind,outd,ren,errtxt',
    [([{
        'a': 2,
        'b': 'c'
    }, {
        'a': 4,
        'b': 'd'
    }], [{
        'e': 2,
        'b': 'c'
    }, {
        'e': 4,
        'b': 'd'
    }], RocfKeyRename(old='a', new='e'), ''),
     ([{
         'foo': 12,
         'bar': 'data'
     }, {
         'fff': 14,
         'bar': 'other'
     }], [{
         'foo': 12
     }, {
         'fff': 14,
         'foo': 'other'
     }], RocfKeyRename(old='bar', new='foo'), 'Inconsistent configuration:\n' +
      'Both new config parameter foo and old bar ' +
      'present.\nIgnoring old parameter bar\n'),
     ([[{
         'a': 1,
         'b': 2
     }, {
         'a': 3,
         'b': 4
     }]], [[{
         'a': 1,
         'c': 2
     }, {
         'a': 3,
         'c': 4
     }]], RocfKeyRename(old='b', new='c'), '')])
def test_bwcompat_single_lst1(capsys, ind, outd, ren, errtxt):
    """Test Config._bwcompat_single_lst for case 1."""
    data = deepcopy(ind)
    rename_json_key_in_list(rename=ren, json_data=data, stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert '' == out
    assert err == errtxt
    assert data == outd


class DummyCfg(Config):
    """Dummy Config for testing only."""

    def __init__(self, stderr_file: TextIO = sys.stderr) -> None:
        """Create a DummyCfg object."""
        self.aa = 'text'
        super().__init__(from_json_data_text='{ "aa": "text" }',
                         from_json_filename=None, stderr_file=stderr_file)

    def _rocf_get_json_key_renames(self) -> list[RocfKeyRename]:
        return [
            RocfKeyRename(old='a', new='x'),
            RocfKeyRename(old='b', new='y'),
            RocfKeyRename(old='c', new='z')
        ]

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Get validation plan for use when validating the Config object."""
        return []


@pytest.mark.parametrize('ind,outd,errtxt', [({
    'p': [{
        'a': 2,
        'b': 'c'
    }, {
        'a': 4,
        'b': 'd'
    }]
}, {
    'p': [{
        'x': 2,
        'y': 'c'
    }, {
        'x': 4,
        'y': 'd'
    }]
}, '')])
def test_rename_backward_compatible(capsys, ind, outd, errtxt):
    """Test Config._rename_backward_compatible."""
    data = deepcopy(ind)
    cfg = DummyCfg(stderr_file=sys.stderr)
    rename_json_keys(config=cfg, json_data=data, stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert '' == out
    assert err == errtxt
    assert data == outd
