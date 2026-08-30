#! /usr/local/bin/python3
"""Test that validation names a nested value by its whole path."""

# Copyright (c) 2026 Tom Björkholm
# MIT License

from io import StringIO
from typing import Optional
import pytest
from pytest import CaptureFixture
from config_as_json.config import Config
from config_as_json.member_path import member_path
from config_as_json.validator import InvalidConfiguration, \
    InvalidConfigurationValue
from .check_capsys import check_capsys
from .member_path_test_configs import BuiltInTop, DottedKeys, Leaf, Middle, \
    Top


def _top_with_bad_leaf(case: str) -> Top:
    """Return one Top whose nested Leaf at ``case`` holds a rejected kind."""
    top = Top()
    leaf = top.section.leaf
    if case == 'optional':
        top.section.spare = Leaf()
        leaf = top.section.spare
    elif case == 'list':
        top.section.leaves = [Leaf(), Leaf(), Leaf()]
        leaf = top.section.leaves[2]
    elif case == 'dict':
        leaf = top.section.by_name['main']
    elif case == 'by_key':
        picked = top.section.mixed['picked']
        assert isinstance(picked, Leaf)
        leaf = picked
    leaf.kind = 'nope'
    return top


def _bad_top_level(config_kind: str) -> Config:
    """Return one top level configuration holding a rejected kind."""
    if config_kind == 'middle':
        middle = Middle()
        middle.leaf.kind = 'nope'
        return middle
    leaf = Leaf()
    leaf.kind = 'nope'
    return leaf


@pytest.mark.parametrize('member_name, name, expected', [
    (None, 'kind', 'kind'),
    ('section', 'kind', 'section.kind'),
    ('outputs[1]', 'kind', 'outputs[1].kind'),
    ('a.b', 'c', 'a.b.c')
])
def test_member_path_join(member_name: Optional[str], name: str,
                          expected: str) -> None:
    """Test that the joining helper starts a path and extends a path."""
    assert member_path(member_name, name) == expected


@pytest.mark.parametrize('case, expected', [
    ('member', 'section.leaf.kind'),
    ('optional', 'section.spare.kind'),
    ('list', 'section.leaves[2].kind'),
    ('dict', 'section.by_name[main].kind'),
    ('by_key', 'section.mixed[picked].kind')
])
def test_nesting_kind_paths(case: str, expected: str,
                            capsys: CaptureFixture[str]) -> None:
    """Test one reported path per nesting kind, two nesting levels deep."""
    top = _top_with_bad_leaf(case)
    stderr_file = StringIO()
    with pytest.raises(InvalidConfigurationValue) as exc:
        top.validate(stderr_file=stderr_file, member_name=None)
    assert exc.value.member_name == expected
    assert f'Value nope for {expected} is not one of' in stderr_file.getvalue()
    check_capsys(capsys)


@pytest.mark.parametrize('config_kind, expected', [
    ('leaf', 'kind'),
    ('middle', 'leaf.kind')
])
def test_top_level_plain_names(config_kind: str, expected: str,
                               capsys: CaptureFixture[str]) -> None:
    """Test that a top level object reports its own members by plain name."""
    config = _bad_top_level(config_kind)
    stderr_file = StringIO()
    with pytest.raises(InvalidConfigurationValue) as exc:
        config.validate(stderr_file=stderr_file, member_name=None)
    assert exc.value.member_name == expected
    check_capsys(capsys)


def test_dotted_dict_key(capsys: CaptureFixture[str]) -> None:
    """Test the documented ambiguous path made by a dict key with a dot."""
    config = DottedKeys()
    config.by_name['a.b'].kind = 'nope'
    stderr_file = StringIO()
    with pytest.raises(InvalidConfigurationValue) as exc:
        config.validate(stderr_file=stderr_file, member_name=None)
    # The path cannot be taken apart again: the dot in the key reads like a
    # step into an attribute. That is accepted, and documented, rather than
    # escaped.
    assert exc.value.member_name == 'by_name[a.b].kind'
    check_capsys(capsys)


@pytest.mark.parametrize('member, value, expected', [
    ('tags', ['nope'], 'section.leaf.tags[0]'),
    ('limits', {'cpu': 99}, 'section.leaf.limits[cpu]')
])
def test_for_each_validator_paths(member: str, value: object, expected: str,
                                  capsys: CaptureFixture[str]) -> None:
    """Test that a for-each validator indexes into the path it was given."""
    top = Top()
    setattr(top.section.leaf, member, value)
    stderr_file = StringIO()
    with pytest.raises(InvalidConfiguration):
        top.validate(stderr_file=stderr_file, member_name=None)
    assert f'for {expected} ' in stderr_file.getvalue()
    check_capsys(capsys)


def test_whole_config_validator_path(capsys: CaptureFixture[str]) -> None:
    """Test that a whole-config validator can name a member by its path."""
    top = Top()
    top.section.leaf.tags = ['bad']
    stderr_file = StringIO()
    with pytest.raises(InvalidConfiguration) as exc:
        top.validate(stderr_file=stderr_file, member_name=None)
    assert 'section.leaf.tags holds a bad tag.' in str(exc.value)
    assert 'section.leaf.tags holds a bad tag.' in stderr_file.getvalue()
    check_capsys(capsys)


def test_warning_without_raise(capsys: CaptureFixture[str]) -> None:
    """Test that a diagnostic that does not stop validation names the path."""
    top = Top()
    top.section.leaf.kind = 'legacy'
    stderr_file = StringIO()
    top.validate(stderr_file=stderr_file, member_name=None)
    assert stderr_file.getvalue() == \
        'Warning: section.leaf.kind still uses a legacy format\n'
    check_capsys(capsys)


def test_wrong_nested_type_path(capsys: CaptureFixture[str]) -> None:
    """Test that a nested member of the wrong type is named by its path."""
    top = Top()
    top.section.leaf = 'not a Leaf'  # type: ignore[assignment]
    stderr_file = StringIO()
    with pytest.raises(TypeError) as exc:
        top.validate(stderr_file=stderr_file, member_name=None)
    assert 'Nested Config member section.leaf must be Leaf' in str(exc.value)
    check_capsys(capsys)


@pytest.mark.parametrize('sizes, pool, expected', [
    ([9], [1, 3], 'Value 9 for built_in.total_size is greater than'),
    ([5], [1, 3], 'does not hold between built_in.sizes and built_in.pool'),
    ([], [], 'Method check_pool at built_in returned False.')
])
def test_built_in_whole_validators(sizes: list[int], pool: list[int],
                                   expected: str,
                                   capsys: CaptureFixture[str]) -> None:
    """Test that the built-in whole-config validators report paths."""
    top = BuiltInTop()
    top.built_in.sizes = sizes
    top.built_in.pool = pool
    stderr_file = StringIO()
    with pytest.raises(InvalidConfiguration) as exc:
        top.validate(stderr_file=stderr_file, member_name=None)
    assert expected in str(exc.value)
    assert expected in stderr_file.getvalue()
    check_capsys(capsys)
