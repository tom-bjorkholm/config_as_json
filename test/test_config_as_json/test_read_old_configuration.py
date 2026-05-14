#! /usr/local/bin/python3
"""Test ReadOldConfiguration normalization rules."""

# Copyright (c) 2026 Tom Björkholm
# MIT License

from copy import deepcopy
from io import StringIO
import pytest
from config_as_json.config_auto_change_hook import ConfigAutoChangeHook
from config_as_json.read_old_configuration import ReadOldConfiguration, \
    RocfConflictError, RocfIncompatiblePathError, RocfKeyMove, \
    RocfKeyRename, RocfPath


class RuleReadOldConfig(ReadOldConfiguration):
    """Read-old processor with rules injected by tests."""

    def __init__(self) -> None:
        """Store the rules this processor should return."""
        self.moves: list[RocfKeyMove] = []
        self.remove_names: list[str] = []
        self.remove_paths: list[RocfPath] = []
        self.missing: dict[RocfPath, object] = {}
        self.renames: list[RocfKeyRename] = []

    def get_json_key_moves(self) -> list[RocfKeyMove]:
        """Return injected move rules."""
        return self.moves

    def get_keys_to_remove_recursively(self) -> list[str]:
        """Return injected recursive remove keys."""
        return self.remove_names

    def get_keys_to_remove(self) -> list[RocfPath]:
        """Return injected path remove rules."""
        return self.remove_paths

    def get_values_for_missing_json_keys(self) -> dict[RocfPath, object]:
        """Return injected missing-value rules."""
        return self.missing

    def get_json_key_renames(self) -> list[RocfKeyRename]:
        """Return injected rename rules."""
        return self.renames


def process_data(rocf: ReadOldConfiguration,
                 data: dict[str, object]) -> tuple[ConfigAutoChangeHook, str]:
    """Process test data and return the hook and diagnostics."""
    hook = ConfigAutoChangeHook()
    stderr_file = StringIO()
    rocf.process_json(data, hook, stderr_file)
    return hook, stderr_file.getvalue()


def test_process_noop_current_data() -> None:
    """Current-shape data passes through unchanged with no hook records."""
    data: dict[str, object] = {'name': 'current', 'outputs': []}
    original = deepcopy(data)
    hook, err = process_data(RuleReadOldConfig(), data)
    assert data == original
    assert not hook.old_keys
    assert not hook.rocf_val_keys
    assert not hook.old_paths_moved
    assert err == ''


def test_remove_paths_and_rename() -> None:
    """Recursive and path removals combine with recursive renames."""
    data: dict[str, object] = {
        'old_name': 'report',
        'drop': True,
        'details': {'drop': False, 'keep': 1, 'temp': 2},
        'items': [{'old_name': 'item', 'drop': True}]
    }
    rocf = RuleReadOldConfig()
    rocf.remove_names = ['drop']
    rocf.remove_paths = [('details', 'temp')]
    rocf.renames = [RocfKeyRename(old='old_name', new='name')]
    hook, err = process_data(rocf, data)
    assert data == {
        'name': 'report',
        'details': {'keep': 1},
        'items': [{'name': 'item'}]
    }
    assert hook.old_keys == ['drop', 'details[temp]', 'old_name']
    assert err == ''


def test_rename_current_wins() -> None:
    """An existing current key wins over a recursive old-key rename."""
    data: dict[str, object] = {'old_name': 'old', 'name': 'current'}
    rocf = RuleReadOldConfig()
    rocf.renames = [RocfKeyRename(old='old_name', new='name')]
    hook, err = process_data(rocf, data)
    assert data == {'name': 'current'}
    assert hook.old_keys == ['old_name']
    assert err == '\n'.join([
        'Inconsistent configuration:',
        'Both new config parameter name and old old_name present.',
        'Ignoring old parameter old_name'
    ]) + '\n'


def test_missing_existing_lists() -> None:
    """Missing-value rules can fill dict paths and existing list elements."""
    data: dict[str, object] = {
        'outputs': [{'name': 'main'}, {'encoding': 'latin-1'}]
    }
    rocf = RuleReadOldConfig()
    rocf.missing = {('meta', 'owner'): 'ops',
                    ('outputs', '[', 'encoding'): 'utf-8',
                    ('outputs', '[', 'name'): 'unnamed'}
    hook, err = process_data(rocf, data)
    assert data == {
        'meta': {'owner': 'ops'},
        'outputs': [{'name': 'main', 'encoding': 'utf-8'},
                    {'encoding': 'latin-1', 'name': 'unnamed'}]
    }
    assert hook.rocf_val_keys == [
        'meta[owner]',
        'outputs[0].encoding',
        'outputs[1].name'
    ]
    assert err == ''


def test_missing_empty_list() -> None:
    """A missing list itself is supplied by using the list member path."""
    data: dict[str, object] = {'name': 'without-output'}
    rocf = RuleReadOldConfig()
    rocf.missing = {('outputs',): [],
                    ('outputs', '[', 'encoding'): 'utf-8'}
    hook, err = process_data(rocf, data)
    assert data == {'name': 'without-output', 'outputs': []}
    assert hook.rocf_val_keys == ['outputs']
    assert err == ''


def test_move_object_to_list() -> None:
    """A non-list old value can move into the first element of a new list."""
    data: dict[str, object] = {
        'output': {'format': 'csv', 'encoding': 'utf-8'}
    }
    rocf = RuleReadOldConfig()
    move = RocfKeyMove(old_path=('output',), new_path=('outputs', '['))
    rocf.moves = [move]
    rocf.missing = {('format_version',): 2}
    hook, err = process_data(rocf, data)
    assert data == {
        'outputs': [{'format': 'csv', 'encoding': 'utf-8'}],
        'format_version': 2
    }
    assert hook.old_paths_moved == [('output', 'outputs[0]')]
    assert hook.old_keys == ['output -> outputs[0]']
    assert hook.rocf_val_keys == ['format_version']
    assert err == ''


def test_move_key_in_each_list_item() -> None:
    """A list wildcard move pairs old and new elements by index."""
    data: dict[str, object] = {
        'outputs': [{'encoding': 'utf-8'}, {'encoding': 'latin-1'}]
    }
    rocf = RuleReadOldConfig()
    rocf.moves = [
        RocfKeyMove(old_path=('outputs', '[', 'encoding'),
                    new_path=('outputs', '[', 'char_encoding'))]
    hook, err = process_data(rocf, data)
    assert data == {
        'outputs': [{'char_encoding': 'utf-8'},
                    {'char_encoding': 'latin-1'}]
    }
    assert hook.old_paths_moved == [
        ('outputs[0].encoding', 'outputs[0].char_encoding'),
        ('outputs[1].encoding', 'outputs[1].char_encoding')
    ]
    assert hook.old_keys == [
        'outputs[0].encoding -> outputs[0].char_encoding',
        'outputs[1].encoding -> outputs[1].char_encoding'
    ]
    assert err == ''


def test_move_current_list_wins() -> None:
    """An existing current list wins over an old object-to-list move."""
    data: dict[str, object] = {
        'output': {'encoding': 'latin-1'},
        'outputs': [{'encoding': 'utf-8'}]
    }
    rocf = RuleReadOldConfig()
    move = RocfKeyMove(old_path=('output',), new_path=('outputs', '['))
    rocf.moves = [move]
    hook, err = process_data(rocf, data)
    assert data == {'outputs': [{'encoding': 'utf-8'}]}
    assert hook.old_paths_moved == [('output', 'outputs[0]')]
    assert hook.old_keys == ['output -> outputs[0]']
    assert err == '\n'.join([
        'Inconsistent configuration:',
        'Both new config parameter outputs[0] and old output present.',
        'Ignoring old parameter output'
    ]) + '\n'


def test_move_target_conflict() -> None:
    """Two move rules cannot both write one actual current target."""
    data: dict[str, object] = {'first': 1, 'second': 2}
    rocf = RuleReadOldConfig()
    rocf.moves = [RocfKeyMove(old_path=('first',), new_path=('current',)),
                  RocfKeyMove(old_path=('second',), new_path=('current',))]
    with pytest.raises(RocfConflictError):
        _ = process_data(rocf, data)


def test_bad_target_raises() -> None:
    """A scalar in the way of a target path is an incompatible path."""
    data: dict[str, object] = {'old_value': 1, 'target': 'scalar'}
    rocf = RuleReadOldConfig()
    rocf.moves = [RocfKeyMove(old_path=('old_value',),
                              new_path=('target', 'value'))]
    with pytest.raises(RocfIncompatiblePathError):
        _ = process_data(rocf, data)


def test_move_descendant_to_ancestor() -> None:
    """Overlapping old and new paths are allowed for valid migrations."""
    data: dict[str, object] = {
        'output': {'file_name': 'report.csv', 'unused': True}
    }
    rocf = RuleReadOldConfig()
    rocf.moves = [RocfKeyMove(old_path=('output', 'file_name'),
                              new_path=('output',))]
    hook, err = process_data(rocf, data)
    assert data == {'output': 'report.csv'}
    assert hook.old_paths_moved == [('output[file_name]', 'output')]
    assert hook.old_keys == ['output[file_name] -> output']
    assert err == ''


@pytest.mark.parametrize(
    'move',
    [RocfKeyMove(old_path=(), new_path=('current',)),
     RocfKeyMove(old_path=('old',), new_path=('[15',)),
     RocfKeyMove(old_path=('items', '[', 'old'), new_path=('current',))])
def test_invalid_move_rules_raise(move: RocfKeyMove) -> None:
    """Invalid move path syntax is rejected before data is changed."""
    data: dict[str, object] = {'old': 1, 'items': [{'old': 2}]}
    with pytest.raises(ValueError):
        rocf = RuleReadOldConfig()
        rocf.moves = [move]
        _ = process_data(rocf, data)
