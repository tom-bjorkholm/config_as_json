#! /usr/local/bin/python3
"""Test ok_to_use_defaults for nested Config objects declared by type.

The JSON data decides which nested objects exist, and defaults only
complete them. A nested object that the JSON data contains is parsed into
the current nested object of the declared class at the same place, or
else it gets the defaults of its class.
"""

# Copyright (c) 2026 Tom Björkholm
# MIT License

import json
import sys
from typing import Optional, TextIO, TypedDict, Unpack, override
import pytest
from pytest import CaptureFixture
from config_as_json.commontypes import JsonPath, PathOrStr
from config_as_json.config import Config
from config_as_json.config_errors import ConfigMissingKey, ConfigUnknownKey
from config_as_json.config_nesting import ConfigNesting, ConfigNestingKind, \
    NestedConfigs
from config_as_json.validator import InvalidConfiguration, ValidationPlan, \
    WholeConfigValidationStep, WholeConfigValidator


class Leaf(Config):
    """Nested configuration whose class default size is 1."""

    def __init__(self, from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 stderr_file: TextIO = sys.stderr, *,
                 member_name: Optional[str] = None) -> None:
        """Construct with the class defaults."""
        self.name = 'leaf'
        self.size = 1
        super().__init__(from_json_data_text, from_json_filename,
                         stderr_file=stderr_file, member_name=member_name)

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Return no validation."""
        _ = stderr_file
        return []


class SubLeaf(Leaf):
    """Subclass of Leaf, never parsed in place for a Leaf declaration."""


def _leaf(size: int, leaf_type: type[Leaf] = Leaf) -> Leaf:
    """Return a Leaf whose size is not the class default."""
    leaf = leaf_type()
    leaf.size = size
    return leaf


def _nesting(kind: ConfigNestingKind,
             config_type: type[Config]) -> ConfigNesting:
    """Return a nesting declaration without a factory function."""
    return ConfigNesting(kind=kind, config_type=config_type)


class Holder(Config):
    """Configuration holding Leaf objects in all five nesting kinds.

    Every current Leaf has a size that differs from the class default 1,
    so a test can tell where a kept value comes from.
    """

    def __init__(self, from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 stderr_file: TextIO = sys.stderr, *,
                 member_name: Optional[str] = None) -> None:
        """Construct with customised nested defaults."""
        self.member = _leaf(7)
        self.optional: Optional[Leaf] = None
        self.items = [_leaf(8)]
        self.by_name = {'a': _leaf(9), 'b': _leaf(10)}
        self.by_key: dict[str, object] = {'leaf': _leaf(6), 'plain': 1}
        super().__init__(from_json_data_text, from_json_filename,
                         stderr_file=stderr_file, member_name=member_name)

    @override
    def nested_configs(self) -> NestedConfigs:
        """Return the Leaf declarations of all five kinds."""
        by_key = ConfigNesting(kind=ConfigNestingKind.DICT_VALUE_BY_KEY,
                               config_type=Leaf, discriminator_key='leaf')
        return {'member': _nesting(ConfigNestingKind.MEMBER, Leaf),
                'optional': _nesting(ConfigNestingKind.OPTIONAL_MEMBER, Leaf),
                'items': _nesting(ConfigNestingKind.LIST_ELEMENT, Leaf),
                'by_name': _nesting(ConfigNestingKind.DICT_VALUE, Leaf),
                'by_key': [by_key]}

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Return no validation."""
        _ = stderr_file
        return []


class Outer(Config):
    """Configuration holding Holder objects, for two levels of nesting."""

    def __init__(self) -> None:
        """Construct with one Holder and an empty list of them."""
        self.inner = Holder()
        self.holders: list[Holder] = []
        super().__init__(None, None)

    @override
    def nested_configs(self) -> NestedConfigs:
        """Return the Holder declarations."""
        return {'inner': _nesting(ConfigNestingKind.MEMBER, Holder),
                'holders': _nesting(ConfigNestingKind.LIST_ELEMENT, Holder)}

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Return no validation."""
        _ = stderr_file
        return []


def _full() -> dict[str, object]:
    """Return complete JSON data for a Holder."""
    return {'member': {'name': 'm', 'size': 2}, 'optional': None,
            'items': [{'name': 'i', 'size': 3}],
            'by_name': {'a': {'name': 'a', 'size': 4}},
            'by_key': {'leaf': {'name': 'k', 'size': 5}, 'plain': 2}}


def _partial_holder() -> dict[str, object]:
    """Return Holder JSON data lacking a member size and the items."""
    data = _full()
    data['member'] = {'name': 'x'}
    del data['items']
    return data


def _parse(cfg: Holder, changes: dict[str, object],
           ok_to_use_defaults: bool = True) -> None:
    """Parse complete Holder JSON data, with some members replaced."""
    data = _full()
    data.update(changes)
    cfg.parse_json(json.dumps(data), ok_to_use_defaults=ok_to_use_defaults,
                   stderr_file=sys.stderr)


def _assert_quiet(capsys: CaptureFixture[str]) -> None:
    """Assert that nothing was written to stdout or stderr."""
    out, err = capsys.readouterr()
    assert out == ''
    assert err == ''


def test_member_in_place(capsys: CaptureFixture[str]) -> None:
    """Test that a partial MEMBER is parsed into the current object."""
    cfg = Holder()
    member = cfg.member
    _parse(cfg, {'member': {'name': 'x'}})
    assert cfg.member is member
    assert (member.name, member.size) == ('x', 7)
    assert cfg.kept_value_paths() == [('member', 'size')]
    _assert_quiet(capsys)


@pytest.mark.parametrize('current_size, json_value, size, same, kept', [
    (None, None, None, True, []),
    (11, None, None, False, []),
    (None, {'name': 'x'}, 1, False, [('optional', 'size')]),
    (11, {'name': 'x'}, 11, True, [('optional', 'size')]),
    (11, {'name': 'x', 'size': 2}, 2, True, [])])
# pylint: disable-next=too-many-arguments,too-many-positional-arguments
def test_optional_member(capsys: CaptureFixture[str],
                         current_size: Optional[int],
                         json_value: Optional[dict[str, object]],
                         size: Optional[int], same: bool,
                         kept: list[JsonPath]) -> None:
    """Test that JSON null gives None, and a partial object is completed.

    The values come from the current object when there is one, and else
    from the class defaults.
    """
    cfg = Holder()
    cfg.optional = None if current_size is None else _leaf(current_size)
    current = cfg.optional
    _parse(cfg, {'optional': json_value})
    assert (cfg.optional is current) == same
    assert (None if cfg.optional is None else cfg.optional.size) == size
    assert cfg.kept_value_paths() == kept
    _assert_quiet(capsys)


@pytest.mark.parametrize('current_count', [0, 1, 3])
def test_list_elements(capsys: CaptureFixture[str],
                       current_count: int) -> None:
    """Test that a list gets exactly the JSON elements.

    Each partial element is completed from the class defaults, also when
    the current list has an element at the same index.
    """
    cfg = Holder()
    cfg.items = [_leaf(8 + i) for i in range(current_count)]
    current = list(cfg.items)
    _parse(cfg, {'items': [{'name': 'x'}, {'name': 'y', 'size': 5}]})
    assert [(i.name, i.size) for i in cfg.items] == [('x', 1), ('y', 5)]
    assert not any(i is c for i in cfg.items for c in current)
    assert cfg.kept_value_paths() == [('items', 0, 'size')]
    _assert_quiet(capsys)


def test_dict_value(capsys: CaptureFixture[str]) -> None:
    """Test that a DICT_VALUE dict gets exactly the JSON keys.

    A partial value at an existing key is parsed in place, at a new key it
    is completed from the class defaults. A key missing from the JSON data
    is not added.
    """
    cfg = Holder()
    current = cfg.by_name['a']
    _parse(cfg, {'by_name': {'a': {'name': 'x'}, 'c': {'name': 'y'}}})
    assert sorted(cfg.by_name) == ['a', 'c']
    assert cfg.by_name['a'] is current
    assert (cfg.by_name['a'].size, cfg.by_name['c'].size) == (9, 1)
    assert sorted(cfg.kept_value_paths()) == [('by_name', 'a', 'size'),
                                              ('by_name', 'c', 'size')]
    _assert_quiet(capsys)


@pytest.mark.parametrize('current, json_value, size', [
    ({'leaf': _leaf(6), 'plain': 1}, {'leaf': {'name': 'x'}}, 6),
    ({'leaf': _leaf(6)}, {'leaf': {'name': 'x'}, 'other': 3}, 6),
    ({'plain': 1}, {'leaf': {'name': 'x'}}, 1)])
def test_dict_by_key(capsys: CaptureFixture[str], current: dict[str, object],
                     json_value: dict[str, object], size: int) -> None:
    """Test that a DICT_VALUE_BY_KEY dict gets exactly the JSON keys.

    A partial declared value is parsed in place when the current dict has
    it, and else completed from the class defaults.
    """
    cfg = Holder()
    cfg.by_key = dict(current)
    _parse(cfg, {'by_key': json_value})
    assert sorted(cfg.by_key) == sorted(json_value)
    leaf = cfg.by_key['leaf']
    assert isinstance(leaf, Leaf)
    assert (leaf is current.get('leaf')) == ('leaf' in current)
    assert leaf.size == size
    assert cfg.kept_value_paths() == [('by_key', 'leaf', 'size')]
    _assert_quiet(capsys)


@pytest.mark.parametrize('name', ['member', 'optional'])
def test_subclass_replaced(capsys: CaptureFixture[str], name: str) -> None:
    """Test that a current object of a subclass is not parsed in place."""
    cfg = Holder()
    setattr(cfg, name, _leaf(12, SubLeaf))
    _parse(cfg, {name: {'name': 'x'}})
    value = getattr(cfg, name)
    assert isinstance(value, Leaf)
    assert not isinstance(value, SubLeaf)
    assert value.size == 1
    _assert_quiet(capsys)


@pytest.mark.parametrize('data, prefix', [
    ({'inner': _partial_holder(), 'holders': []}, ('inner',)),
    ({'inner': _full(), 'holders': [_partial_holder()]}, ('holders', 0))])
def test_two_levels(capsys: CaptureFixture[str], data: dict[str, object],
                    prefix: JsonPath) -> None:
    """Test that kept paths two levels deep are prefixed by both levels.

    The member size is 7 both in place and from the Holder class defaults,
    since Holder customises it.
    """
    cfg = Outer()
    cfg.parse_json(json.dumps(data), ok_to_use_defaults=True)
    holder = cfg.inner if prefix == ('inner',) else cfg.holders[0]
    assert (holder.member.name, holder.member.size) == ('x', 7)
    assert sorted(cfg.kept_value_paths()) == [prefix + ('items',),
                                              prefix + ('member', 'size')]
    _assert_quiet(capsys)


_PARTIAL_CASES = [({'member': {'name': 'x'}}, ('member',)),
                  ({'optional': {'name': 'x'}}, ('optional',)),
                  ({'items': [{'name': 'x', 'size': 2}, {'name': 'x'}]},
                   ('items', 1)),
                  ({'by_name': {'a': {'name': 'x'}}}, ('by_name', 'a')),
                  ({'by_name': {'c': {'name': 'x'}}}, ('by_name', 'c')),
                  ({'by_key': {'leaf': {'name': 'x'}}}, ('by_key', 'leaf'))]


@pytest.mark.parametrize('changes, path', _PARTIAL_CASES)
def test_strict_missing(capsys: CaptureFixture[str],
                        changes: dict[str, object], path: JsonPath) -> None:
    """Test that a strict parse still rejects a partial nested object."""
    cfg = Holder()
    with pytest.raises(ConfigMissingKey) as exc_info:
        _parse(cfg, changes, ok_to_use_defaults=False)
    assert exc_info.value.json_path == path + ('size',)
    out, err = capsys.readouterr()
    assert out == ''
    assert 'No value for' in err


def test_strict_replaces(capsys: CaptureFixture[str]) -> None:
    """Test that a strict parse constructs new nested objects."""
    cfg = Holder()
    cfg.optional = _leaf(11)
    old = [cfg.member, cfg.optional, cfg.by_name['a'], cfg.by_key['leaf']]
    _parse(cfg, {'optional': {'name': 'o', 'size': 2}},
           ok_to_use_defaults=False)
    new = [cfg.member, cfg.optional, cfg.by_name['a'], cfg.by_key['leaf']]
    assert not any(i is j for i, j in zip(new, old))
    assert sorted(cfg.by_name) == ['a']
    assert not cfg.kept_value_paths()
    _assert_quiet(capsys)


@pytest.mark.parametrize('changes, path', _PARTIAL_CASES)
def test_nested_error_path(capsys: CaptureFixture[str],
                           changes: dict[str, object], path: JsonPath) -> None:
    """Test that a nested parse error carries the whole json_path.

    The cases cover parsing in place and completing from class defaults.
    The last nested object of each case gets an unknown key.
    """
    head, _, tail = json.dumps(changes).rpartition('"name"')
    bad = json.loads(head + '"bogus"' + tail)
    cfg = Holder()
    with pytest.raises(ConfigUnknownKey) as exc_info:
        _parse(cfg, bad)
    assert exc_info.value.json_path == path + ('bogus',)
    out, err = capsys.readouterr()
    assert out == ''
    assert 'Unexpected parameter' in err


# pylint: disable-next=too-few-public-methods
class NameValidator(WholeConfigValidator):
    """Reject an empty name."""

    def validate(self, config: Config, stderr_file: TextIO = sys.stderr, *,
                 member_name: Optional[str] = None) -> None:
        """Raise InvalidConfiguration when the name is empty."""
        _ = member_name
        assert isinstance(config, BlankLeaf)
        if not config.name:
            msg = 'Empty name'
            print(msg, file=stderr_file)
            raise InvalidConfiguration(msg)


class BlankLeaf(Config):
    """Nested configuration whose defaults are not valid on their own."""

    def __init__(self, from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 stderr_file: TextIO = sys.stderr, *,
                 member_name: Optional[str] = None,
                 ok_to_use_defaults: bool = False) -> None:
        """Construct with an empty name, and forward ok_to_use_defaults."""
        self.name = ''
        self.size = 1
        super().__init__(from_json_data_text, from_json_filename,
                         stderr_file=stderr_file, member_name=member_name,
                         ok_to_use_defaults=ok_to_use_defaults)

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Return the name validation."""
        _ = stderr_file
        return [WholeConfigValidationStep(validator=NameValidator())]


class StrictBlankLeaf(BlankLeaf):
    """BlankLeaf whose constructor does not accept ok_to_use_defaults."""

    def __init__(self, from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 stderr_file: TextIO = sys.stderr, *,
                 member_name: Optional[str] = None) -> None:
        """Construct without ok_to_use_defaults."""
        super().__init__(from_json_data_text, from_json_filename, stderr_file,
                         member_name=member_name)


class _LeafKeywords(TypedDict, total=False):
    """Keyword arguments that KwargsBlankLeaf forwards."""

    stderr_file: TextIO
    member_name: Optional[str]
    ok_to_use_defaults: bool


class KwargsBlankLeaf(BlankLeaf):
    """BlankLeaf whose constructor forwards ``**kwargs``."""

    def __init__(self, from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 **kwargs: Unpack[_LeafKeywords]) -> None:
        """Construct, forwarding every keyword argument."""
        super().__init__(from_json_data_text, from_json_filename, **kwargs)


class BlankHolder(Config):
    """Configuration holding a list of a BlankLeaf class."""

    def __init__(self, leaf_type: type[BlankLeaf]) -> None:
        """Construct with an empty list of the given BlankLeaf class."""
        self._leaf_type = leaf_type
        self.leaves: list[BlankLeaf] = []
        super().__init__(None, None)

    @override
    def nested_configs(self) -> NestedConfigs:
        """Return the list declaration of the BlankLeaf class."""
        return {'leaves': _nesting(ConfigNestingKind.LIST_ELEMENT,
                                   self._leaf_type)}

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Return no validation."""
        _ = stderr_file
        return []


@pytest.mark.parametrize('leaf_type', [BlankLeaf, KwargsBlankLeaf])
def test_constructor_keyword(capsys: CaptureFixture[str],
                             leaf_type: type[BlankLeaf]) -> None:
    """Test that a constructor accepting ok_to_use_defaults gets it.

    The class defaults are then never validated on their own.
    """
    cfg = BlankHolder(leaf_type)
    cfg.parse_json('{"leaves": [{"name": "x"}]}', ok_to_use_defaults=True)
    assert isinstance(cfg.leaves[0], leaf_type)
    assert (cfg.leaves[0].name, cfg.leaves[0].size) == ('x', 1)
    assert cfg.kept_value_paths() == [('leaves', 0, 'size')]
    _assert_quiet(capsys)


def test_constructor_defaults(capsys: CaptureFixture[str]) -> None:
    """Test that other class defaults are validated on their own first."""
    cfg = BlankHolder(StrictBlankLeaf)
    with pytest.raises(InvalidConfiguration):
        cfg.parse_json('{"leaves": [{"name": "x"}]}', ok_to_use_defaults=True,
                       stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert out == ''
    assert 'Empty name' in err


@pytest.mark.parametrize('leaf_type',
                         [BlankLeaf, StrictBlankLeaf, KwargsBlankLeaf])
def test_constructor_strict(capsys: CaptureFixture[str],
                            leaf_type: type[BlankLeaf]) -> None:
    """Test that a strict parse never passes ok_to_use_defaults."""
    cfg = BlankHolder(leaf_type)
    cfg.parse_json('{"leaves": [{"name": "x", "size": 2}]}')
    assert (cfg.leaves[0].name, cfg.leaves[0].size) == ('x', 2)
    assert not cfg.kept_value_paths()
    _assert_quiet(capsys)
