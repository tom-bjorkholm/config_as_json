#! /usr/local/bin/python3
"""Test the Config class (part 2 of tests)."""

# Copyright (c) 2024-2026 Tom Björkholm
# MIT License

from copy import deepcopy
from enum import Enum, auto
import json
import sys
from typing import Any, Optional, cast, TextIO
import pytest
from pytest import CaptureFixture
from config_as_json.config import Config, RocfKeyRename, ParseConverter
from config_as_json.config_auto_change_hook import ConfigAutoChangeHook
from config_as_json.config_nesting import ConfigNesting, ConfigNestingKind, \
    NestedConfigs
from config_as_json.commontypes import JsonType
from config_as_json.validator import InvalidConfiguration, ValidationPlan, \
    WholeConfigValidationStep, WholeConfigValidator


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


# pylint: disable-next=too-few-public-methods
class NestedOutputValidator(WholeConfigValidator):
    """Normalize the output format in nested Config tests."""

    def validate(self, config: Config,
                 stderr_file: TextIO = sys.stderr) -> None:
        """Validate and normalize one nested output configuration."""
        assert isinstance(config, NestedOutputConfig)
        value = config.output_format.lower()
        if value in ('csv', 'txt'):
            config.output_format = value.upper()
            return
        msg = 'Nested output format must be CSV or TXT'
        print(msg, file=stderr_file)
        raise InvalidConfiguration(msg)


class NestedOutputConfig(Config):
    """Nested configuration class used by nested Config tests."""

    def __init__(self, from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[str] = None,
                 stderr_file: TextIO = sys.stderr) -> None:
        """Construct the nested output configuration."""
        self.output_format = self._default_format()
        super().__init__(from_json_data_text=from_json_data_text,
                         from_json_filename=from_json_filename,
                         stderr_file=stderr_file)

    @staticmethod
    def _default_format() -> str:
        """Return the default output format for nested Config tests."""
        return 'CSV'

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Get validation plan for use when validating the Config object."""
        _ = stderr_file
        return [self._output_format_step()]

    @staticmethod
    def _output_format_step() -> WholeConfigValidationStep:
        """Return the validation step for the nested output format."""
        return WholeConfigValidationStep(validator=NestedOutputValidator())


# pylint: disable-next=too-few-public-methods
class NestedParentValidator(WholeConfigValidator):
    """Validate that the parent sees normalized nested values."""

    def validate(self, config: Config,
                 stderr_file: TextIO = sys.stderr) -> None:
        """Validate the parent against the nested output format."""
        assert isinstance(config, NestedParentConfig)
        if config.output.output_format == config.expected_format:
            return
        msg = 'Nested output format was not normalized before parent'
        print(msg, file=stderr_file)
        raise InvalidConfiguration(msg)


class NestedParentConfig(Config):
    """Parent configuration with one direct nested Config member."""

    def __init__(self, from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[str] = None,
                 stderr_file: TextIO = sys.stderr) -> None:
        """Construct a parent configuration with one nested child."""
        self.output = NestedOutputConfig(None, None, stderr_file=stderr_file)
        self.expected_format = 'CSV'
        self._nested_configs: NestedConfigs = {
            'output': ConfigNesting(kind=ConfigNestingKind.MEMBER,
                                    config_type=NestedOutputConfig)
        }
        super().__init__(from_json_data_text=from_json_data_text,
                         from_json_filename=from_json_filename,
                         stderr_file=stderr_file)

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Get validation plan for use when validating the Config object."""
        _ = stderr_file
        return [self._parent_step()]

    @staticmethod
    def _parent_step() -> WholeConfigValidationStep:
        """Return the validation step for parent validation order tests."""
        return WholeConfigValidationStep(validator=NestedParentValidator())


class OptionalNestedParentConfig(Config):
    """Parent configuration with an optional nested Config member."""

    def __init__(self, from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[str] = None,
                 stderr_file: TextIO = sys.stderr) -> None:
        """Construct a parent configuration with an optional child."""
        self.required_name = 'default'
        self.optional_output: Optional[NestedOutputConfig] = None
        self._nested_configs: NestedConfigs = {
            'optional_output': ConfigNesting(
                kind=ConfigNestingKind.OPTIONAL_MEMBER,
                config_type=NestedOutputConfig)
        }
        super().__init__(from_json_data_text=from_json_data_text,
                         from_json_filename=from_json_filename,
                         stderr_file=stderr_file)

    def _omit_none_from_json(self) -> list[str]:
        """Return the keys omitted while their value is None."""
        return ['optional_output']

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Get validation plan for use when validating the Config object."""
        _ = stderr_file
        return []


class BadNestedParentConfig(Config):
    """Parent configuration with injected nested Config metadata."""

    def __init__(self, nesting: object,
                 stderr_file: TextIO = sys.stderr) -> None:
        """Construct a parent configuration using the supplied metadata."""
        self.child = NestedOutputConfig(None, None, stderr_file=stderr_file)
        self._nested_configs = cast(NestedConfigs, {'child': nesting})
        super().__init__(from_json_data_text=None, from_json_filename=None,
                         stderr_file=stderr_file)

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Get validation plan for use when validating the Config object."""
        _ = stderr_file
        return []


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


def test_cfg_abc_dump_ok(capsys: CaptureFixture[str]) -> None:
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


def test_omit_none_defaults(capsys: CaptureFixture[str]) -> None:
    """Test that default None members are omitted from JSON."""
    cfg = OmitNoneConfig(stderr_file=sys.stderr)
    json_data = json.loads(cfg.as_json_string(stderr_file=sys.stderr))
    out, err = capsys.readouterr()
    assert '' == out
    assert '' == err
    assert json_data == {'required_name': 'default'}


def test_omit_none_missing(capsys: CaptureFixture[str]) -> None:
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


def test_omit_none_explicit_null(capsys: CaptureFixture[str]) -> None:
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


def test_omit_none_values(capsys: CaptureFixture[str]) -> None:
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


def test_omit_none_requires_normal(capsys: CaptureFixture[str]) -> None:
    """Test that omit-None handling does not hide missing required keys."""
    with pytest.raises(KeyError):
        _ = OmitNoneConfig(from_json_data_text='{"optional_text": "note"}',
                           stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert '' == out
    assert 'No value for required_name in JSON data' in err


def test_omit_none_unknown_member(capsys: CaptureFixture[str]) -> None:
    """Test that omit-None member names must exist."""
    with pytest.raises(KeyError) as exc:
        _ = OmitNoneUnknownMemberConfig(stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert '' == out
    assert '' == err
    assert '_omit_none_from_json() returned unknown key missing_member' in \
        str(exc.value)


def test_omit_none_non_none_default(capsys: CaptureFixture[str]) -> None:
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
def test_omit_none_rejects_bad_hook(capsys: CaptureFixture[str],
                                    omitted_keys: object,
                                    message: str) -> None:
    """Test that omit-None hook return values are type checked."""
    with pytest.raises(TypeError) as exc:
        _ = OmitNoneBadReturnConfig(omitted_keys, stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert '' == out
    assert '' == err
    assert message in str(exc.value)


def test_nested_member_parse_write(capsys: CaptureFixture[str]) -> None:
    """Test parsing and writing one direct nested Config member."""
    cfg = NestedParentConfig(
        from_json_data_text='{"expected_format": "TXT", '
        '"output": {"output_format": "txt"}}',
        stderr_file=sys.stderr)
    json_data = json.loads(cfg.as_json_string(stderr_file=sys.stderr))
    out, err = capsys.readouterr()
    assert '' == out
    assert '' == err
    assert isinstance(cfg.output, NestedOutputConfig)
    assert cfg.output.output_format == 'TXT'
    assert json_data == {
        'expected_format': 'TXT',
        'output': {
            'output_format': 'TXT'
        }
    }


def test_nested_validation_order(capsys: CaptureFixture[str]) -> None:
    """Test that nested validation runs before parent validation."""
    cfg = NestedParentConfig(stderr_file=sys.stderr)
    cfg.output.output_format = 'txt'
    cfg.expected_format = 'TXT'
    cfg.validate(stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert '' == out
    assert '' == err
    assert cfg.output.output_format == 'TXT'


def test_nested_optional_omit_none(capsys: CaptureFixture[str]) -> None:
    """Test omitted, null, and present optional nested Config values."""
    default_cfg = OptionalNestedParentConfig(stderr_file=sys.stderr)
    default_json = json.loads(default_cfg.as_json_string(
        stderr_file=sys.stderr))
    missing_cfg = OptionalNestedParentConfig(
        from_json_data_text='{"required_name": "read"}',
        stderr_file=sys.stderr)
    null_cfg = OptionalNestedParentConfig(
        from_json_data_text='{"required_name": "read", '
        '"optional_output": null}', stderr_file=sys.stderr)
    value_cfg = OptionalNestedParentConfig(
        from_json_data_text='{"required_name": "read", '
        '"optional_output": {"output_format": "txt"}}',
        stderr_file=sys.stderr)
    value_json = json.loads(value_cfg.as_json_string(stderr_file=sys.stderr))
    out, err = capsys.readouterr()
    assert '' == out
    assert '' == err
    assert default_json == {'required_name': 'default'}
    assert missing_cfg.optional_output is None
    assert null_cfg.optional_output is None
    assert isinstance(value_cfg.optional_output, NestedOutputConfig)
    assert value_cfg.optional_output.output_format == 'TXT'
    assert value_json == {
        'optional_output': {
            'output_format': 'TXT'
        },
        'required_name': 'read'
    }


def test_nested_discriminator_kind(capsys: CaptureFixture[str]) -> None:
    """Test that discriminator_key is only accepted for its future kind."""
    nesting = ConfigNesting(kind=ConfigNestingKind.MEMBER,
                            config_type=NestedOutputConfig,
                            discriminator_key='file_format')
    with pytest.raises(ValueError) as exc:
        _ = BadNestedParentConfig(nesting, stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert '' == out
    assert '' == err
    assert 'discriminator_key is reserved for DICT_VALUE_BY_KEY' in \
        str(exc.value)


@pytest.mark.parametrize(
    'jstext, aval, cval, fval',
    [('{ "ab": "a1b2", "cd": "c3d4", "ef": "e5f6" }', 'a1b2', 'c3d4', 'e5f6'),
     ('{ "ab": "donald", "cd": "duck", "ef": "mouse" }', 'donald', 'duck',
      'mouse'), ('{ "ab": "aaa", "cd": "mickey" }', 'aaa', 'mickey', 'ef99'),
     ('{ "ab": "donald", "ef": "duck" }', 'donald', 'cd99', 'duck'),
     ('{ "ab": "duck"}', 'duck', 'cd99', 'ef99')])
def test_cfg_rocf_val_json_ok(capsys: CaptureFixture[str], jstext: str,
                              aval: str, cval: str, fval: str) -> None:
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
def test_cfg_rocf_val_json_nok(capsys: CaptureFixture[str],
                               jstext: str) -> None:
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
def test_rocf_remove_key_dict(capsys: CaptureFixture[str],
                              ind: dict[str, JsonType],
                              outd: dict[str, JsonType], key: str,
                              changed: bool) -> None:
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
def test_rocf_remove_key_list(capsys: CaptureFixture[str], ind: list[JsonType],
                              outd: list[JsonType], key: str,
                              changed: bool) -> None:
    """Test removing one ROCF key from nested lists."""
    data = deepcopy(ind)
    assert remove_json_key_in_list(key=key, json_data=data) == changed
    out, err = capsys.readouterr()
    assert '' == out
    assert '' == err
    assert data == outd


@pytest.mark.parametrize('json_data', [{'a': 'b'}, [{'a': 'b'}]])
def test_rocf_remove_rejects_none(
        capsys: CaptureFixture[str],
        json_data: dict[str, JsonType] | list[JsonType]) -> None:
    """Test that removing a None key fails like invalid ROCF rename rules."""
    with pytest.raises(AssertionError):
        if isinstance(json_data, dict):
            remove_json_key_in_dict(key=cast(Any, None), json_data=json_data)
        else:
            remove_json_key_in_list(key=cast(Any, None), json_data=json_data)
    out, _ = capsys.readouterr()
    assert '' == out


def test_rocf_removed_keys_reported(capsys: CaptureFixture[str]) -> None:
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


def test_rocf_no_removed_keys(capsys: CaptureFixture[str]) -> None:
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
def test_bw_compat_single1(
        capsys: CaptureFixture[str], ind: dict[str, JsonType],
        outd: dict[str, JsonType], ren: RocfKeyRename, errtxt: str) -> None:
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
def test_bw_compat_single2(capsys: CaptureFixture[str],
                           ren: RocfKeyRename) -> None:
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
def test_bwcompat_list1(capsys: CaptureFixture[str], ind: list[JsonType],
                        outd: list[JsonType], ren: RocfKeyRename,
                        errtxt: str) -> None:
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
def test_rename_backward_compatible(capsys: CaptureFixture[str],
                                    ind: dict[str, JsonType],
                                    outd: dict[str, JsonType],
                                    errtxt: str) -> None:
    """Test Config._rename_backward_compatible."""
    data = deepcopy(ind)
    cfg = DummyCfg(stderr_file=sys.stderr)
    rename_json_keys(config=cfg, json_data=data, stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert '' == out
    assert err == errtxt
    assert data == outd
