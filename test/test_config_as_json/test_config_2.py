#! /usr/local/bin/python3
"""Test the Config class (part 2 of tests)."""

# Copyright (c) 2024-2026 Tom Björkholm
# MIT License

from enum import Enum, auto
from io import StringIO
import json
import sys
import warnings
from typing import Optional, cast, override, TextIO
import pytest
from pytest import CaptureFixture
from config_as_json import ReadOldConfiguration, RocfKeyRename
from config_as_json.config import Config, ParseConverter
from config_as_json.config_auto_change_hook import ConfigAutoChangeHook
from config_as_json.config_nesting import ConfigNesting, ConfigNestingKind, \
    NestedConfigs
from config_as_json.commontypes import ConfigPath, JsonType
from config_as_json.validator import InvalidConfiguration, ValidationPlan, \
    WholeConfigValidationStep, WholeConfigValidator


class AbcReadOldConfig(ReadOldConfiguration):
    """Provide compatibility defaults for ``AbcConfig``."""

    def get_missing_path_values(self) -> dict[ConfigPath, object]:
        """Return default values for optional parameters."""
        return {('cd',): 'cd99', ('ef',): 'ef99'}


class AbcConfig(Config):
    """Class to test defualt values."""

    def __init__(self, from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[str] = None,
                 stderr_file: TextIO = sys.stderr,
                 member_name: Optional[str] = None) -> None:
        """Construct test config object."""
        self.ab = 'a1b2'
        self.cd = 'c3d4'
        self.ef = 'e5f6'
        super().__init__(from_json_data_text=from_json_data_text,
                         from_json_filename=from_json_filename,
                         stderr_file=stderr_file, member_name=member_name)

    def _get_read_old_config(self) -> ReadOldConfiguration:
        """Return the object that normalizes old test files."""
        return AbcReadOldConfig()

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Get validation plan for use when validating the Config object."""
        return []


class HookReadOldConfig(ReadOldConfiguration):
    """Read-old processor returned by hook compatibility tests."""

    def get_missing_path_values(self) -> dict[ConfigPath, object]:
        """Return a missing value that proves the hook was used."""
        return {('name',): 'legacy'}


# The small one-member test configuration below is boilerplate that other
# test modules write the same way for their own purposes.
# pylint: disable=duplicate-code
class HookConfigBase(Config):
    """Base configuration for read-old hook compatibility tests."""

    def __init__(self, from_json_data_text: Optional[str] = None,
                 stderr_file: TextIO = sys.stderr,
                 member_name: Optional[str] = None) -> None:
        """Construct a simple configuration with one current member."""
        self.name = 'current'
        super().__init__(from_json_data_text=from_json_data_text,
                         from_json_filename=None, stderr_file=stderr_file,
                         member_name=member_name)

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Get validation plan for use when validating the Config object."""
        _ = stderr_file
        return []


# pylint: enable=duplicate-code
class NewHookConfig(HookConfigBase):
    """Config using the current read-old hook name."""

    @override
    def _get_read_old_config(self) -> ReadOldConfiguration:
        """Return the read-old processor through the current hook."""
        return HookReadOldConfig()


class LegacyHookConfig(HookConfigBase):
    """Config using the deprecated read-old hook name."""

    @override
    def _get_read_old_configuration(self) -> ReadOldConfiguration:
        """Return the read-old processor through the deprecated hook."""
        return HookReadOldConfig()


class ConflictingHookConfig(LegacyHookConfig):
    """Config overriding both read-old hook names."""

    @override
    def _get_read_old_config(self) -> ReadOldConfiguration:
        """Return the read-old processor through the current hook."""
        return HookReadOldConfig()


class OptionalOutputMode(Enum):
    """Output modes used by omit-None tests."""

    FAST = auto()
    CAREFUL = auto()


class OmitNoneConfig(Config):
    """Class to test omit-when-None configuration values."""

    def __init__(self, from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[str] = None,
                 stderr_file: TextIO = sys.stderr,
                 member_name: Optional[str] = None) -> None:
        """Construct a config object with true optional members."""
        self.required_name = 'default'
        self.optional_text: Optional[str] = None
        self.optional_mode: Optional[OptionalOutputMode] = None
        super().__init__(from_json_data_text=from_json_data_text,
                         from_json_filename=from_json_filename,
                         stderr_file=stderr_file, member_name=member_name)

    @override
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

    @override
    def _omit_none_from_json(self) -> list[str]:
        """Return an invalid omit-None member name."""
        return ['missing_member']


class OmitNoneNonNoneDefaultConfig(Config):
    """Class with omit-None members and visible teaching defaults."""

    def __init__(self, from_json_data_text: Optional[str] = None,
                 stderr_file: TextIO = sys.stderr,
                 member_name: Optional[str] = None) -> None:
        """Construct a config object with omit-None teaching defaults."""
        self.required_name = 'default'
        self.optional_text: Optional[str] = 'visible'
        self.optional_mode: Optional[OptionalOutputMode] = \
            OptionalOutputMode.CAREFUL
        super().__init__(from_json_data_text=from_json_data_text,
                         from_json_filename=None, stderr_file=stderr_file,
                         member_name=member_name)

    @override
    def _omit_none_from_json(self) -> list[str]:
        """Return keys whose missing strict-read value is None."""
        return ['optional_text', 'optional_mode']

    def parse_converters(self) -> dict[str, ParseConverter]:
        """Return converters for enum-valued test members."""
        return {'optional_mode': self.get_converter_dict(OptionalOutputMode)}

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Get validation plan for use when validating the Config object."""
        _ = stderr_file
        return []


class OmitNoneBadReturnConfig(OmitNoneConfig):
    """Class with an invalid omit-None hook return value."""

    def __init__(self, omitted_keys: object, stderr_file: TextIO = sys.stderr,
                 member_name: Optional[str] = None) -> None:
        """Construct an invalid config object for omit-None hook tests."""
        self._omitted_keys = omitted_keys
        super().__init__(stderr_file=stderr_file, member_name=member_name)

    @override
    def _omit_none_from_json(self) -> list[str]:
        """Return the configured invalid omit-None hook value."""
        return cast(list[str], self._omitted_keys)


# pylint: disable-next=too-few-public-methods
class NestedOutputValidator(WholeConfigValidator):
    """Normalize the output format in nested Config tests."""

    def validate(self, config: Config, stderr_file: TextIO = sys.stderr, *,
                 member_name: Optional[str] = None) -> None:
        """Validate and normalize one nested output configuration."""
        _ = member_name
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
                 stderr_file: TextIO = sys.stderr,
                 member_name: Optional[str] = None) -> None:
        """Construct the nested output configuration."""
        self.output_format = self._default_format()
        super().__init__(from_json_data_text=from_json_data_text,
                         from_json_filename=from_json_filename,
                         stderr_file=stderr_file, member_name=member_name)

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

    def validate(self, config: Config, stderr_file: TextIO = sys.stderr, *,
                 member_name: Optional[str] = None) -> None:
        """Validate the parent against the nested output format."""
        _ = member_name
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
                 stderr_file: TextIO = sys.stderr,
                 member_name: Optional[str] = None) -> None:
        """Construct a parent configuration with one nested child."""
        self.output = NestedOutputConfig(None, None, stderr_file=stderr_file)
        self.expected_format = 'CSV'
        super().__init__(from_json_data_text=from_json_data_text,
                         from_json_filename=from_json_filename,
                         stderr_file=stderr_file, member_name=member_name)

    @override
    def nested_configs(self) -> NestedConfigs:
        """Return nested Config declarations."""
        return {
            'output': ConfigNesting(kind=ConfigNestingKind.MEMBER,
                                    config_type=NestedOutputConfig)
        }

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
                 stderr_file: TextIO = sys.stderr,
                 member_name: Optional[str] = None) -> None:
        """Construct a parent configuration with an optional child."""
        self.required_name = 'default'
        self.optional_output: Optional[NestedOutputConfig] = None
        super().__init__(from_json_data_text=from_json_data_text,
                         from_json_filename=from_json_filename,
                         stderr_file=stderr_file, member_name=member_name)

    @override
    def nested_configs(self) -> NestedConfigs:
        """Return nested Config declarations."""
        return {
            'optional_output': ConfigNesting(
                kind=ConfigNestingKind.OPTIONAL_MEMBER,
                config_type=NestedOutputConfig)
        }

    @override
    def _omit_none_from_json(self) -> list[str]:
        """Return the keys omitted while their value is None."""
        return ['optional_output']

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Get validation plan for use when validating the Config object."""
        _ = stderr_file
        return []


class BadNestedParentConfig(Config):
    """Parent configuration with injected nested Config metadata."""

    def __init__(self, nesting: object, stderr_file: TextIO = sys.stderr,
                 member_name: Optional[str] = None) -> None:
        """Construct a parent configuration using the supplied metadata."""
        self.child = NestedOutputConfig(None, None, stderr_file=stderr_file)
        self._nesting = nesting
        super().__init__(from_json_data_text=None, from_json_filename=None,
                         stderr_file=stderr_file, member_name=member_name)

    @override
    def nested_configs(self) -> NestedConfigs:
        """Return injected nested Config declarations."""
        return cast(NestedConfigs, {'child': self._nesting})

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


class RocfRemoveReadOldConfig(ReadOldConfiguration):
    """Normalize old files used by removed-key parser tests."""

    def get_keys_to_prune(self) -> list[str]:
        """Return old keys that should be dropped from JSON input."""
        return ['obsolete_top', 'obsolete_nested']

    def get_missing_path_values(self) -> dict[ConfigPath, object]:
        """Return current values for paths missing from old files."""
        return {('version',): 2}

    def get_json_key_renames(self) -> list[RocfKeyRename]:
        """Return old key names that should be mapped to current names."""
        return [RocfKeyRename(old='title', new='name')]


class RocfRemoveConfig(Config):
    """Class to test removed old JSON keys during ROCF parsing."""

    def __init__(self, from_json_data_text: Optional[str] = None,
                 auto_ch_hook: Optional[ConfigAutoChangeHook] = None,
                 stderr_file: TextIO = sys.stderr,
                 member_name: Optional[str] = None) -> None:
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
                         stderr_file=stderr_file, member_name=member_name)

    def _get_read_old_config(self) -> ReadOldConfiguration:
        """Return the object that normalizes old test files."""
        return RocfRemoveReadOldConfig()

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Get validation plan for use when validating the Config object."""
        _ = stderr_file
        return []


def test_cfg_abc_dump_ok(capsys: CaptureFixture[str]) -> None:
    """Test dump of default constructed AbcConfig."""
    abc = AbcConfig(stderr_file=sys.stderr)
    jstext = abc.as_json_string(stderr_file=sys.stderr, member_name=None)
    out, err = capsys.readouterr()
    assert '' == out
    assert '' == err
    jstext = jstext.replace('\n', ' ')
    for _ in range(10):
        jstext = jstext.replace('  ', ' ')
    assert jstext == '{ "ab": "a1b2", "cd": "c3d4", "ef": "e5f6" }'


def test_new_rocf_hook_no_warn() -> None:
    """Current read-old hook name works without deprecation warnings."""
    stderr = StringIO()
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        cfg = NewHookConfig(from_json_data_text='{}', stderr_file=stderr)
    assert cfg.name == 'legacy'
    assert not caught
    assert stderr.getvalue() == ''


def test_depr_rocf_hook_warns() -> None:
    """Deprecated read-old hook override warns and still works."""
    stderr = StringIO()
    with pytest.warns(DeprecationWarning, match='_get_read_old_config'):
        cfg = LegacyHookConfig(from_json_data_text='{}', stderr_file=stderr)
    assert cfg.name == 'legacy'
    assert stderr.getvalue() == ''


def test_depr_rocf_direct() -> None:
    """Deprecated read-old hook warns when called directly."""
    cfg = NewHookConfig(stderr_file=StringIO())
    with pytest.warns(DeprecationWarning, match='_get_read_old_config'):
        # pylint: disable-next=protected-access
        rocf = cfg._get_read_old_configuration()
    assert isinstance(rocf, HookReadOldConfig)


def test_rocf_hook_conflict() -> None:
    """Overriding both read-old hook names is invalid."""
    with pytest.raises(TypeError) as exc:
        _ = ConflictingHookConfig(from_json_data_text='{}',
                                  stderr_file=StringIO())
    assert '_get_read_old_configuration()' in str(exc.value)
    assert '_get_read_old_config()' in str(exc.value)


def test_omit_none_defaults(capsys: CaptureFixture[str]) -> None:
    """Test that default None members are omitted from JSON."""
    cfg = OmitNoneConfig(stderr_file=sys.stderr)
    json_data = json.loads(cfg.as_json_string(stderr_file=sys.stderr,
                                              member_name=None))
    out, err = capsys.readouterr()
    assert '' == out
    assert '' == err
    assert json_data == {'required_name': 'default'}


def test_omit_none_missing(capsys: CaptureFixture[str]) -> None:
    """Test that missing omit-None members remain None."""
    cfg = OmitNoneConfig(from_json_data_text='{"required_name": "read"}',
                         stderr_file=sys.stderr)
    json_data = json.loads(cfg.as_json_string(stderr_file=sys.stderr,
                                              member_name=None))
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
    json_data = json.loads(cfg.as_json_string(stderr_file=sys.stderr,
                                              member_name=None))
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
    json_data = json.loads(cfg.as_json_string(stderr_file=sys.stderr,
                                              member_name=None))
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


def test_omit_none_visible_defaults(capsys: CaptureFixture[str]) -> None:
    """Test that omit-None members may use visible defaults."""
    cfg = OmitNoneNonNoneDefaultConfig(stderr_file=sys.stderr)
    json_data = json.loads(cfg.as_json_string(stderr_file=sys.stderr,
                                              member_name=None))
    out, err = capsys.readouterr()
    assert '' == out
    assert '' == err
    assert cfg.optional_text == 'visible'
    assert cfg.optional_mode == OptionalOutputMode.CAREFUL
    assert json_data == {
        'optional_mode': 'CAREFUL',
        'optional_text': 'visible',
        'required_name': 'default'
    }


def test_omit_none_omits_later_none(capsys: CaptureFixture[str]) -> None:
    """Test that listed non-default members are omitted only when None."""
    cfg = OmitNoneNonNoneDefaultConfig(stderr_file=sys.stderr)
    cfg.optional_text = None
    cfg.optional_mode = None
    json_data = json.loads(cfg.as_json_string(stderr_file=sys.stderr,
                                              member_name=None))
    out, err = capsys.readouterr()
    assert '' == out
    assert '' == err
    assert json_data == {'required_name': 'default'}


def test_omit_none_missing_is_none(capsys: CaptureFixture[str]) -> None:
    """Test that missing strict-read omit-None keys become None."""
    cfg = OmitNoneNonNoneDefaultConfig(
        from_json_data_text='{"required_name": "read"}',
        stderr_file=sys.stderr)
    json_data = json.loads(cfg.as_json_string(stderr_file=sys.stderr,
                                              member_name=None))
    out, err = capsys.readouterr()
    assert '' == out
    assert '' == err
    assert cfg.required_name == 'read'
    assert cfg.optional_text is None
    assert cfg.optional_mode is None
    assert json_data == {'required_name': 'read'}


def test_omit_none_defaults_allowed(capsys: CaptureFixture[str]) -> None:
    """Test that ok_to_use_defaults preserves omitted listed defaults."""
    cfg = OmitNoneNonNoneDefaultConfig(stderr_file=sys.stderr)
    cfg.parse_json('{"required_name": "read"}', ok_to_use_defaults=True,
                   stderr_file=sys.stderr, member_name=None)
    json_data = json.loads(cfg.as_json_string(stderr_file=sys.stderr,
                                              member_name=None))
    out, err = capsys.readouterr()
    assert '' == out
    assert '' == err
    assert cfg.required_name == 'read'
    assert cfg.optional_text == 'visible'
    assert cfg.optional_mode == OptionalOutputMode.CAREFUL
    assert json_data == {
        'optional_mode': 'CAREFUL',
        'optional_text': 'visible',
        'required_name': 'read'
    }


@pytest.mark.parametrize('ok_to_use_defaults', [False, True])
def test_omit_none_null_is_none(capsys: CaptureFixture[str],
                                ok_to_use_defaults: bool) -> None:
    """Test that explicit null overrides non-None defaults."""
    cfg = OmitNoneNonNoneDefaultConfig(stderr_file=sys.stderr)
    cfg.parse_json('{"required_name": "read", "optional_text": null, '
                   '"optional_mode": null}',
                   ok_to_use_defaults=ok_to_use_defaults,
                   stderr_file=sys.stderr, member_name=None)
    json_data = json.loads(cfg.as_json_string(stderr_file=sys.stderr,
                                              member_name=None))
    out, err = capsys.readouterr()
    assert '' == out
    assert '' == err
    assert cfg.optional_text is None
    assert cfg.optional_mode is None
    assert json_data == {'required_name': 'read'}


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
    json_data = json.loads(cfg.as_json_string(stderr_file=sys.stderr,
                                              member_name=None))
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
    cfg.validate(stderr_file=sys.stderr, member_name=None)
    out, err = capsys.readouterr()
    assert '' == out
    assert '' == err
    assert cfg.output.output_format == 'TXT'


def test_nested_optional_omit_none(capsys: CaptureFixture[str]) -> None:
    """Test omitted, null, and present optional nested Config values."""
    default_cfg = OptionalNestedParentConfig(stderr_file=sys.stderr)
    default_json = json.loads(default_cfg.as_json_string(
        stderr_file=sys.stderr, member_name=None))
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
    value_json = json.loads(value_cfg.as_json_string(stderr_file=sys.stderr,
                                                     member_name=None))
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


def _as_list(value: object) -> list[object]:
    """Return one bare configured value wrapped in a list.

    A value that already is a list never reaches this function, because
    ``ParseConverter.result_type`` says what needs no conversion.
    """
    assert not isinstance(value, list)
    return [value]


class TagListConfig(Config):
    """Class with a list member that also accepts one bare value."""

    def __init__(self, from_json_data_text: Optional[str] = None,
                 stderr_file: TextIO = sys.stderr,
                 member_name: Optional[str] = None) -> None:
        """Construct a config object with an optional list member."""
        self.tags: Optional[list[str]] = None
        super().__init__(from_json_data_text=from_json_data_text,
                         from_json_filename=None, stderr_file=stderr_file,
                         member_name=member_name)

    @override
    def _omit_none_from_json(self) -> list[str]:
        """Return the key omitted while its value is None."""
        return ['tags']

    def parse_converters(self) -> dict[str, ParseConverter]:
        """Return the converter widening one bare value into a list."""
        return {'tags': ParseConverter(result_type=list, func=_as_list,
                                       args={})}

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Get validation plan for use when validating the Config object."""
        _ = stderr_file
        return []


@pytest.mark.parametrize('jstext, expected', [
    ('{"tags": "one"}', ['one']),
    ('{"tags": ["one", "two"]}', ['one', 'two']),
    ('{"tags": []}', []),
    ('{"tags": null}', None),
    ('{}', None)])
def test_parse_conv_typed(jstext: str, expected: Optional[list[str]],
                          capsys: CaptureFixture[str]) -> None:
    """Test that a parsed value of the result type is not converted."""
    cfg = TagListConfig(from_json_data_text=jstext, stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert cfg.tags == expected
    assert '' == out
    assert '' == err
