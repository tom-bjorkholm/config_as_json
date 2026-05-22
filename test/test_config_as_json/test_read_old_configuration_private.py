#! /usr/local/bin/python3
"""Test private helpers used by ReadOldConfiguration."""

# Copyright (c) 2026 Tom Björkholm
# MIT License

# The tests in this file intentionally exercise private functions. They are
# small migration primitives where regressions are otherwise hard to diagnose.
# pylint: disable=protected-access

from io import StringIO
from typing import Optional, TextIO, cast
import pytest
from config_as_json.config_auto_change_hook import ConfigAutoChangeHook
from config_as_json.commontypes import ConfigPath
from config_as_json.validator import InvalidConfiguration
import config_as_json.read_old_configuration as rocf_mod
from .test_read_old_configuration import RuleReadOldConfig


class MethodReadOldConfig(RuleReadOldConfig):
    """Read-old processor exposing private methods through test wrappers."""

    def run_remove_recursive(self, data: dict[str, object],
                             hook: ConfigAutoChangeHook) -> None:
        """Run recursive removal through the private method."""
        self._remove_keys_recursively(data, hook)

    def run_remove_paths(self, data: dict[str, object],
                         hook: ConfigAutoChangeHook) -> None:
        """Run path removal through the private method."""
        self._remove_keys_by_path(data, hook)

    def run_renames(self, data: dict[str, object], hook: ConfigAutoChangeHook,
                    stderr_file: TextIO) -> None:
        """Run recursive renames through the private method."""
        self._rename_json_keys(data, hook, stderr_file)

    def run_moves(self, data: dict[str, object], hook: ConfigAutoChangeHook,
                  stderr_file: TextIO) -> None:
        """Run path moves through the private method."""
        self._move_json_keys(data, hook, stderr_file)

    def run_one_move(self, context: rocf_mod._MoveContext,
                     move: rocf_mod.RocfKeyMove,
                     value: rocf_mod._MovedValue) -> None:
        """Run one actual path move through the private method."""
        self._move_one_path(context, move, value)

    def run_target_current(self, context: rocf_mod._MoveContext,
                           value: rocf_mod._MovedValue,
                           wrap_prefix: Optional[list[str | int]],
                           target: list[str | int]) -> bool:
        """Run current-target detection through the private method."""
        return self._target_is_current(context, value, wrap_prefix, target)

    def run_missing_values(self, data: dict[str, object],
                           hook: ConfigAutoChangeHook) -> None:
        """Run missing-value handling through the private method."""
        self._apply_missing_values(data, hook)


def assert_no_error(stderr_file: StringIO) -> None:
    """Assert that no diagnostic text was written."""
    assert stderr_file.getvalue() == ''


@pytest.mark.parametrize('value, expected', [({'a': 1}, {'a': 1}),
                                             ({}, {})])
def test_as_dict_ok(value: object, expected: dict[str, object]) -> None:
    """Test dictionary recognition for dictionary values."""
    assert rocf_mod._as_dict(value) == expected


@pytest.mark.parametrize('value', [[], 'text', 7, None])
def test_as_dict_bad(value: object) -> None:
    """Test dictionary recognition for non-dictionary values."""
    assert rocf_mod._as_dict(value) is None


@pytest.mark.parametrize('value, expected', [([1, 2], [1, 2]), ([], [])])
def test_as_list_ok(value: object, expected: list[object]) -> None:
    """Test list recognition for list values."""
    assert rocf_mod._as_list(value) == expected


@pytest.mark.parametrize('value', [{}, 'text', 7, None])
def test_as_list_bad(value: object) -> None:
    """Test list recognition for non-list values."""
    assert rocf_mod._as_list(value) is None


@pytest.mark.parametrize(
    'path, expected',
    [(['root'], 'root'),
     (['output', 'file_name'], 'output[file_name]'),
     (['outputs', 2, 'csv_params', 'delimiter'],
      'outputs[2][csv_params][delimiter]'),
     (['outputs', 2], 'outputs[2]'),
     (['outputs', 2, 'name'], 'outputs[2][name]'),
     ([], '')])
def test_path_text_ok(path: list[str | int], expected: str) -> None:
    """Test path rendering used in diagnostics and hook calls."""
    assert rocf_mod._path_text(path) == expected


@pytest.mark.parametrize('path', [('name',), ('outputs', '[', 'format')])
def test_validate_path_ok(path: ConfigPath) -> None:
    """Test accepted declarative path syntax."""
    rocf_mod._validate_path(path, 'path')


@pytest.mark.parametrize(
    'path, error_type',
    [((), ValueError), (('[', 'name'), ValueError), (('[5',), ValueError),
     (cast(ConfigPath, ('ok', 1)), TypeError)])
def test_validate_path_bad(path: ConfigPath,
                           error_type: type[Exception]) -> None:
    """Test rejected declarative path syntax."""
    with pytest.raises(error_type):
        rocf_mod._validate_path(path, 'path')


@pytest.mark.parametrize(
    'path, expected',
    [(('name',), 0), (('outputs', '[', 'format'), 1),
     (('a', '[', 'b', '[', 'c'), 2)])
def test_list_marker_count(path: ConfigPath, expected: int) -> None:
    """Test counting of list wildcards in a declarative path."""
    assert rocf_mod._list_marker_count(path) == expected


@pytest.mark.parametrize(
    'move',
    [rocf_mod.RocfKeyMove(old_path=('old',), new_path=('new',)),
     rocf_mod.RocfKeyMove(old_path=('output',), new_path=('outputs', '[')),
     rocf_mod.RocfKeyMove(old_path=('items', '[', 'old'),
                          new_path=('items', '[', 'new'))])
def test_validate_move_ok(move: rocf_mod.RocfKeyMove) -> None:
    """Test accepted declarative move rules."""
    rocf_mod._validate_move(move)


@pytest.mark.parametrize(
    'move',
    [rocf_mod.RocfKeyMove(old_path=(), new_path=('new',)),
     rocf_mod.RocfKeyMove(old_path=('same',), new_path=('same',)),
     rocf_mod.RocfKeyMove(old_path=('items', '[', 'old'), new_path=('new',)),
     rocf_mod.RocfKeyMove(old_path=('old',), new_path=('[5',))])
def test_validate_move_bad(move: rocf_mod.RocfKeyMove) -> None:
    """Test rejected declarative move rules."""
    with pytest.raises(ValueError):
        rocf_mod._validate_move(move)


def test_conflict_diag() -> None:
    """Test the standard current-value-wins diagnostic."""
    stderr_file = StringIO()
    rocf_mod._conflict_diag('old.path', 'new.path', stderr_file)
    assert stderr_file.getvalue() == '\n'.join([
        'Inconsistent configuration:',
        'Both new config parameter new.path and old old.path present.',
        'Ignoring old parameter old.path'
    ]) + '\n'


@pytest.mark.parametrize(
    'data, key, expected_data, expected_found',
    [({'drop': 1, 'keep': {'drop': 2}}, 'drop', {'keep': {}}, True),
     ({'items': [{'drop': 1}, {'keep': 2}]}, 'drop',
      {'items': [{}, {'keep': 2}]}, True),
     ({'keep': 1}, 'drop', {'keep': 1}, False)])
def test_remove_key_recursive(data: dict[str, object], key: str,
                              expected_data: dict[str, object],
                              expected_found: bool) -> None:
    """Test recursive key removal through dictionaries and lists."""
    assert rocf_mod._remove_key_recursive(data, key) == expected_found
    assert data == expected_data


@pytest.mark.parametrize('data', ['text', 7, None])
def test_remove_key_recursive_bad(data: object) -> None:
    """Test recursive key removal on non-container data."""
    assert not rocf_mod._remove_key_recursive(data, 'drop')


@pytest.mark.parametrize(
    'data, expected_data, expected_found, expected_err',
    [({'old': 1}, {'new': 1}, True, ''),
     ({'items': [{'old': 1}]}, {'items': [{'new': 1}]}, True, ''),
     ({'old': 1, 'new': 2}, {'new': 2}, True,
      'Inconsistent configuration:\n'
      'Both new config parameter new and old old present.\n'
      'Ignoring old parameter old\n'),
     ({'keep': 1}, {'keep': 1}, False, '')])
def test_rename_key_recursive(
        data: dict[str, object], expected_data: dict[str, object],
        expected_found: bool, expected_err: str) -> None:
    """Test recursive key rename behavior."""
    stderr_file = StringIO()
    rename = rocf_mod.RocfKeyRename(old='old', new='new')
    assert rocf_mod._rename_key_recursive(rename, data, stderr_file) == \
        expected_found
    assert data == expected_data
    assert stderr_file.getvalue() == expected_err


def test_rename_key_recursive_bad() -> None:
    """Test invalid recursive key rename input."""
    rename = rocf_mod.RocfKeyRename(old='same', new='same')
    with pytest.raises(AssertionError):
        rocf_mod._rename_key_recursive(rename, {}, StringIO())


@pytest.mark.parametrize(
    'data, path, expected',
    [({'old': 1}, ('old',), [(['old'], [], 1)]),
     ({'items': ['a', 'b']}, ('items', '['),
      [(['items', 0], [0], 'a'), (['items', 1], [1], 'b')]),
     ({'items': [{'old': 1}, {'old': 2}]}, ('items', '[', 'old'),
      [(['items', 0, 'old'], [0], 1), (['items', 1, 'old'], [1], 2)]),
     ({'items': 'bad'}, ('items', '[', 'old'), []),
     ({'missing': {}}, ('items', '[', 'old'), [])])
def test_collect_path_values(
        data: dict[str, object], path: ConfigPath,
        expected: list[tuple[list[str | int], list[int], object]]) -> None:
    """Test collection of actual values for declarative paths."""
    collected = rocf_mod._collect_path_values(data, path, [], [])
    assert [(item.actual_path, item.indexes, item.value)
            for item in collected] == expected


@pytest.mark.parametrize(
    'new_path, indexes, expected',
    [(('new',), [], ['new']),
     (('outputs', '[', 'name'), [], ['outputs', 0, 'name']),
     (('outputs', '[', 'name'), [3], ['outputs', 3, 'name'])])
def test_target_path(new_path: ConfigPath, indexes: list[int],
                     expected: list[str | int]) -> None:
    """Test creation of an actual target path from a move rule."""
    assert rocf_mod._target_path(new_path, indexes) == expected


@pytest.mark.parametrize(
    'data, path, expected',
    [({'old': 1, 'keep': 2}, ['old'], {'keep': 2}),
     ({'items': [{'old': 1}, {'old': 2}]}, ['items', 1, 'old'],
      {'items': [{'old': 1}, {}]}),
     ({'items': [1, 2, 3]}, ['items', 1], {'items': [1, 3]}),
     ({'keep': 1}, ['missing'], {'keep': 1})])
def test_delete_path(data: dict[str, object], path: list[str | int],
                     expected: dict[str, object]) -> None:
    """Test deletion of one actual path."""
    rocf_mod._delete_path(data, path)
    assert data == expected


@pytest.mark.parametrize('path', [[], ['missing', 0], ['items', 3]])
def test_delete_path_bad(path: list[str | int]) -> None:
    """Test no-op deletion when an actual path cannot be reached."""
    data: dict[str, object] = {'items': [1]}
    rocf_mod._delete_path(data, path)
    assert data == {'items': [1]}


@pytest.mark.parametrize(
    'data, path, expected',
    [({'old': 1}, ['old'], True), ({'items': [1]}, ['items', 0], True),
     ({'items': [1]}, ['items', 1], False),
     ({'items': 'bad'}, ['items', 0], False),
     ({'items': [{}]}, ['items', 0, 'name'], False)])
def test_path_exists(data: dict[str, object], path: list[str | int],
                     expected: bool) -> None:
    """Test actual path existence checks."""
    assert rocf_mod._path_exists(data, path) is expected


@pytest.mark.parametrize(
    'first, second, expected',
    [(['a'], ['a', 'b'], True), (['a', 'b'], ['a'], False),
     (['a'], ['b'], False), ([], ['a'], True)])
def test_path_is_prefix(first: list[str | int], second: list[str | int],
                        expected: bool) -> None:
    """Test path prefix detection."""
    assert rocf_mod._path_is_prefix(first, second) is expected


@pytest.mark.parametrize(
    'first, second, expected',
    [(['a'], ['a', 'b'], True), (['a', 'b'], ['a'], True),
     (['a'], ['b'], False)])
def test_paths_overlap(first: list[str | int], second: list[str | int],
                       expected: bool) -> None:
    """Test ancestor-or-descendant path overlap detection."""
    assert rocf_mod._paths_overlap(first, second) is expected


@pytest.mark.parametrize(
    'move, target, expected',
    [(rocf_mod.RocfKeyMove(old_path=('old',), new_path=('items', '[')),
      ['items', 0], ['items']),
     (rocf_mod.RocfKeyMove(old_path=('items', '[', 'old'),
                           new_path=('items', '[', 'new')),
      ['items', 2, 'new'], None),
     (rocf_mod.RocfKeyMove(old_path=('old',), new_path=('items', '[')),
      ['items'], None),
     (rocf_mod.RocfKeyMove(old_path=('old',), new_path=('new',)),
      ['new'], None)])
def test_wrap_prefix(move: rocf_mod.RocfKeyMove, target: list[str | int],
                     expected: Optional[list[str | int]]) -> None:
    """Test current-list prefix detection for object-to-list moves."""
    assert rocf_mod._wrap_prefix(move, target) == expected


@pytest.mark.parametrize(
    'data, path, expected',
    [({'old': 1}, ['old'], (True, 1)),
     ({'items': [{'name': 'a'}]}, ['items', 0, 'name'], (True, 'a')),
     ({'items': []}, ['items', 0], (False, None)),
     ({'items': 'bad'}, ['items', 0], (False, None))])
def test_get_existing_value(data: dict[str, object], path: list[str | int],
                            expected: tuple[bool, object]) -> None:
    """Test retrieving one existing actual path value."""
    assert rocf_mod._get_existing_value(data, path) == expected


@pytest.mark.parametrize('next_part, expected', [(0, []), ('name', {})])
def test_container_for(next_part: str | int, expected: object) -> None:
    """Test inferred intermediate container creation."""
    assert rocf_mod._container_for(next_part) == expected


def test_require_dict_ok() -> None:
    """Test dictionary requirement for dictionary values."""
    value: object = {'a': 1}
    assert rocf_mod._require_dict(value, []) == {'a': 1}


@pytest.mark.parametrize('value', [[], 'text', 7, None])
def test_require_dict_bad(value: object) -> None:
    """Test dictionary requirement for non-dictionary values."""
    with pytest.raises(rocf_mod.RocfIncompatiblePathError):
        rocf_mod._require_dict(value, ['path'])


def test_require_list_ok() -> None:
    """Test list requirement for list values."""
    value: object = [1, 2]
    assert rocf_mod._require_list(value, []) == [1, 2]


@pytest.mark.parametrize('value', [{}, 'text', 7, None])
def test_require_list_bad(value: object) -> None:
    """Test list requirement for non-list values."""
    with pytest.raises(rocf_mod.RocfIncompatiblePathError):
        rocf_mod._require_list(value, ['path'])


@pytest.mark.parametrize(
    'path, value, expected',
    [(['new'], 1, {'new': 1}),
     (['nested', 'value'], 2, {'nested': {'value': 2}}),
     (['items', 0, 'name'], 'a', {'items': [{'name': 'a'}]})])
def test_write_path(path: list[str | int], value: object,
                    expected: dict[str, object]) -> None:
    """Test writing one actual path with created containers."""
    data: dict[str, object] = {}
    rocf_mod._write_path(data, path, value)
    assert data == expected


@pytest.mark.parametrize(
    'data, path',
    [({'nested': 'bad'}, ['nested', 'value']),
     ({'items': 'bad'}, ['items', 0])])
def test_write_path_bad(data: dict[str, object],
                        path: list[str | int]) -> None:
    """Test incompatible container values while writing paths."""
    with pytest.raises(rocf_mod.RocfIncompatiblePathError):
        rocf_mod._write_path(data, path, 1)


@pytest.mark.parametrize(
    'data, path, expected_data, expected_removed',
    [({'old': 1}, ('old',), {}, ['old']),
     ({'items': [{'old': 1}, {'old': 2}]}, ('items', '[', 'old'),
      {'items': [{}, {}]}, ['items[0][old]', 'items[1][old]']),
     ({'items': [1, 2]}, ('items', '['), {'items': []},
      ['items[0]', 'items[1]']),
     ({'items': 'bad'}, ('items', '[', 'old'), {'items': 'bad'}, [])])
def test_remove_path(data: dict[str, object], path: ConfigPath,
                     expected_data: dict[str, object],
                     expected_removed: list[str]) -> None:
    """Test path-based removal rules."""
    assert rocf_mod._remove_path(data, path, []) == expected_removed
    assert data == expected_data


@pytest.mark.parametrize(
    'data, path, value, expected_data, expected_applied',
    [({}, ('name',), 'default', {'name': 'default'}, ['name']),
     ({'name': 'current'}, ('name',), 'default', {'name': 'current'}, []),
     ({}, ('meta', 'owner'), 'ops', {'meta': {'owner': 'ops'}},
      ['meta[owner]']),
     ({'items': [{}, {'name': 'b'}]}, ('items', '[', 'name'), 'a',
      {'items': [{'name': 'a'}, {'name': 'b'}]}, ['items[0][name]']),
     ({'items': [1, 2]}, ('items', '['), 'a', {'items': [1, 2]}, []),
     ({}, ('items', '[', 'name'), 'a', {}, [])])
def test_apply_missing(
        data: dict[str, object], path: ConfigPath, value: object,
        expected_data: dict[str, object], expected_applied: list[str]) -> None:
    """Test missing-value application."""
    assert rocf_mod._apply_missing(data, path, value, []) == expected_applied
    assert data == expected_data


@pytest.mark.parametrize(
    'data, path',
    [({'items': 'bad'}, ('items', '[', 'name')),
     ({'meta': 'bad'}, ('meta', 'owner'))])
def test_apply_missing_bad(data: dict[str, object], path: ConfigPath) -> None:
    """Test missing-value application through incompatible containers."""
    with pytest.raises(rocf_mod.RocfIncompatiblePathError):
        rocf_mod._apply_missing(data, path, 'value', [])


def test_private_remove_recursive_ok() -> None:
    """Test private recursive-removal method success."""
    data: dict[str, object] = {'drop': 1, 'nested': {'drop': 2}}
    hook = ConfigAutoChangeHook()
    rocf = MethodReadOldConfig()
    rocf.remove_names = ['drop']
    rocf.run_remove_recursive(data, hook)
    assert data == {'nested': {}}
    assert hook.old_keys == ['drop']


def test_priv_remove_recursive_bad() -> None:
    """Test private recursive-removal method error handling."""
    rocf = MethodReadOldConfig()
    rocf.remove_names = cast(list[str], [1])
    with pytest.raises(TypeError):
        rocf.run_remove_recursive({}, ConfigAutoChangeHook())


def test_private_remove_paths_ok() -> None:
    """Test private path-removal method success."""
    data: dict[str, object] = {'items': [{'drop': 1}, {'drop': 2}]}
    hook = ConfigAutoChangeHook()
    rocf = MethodReadOldConfig()
    rocf.remove_paths = [('items', '[', 'drop')]
    rocf.run_remove_paths(data, hook)
    assert data == {'items': [{}, {}]}
    assert hook.old_keys == ['items[0][drop]', 'items[1][drop]']


def test_private_remove_paths_bad() -> None:
    """Test private path-removal method error handling."""
    rocf = MethodReadOldConfig()
    rocf.remove_paths = [()]
    with pytest.raises(ValueError):
        rocf.run_remove_paths({}, ConfigAutoChangeHook())


def test_private_renames_ok() -> None:
    """Test private recursive-rename method success."""
    data: dict[str, object] = {'old': 1}
    hook = ConfigAutoChangeHook()
    rocf = MethodReadOldConfig()
    rocf.renames = [rocf_mod.RocfKeyRename(old='old', new='new')]
    stderr_file = StringIO()
    rocf.run_renames(data, hook, stderr_file)
    assert data == {'new': 1}
    assert hook.old_keys == ['old']
    assert_no_error(stderr_file)


def test_private_renames_bad() -> None:
    """Test private recursive-rename method error handling."""
    rocf = MethodReadOldConfig()
    rocf.renames = [rocf_mod.RocfKeyRename(old='same', new='same')]
    with pytest.raises(AssertionError):
        rocf.run_renames({}, ConfigAutoChangeHook(), StringIO())


def test_private_moves_ok() -> None:
    """Test private path-move method success."""
    data: dict[str, object] = {'old': 1}
    hook = ConfigAutoChangeHook()
    rocf = MethodReadOldConfig()
    rocf.moves = [rocf_mod.RocfKeyMove(old_path=('old',), new_path=('new',))]
    stderr_file = StringIO()
    rocf.run_moves(data, hook, stderr_file)
    assert data == {'new': 1}
    assert hook.old_paths_moved == [('old', 'new')]
    assert hook.old_keys == ['old -> new']
    assert_no_error(stderr_file)


@pytest.mark.parametrize(
    'moves, error_type',
    [([rocf_mod.RocfKeyMove(old_path=(), new_path=('new',))], ValueError),
     ([rocf_mod.RocfKeyMove(old_path=('a',), new_path=('new',)),
       rocf_mod.RocfKeyMove(old_path=('b',), new_path=('new',))],
      rocf_mod.RocfConflictError)])
def test_private_moves_bad(moves: list[rocf_mod.RocfKeyMove],
                           error_type: type[Exception]) -> None:
    """Test private path-move method error handling."""
    rocf = MethodReadOldConfig()
    rocf.moves = moves
    with pytest.raises(error_type):
        rocf.run_moves({'a': 1, 'b': 2}, ConfigAutoChangeHook(), StringIO())


def test_private_one_move_ok() -> None:
    """Test private one-path move method success."""
    data: dict[str, object] = {'old': 1}
    hook = ConfigAutoChangeHook()
    context = rocf_mod._MoveContext(
        json_data=data, written_paths=set(), auto_ch_hook=hook,
        stderr_file=StringIO())
    move = rocf_mod.RocfKeyMove(old_path=('old',), new_path=('new',))
    value = rocf_mod._MovedValue(actual_path=['old'], indexes=[], value=1)
    MethodReadOldConfig().run_one_move(context, move, value)
    assert data == {'new': 1}
    assert context.written_paths == {'new'}
    assert hook.old_keys == ['old -> new']


def test_private_one_move_bad() -> None:
    """Test private one-path move conflict handling."""
    data: dict[str, object] = {'old': 1}
    context = rocf_mod._MoveContext(
        json_data=data, written_paths={'new'},
        auto_ch_hook=ConfigAutoChangeHook(), stderr_file=StringIO())
    move = rocf_mod.RocfKeyMove(old_path=('old',), new_path=('new',))
    value = rocf_mod._MovedValue(actual_path=['old'], indexes=[], value=1)
    with pytest.raises(rocf_mod.RocfConflictError):
        MethodReadOldConfig().run_one_move(context, move, value)


@pytest.mark.parametrize(
    'data, wrap_prefix, target, expected',
    [({'old': 1, 'new': 2}, None, ['new'], True),
     ({'old': 1}, None, ['new'], False),
     ({'output': {'name': 'old'}, 'outputs': []}, ['outputs'],
      ['outputs', 0], True)])
def test_private_target_current_ok(
        data: dict[str, object], wrap_prefix: Optional[list[str | int]],
        target: list[str | int], expected: bool) -> None:
    """Test private current-target detection."""
    hook = ConfigAutoChangeHook()
    context = rocf_mod._MoveContext(
        json_data=data, written_paths=set(), auto_ch_hook=hook,
        stderr_file=StringIO())
    value = rocf_mod._MovedValue(actual_path=['old'], indexes=[], value=1)
    result = MethodReadOldConfig().run_target_current(
        context, value, wrap_prefix, target)
    assert result is expected


def test_private_target_current_bad() -> None:
    """Test private current-target detection error handling."""
    data: dict[str, object] = {'old': 1, 'outputs': 'bad'}
    context = rocf_mod._MoveContext(
        json_data=data, written_paths=set(),
        auto_ch_hook=ConfigAutoChangeHook(), stderr_file=StringIO())
    value = rocf_mod._MovedValue(actual_path=['old'], indexes=[], value=1)
    with pytest.raises(rocf_mod.RocfIncompatiblePathError):
        MethodReadOldConfig().run_target_current(
            context, value, ['outputs'], ['outputs', 0])


def test_private_missing_values_ok() -> None:
    """Test private missing-value method success."""
    data: dict[str, object] = {'items': [{}, {'name': 'b'}]}
    hook = ConfigAutoChangeHook()
    rocf = MethodReadOldConfig()
    rocf.missing = {('items', '[', 'name'): 'a', ('version',): 2}
    rocf.run_missing_values(data, hook)
    assert data == {'items': [{'name': 'a'}, {'name': 'b'}], 'version': 2}
    assert hook.rocf_val_keys == ['items[0][name]', 'version']


def test_private_missing_values_bad() -> None:
    """Test private missing-value method error handling."""
    rocf = MethodReadOldConfig()
    rocf.missing = {('items', '[', 'name'): 'a'}
    with pytest.raises(InvalidConfiguration):
        rocf.run_missing_values({'items': 'bad'}, ConfigAutoChangeHook())
