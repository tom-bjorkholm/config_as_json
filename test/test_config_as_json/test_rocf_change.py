#! /usr/local/bin/python3
"""Test detailed automatic change records and how they are reported."""

# Copyright (c) 2026 Tom Björkholm
# MIT License

import sys
from io import StringIO
from typing import Optional, TextIO, override
import pytest
from config_as_json import Config, ConfigAutoChangeHook, ConfigNesting, \
    ConfigNestingKind, HookDataVersionError, NestedConfigs, PathOrStr, \
    ReadOldConfiguration, RocfChange, RocfChangeKind, RocfKeyMove, \
    RocfKeyRename, RocfValueMigration, RocfValueWrite, ValidationPlan
from .test_read_old_configuration import RuleReadOldConfig, process_data


def _is_fast(value: object) -> bool:
    """Return whether an old mode value selects the fast current mode."""
    return value == 'fast'


def test_change_key_pruned() -> None:
    """A recursive prune records the actual path of every removal."""
    rocf = RuleReadOldConfig()
    rocf.remove_names = ['drop']
    hook, _ = process_data(rocf, {'drop': 1, 'items': [{'drop': 2}]})
    assert hook.changes == [
        RocfChange(RocfChangeKind.KEY_PRUNED, 'drop', None),
        RocfChange(RocfChangeKind.KEY_PRUNED, 'items[0][drop]', None)]
    assert hook.old_keys == ['drop']


def test_change_path_removed() -> None:
    """A path removal records one change per actual removed path."""
    rocf = RuleReadOldConfig()
    rocf.remove_paths = [('sections', '[', 'stale')]
    hook, _ = process_data(rocf, {'sections': [{'stale': 1}, {'stale': 2}]})
    assert hook.changes == [
        RocfChange(RocfChangeKind.PATH_REMOVED, 'sections[0][stale]', None),
        RocfChange(RocfChangeKind.PATH_REMOVED, 'sections[1][stale]', None)]
    assert hook.old_keys == ['sections[0][stale]', 'sections[1][stale]']


def test_change_key_renamed() -> None:
    """A recursive rename records both actual paths of every rename."""
    rocf = RuleReadOldConfig()
    rocf.renames = [RocfKeyRename(old='title', new='report_name')]
    hook, _ = process_data(rocf, {'title': 'a', 'items': [{'title': 'b'}]})
    assert hook.changes == [
        RocfChange(RocfChangeKind.KEY_RENAMED, 'title', 'report_name'),
        RocfChange(RocfChangeKind.KEY_RENAMED, 'items[0][title]',
                   'items[0][report_name]')]
    assert hook.old_keys == ['title']


def test_change_rename_discarded() -> None:
    """An existing current key name discards the old value."""
    rocf = RuleReadOldConfig()
    rocf.renames = [RocfKeyRename(old='title', new='report_name')]
    hook, err = process_data(rocf, {'title': 'a', 'report_name': 'b'})
    assert hook.changes == [
        RocfChange(RocfChangeKind.OLD_VALUE_DISCARDED, 'title', None)]
    assert 'Ignoring old parameter title' in err


def test_change_path_moved() -> None:
    """A move records the actual old path and the actual current path."""
    rocf = RuleReadOldConfig()
    rocf.moves = [RocfKeyMove(old_path=('output',), new_path=('outputs', '['))]
    hook, _ = process_data(rocf, {'output': {'file': 'a.csv'}})
    assert hook.changes == [
        RocfChange(RocfChangeKind.PATH_MOVED, 'output', 'outputs[0]')]
    assert hook.old_paths_moved == [('output', 'outputs[0]')]


def test_change_move_discarded() -> None:
    """An existing current value wins over an old value that could move."""
    rocf = RuleReadOldConfig()
    rocf.moves = [RocfKeyMove(old_path=('old_name',),
                              new_path=('report_name',))]
    hook, err = process_data(rocf, {'old_name': 'a', 'report_name': 'b'})
    assert hook.changes == [
        RocfChange(RocfChangeKind.OLD_VALUE_DISCARDED, 'old_name',
                   'report_name')]
    assert hook.old_paths_moved == [('old_name', 'report_name')]
    assert 'Ignoring old parameter old_name' in err


def test_change_value_migrated() -> None:
    """A value migration write is recorded as a migrated value."""
    rocf = RuleReadOldConfig()
    rocf.value_migrations = [RocfValueMigration(
        old_path=('old_mode',), writes=[RocfValueWrite(new_path=('mode',))])]
    hook, _ = process_data(rocf, {'old_mode': 'fast'})
    assert hook.changes == [
        RocfChange(RocfChangeKind.VALUE_MIGRATED, 'old_mode', 'mode')]
    assert hook.old_paths_moved == [('old_mode', 'mode')]


@pytest.mark.parametrize('data, expected_new',
                         [({'old_mode': 'fast', 'mode': 'slow'}, 'mode'),
                          ({'old_mode': 'skip'}, None)])
def test_change_migration_discard(data: dict[str, object],
                                  expected_new: Optional[str]) -> None:
    """A value migration that writes nothing discards the old value."""
    rocf = RuleReadOldConfig()
    rocf.value_migrations = [RocfValueMigration(
        old_path=('old_mode',),
        writes=[RocfValueWrite(new_path=('mode',), condition=_is_fast)])]
    hook, _ = process_data(rocf, data)
    assert hook.changes == [
        RocfChange(RocfChangeKind.OLD_VALUE_DISCARDED, 'old_mode',
                   expected_new)]
    assert hook.old_keys == ['old_mode']


def test_change_missing_value() -> None:
    """A supplied missing value records the current path and the value."""
    rocf = RuleReadOldConfig()
    rocf.missing = {('format_version',): 2}
    hook, _ = process_data(rocf, {'other': 1})
    assert hook.changes == [
        RocfChange(RocfChangeKind.MISSING_VALUE_ADDED, None, 'format_version',
                   2)]
    assert hook.rocf_val_keys == ['format_version']


def test_missing_value_is_copied() -> None:
    """The recorded missing value does not alias the configuration data."""
    rocf = RuleReadOldConfig()
    declared: list[int] = [1, 2]
    rocf.missing = {('numbers',): declared}
    hook, _ = process_data(rocf, {'other': 1})
    declared.append(3)
    assert hook.changes[0].value == [1, 2]


def test_legacy_entry_points() -> None:
    """The legacy recording methods also produce detailed records."""
    hook = ConfigAutoChangeHook()
    hook.old_key_handled('old_key')
    hook.rocf_missing_value_provided('new_key')
    hook.old_path_moved('a', 'b')
    assert hook.changes == [
        RocfChange(RocfChangeKind.OLD_KEY_HANDLED, 'old_key', None),
        RocfChange(RocfChangeKind.MISSING_VALUE_ADDED, None, 'new_key'),
        RocfChange(RocfChangeKind.PATH_MOVED, 'a', 'b')]
    assert hook.old_keys == ['old_key', 'a -> b']
    assert hook.rocf_val_keys == ['new_key']
    assert hook.old_paths_moved == [('a', 'b')]


def test_print_changes_empty() -> None:
    """Nothing is printed when no automatic change was recorded."""
    out = StringIO()
    ConfigAutoChangeHook().print_changes(stderr_file=out)
    assert out.getvalue() == ''


def test_print_changes_report() -> None:
    """Every recorded change kind gets one readable report line."""
    hook = ConfigAutoChangeHook()
    hook.key_pruned(key='drop', at_paths=['items[0][drop]'])
    hook.path_removed(path='stale')
    hook.key_renamed(old_key='title', at_paths=[('title', 'report_name')])
    hook.old_path_moved(old_path='output', new_path='outputs[0]')
    hook.value_migrated(old_path='old_mode', new_path='mode')
    hook.move_discarded(old_path='old_name', new_path='report_name')
    hook.migration_discarded(old_path='gone', new_paths=[])
    hook.missing_value_added(path='format_version', value=2)
    hook.old_key_handled('handled_by_app')
    out = StringIO()
    hook.print_changes(stderr_file=out)
    assert out.getvalue() == '\n'.join([
        'Automatic configuration changes were applied:',
        '  pruned old key   items[0][drop]',
        '  removed old path stale',
        '  renamed key      title -> report_name',
        '  moved value      output -> outputs[0]',
        '  migrated value   old_mode -> mode',
        '  discarded old    old_name (current report_name wins)',
        '  discarded old    gone',
        '  supplied value   format_version = 2',
        '  handled old key  handled_by_app']) + '\n'


def test_check_data_version_ok() -> None:
    """The version the library records is accepted."""
    version = ConfigAutoChangeHook.DATA_STRUCTURE_VERSION
    ConfigAutoChangeHook.check_data_version(written_for=version)


def test_check_data_version_bad() -> None:
    """A derived class written for another version is rejected."""
    version = ConfigAutoChangeHook.DATA_STRUCTURE_VERSION
    with pytest.raises(HookDataVersionError, match='ConfigAutoChangeHook'):
        ConfigAutoChangeHook.check_data_version(written_for=version + 1)


def test_clear_and_has_changes() -> None:
    """Clearing empties every recorded member of the hook."""
    hook = ConfigAutoChangeHook()
    assert not hook.has_changes()
    hook.old_path_moved(old_path='a', new_path='b')
    hook.missing_value_added(path='c', value=1)
    assert hook.has_changes()
    hook.clear()
    assert not hook.has_changes()
    assert not hook.changes
    assert not hook.old_keys
    assert not hook.rocf_val_keys
    assert not hook.old_paths_moved


@pytest.mark.parametrize(
    'nested_path, expected',
    [('char_encoding', 'outputs[0][char_encoding]'),
     ('csv_params[delimiter]', 'outputs[0][csv_params][delimiter]')])
def test_merge_nested_paths(nested_path: str, expected: str) -> None:
    """Nested paths become absolute paths in the parent configuration."""
    nested = ConfigAutoChangeHook()
    nested.path_removed(path=nested_path)
    parent = ConfigAutoChangeHook()
    parent.merge_nested(nested=nested, path_prefix='outputs[0]')
    assert parent.changes == [
        RocfChange(RocfChangeKind.PATH_REMOVED, expected, None)]
    assert parent.old_keys == [expected]


def test_merge_nested_legacy() -> None:
    """Merged nested changes also reach the backward-compatible members."""
    nested = ConfigAutoChangeHook()
    nested.old_path_moved(old_path='old', new_path='new')
    nested.missing_value_added(path='version', value=2)
    parent = ConfigAutoChangeHook()
    parent.merge_nested(nested=nested, path_prefix='child')
    assert parent.old_paths_moved == [('child[old]', 'child[new]')]
    assert parent.old_keys == ['child[old] -> child[new]']
    assert parent.rocf_val_keys == ['child[version]']


def test_merge_nested_into_itself() -> None:
    """Merging a hook into itself records nothing extra."""
    hook = ConfigAutoChangeHook()
    hook.path_removed(path='stale')
    hook.merge_nested(nested=hook, path_prefix='outputs[0]')
    assert hook.changes == [
        RocfChange(RocfChangeKind.PATH_REMOVED, 'stale', None)]


class NestedOldConfig(ReadOldConfiguration):
    """Old-file rules for the nested section used in these tests."""

    def get_json_key_renames(self) -> list[RocfKeyRename]:
        """Return the old nested key name and its current name."""
        return [RocfKeyRename(old='encoding', new='char_encoding')]


class TopOldConfig(ReadOldConfiguration):
    """Old-file rules for the top-level shape used in these tests."""

    def get_json_key_renames(self) -> list[RocfKeyRename]:
        """Return the old top-level key name and its current name."""
        return [RocfKeyRename(old='title', new='report_name')]


class OutputSection(Config):
    """Nested configuration section with old-file rules of its own."""

    def __init__(self, from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 stderr_file: TextIO = sys.stderr) -> None:
        """Construct the nested output section."""
        self.char_encoding: str = 'UTF-8'
        super().__init__(from_json_data_text=from_json_data_text,
                         from_json_filename=from_json_filename,
                         stderr_file=stderr_file)

    def _get_read_old_config(self) -> ReadOldConfiguration:
        """Return the old-file rules for this nested section."""
        return NestedOldConfig()

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Return no extra validation for this test shape."""
        _ = stderr_file
        return []


class TopConfig(Config):
    """Top-level configuration owning one nested section."""

    def __init__(self, from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 auto_ch_hook: Optional[ConfigAutoChangeHook] = None,
                 stderr_file: TextIO = sys.stderr) -> None:
        """Construct the top-level configuration."""
        self.report_name: str = 'daily'
        self.output: OutputSection = OutputSection(stderr_file=stderr_file)
        super().__init__(from_json_data_text=from_json_data_text,
                         from_json_filename=from_json_filename,
                         auto_ch_hook=auto_ch_hook, stderr_file=stderr_file)

    @override
    def nested_configs(self) -> NestedConfigs:
        """Return the nested section declaration."""
        return {'output': ConfigNesting(kind=ConfigNestingKind.MEMBER,
                                        config_type=OutputSection)}

    def _get_read_old_config(self) -> ReadOldConfiguration:
        """Return the old-file rules for the top-level shape."""
        return TopOldConfig()

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Return no extra validation for this test shape."""
        _ = stderr_file
        return []


class CallRecordHook(ConfigAutoChangeHook):
    """Hook recording the old keys reported to each auto_changed call."""

    def __init__(self) -> None:
        """Initialize empty call recording state."""
        super().__init__()
        self.calls: list[list[str]] = []

    @override
    def clear(self) -> None:
        """Clear the recorded calls together with the recorded changes."""
        self.calls.clear()
        super().clear()

    def auto_changed(self, old_keys_handled: list[str],
                     rocf_vals_handled: list[str],
                     stderr_file: TextIO) -> None:
        """Record the old keys reported by this call."""
        _ = rocf_vals_handled, stderr_file
        self.calls.append(old_keys_handled)


OLD_JSON = '{"title": "old", "output": {"encoding": "latin-1"}}'
NEW_JSON = '{"report_name": "new", "output": {"char_encoding": "UTF-8"}}'


def test_hook_is_not_copied() -> None:
    """The hook object the application owns receives the recorded changes."""
    hook = ConfigAutoChangeHook()
    cfg = TopConfig(from_json_data_text=OLD_JSON, auto_ch_hook=hook,
                    stderr_file=StringIO())
    assert cfg.auto_change_hook() is hook
    assert hook.old_keys == ['title', 'output[encoding]']


def test_nested_changes_reported() -> None:
    """Old-file changes inside a nested Config reach the top-level hook."""
    hook = ConfigAutoChangeHook()
    _ = TopConfig(from_json_data_text=OLD_JSON, auto_ch_hook=hook,
                  stderr_file=StringIO())
    assert hook.changes == [
        RocfChange(RocfChangeKind.KEY_RENAMED, 'title', 'report_name'),
        RocfChange(RocfChangeKind.KEY_RENAMED, 'output[encoding]',
                   'output[char_encoding]')]


def test_auto_changed_has_nested() -> None:
    """The backward-compatible callback also reports nested changes."""
    hook = CallRecordHook()
    _ = TopConfig(from_json_data_text=OLD_JSON, auto_ch_hook=hook,
                  stderr_file=StringIO())
    assert hook.calls == [['title', 'output[encoding]']]


def test_reused_hook_two_objects() -> None:
    """One hook used for two Config objects reports the latest parse only."""
    hook = ConfigAutoChangeHook()
    _ = TopConfig(from_json_data_text=OLD_JSON, auto_ch_hook=hook,
                  stderr_file=StringIO())
    assert hook.has_changes()
    cfg = TopConfig(from_json_data_text=NEW_JSON, auto_ch_hook=hook,
                    stderr_file=StringIO())
    assert not hook.has_changes()
    assert cfg.report_name == 'new'


def test_reparse_same_object() -> None:
    """Parsing twice on one Config object reports the latest parse only."""
    hook = ConfigAutoChangeHook()
    cfg = TopConfig(from_json_data_text=OLD_JSON, auto_ch_hook=hook,
                    stderr_file=StringIO())
    cfg.parse_json(NEW_JSON, stderr_file=StringIO())
    assert not hook.changes
    assert cfg.report_name == 'new'
