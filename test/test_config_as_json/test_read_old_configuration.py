#! /usr/local/bin/python3
"""Test ReadOldConfiguration normalization rules."""

# Copyright (c) 2026 Tom Björkholm
# MIT License

from copy import deepcopy
from io import StringIO
import pytest
from config_as_json import ConfigAutoChangeHook, ConfigPath, \
    ReadOldConfiguration, RocfConflictError, RocfIncompatiblePathError, \
    RocfKeyMove, RocfKeyRename, RocfValueMigration, RocfValueWrite


class RuleReadOldConfig(ReadOldConfiguration):
    """Read-old processor with rules injected by tests."""

    def __init__(self) -> None:
        """Store the rules this processor should return."""
        self.moves: list[RocfKeyMove] = []
        self.remove_names: list[str] = []
        self.remove_paths: list[ConfigPath] = []
        self.missing: dict[ConfigPath, object] = {}
        self.renames: list[RocfKeyRename] = []
        self.value_migrations: list[RocfValueMigration] = []

    def get_json_key_moves(self) -> list[RocfKeyMove]:
        """Return injected move rules."""
        return self.moves

    def get_value_migrations(self) -> list[RocfValueMigration]:
        """Return injected value migration rules."""
        return self.value_migrations

    def get_keys_to_prune(self) -> list[str]:
        """Return injected recursive remove keys."""
        return self.remove_names

    def get_keys_to_remove(self) -> list[ConfigPath]:
        """Return injected path remove rules."""
        return self.remove_paths

    def get_missing_path_values(self) -> dict[ConfigPath, object]:
        """Return injected missing-value rules."""
        return self.missing

    def get_json_key_renames(self) -> list[RocfKeyRename]:
        """Return injected rename rules."""
        return self.renames


class LegacyPruneReadOldConfig(ReadOldConfiguration):
    """Read-old processor using the deprecated recursive remove hook."""

    def get_keys_to_remove_recursively(self) -> list[str]:
        """Return old key names through the deprecated hook."""
        return ['drop']


class LegacyMissingReadOldConfig(ReadOldConfiguration):
    """Read-old processor using the deprecated missing-value hook."""

    def get_values_for_missing_json_keys(self) -> dict[ConfigPath, object]:
        """Return missing path values through the deprecated hook."""
        return {('version',): 2}


class LegacyPruneBase(ReadOldConfiguration):
    """Intermediate base class using the deprecated remove hook."""

    def get_keys_to_remove_recursively(self) -> list[str]:
        """Return old key names through an inherited deprecated hook."""
        return ['drop']


class LegacyPruneChild(LegacyPruneBase):
    """Read-old processor inheriting a deprecated hook override."""


class ConflictingPruneReadOldConfig(ReadOldConfiguration):
    """Read-old processor overriding both recursive remove hook names."""

    def get_keys_to_prune(self) -> list[str]:
        """Return old key names through the new hook."""
        return ['new_drop']

    def get_keys_to_remove_recursively(self) -> list[str]:
        """Return old key names through the deprecated hook."""
        return ['old_drop']


class ConflictingMissingReadOldConfig(ReadOldConfiguration):
    """Read-old processor overriding both missing-value hook names."""

    def get_missing_path_values(self) -> dict[ConfigPath, object]:
        """Return missing path values through the new hook."""
        return {('new_version',): 2}

    def get_values_for_missing_json_keys(self) -> dict[ConfigPath, object]:
        """Return missing path values through the deprecated hook."""
        return {('old_version',): 1}


def process_data(rocf: ReadOldConfiguration,
                 data: dict[str, object]) -> tuple[ConfigAutoChangeHook, str]:
    """Process test data and return the hook and diagnostics."""
    hook = ConfigAutoChangeHook()
    stderr_file = StringIO()
    rocf.process_json(data, hook, stderr_file)
    return hook, stderr_file.getvalue()


def test_depr_prune_direct_warns() -> None:
    """Deprecated recursive remove hook warns when called directly."""
    rocf = ReadOldConfiguration()
    with pytest.warns(DeprecationWarning, match='get_keys_to_prune'):
        keys = rocf.get_keys_to_remove_recursively()
    assert not keys


def test_depr_missing_direct_warns() -> None:
    """Deprecated missing-value hook warns when called directly."""
    rocf = ReadOldConfiguration()
    with pytest.warns(DeprecationWarning, match='get_missing_path_values'):
        values = rocf.get_values_for_missing_json_keys()
    assert not values


def test_legacy_prune_warns_works() -> None:
    """Deprecated recursive remove override warns and still works."""
    data: dict[str, object] = {'drop': True, 'keep': True}
    with pytest.warns(DeprecationWarning, match='get_keys_to_prune'):
        hook, err = process_data(LegacyPruneReadOldConfig(), data)
    assert data == {'keep': True}
    assert hook.old_keys == ['drop']
    assert err == ''


def test_legacy_missing_warns_works() -> None:
    """Deprecated missing-value override warns and still works."""
    data: dict[str, object] = {}
    with pytest.warns(DeprecationWarning, match='get_missing_path_values'):
        hook, err = process_data(LegacyMissingReadOldConfig(), data)
    assert data == {'version': 2}
    assert hook.rocf_val_keys == ['version']
    assert err == ''


def test_legacy_base_warns_works() -> None:
    """Deprecated overrides inherited from an app base are detected."""
    data: dict[str, object] = {'drop': True, 'keep': True}
    with pytest.warns(DeprecationWarning, match='get_keys_to_prune'):
        hook, err = process_data(LegacyPruneChild(), data)
    assert data == {'keep': True}
    assert hook.old_keys == ['drop']
    assert err == ''


def test_conflicting_prune_raise() -> None:
    """Overriding both recursive remove hook names is invalid."""
    with pytest.raises(TypeError) as exc:
        _ = process_data(ConflictingPruneReadOldConfig(), {})
    assert 'get_keys_to_remove_recursively()' in str(exc.value)
    assert 'get_keys_to_prune()' in str(exc.value)


def test_conflicting_missing_raise() -> None:
    """Overriding both missing-value hook names is invalid."""
    with pytest.raises(TypeError) as exc:
        _ = process_data(ConflictingMissingReadOldConfig(), {})
    assert 'get_values_for_missing_json_keys()' in str(exc.value)
    assert 'get_missing_path_values()' in str(exc.value)


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


def test_rename_transform_value() -> None:
    """A recursive key rename may transform the old value before writing."""

    def mode_from_old(value: object) -> str:
        """Convert an old textual mode to the current textual mode."""
        assert isinstance(value, str)
        return {'legacy': 'current'}[value]

    data: dict[str, object] = {
        'items': [{'old_mode': 'legacy'}, {'old_mode': 'legacy'}]
    }
    rocf = RuleReadOldConfig()
    rocf.renames = [
        RocfKeyRename(old='old_mode', new='mode',
                      transform_value=mode_from_old)]
    hook, err = process_data(rocf, data)
    assert data == {'items': [{'mode': 'current'}, {'mode': 'current'}]}
    assert hook.old_keys == ['old_mode']
    assert err == ''


def test_rename_transform_conflict() -> None:
    """A rename conflict discards the old value without transforming it."""

    def fail_transform(value: object) -> object:
        """Fail if a current value should have won instead."""
        _ = value
        raise AssertionError('transform should not be called')

    data: dict[str, object] = {'old_mode': 'legacy', 'mode': 'current'}
    rocf = RuleReadOldConfig()
    rocf.renames = [
        RocfKeyRename(old='old_mode', new='mode',
                      transform_value=fail_transform)]
    hook, err = process_data(rocf, data)
    assert data == {'mode': 'current'}
    assert hook.old_keys == ['old_mode']
    assert err == '\n'.join([
        'Inconsistent configuration:',
        'Both new config parameter mode and old old_mode present.',
        'Ignoring old parameter old_mode'
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
        'outputs[0][encoding]',
        'outputs[1][name]'
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
        ('outputs[0][encoding]', 'outputs[0][char_encoding]'),
        ('outputs[1][encoding]', 'outputs[1][char_encoding]')
    ]
    assert hook.old_keys == [
        'outputs[0][encoding] -> outputs[0][char_encoding]',
        'outputs[1][encoding] -> outputs[1][char_encoding]'
    ]
    assert err == ''


def test_move_transform_value() -> None:
    """A move may transform the old value before writing the current path."""

    def interval_to_seconds(value: object) -> int:
        """Convert old minute values to current second values."""
        assert isinstance(value, int)
        return value * 60

    data: dict[str, object] = {'refresh_minutes': 5}
    rocf = RuleReadOldConfig()
    rocf.moves = [
        RocfKeyMove(old_path=('refresh_minutes',),
                    new_path=('refresh_seconds',),
                    transform_value=interval_to_seconds)]
    hook, err = process_data(rocf, data)
    assert data == {'refresh_seconds': 300}
    assert hook.old_paths_moved == [
        ('refresh_minutes', 'refresh_seconds')
    ]
    assert err == ''


def test_move_transform_list_items() -> None:
    """A wildcard move transforms each old list element value."""

    def required_from_optional(value: object) -> bool:
        """Invert an old optional flag to the current required flag."""
        assert isinstance(value, bool)
        return not value

    data: dict[str, object] = {
        'sections': [{'optional': False}, {'optional': True}]
    }
    rocf = RuleReadOldConfig()
    rocf.moves = [
        RocfKeyMove(old_path=('sections', '[', 'optional'),
                    new_path=('sections', '[', 'required'),
                    transform_value=required_from_optional)]
    hook, err = process_data(rocf, data)
    assert data == {
        'sections': [{'required': True}, {'required': False}]
    }
    assert hook.old_paths_moved == [
        ('sections[0][optional]', 'sections[0][required]'),
        ('sections[1][optional]', 'sections[1][required]')
    ]
    assert err == ''


def test_move_transform_copy() -> None:
    """A move transform receives a copy so shared old data is not changed."""

    def add_current_marker(value: object) -> object:
        """Mutate and return the moved object copy."""
        assert isinstance(value, dict)
        items = value['items']
        assert isinstance(items, list)
        items.append('current')
        return value

    shared: dict[str, object] = {'items': ['old']}
    data: dict[str, object] = {'old': shared, 'alias': shared}
    rocf = RuleReadOldConfig()
    rocf.moves = [
        RocfKeyMove(old_path=('old',), new_path=('new',),
                    transform_value=add_current_marker)]
    hook, err = process_data(rocf, data)
    assert data == {
        'alias': {'items': ['old']},
        'new': {'items': ['old', 'current']}
    }
    assert hook.old_paths_moved == [('old', 'new')]
    assert err == ''


def test_move_transform_error_safe() -> None:
    """A move transform failure does not delete the old value first."""

    def fail_transform(value: object) -> object:
        """Raise the error under test."""
        _ = value
        raise RuntimeError('bad legacy value')

    data: dict[str, object] = {'old': {'value': 1}}
    original = deepcopy(data)
    rocf = RuleReadOldConfig()
    rocf.moves = [
        RocfKeyMove(old_path=('old',), new_path=('new',),
                    transform_value=fail_transform)]
    with pytest.raises(RuntimeError):
        _ = process_data(rocf, data)
    assert data == original


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


def test_move_transform_conflict() -> None:
    """A move conflict discards the old value without transforming it."""

    def fail_transform(value: object) -> object:
        """Fail if a current value should have won instead."""
        _ = value
        raise AssertionError('transform should not be called')

    data: dict[str, object] = {'old': 'legacy', 'new': 'current'}
    rocf = RuleReadOldConfig()
    rocf.moves = [
        RocfKeyMove(old_path=('old',), new_path=('new',),
                    transform_value=fail_transform)]
    hook, err = process_data(rocf, data)
    assert data == {'new': 'current'}
    assert hook.old_paths_moved == [('old', 'new')]
    assert err == '\n'.join([
        'Inconsistent configuration:',
        'Both new config parameter new and old old present.',
        'Ignoring old parameter old'
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


def test_val_mig_routes_value() -> None:
    """A value migration can route one old value to one current path."""

    def is_csv(value: object) -> bool:
        """Return whether the old format value means CSV output."""
        assert isinstance(value, str)
        return value == 'csv'

    def is_text(value: object) -> bool:
        """Return whether the old format value means text output."""
        assert isinstance(value, str)
        return value == 'text'

    def enabled_from_format(value: object) -> bool:
        """Convert any accepted old format value to an enabled flag."""
        assert isinstance(value, str)
        return bool(value)

    data: dict[str, object] = {'legacy_format': 'csv'}
    rocf = RuleReadOldConfig()
    rocf.value_migrations = [
        RocfValueMigration(
            old_path=('legacy_format',),
            writes=[
                RocfValueWrite(new_path=('csv_output', 'enabled'),
                               condition=is_csv,
                               transform_value=enabled_from_format),
                RocfValueWrite(new_path=('text_output', 'enabled'),
                               condition=is_text,
                               transform_value=enabled_from_format)])]
    hook, err = process_data(rocf, data)
    assert data == {'csv_output': {'enabled': True}}
    assert hook.old_paths_moved == [
        ('legacy_format', 'csv_output[enabled]')
    ]
    assert hook.old_keys == ['legacy_format -> csv_output[enabled]']
    assert err == ''


def test_val_mig_splits_value() -> None:
    """A value migration can split one old object into several values."""

    def attempts_from_retry(value: object) -> int:
        """Return current max attempts from an old retry object."""
        assert isinstance(value, dict)
        attempts = value['attempts']
        assert isinstance(attempts, int)
        return attempts

    def delay_from_retry(value: object) -> int:
        """Return current delay seconds from an old retry object."""
        assert isinstance(value, dict)
        delay_minutes = value['delay_minutes']
        assert isinstance(delay_minutes, int)
        return delay_minutes * 60

    data: dict[str, object] = {
        'retry': {'attempts': 3, 'delay_minutes': 2}
    }
    rocf = RuleReadOldConfig()
    rocf.value_migrations = [
        RocfValueMigration(
            old_path=('retry',),
            writes=[
                RocfValueWrite(new_path=('retry_policy', 'max_attempts'),
                               transform_value=attempts_from_retry),
                RocfValueWrite(new_path=('retry_policy', 'delay_seconds'),
                               transform_value=delay_from_retry)])]
    hook, err = process_data(rocf, data)
    assert data == {
        'retry_policy': {'max_attempts': 3, 'delay_seconds': 120}
    }
    assert hook.old_paths_moved == [
        ('retry', 'retry_policy[max_attempts]'),
        ('retry', 'retry_policy[delay_seconds]')
    ]
    assert err == ''


def test_val_mig_conflict_skips() -> None:
    """Current values win before value-migration callbacks are called."""

    def fail_condition(value: object) -> bool:
        """Fail if conflict detection did not happen first."""
        _ = value
        raise AssertionError('condition should not be called')

    def fail_transform(value: object) -> object:
        """Fail if conflict detection did not happen first."""
        _ = value
        raise AssertionError('transform should not be called')

    data: dict[str, object] = {
        'legacy_format': 'csv',
        'csv_output': {'enabled': False}
    }
    rocf = RuleReadOldConfig()
    rocf.value_migrations = [
        RocfValueMigration(
            old_path=('legacy_format',),
            writes=[
                RocfValueWrite(new_path=('csv_output', 'enabled'),
                               condition=fail_condition,
                               transform_value=fail_transform),
                RocfValueWrite(new_path=('text_output', 'enabled'),
                               condition=fail_condition,
                               transform_value=fail_transform)])]
    hook, err = process_data(rocf, data)
    assert data == {'csv_output': {'enabled': False}}
    assert hook.old_keys == ['legacy_format']
    assert not hook.old_paths_moved
    assert err == '\n'.join([
        'Inconsistent configuration:',
        'Both new config parameter one of csv_output[enabled], '
        'text_output[enabled] and old legacy_format present.',
        'Existing current parameter(s): csv_output[enabled]',
        'Ignoring old parameter legacy_format'
    ]) + '\n'


def test_val_mig_no_write_handles() -> None:
    """A value migration removes the old value when no write applies."""

    def never(value: object) -> bool:
        """Return False for the no-write test case."""
        _ = value
        return False

    data: dict[str, object] = {'legacy_format': 'unknown'}
    rocf = RuleReadOldConfig()
    rocf.value_migrations = [
        RocfValueMigration(
            old_path=('legacy_format',),
            writes=[RocfValueWrite(new_path=('format',), condition=never)])]
    hook, err = process_data(rocf, data)
    assert not data
    assert hook.old_keys == ['legacy_format']
    assert not hook.old_paths_moved
    assert err == ''


def test_val_mig_empty_writes() -> None:
    """A value migration with no writes accepts and removes old data."""
    data: dict[str, object] = {'obsolete': True}
    rocf = RuleReadOldConfig()
    rocf.value_migrations = [
        RocfValueMigration(old_path=('obsolete',), writes=[])]
    hook, err = process_data(rocf, data)
    assert not data
    assert hook.old_keys == ['obsolete']
    assert err == ''


def test_val_mig_callbacks_copy() -> None:
    """Each value-migration callback gets an independent old value copy."""

    def condition_mutates(value: object) -> bool:
        """Mutate the condition copy and accept the migration."""
        assert isinstance(value, dict)
        items = value['items']
        assert isinstance(items, list)
        items.append('condition')
        return True

    def transform_mutates(value: object) -> object:
        """Mutate and return the transform copy."""
        assert isinstance(value, dict)
        items = value['items']
        assert isinstance(items, list)
        items.append('transform')
        return value

    shared: dict[str, object] = {'items': ['old']}
    data: dict[str, object] = {'legacy': shared, 'alias': shared}
    rocf = RuleReadOldConfig()
    rocf.value_migrations = [
        RocfValueMigration(
            old_path=('legacy',),
            writes=[RocfValueWrite(new_path=('current',),
                                   condition=condition_mutates,
                                   transform_value=transform_mutates)])]
    hook, err = process_data(rocf, data)
    assert data == {
        'alias': {'items': ['old']},
        'current': {'items': ['old', 'transform']}
    }
    assert hook.old_paths_moved == [('legacy', 'current')]
    assert err == ''


def test_val_mig_error_safe() -> None:
    """A transform failure leaves the actual old value unchanged."""

    def fail_transform(value: object) -> object:
        """Raise the error used by this test."""
        _ = value
        raise RuntimeError('bad old value')

    data: dict[str, object] = {'legacy': {'value': 1}}
    original = deepcopy(data)
    rocf = RuleReadOldConfig()
    rocf.value_migrations = [
        RocfValueMigration(
            old_path=('legacy',),
            writes=[RocfValueWrite(new_path=('current',),
                                   transform_value=fail_transform)])]
    with pytest.raises(RuntimeError):
        _ = process_data(rocf, data)
    assert data == original


def test_val_mig_bad_target_safe() -> None:
    """An incompatible write path leaves the old value unchanged."""
    data: dict[str, object] = {'legacy': 1, 'current': 'bad'}
    original = deepcopy(data)
    rocf = RuleReadOldConfig()
    rocf.value_migrations = [
        RocfValueMigration(
            old_path=('legacy',),
            writes=[RocfValueWrite(new_path=('current', 'value'))])]
    with pytest.raises(RocfIncompatiblePathError):
        _ = process_data(rocf, data)
    assert data == original


def test_val_mig_list_items() -> None:
    """A value migration can handle each old list item separately."""

    def is_file(value: object) -> bool:
        """Return whether one old output kind means file output."""
        assert isinstance(value, str)
        return value == 'file'

    def is_stream(value: object) -> bool:
        """Return whether one old output kind means stream output."""
        assert isinstance(value, str)
        return value == 'stream'

    def standard_name(value: object) -> str:
        """Return a deterministic name for the selected output kind."""
        assert isinstance(value, str)
        return value + '-main'

    data: dict[str, object] = {
        'outputs': [{'legacy_kind': 'file'}, {'legacy_kind': 'stream'}]
    }
    rocf = RuleReadOldConfig()
    rocf.value_migrations = [
        RocfValueMigration(
            old_path=('outputs', '[', 'legacy_kind'),
            writes=[
                RocfValueWrite(new_path=('outputs', '[', 'file_name'),
                               condition=is_file,
                               transform_value=standard_name),
                RocfValueWrite(new_path=('outputs', '[', 'stream_name'),
                               condition=is_stream,
                               transform_value=standard_name)])]
    hook, err = process_data(rocf, data)
    assert data == {
        'outputs': [{'file_name': 'file-main'},
                    {'stream_name': 'stream-main'}]
    }
    assert hook.old_paths_moved == [
        ('outputs[0][legacy_kind]', 'outputs[0][file_name]'),
        ('outputs[1][legacy_kind]', 'outputs[1][stream_name]')
    ]
    assert err == ''


def test_val_mig_wraps_list() -> None:
    """A non-list old value can be migrated into a new current list."""
    data: dict[str, object] = {'legacy_output': 'main'}
    rocf = RuleReadOldConfig()
    rocf.value_migrations = [
        RocfValueMigration(
            old_path=('legacy_output',),
            writes=[RocfValueWrite(new_path=('outputs', '[', 'name'))])]
    hook, err = process_data(rocf, data)
    assert data == {'outputs': [{'name': 'main'}]}
    assert hook.old_paths_moved == [
        ('legacy_output', 'outputs[0][name]')
    ]
    assert err == ''


def test_val_mig_current_list_wins() -> None:
    """An existing current list wins over a scalar-to-list migration."""

    def fail_transform(value: object) -> object:
        """Fail if the current list conflict was not found first."""
        _ = value
        raise AssertionError('transform should not be called')

    data: dict[str, object] = {'legacy_output': 'main', 'outputs': []}
    rocf = RuleReadOldConfig()
    rocf.value_migrations = [
        RocfValueMigration(
            old_path=('legacy_output',),
            writes=[RocfValueWrite(new_path=('outputs', '[', 'name'),
                                   transform_value=fail_transform)])]
    hook, err = process_data(rocf, data)
    assert data == {'outputs': []}
    assert hook.old_keys == ['legacy_output']
    assert err == '\n'.join([
        'Inconsistent configuration:',
        'Both new config parameter outputs[0][name] and old legacy_output '
        'present.',
        'Existing current parameter(s): outputs',
        'Ignoring old parameter legacy_output'
    ]) + '\n'


def test_val_mig_dup_targets_raise() -> None:
    """Two writes in one value migration cannot target the same path."""
    data: dict[str, object] = {'legacy': 1}
    original = deepcopy(data)
    rocf = RuleReadOldConfig()
    rocf.value_migrations = [
        RocfValueMigration(
            old_path=('legacy',),
            writes=[RocfValueWrite(new_path=('current',)),
                    RocfValueWrite(new_path=('current',))])]
    with pytest.raises(RocfConflictError):
        _ = process_data(rocf, data)
    assert data == original


@pytest.mark.parametrize(
    'migration',
    [RocfValueMigration(old_path=(), writes=[]),
     RocfValueMigration(old_path=('old',),
                        writes=[RocfValueWrite(new_path=('[1',))]),
     RocfValueMigration(old_path=('items', '[', 'old'),
                        writes=[RocfValueWrite(new_path=('current',))])])
def test_invalid_val_migrations(migration: RocfValueMigration) -> None:
    """Invalid value migration path syntax is rejected."""
    data: dict[str, object] = {'old': 1, 'items': [{'old': 2}]}
    original = deepcopy(data)
    rocf = RuleReadOldConfig()
    rocf.value_migrations = [migration]
    with pytest.raises(ValueError):
        _ = process_data(rocf, data)
    assert data == original


def test_val_mig_move_missing_order() -> None:
    """Value migrations run after moves and before missing values."""

    def is_fast(value: object) -> bool:
        """Return whether the old mode asks for fast mode."""
        assert isinstance(value, str)
        return value == 'fast'

    def to_true(value: object) -> bool:
        """Convert any accepted old mode value to True."""
        assert isinstance(value, str)
        return bool(value)

    data: dict[str, object] = {'old_mode': 'fast'}
    rocf = RuleReadOldConfig()
    rocf.moves = [RocfKeyMove(old_path=('old_mode',),
                              new_path=('legacy_mode',))]
    rocf.value_migrations = [
        RocfValueMigration(
            old_path=('legacy_mode',),
            writes=[RocfValueWrite(new_path=('fast_mode',), condition=is_fast,
                                   transform_value=to_true)])]
    rocf.missing = {('fast_mode',): False, ('slow_mode',): False}
    hook, err = process_data(rocf, data)
    assert data == {'fast_mode': True, 'slow_mode': False}
    assert hook.old_paths_moved == [
        ('old_mode', 'legacy_mode'),
        ('legacy_mode', 'fast_mode')
    ]
    assert hook.rocf_val_keys == ['slow_mode']
    assert err == ''
