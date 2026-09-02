#! /usr/local/bin/python3
"""Test that ``member_name`` may be left out of every public call.

An application written before the reported name became a whole path calls
``parse_json``, ``validate``, ``read``, ``as_json_string``, a Config
constructor and the two key checks without ``member_name``. Every one of
them treats the object it is given as the top level, which is what the old
version did, so such an application keeps reporting plain member names.

An application written for this version passes the argument everywhere, and
it must never be warned about anything.
"""

# Copyright (c) 2026 Tom Björkholm
# MIT License

import sys
from io import StringIO
from pathlib import Path
import pytest
from config_as_json.config import Config
from config_as_json.config_factory import MatchConfig, \
    config_factory_from_json
from .check_capsys import check_capsys
from .member_name_compat_tools import HOLDER_JSON, PlainHolder, PlainLeaf, \
    deprecations
from .member_path_test_configs import Leaf
from .validator_test_helpers import EmptyValidationConfig


def test_construct_without_name(capsys: pytest.CaptureFixture[str]) -> None:
    """A Config object is constructed without saying it is the top level."""
    cfg = PlainHolder(from_json_data_text=HOLDER_JSON)
    assert isinstance(cfg.part, PlainLeaf)
    assert cfg.part.kind == 'parsed'
    check_capsys(capsys)


def test_parse_json_without_name(capsys: pytest.CaptureFixture[str]) -> None:
    """``parse_json`` treats the object it is given as the top level."""
    cfg = PlainHolder()
    cfg.parse_json(HOLDER_JSON, stderr_file=sys.stderr)
    assert isinstance(cfg.part, PlainLeaf)
    assert cfg.part.kind == 'parsed'
    check_capsys(capsys)


def test_validate_without_name(capsys: pytest.CaptureFixture[str]) -> None:
    """``validate`` treats the object it is given as the top level."""
    cfg = PlainHolder()
    cfg.validate(stderr_file=sys.stderr)
    check_capsys(capsys)


def test_read_write_without_name(tmp_path: Path,
                                 capsys: pytest.CaptureFixture[str]) -> None:
    """``read`` and ``as_json_string`` need no name of their own."""
    filename = tmp_path / 'holder.json'
    filename.write_text(HOLDER_JSON, encoding='UTF-8')
    cfg = PlainHolder()
    cfg.read(filename, stderr_file=sys.stderr)
    assert isinstance(cfg.part, PlainLeaf)
    assert cfg.part.kind == 'parsed'
    assert '"kind": "parsed"' in cfg.as_json_string(stderr_file=sys.stderr)
    check_capsys(capsys)


def test_factory_without_name(capsys: pytest.CaptureFixture[str]) -> None:
    """``config_factory_from_json`` needs no name of its own."""
    matchers = [MatchConfig(match_func=lambda text, stderr: True,
                            config_class=PlainHolder)]
    cfg = config_factory_from_json(match_configs=matchers,
                                   auto_ch_hook=PlainHolder().
                                   auto_change_hook(),
                                   from_json_data_text=HOLDER_JSON,
                                   stderr_file=sys.stderr)
    assert isinstance(cfg, PlainHolder)
    assert isinstance(cfg.part, PlainLeaf)
    check_capsys(capsys)


@pytest.mark.parametrize('keys, in_err', [
    (['kind', 'extra'], 'Unexpected parameter extra'),
    ([], 'No value for kind')])
def test_key_match_without_name(keys: list[str], in_err: str) -> None:
    """``check_key_match`` reports a plain key name for the top level."""
    stderr = StringIO()
    with pytest.raises(KeyError) as exc:
        Config.check_key_match(['kind'], keys, False, stderr)
    assert in_err in str(exc.value)
    assert in_err in stderr.getvalue()


def test_dict_parse_without_name() -> None:
    """``check_dict_parse`` reports the bare key when told no path.

    ``parse_json`` tells it the path of the checked member, and the key is
    then reported as ``limits[b]``. An old application that calls the check
    itself tells it nothing, and gets the bare key that the old version
    reported.
    """
    stderr = StringIO()
    with pytest.raises(KeyError) as exc:
        Config.check_dict_parse({'a': 1}, {'a': 1, 'b': 2}, 'limits', False,
                                [], stderr)
    assert 'Unexpected parameter b in JSON data' in str(exc.value)


def test_plain_name_reported() -> None:
    """A diagnostic about the top level names a plain member name.

    The same configuration reports ``section.leaf.kind`` when it is
    validated as a nested member, which is what the tests of the whole path
    check. A ``validate()`` that is not told a name reports ``kind``.
    """
    stderr = StringIO()
    leaf = Leaf(stderr_file=stderr)
    leaf.kind = 'legacy'
    leaf.validate(stderr_file=stderr)
    assert 'Warning: kind still uses a legacy format' in stderr.getvalue()


def test_new_style_never_warns(tmp_path: Path) -> None:
    """Code written for this version is not warned about anything."""
    filename = tmp_path / 'holder.json'
    filename.write_text(HOLDER_JSON, encoding='UTF-8')
    out = tmp_path / 'written.json'

    def whole_traversal() -> None:
        """Construct, parse, read, validate and write one configuration."""
        cfg = PlainHolder(from_json_data_text=HOLDER_JSON,
                          member_name='outputs[1]')
        cfg.parse_json(HOLDER_JSON, stderr_file=sys.stderr, member_name=None)
        cfg.read(filename, stderr_file=sys.stderr, member_name=None)
        cfg.validate(stderr_file=sys.stderr, member_name=None)
        cfg.write(to_json_filename=out, stderr_file=sys.stderr)
        _ = EmptyValidationConfig()
    assert deprecations(whole_traversal) == []
