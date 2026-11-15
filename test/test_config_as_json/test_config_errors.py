#! /usr/local/bin/python3
"""Test the specific exceptions for problems in configuration JSON data."""

# Copyright (c) 2026 Tom Björkholm
# MIT License

from enum import Enum
from io import StringIO
import json
import sys
from typing import Optional, TextIO, override
import pytest
from config_as_json import Config, ConfigBadJson, ConfigConversionFailed, \
    ConfigKeysNotStrings, ConfigMissingKey, ConfigMustBeJson, \
    ConfigMustBeList, ConfigNesting, ConfigNestingKind, ConfigNotDict, \
    ConfigParseError, ConfigRootNotDict, ConfigUnexpectedDict, \
    ConfigUnknownKey, ConfigWrongShape, JsonPath, JsonType, NestedConfigs, \
    ParseConverter, PathOrStr, ValidationPlan
import config_as_json.config


class Color(Enum):
    """Enum read from JSON by a parse converter."""

    RED = 1
    BLUE = 2


class NoRulesConfig(Config):
    """Configuration base without validation steps."""

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Return no validation steps."""
        _ = stderr_file
        return []


class SubSection(NoRulesConfig):
    """Innermost nested configuration."""

    def __init__(self, from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 stderr_file: TextIO = sys.stderr,
                 member_name: Optional[str] = None) -> None:
        """Construct the innermost nested configuration."""
        self.level = 1
        super().__init__(from_json_data_text=from_json_data_text,
                         from_json_filename=from_json_filename,
                         stderr_file=stderr_file, member_name=member_name)


class LeafSection(NoRulesConfig):
    """Nested configuration with a converter, a dict and a nested member."""

    def __init__(self, from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 stderr_file: TextIO = sys.stderr,
                 member_name: Optional[str] = None) -> None:
        """Construct the nested configuration."""
        self.port = 1
        self.color = Color.RED
        self.limits = {'cpu': 1}
        self.sub = SubSection(stderr_file=stderr_file)
        super().__init__(from_json_data_text=from_json_data_text,
                         from_json_filename=from_json_filename,
                         stderr_file=stderr_file, member_name=member_name)

    @override
    def nested_configs(self) -> NestedConfigs:
        """Return nested Config declarations."""
        return {'sub': ConfigNesting(kind=ConfigNestingKind.MEMBER,
                                     config_type=SubSection)}

    @override
    def parse_converters(self) -> Optional[dict[str, ParseConverter]]:
        """Return the converter reading ``color`` as a Color."""
        return {'color': self.get_converter_dict(Color)}


class TopConfig(NoRulesConfig):
    """Top level configuration with every kind of nesting under test."""

    def __init__(self, from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 stderr_file: TextIO = sys.stderr,
                 member_name: Optional[str] = None) -> None:
        """Construct the top level configuration."""
        self.name = 'x'
        self.settings = {'k': 1, 'deep': {'z': 1}}
        self.leaf = LeafSection(stderr_file=stderr_file)
        self.leaves: list[LeafSection] = []
        self.by_name: dict[str, LeafSection] = {}
        super().__init__(from_json_data_text=from_json_data_text,
                         from_json_filename=from_json_filename,
                         stderr_file=stderr_file, member_name=member_name)

    @override
    def nested_configs(self) -> NestedConfigs:
        """Return nested Config declarations."""
        member = ConfigNestingKind.MEMBER
        return {
            'leaf': ConfigNesting(kind=member, config_type=LeafSection),
            'leaves': ConfigNesting(kind=ConfigNestingKind.LIST_ELEMENT,
                                    config_type=LeafSection),
            'by_name': ConfigNesting(kind=ConfigNestingKind.DICT_VALUE,
                                     config_type=LeafSection)}


class _Missing:  # pylint: disable=too-few-public-methods
    """Marker for a key that a test case removes from the data."""


MISSING = _Missing()
"""Value of a test case that removes the key instead of setting it."""


def _leaf_data(color: str = 'RED') -> dict[str, JsonType]:
    """Return valid JSON data for one LeafSection."""
    return {'port': 1, 'color': color, 'limits': {'cpu': 1},
            'sub': {'level': 1}}


def _top_data() -> dict[str, JsonType]:
    """Return valid JSON data for TopConfig."""
    return {'name': 'x', 'settings': {'k': 1, 'deep': {'z': 1}},
            'leaf': _leaf_data(), 'leaves': [_leaf_data(), _leaf_data()],
            'by_name': {'a.b': _leaf_data()}}


def _child(node: JsonType, step: str | int) -> JsonType:
    """Return the child of a dict or a list at one path step."""
    if isinstance(step, int):
        assert isinstance(node, list)
        return node[step]
    assert isinstance(node, dict)
    return node[step]


def _set_child(node: JsonType, step: str | int,
               value: JsonType | _Missing) -> None:
    """Set, or with MISSING remove, the child at one path step."""
    if isinstance(step, int):
        assert isinstance(node, list)
        assert not isinstance(value, _Missing)
        node[step] = value
        return
    assert isinstance(node, dict)
    if isinstance(value, _Missing):
        del node[step]
    else:
        node[step] = value


def _changed_text(path: JsonPath, value: JsonType | _Missing) -> str:
    """Return TopConfig JSON text with the value at ``path`` changed."""
    data: JsonType = _top_data()
    parent = data
    for step in path[:-1]:
        parent = _child(parent, step)
    _set_child(parent, path[-1], value)
    return json.dumps(data)


def test_valid_data_parses() -> None:
    """Test that the unchanged test data is valid."""
    config = TopConfig(from_json_data_text=json.dumps(_top_data()))
    assert config.by_name['a.b'].sub.level == 1


# Each case changes the value at the path, and the exception is expected to
# report that same path as json_path.
@pytest.mark.parametrize('path, value, error_type, member_name', [
    (('name',), MISSING, ConfigMissingKey, 'name'),
    (('extra',), 1, ConfigUnknownKey, 'extra'),
    (('settings', 'k'), MISSING, ConfigMissingKey, 'settings[k]'),
    (('settings', 'deep', 'q'), 1, ConfigUnknownKey, 'settings[deep][q]'),
    (('settings',), 5, ConfigNotDict, 'settings'),
    (('name',), {}, ConfigUnexpectedDict, 'name'),
    (('leaves',), {}, ConfigMustBeList, 'leaves'),
    (('leaves', 0), 3, ConfigNotDict, 'leaves[0]'),
    (('leaf',), 3, ConfigNotDict, 'leaf'),
    (('by_name',), [], ConfigNotDict, 'by_name'),
    (('leaves', 1, 'port'), MISSING, ConfigMissingKey, 'leaves[1].port'),
    (('by_name', 'a.b', 'x'), 1, ConfigUnknownKey, 'by_name[a.b].x'),
    (('leaf', 'limits'), 2, ConfigNotDict, 'leaf.limits'),
    (('leaf', 'sub'), [], ConfigNotDict, 'leaf.sub'),
    (('leaves', 0, 'sub', 'level'), MISSING, ConfigMissingKey,
     'leaves[0].sub.level')])
def test_key_error_location(path: JsonPath, value: JsonType | _Missing,
                            error_type: type[ConfigParseError],
                            member_name: str) -> None:
    """Test type, legacy base, location and text of KeyError problems."""
    stderr_file = StringIO()
    with pytest.raises(error_type) as exc:
        TopConfig(from_json_data_text=_changed_text(path, value),
                  stderr_file=stderr_file)
    assert isinstance(exc.value, KeyError)
    assert exc.value.member_name == member_name
    assert exc.value.json_path == path
    assert str(exc.value) + '\n' == stderr_file.getvalue()


@pytest.mark.parametrize('path, value, attribute', [
    (('leaves', 1, 'port'), MISSING, 'missing_key'),
    (('by_name', 'a.b', 'x'), 1, 'unknown_key')])
def test_local_key_member(path: JsonPath, value: JsonType | _Missing,
                          attribute: str) -> None:
    """Test that missing and unknown keys name the local key."""
    with pytest.raises(KeyError) as exc:
        TopConfig(from_json_data_text=_changed_text(path, value),
                  stderr_file=StringIO())
    assert getattr(exc.value, attribute) == path[-1]


def _leaves_text() -> str:
    """Return TopConfig JSON text with a bad color in ``leaves[1]``."""
    data = _top_data()
    data['leaves'] = [_leaf_data(), _leaf_data('PURPLE')]
    return json.dumps(data)


@pytest.mark.parametrize('config_type, text, member_name, json_path', [
    (LeafSection, json.dumps(_leaf_data('PURPLE')), None, ()),
    (TopConfig, _leaves_text(), 'leaves[1]', ('leaves', 1))])
def test_conversion_failed(config_type: type[Config], text: str,
                           member_name: Optional[str],
                           json_path: JsonPath) -> None:
    """Test that a refusing converter names its key and Config object."""
    with pytest.raises(ConfigConversionFailed) as exc:
        config_type(from_json_data_text=text, from_json_filename=None,
                    stderr_file=StringIO())
    assert isinstance(exc.value, ConfigBadJson)
    assert exc.value.converted_key == 'color'
    assert exc.value.member_name == member_name
    assert exc.value.json_path == json_path
    assert isinstance(exc.value.__cause__, KeyError)


@pytest.mark.parametrize('text, error_type, lineno, colno', [
    ('{\n "name": }', ConfigMustBeJson, 2, 10),
    ('[1]', ConfigRootNotDict, 1, 1)])
def test_bad_json_text(text: str, error_type: type[ConfigBadJson], lineno: int,
                       colno: int) -> None:
    """Test problems with the JSON text as a whole."""
    stderr_file = StringIO()
    with pytest.raises(error_type) as exc:
        TopConfig(from_json_data_text=text, stderr_file=stderr_file)
    assert not isinstance(exc.value, KeyError)
    assert exc.value.member_name is None
    assert exc.value.json_path == ()
    assert (exc.value.lineno, exc.value.colno) == (lineno, colno)
    assert str(exc.value).startswith(stderr_file.getvalue().rstrip('\n'))


@pytest.mark.parametrize('error_type, legacy_type', [
    (ConfigMissingKey, KeyError),
    (ConfigUnknownKey, KeyError),
    (ConfigWrongShape, KeyError),
    (ConfigMustBeList, ConfigWrongShape),
    (ConfigNotDict, ConfigWrongShape),
    (ConfigUnexpectedDict, ConfigWrongShape),
    (ConfigKeysNotStrings, ConfigWrongShape),
    (ConfigBadJson, json.JSONDecodeError),
    (ConfigMustBeJson, ConfigBadJson),
    (ConfigRootNotDict, ConfigBadJson),
    (ConfigConversionFailed, ConfigBadJson)])
def test_hierarchy(error_type: type[ConfigParseError],
                   legacy_type: type[Exception]) -> None:
    """Test that each type derives from its legacy type and the base."""
    assert issubclass(error_type, legacy_type)
    assert issubclass(error_type, ConfigParseError)


def test_bad_json_legacy_use() -> None:
    """Test that ConfigBadJson is constructed and imported as before."""
    exc = config_as_json.config.ConfigBadJson(msg='Oops', doc='ab', pos=1)
    assert str(exc) == 'Oops: line 1 column 2 (char 1)'
    assert exc.member_name is None
    assert not exc.json_path


def test_check_dict_parse_path() -> None:
    """Test the default json_path of a direct check_dict_parse call."""
    with pytest.raises(ConfigNotDict) as exc:
        Config.check_dict_parse({'a': 1}, 5, 'limits', False, [], StringIO())
    assert exc.value.json_path == ('limits',)
    assert exc.value.member_name == 'limits'
