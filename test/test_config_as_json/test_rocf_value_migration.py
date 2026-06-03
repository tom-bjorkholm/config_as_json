#! /usr/local/bin/python3
"""Test RocfValueMigration corner cases."""

# Copyright (c) 2026 Tom Björkholm
# MIT License

from copy import deepcopy
import pytest
from config_as_json import RocfConflictError, RocfValueMigration, \
    RocfValueWrite
from .test_read_old_configuration import RuleReadOldConfig, process_data


def test_val_mig_old_absent() -> None:
    """A value migration is a no-op when the old path is missing."""

    def fail_condition(value: object) -> bool:
        """Fail if a missing old path still calls application code."""
        _ = value
        raise AssertionError('condition should not be called')

    def fail_transform(value: object) -> object:
        """Fail if a missing old path still calls application code."""
        _ = value
        raise AssertionError('transform should not be called')

    data: dict[str, object] = {'current': 1}
    original = deepcopy(data)
    rocf = RuleReadOldConfig()
    rocf.value_migrations = [
        RocfValueMigration(old_path=('old',),
                           writes=[
                               RocfValueWrite(new_path=('current',),
                                              condition=fail_condition,
                                              transform_value=fail_transform)
                           ])]
    hook, err = process_data(rocf, data)
    assert data == original
    assert not hook.old_keys
    assert not hook.old_paths_moved
    assert err == ''


def test_val_mig_bad_old_type() -> None:
    """Wrong container types while finding the old path are ignored."""

    def fail_transform(value: object) -> object:
        """Fail if an unreachable old list member is transformed."""
        _ = value
        raise AssertionError('transform should not be called')

    data: dict[str, object] = {'items': 'already-current'}
    original = deepcopy(data)
    rocf = RuleReadOldConfig()
    rocf.value_migrations = [
        RocfValueMigration(old_path=('items', '[', 'legacy'),
                           writes=[
                               RocfValueWrite(
                                   new_path=('items', '[', 'current'),
                                   transform_value=fail_transform)])]
    hook, err = process_data(rocf, data)
    assert data == original
    assert not hook.old_keys
    assert not hook.old_paths_moved
    assert err == ''


def test_val_mig_cond_error() -> None:
    """A condition failure leaves the old value and current data untouched."""

    def fail_condition(value: object) -> bool:
        """Raise the condition error under test."""
        _ = value
        raise RuntimeError('bad condition')

    def fail_transform(value: object) -> object:
        """Fail if transform runs after a condition error."""
        _ = value
        raise AssertionError('transform should not be called')

    data: dict[str, object] = {'legacy': {'value': 1}}
    original = deepcopy(data)
    rocf = RuleReadOldConfig()
    rocf.value_migrations = [
        RocfValueMigration(old_path=('legacy',),
                           writes=[
                               RocfValueWrite(new_path=('current',),
                                              condition=fail_condition,
                                              transform_value=fail_transform)
                           ])]
    with pytest.raises(RuntimeError):
        _ = process_data(rocf, data)
    assert data == original


def test_val_mig_split_error() -> None:
    """A later transform failure prevents all writes from the old value."""

    def first_value(value: object) -> int:
        """Return the first value that would be written."""
        assert isinstance(value, dict)
        return 1

    def fail_transform(value: object) -> object:
        """Raise the second transform error under test."""
        _ = value
        raise RuntimeError('bad split')

    data: dict[str, object] = {'legacy': {'value': 1}}
    original = deepcopy(data)
    rocf = RuleReadOldConfig()
    rocf.value_migrations = [
        RocfValueMigration(old_path=('legacy',),
                           writes=[
                               RocfValueWrite(new_path=('first',),
                                              transform_value=first_value),
                               RocfValueWrite(new_path=('second',),
                                              transform_value=fail_transform)
                           ])]
    with pytest.raises(RuntimeError):
        _ = process_data(rocf, data)
    assert data == original


def test_val_mig_none_write() -> None:
    """A transformed None value is a real current value."""

    def to_none(value: object) -> object:
        """Return None as the migrated current value."""
        _ = value
        result: object = None
        return result

    data: dict[str, object] = {'legacy': 'set-to-none'}
    rocf = RuleReadOldConfig()
    rocf.value_migrations = [
        RocfValueMigration(old_path=('legacy',),
                           writes=[
                               RocfValueWrite(new_path=('current',),
                                              transform_value=to_none)])]
    hook, err = process_data(rocf, data)
    assert data == {'current': None}
    assert hook.old_paths_moved == [('legacy', 'current')]
    assert err == ''


def test_val_mig_none_current() -> None:
    """An existing current None value wins over an old value."""

    def fail_transform(value: object) -> object:
        """Fail if an existing None is treated as missing."""
        _ = value
        raise AssertionError('transform should not be called')

    data: dict[str, object] = {'legacy': 'old', 'current': None}
    rocf = RuleReadOldConfig()
    rocf.value_migrations = [
        RocfValueMigration(old_path=('legacy',),
                           writes=[
                               RocfValueWrite(new_path=('current',),
                                              transform_value=fail_transform)
                           ])]
    hook, err = process_data(rocf, data)
    assert data == {'current': None}
    assert hook.old_keys == ['legacy']
    assert not hook.old_paths_moved
    assert err == '\n'.join([
        'Inconsistent configuration:',
        'Both new config parameter current and old legacy present.',
        'Existing current parameter(s): current',
        'Ignoring old parameter legacy'
    ]) + '\n'


def test_val_mig_wrap_wins() -> None:
    """An existing current list wins before write conditions are called."""

    def fail_condition(value: object) -> bool:
        """Fail if wrap-list conflict detection calls the condition."""
        _ = value
        raise AssertionError('condition should not be called')

    data: dict[str, object] = {'legacy': 'old', 'items': []}
    rocf = RuleReadOldConfig()
    rocf.value_migrations = [
        RocfValueMigration(old_path=('legacy',),
                           writes=[
                               RocfValueWrite(new_path=('items', '[', 'name'),
                                              condition=fail_condition)])]
    hook, err = process_data(rocf, data)
    assert data == {'items': []}
    assert hook.old_keys == ['legacy']
    assert err == '\n'.join([
        'Inconsistent configuration:',
        'Both new config parameter items[0][name] and old legacy present.',
        'Existing current parameter(s): items',
        'Ignoring old parameter legacy'
    ]) + '\n'


def test_val_mig_same_target() -> None:
    """Two value migrations cannot both write the same current target."""
    data: dict[str, object] = {'first': 1, 'second': 2}
    rocf = RuleReadOldConfig()
    rocf.value_migrations = [
        RocfValueMigration(old_path=('first',),
                           writes=[RocfValueWrite(new_path=('current',))]),
        RocfValueMigration(old_path=('second',),
                           writes=[RocfValueWrite(new_path=('current',))])]
    with pytest.raises(RocfConflictError):
        _ = process_data(rocf, data)
    assert data == {'second': 2, 'current': 1}


def test_val_mig_item_same() -> None:
    """Whole old list elements can be transformed in place by index."""

    def double_value(value: object) -> int:
        """Double one old list value."""
        assert isinstance(value, int)
        return value * 2

    data: dict[str, object] = {'items': [1, 2]}
    rocf = RuleReadOldConfig()
    rocf.value_migrations = [
        RocfValueMigration(old_path=('items', '['),
                           writes=[
                               RocfValueWrite(new_path=('items', '['),
                                              transform_value=double_value)])]
    hook, err = process_data(rocf, data)
    assert data == {'items': [2, 4]}
    assert sorted(hook.old_paths_moved) == [
        ('items[0]', 'items[0]'),
        ('items[1]', 'items[1]')
    ]
    assert err == ''


def test_val_mig_item_to_dict() -> None:
    """Whole old list elements can produce fields in the same list slot."""
    data: dict[str, object] = {'items': ['alpha', 'beta']}
    rocf = RuleReadOldConfig()
    rocf.value_migrations = [
        RocfValueMigration(old_path=('items', '['),
                           writes=[
                               RocfValueWrite(
                                   new_path=('items', '[', 'name'))])]
    hook, err = process_data(rocf, data)
    assert data == {'items': [{'name': 'alpha'}, {'name': 'beta'}]}
    assert sorted(hook.old_paths_moved) == [
        ('items[0]', 'items[0][name]'),
        ('items[1]', 'items[1][name]')
    ]
    assert err == ''
