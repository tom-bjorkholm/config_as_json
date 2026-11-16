#! /usr/local/bin/python3
"""Test kept_value_paths() after parsing with ok_to_use_defaults."""

# Copyright (c) 2026 Tom Björkholm
# MIT License

from copy import deepcopy
import json
import sys
from pathlib import Path
from typing import Optional, TextIO, override
import pytest
from pytest import CaptureFixture
from config_as_json.commontypes import ConfigPath, JsonPath, PathOrStr
from config_as_json.config import Config
from config_as_json.config_errors import ConfigBadJson, ConfigMissingKey, \
    ConfigUnknownKey
from config_as_json.config_nesting import ConfigNesting, ConfigNestingKind, \
    NestedConfigs
from config_as_json.read_old_configuration import ReadOldConfiguration
from config_as_json.validator import InvalidConfiguration, ValidationPlan, \
    WholeConfigValidationStep, WholeConfigValidator
from .test_nested_config import ParticipantSection
_FULL: dict[str, object] = {'title': 't', 'count': 4, 'note': 'n',
                            'extra': 'e',
                            'limits': {'max': 5, 'min': 2,
                                       'inner': {'a': 3, 'b': 4}},
                            'section': {'file_name': 's.csv',
                                        'columns': ['s']}}
_ALL_KEPT: list[JsonPath] = [('title',), ('count',), ('note',), ('limits',),
                             ('section',)]


# pylint: disable-next=too-few-public-methods
class CountValidator(WholeConfigValidator):
    """Reject a negative count."""

    def validate(self, config: Config, stderr_file: TextIO = sys.stderr, *,
                 member_name: Optional[str] = None) -> None:
        """Raise InvalidConfiguration when the count is negative."""
        _ = member_name
        assert isinstance(config, KeptConfig)
        if config.count < 0:
            msg = 'Negative count'
            print(msg, file=stderr_file)
            raise InvalidConfiguration(msg)


class KeptConfig(Config):
    """Configuration with plain, omit-None, dict and nested members."""

    def __init__(self, from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None, *,
                 ok_to_use_defaults: bool = False) -> None:
        """Construct with defaults, and forward ok_to_use_defaults."""
        self.title = 'default'
        self.count = 3
        self.note: Optional[str] = 'note'
        self.extra: Optional[str] = None
        self.limits: dict[str, object] = {'max': 10, 'min': 1,
                                          'inner': {'a': 1, 'b': 2}}
        self.section = ParticipantSection()
        super().__init__(from_json_data_text, from_json_filename,
                         stderr_file=sys.stderr,
                         ok_to_use_defaults=ok_to_use_defaults)

    @override
    def nested_configs(self) -> NestedConfigs:
        """Return the nested section declaration."""
        return {'section': ConfigNesting(kind=ConfigNestingKind.MEMBER,
                                         config_type=ParticipantSection)}

    @override
    def _omit_none_from_json(self) -> list[str]:
        """Return the members omitted while their value is None."""
        return ['note', 'extra']

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Return the count validation."""
        _ = stderr_file
        return [WholeConfigValidationStep(validator=CountValidator())]


class FillTitle(ReadOldConfiguration):
    """Read-old processor that supplies a missing title."""

    @override
    def get_missing_path_values(self) -> dict[ConfigPath, object]:
        """Return the value for a missing title."""
        return {('title',): 'old'}


class RocfKeptConfig(KeptConfig):
    """KeptConfig whose read-old processor supplies a missing title."""

    @override
    def _get_read_old_config(self) -> ReadOldConfiguration:
        """Return the processor that supplies a missing title."""
        return FillTitle()


def _json_text(drop: list[JsonPath]) -> str:
    """Return the JSON text of _FULL without the values at the paths."""
    data = deepcopy(_FULL)
    for path in drop:
        parent: object = data
        for step in path[:-1]:
            assert isinstance(parent, dict)
            parent = parent[step]
        assert isinstance(parent, dict)
        del parent[path[-1]]
    return json.dumps(data)


def _assert_quiet(capsys: CaptureFixture[str]) -> None:
    """Assert that nothing was written to stdout or stderr."""
    out, err = capsys.readouterr()
    assert out == ''
    assert err == ''


@pytest.mark.parametrize('drop, expected', [
    ([], []),
    ([('title',)], [('title',)]),
    ([('title',), ('count',)], [('title',), ('count',)]),
    ([('note',)], [('note',)]),
    ([('extra',)], []),
    ([('section',)], [('section',)]),
    ([('limits', 'min')], [('limits', 'min')]),
    ([('limits', 'inner', 'a')], [('limits', 'inner', 'a')]),
    ([('limits', 'inner')], [('limits', 'inner')]),
    ([('limits',)], [('limits',)]),
    ([('extra',)] + _ALL_KEPT, _ALL_KEPT)])
def test_kept_paths(capsys: CaptureFixture[str], drop: list[JsonPath],
                    expected: list[JsonPath]) -> None:
    """Test the kept paths of absent members and filled dict keys.

    An absent omit-None member is kept only when its value is not None.
    """
    cfg = KeptConfig()
    cfg.parse_json(_json_text(drop), ok_to_use_defaults=True)
    assert sorted(cfg.kept_value_paths()) == sorted(expected)
    _assert_quiet(capsys)


@pytest.mark.parametrize('drop', [[], [('note',), ('extra',)]])
def test_strict_kept_empty(capsys: CaptureFixture[str],
                           drop: list[JsonPath]) -> None:
    """Test that a strict parse clears the paths of a previous parse."""
    cfg = KeptConfig()
    cfg.parse_json(_json_text([('title',)]), ok_to_use_defaults=True)
    assert cfg.kept_value_paths() == [('title',)]
    cfg.parse_json(_json_text(drop))
    assert not cfg.kept_value_paths()
    _assert_quiet(capsys)


@pytest.mark.parametrize('ok_to_use_defaults', [False, True])
def test_no_json_kept_empty(capsys: CaptureFixture[str],
                            ok_to_use_defaults: bool) -> None:
    """Test that construction without JSON data keeps nothing."""
    cfg = KeptConfig(ok_to_use_defaults=ok_to_use_defaults)
    assert not cfg.kept_value_paths()
    assert cfg.title == 'default'
    _assert_quiet(capsys)


def test_second_parse(capsys: CaptureFixture[str]) -> None:
    """Test that a second parse reports only what its own JSON lacked.

    The omit-None member ``extra`` is None by default, but holds the value
    of the first parse when the second parse keeps it.
    """
    cfg = KeptConfig()
    cfg.parse_json(_json_text([('title',)]), ok_to_use_defaults=True)
    cfg.parse_json(_json_text([('count',), ('extra',)]),
                   ok_to_use_defaults=True)
    assert sorted(cfg.kept_value_paths()) == [('count',), ('extra',)]
    assert (cfg.title, cfg.count, cfg.extra) == ('t', 4, 'e')
    _assert_quiet(capsys)


def test_new_list_each_call(capsys: CaptureFixture[str]) -> None:
    """Test that changing a returned list does not change the next one."""
    cfg = KeptConfig()
    cfg.parse_json(_json_text([('title',)]), ok_to_use_defaults=True)
    first = cfg.kept_value_paths()
    first.append(('count',))
    assert cfg.kept_value_paths() == [('title',)]
    assert cfg.kept_value_paths() is not cfg.kept_value_paths()
    _assert_quiet(capsys)


@pytest.mark.parametrize('text, error, expected, message', [
    ('{"unknown": 1}', ConfigUnknownKey, [], 'Unexpected parameter unknown'),
    ('not json', ConfigBadJson, [], 'Expecting value'),
    ('{"count": -1}', InvalidConfiguration,
     [('title',), ('note',), ('extra',), ('limits',), ('section',)],
     'Negative count')])
def test_failed_parse(capsys: CaptureFixture[str], text: str,
                      error: type[Exception], expected: list[JsonPath],
                      message: str) -> None:
    """Test the kept paths after a parse that fails.

    The paths are cleared when the parse starts, and set before validation.
    ``extra`` is kept since the first parse gave it a value.
    """
    cfg = KeptConfig()
    cfg.parse_json(_json_text([('title',)]), ok_to_use_defaults=True)
    with pytest.raises(error):
        cfg.parse_json(text, ok_to_use_defaults=True, stderr_file=sys.stderr)
    assert sorted(cfg.kept_value_paths()) == sorted(expected)
    out, err = capsys.readouterr()
    assert out == ''
    assert message in err


def test_rocf_value_not_kept(capsys: CaptureFixture[str]) -> None:
    """Test that a value supplied by the read-old processor is not kept."""
    cfg = RocfKeptConfig()
    cfg.parse_json(_json_text([('title',), ('count',)]),
                   ok_to_use_defaults=True)
    assert cfg.title == 'old'
    assert cfg.kept_value_paths() == [('count',)]
    _assert_quiet(capsys)


@pytest.mark.parametrize('use_file', [False, True])
def test_constructor_keyword(capsys: CaptureFixture[str], tmp_path: Path,
                             use_file: bool) -> None:
    """Test ok_to_use_defaults on the constructor with text and a file."""
    text = _json_text([('title',), ('limits', 'min')])
    if use_file:
        file_name = tmp_path / 'kept.cfg'
        file_name.write_text(text, encoding='UTF-8')
        cfg = KeptConfig(None, file_name, ok_to_use_defaults=True)
    else:
        cfg = KeptConfig(text, None, ok_to_use_defaults=True)
    assert cfg.title == 'default'
    assert cfg.limits == {'max': 5, 'min': 1, 'inner': {'a': 3, 'b': 4}}
    assert sorted(cfg.kept_value_paths()) == [('limits', 'min'), ('title',)]
    _assert_quiet(capsys)


def test_constructor_strict(capsys: CaptureFixture[str]) -> None:
    """Test that the constructor parses strictly by default."""
    with pytest.raises(ConfigMissingKey) as exc_info:
        KeptConfig(_json_text([('title',)]))
    assert exc_info.value.json_path == ('title',)
    out, err = capsys.readouterr()
    assert out == ''
    assert 'No value for title in JSON data' in err
