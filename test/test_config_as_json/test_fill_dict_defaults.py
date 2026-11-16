#! /usr/local/bin/python3
"""Test that ok_to_use_defaults fills the missing keys of checked dicts."""

# Copyright (c) 2026 Tom Björkholm
# MIT License

import json
import sys
from typing import TextIO
import pytest
from pytest import CaptureFixture
from config_as_json.commontypes import JsonPath
from config_as_json.config import Config
from config_as_json.config_errors import ConfigMissingKey
from config_as_json.validator import ValidationPlan
from config_as_json._config_key_check import fill_missing_keys
_UNCHECKED = ['free', 'loose']
# Assigned by reference in LimitsConfig, as a module-level default may be.
_DEFAULT_LIMITS: dict[str, object] = {'max': 10, 'min': 1,
                                      'inner': {'a': 1, 'b': 2},
                                      'loose': {'u': 1, 'v': 2}}


class LimitsConfig(Config):
    """Config class with checked and unchecked dict members."""

    def __init__(self) -> None:
        """Construct with the module-level default dict by reference."""
        self._unchecked_dicts: list[str] = list(_UNCHECKED)
        self.limits: dict[str, object] = _DEFAULT_LIMITS
        self.free: dict[str, int] = {'p': 1, 'q': 2}
        super().__init__(None, None, stderr_file=sys.stderr)

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Get validation plan for use when validating the Config object."""
        _ = stderr_file
        return []


@pytest.mark.parametrize('json_data, expected, paths', [
    ({'max': 5, 'inner': {'a': 7, 'b': 8}, 'loose': {'u': 3}},
     {'max': 5, 'inner': {'a': 7, 'b': 8}, 'loose': {'u': 3}, 'min': 1},
     [('limits', 'min')]),
    ({'max': 5, 'min': 2, 'inner': {'b': 8}, 'loose': {'u': 3}},
     {'max': 5, 'min': 2, 'inner': {'b': 8, 'a': 1}, 'loose': {'u': 3}},
     [('limits', 'inner', 'a')]),
    ({'max': 5, 'min': 2, 'loose': {'u': 3}},
     {'max': 5, 'min': 2, 'loose': {'u': 3}, 'inner': {'a': 1, 'b': 2}},
     [('limits', 'inner')]),
    ({}, _DEFAULT_LIMITS,
     [('limits', 'max'), ('limits', 'min'), ('limits', 'inner'),
      ('limits', 'loose')]),
    ({'loose': {'u': 3}, 'min': 2, 'inner': {'b': 8, 'a': 7}, 'max': 5},
     {'loose': {'u': 3}, 'min': 2, 'inner': {'b': 8, 'a': 7}, 'max': 5},
     [])])
def test_fill_checked_dict(json_data: dict[str, object],
                           expected: dict[str, object],
                           paths: list[JsonPath]) -> None:
    """Test filled values, key order and filled paths of a checked dict.

    The JSON keys keep their order and the filled keys follow in default
    order; ``json.dumps`` without sorting compares that order at all depths.
    """
    value, filled = fill_missing_keys(_DEFAULT_LIMITS, json_data, 'limits',
                                      _UNCHECKED, ('limits',))
    assert json.dumps(value) == json.dumps(expected)
    assert sorted(filled) == sorted(paths)


@pytest.mark.parametrize('self_data, json_data, key', [
    ({'p': 1, 'q': 2}, {'p': 7}, 'free'),
    ({'u': 1, 'v': 2}, {}, 'loose'),
    (3, 4, 'max'),
    ('text', None, 'name')])
def test_fill_not_checked(self_data: object, json_data: object,
                          key: str) -> None:
    """Test that unchecked dicts and non-dict values are returned as is."""
    value, filled = fill_missing_keys(self_data, json_data, key, _UNCHECKED,
                                      (key,))
    assert value is json_data
    assert not filled


@pytest.mark.parametrize('txt, expected', [
    ('{"limits": {"max": 5}}',
     {'max': 5, 'min': 1, 'inner': {'a': 1, 'b': 2},
      'loose': {'u': 1, 'v': 2}}),
    ('{"limits": {"inner": {"b": 8}, "loose": {"u": 3}}}',
     {'inner': {'b': 8, 'a': 1}, 'loose': {'u': 3}, 'max': 10, 'min': 1}),
    ('{"free": {"p": 7}}', _DEFAULT_LIMITS)])
def test_parse_fills_dict(capsys: CaptureFixture[str], txt: str,
                          expected: dict[str, object]) -> None:
    """Test that parse_json fills checked dicts but not unchecked ones."""
    cfg = LimitsConfig()
    cfg.parse_json(txt, ok_to_use_defaults=True)
    assert json.dumps(cfg.limits) == json.dumps(expected)
    assert cfg.free == ({'p': 7} if 'free' in txt else {'p': 1, 'q': 2})
    out, err = capsys.readouterr()
    assert out == ''
    assert err == ''


@pytest.mark.parametrize('txt, path, missing', [
    ('{"limits": {"max": 5, "inner": {"a": 1, "b": 2}, "loose": {}}, '
     '"free": {}}', ('limits', 'min'), 'limits[min]'),
    ('{"limits": {"max": 5, "min": 2, "inner": {"a": 1}, "loose": {}}, '
     '"free": {}}', ('limits', 'inner', 'b'), 'limits[inner][b]')])
def test_strict_not_filled(capsys: CaptureFixture[str], txt: str,
                           path: JsonPath, missing: str) -> None:
    """Test that strict parsing still raises for a missing dict key."""
    cfg = LimitsConfig()
    with pytest.raises(ConfigMissingKey) as exc_info:
        cfg.parse_json(txt, stderr_file=sys.stderr)
    assert exc_info.value.json_path == path
    out, err = capsys.readouterr()
    assert out == ''
    assert f'No value for {missing} in JSON data' in err


def test_strict_unchecked_kept() -> None:
    """Test that strict parsing assigns unchecked dicts as they are."""
    cfg = LimitsConfig()
    cfg.parse_json('{"limits": {"max": 5, "min": 2, "inner": {"a": 1, '
                   '"b": 2}, "loose": {"u": 3}}, "free": {"p": 7}}')
    assert cfg.free == {'p': 7}
    assert cfg.limits['loose'] == {'u': 3}


def test_filled_value_is_copy() -> None:
    """Test that changing a filled value leaves the default untouched."""
    cfg = LimitsConfig()
    cfg.parse_json('{"limits": {"max": 5}}', ok_to_use_defaults=True)
    inner = cfg.limits['inner']
    loose = cfg.limits['loose']
    assert isinstance(inner, dict) and isinstance(loose, dict)
    inner['a'] = 99
    loose['u'] = 99
    assert _DEFAULT_LIMITS == {'max': 10, 'min': 1, 'inner': {'a': 1, 'b': 2},
                               'loose': {'u': 1, 'v': 2}}
    assert LimitsConfig().limits['inner'] == {'a': 1, 'b': 2}


def test_second_parse_keeps() -> None:
    """Test that a second parse fills from the values of the first parse."""
    cfg = LimitsConfig()
    cfg.parse_json('{"limits": {"min": 3, "inner": {"a": 4}}}',
                   ok_to_use_defaults=True)
    cfg.parse_json('{"limits": {"max": 6}}', ok_to_use_defaults=True)
    assert cfg.limits == {'max': 6, 'min': 3, 'inner': {'a': 4, 'b': 2},
                          'loose': {'u': 1, 'v': 2}}
