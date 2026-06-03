#! /usr/local/bin/python3
"""Define declarative ROCF rules for value-producing migrations.

Application code can use these small rule objects when one old
configuration value needs to produce zero, one or several current JSON
values. The processing code in this module applies those rules while reading
old configuration files.
"""

# Copyright (c) 2026 Tom Björkholm
# MIT License

from copy import deepcopy
from typing import Callable, NamedTuple, Optional, Sequence, TextIO, cast
from config_as_json.config_auto_change_hook import ConfigAutoChangeHook
from config_as_json.commontypes import ConfigPath
from config_as_json.validator import InvalidConfiguration


class RocfConflictError(InvalidConfiguration):
    """Raised when several old-file rules write one current path.

    Application code may declare several compatibility rules with the same
    current path when one current configuration version can read files from
    more than one older version. The library raises this exception only if
    more than one old value actually writes to the same current target while
    processing one input file.
    """


class RocfIncompatiblePathError(InvalidConfiguration):
    """Raised when the library cannot create a declared current path.

    Declarative read old configuration file (ROCF) processing raises this when
    a move, value migration or missing-value rule needs an intermediate
    dictionary or list, but the input data already has an incompatible value at
    that location.
    """


def _identity_value(value: object) -> object:
    """Return ``value`` unchanged for default transform callbacks."""
    return value


def _always_true(value: object) -> bool:
    """Return ``True`` for default condition callbacks."""
    _ = value
    return True


class RocfValueWrite(NamedTuple):
    """Declare one possible current value written by a value migration.

    Application code uses this rule inside :class:`RocfValueMigration` when
    one old configuration value can create a value at one current JSON path.
    The containing migration decides when all writes are applied or skipped
    as one unit.

    ``new_path`` uses the same ROCF path syntax and validation rules as
    :class:`RocfKeyMove` target paths. The containing
    :class:`RocfValueMigration` validates how list wildcards in ``new_path``
    relate to the old path.

    ``condition`` is not a current-value conflict guard. Every declared
    ``new_path`` participates in current-value conflict detection before any
    callback is called, even when ``condition`` would return ``False``. If any
    declared current path already exists, current values win, no declared
    writes are applied, no ``condition`` or ``transform_value`` callbacks are
    called, and the old value is removed as handled old-schema data.

    When no current conflict skips the containing migration, the library calls
    ``condition`` with a deep copy of the old value. If it returns ``True``,
    the library calls ``transform_value`` with another deep copy of the old
    value and writes the returned value to ``new_path``. If ``condition``
    returns ``False``, this write does not produce a value for this
    ``new_path``. Application callbacks should not rely on mutating the
    received value because each callback receives its own copy.

    The value returned by ``transform_value`` is inserted into the parsed JSON
    data before normal current-schema validation. It should therefore be the
    Python representation expected by the current configuration at
    ``new_path``.

    Args:
        new_path: Absolute path where a produced value belongs in the current
            configuration data object.
        condition: Function deciding whether this write applies to the old
            value. Defaults to a function returning ``True``.
        transform_value: Function transforming the old value into the value to
            write at ``new_path``. Defaults to the identity function.
    """

    new_path: ConfigPath
    condition: Callable[[object], bool] = _always_true
    transform_value: Callable[[object], object] = _identity_value


class RocfValueMigration(NamedTuple):
    """Declare that one old value produces current configuration values.

    Application subclasses return these rules from a
    ``ReadOldConfiguration.get_value_migrations()`` method when an old
    configuration parameter cannot be described as one fixed
    :class:`RocfKeyMove`. Typical cases are a value that routes to one of
    several current paths, or a value that is split into several derived
    current values.

    ``old_path`` and all write ``new_path`` values use the same ROCF path
    syntax, validation rules and list wildcard semantics as
    :class:`RocfKeyMove` paths. If ``old_path`` contains list wildcards, each
    actual old value reached by the expanded path is handled as a separate
    value migration.

    The allowed list wildcard shapes are intentionally the same as for
    :class:`RocfKeyMove`, and each write is checked against ``old_path``
    separately:

    - If old and new paths contain the same number of ``'['`` elements, list
      elements are paired by wildcard position and by actual list index.
    - If the new path contains one ``'['`` and the old path contains none,
      the old value is written as the first element of a new single-element
      current list when that current list is absent.
    - If the old path contains more ``'['`` elements than a write path, the
      migration is undefined in this declarative API.
    - Moving only one selected list element is not supported in this version.
    - All other unequal wildcard counts are rejected.

    Declared write paths for one actual old value must be distinct after
    wildcard expansion. If two writes could target the same actual current
    path, the application rule is ambiguous and should be rejected before the
    JSON data is changed.

    A value migration is transactional for each old value reached by
    ``old_path``. If the old path is absent, or if traversal of ``old_path``
    reaches a value with the wrong container type, the rule is a no-op. If
    any declared ``new_path`` already exists, current values win and none of
    the writes are applied. In that conflict case, no ``condition`` or
    ``transform_value`` callbacks are called and the old value is removed as
    handled old-schema data.

    Current-value conflict detection considers every declared write path, not
    only writes whose ``condition`` would return ``True``. This keeps
    application code reviews simple: the declared write set is the complete
    set of current paths that may be affected by the migration.

    Existing current values that overlap the actual old path being removed
    are handled the same way as overlapping :class:`RocfKeyMove` paths. The
    old value is read first, the old path is removed, and then current values
    are written.

    If the implementation needs to create an intermediate dictionary or list
    below a write path and an incompatible value already exists there,
    processing fails with :class:`RocfIncompatiblePathError`.

    If no current conflict exists, all writes whose condition returns
    ``True`` are applied. An empty ``writes`` list is valid. If ``writes`` is
    empty, or if no write condition returns ``True``, the migration is still
    considered handled and the old value is removed without writing any
    current values.

    The implementation evaluates callbacks and prepares all produced current
    values before mutating the JSON data for the actual old value. If a
    ``condition`` or ``transform_value`` callback raises, processing of that
    actual old value fails without deleting its old value or writing any
    values from this migration. Earlier ROCF rules, earlier actual values
    from the same wildcard migration, or earlier value migrations may already
    have changed the in-memory configuration data. Application code should
    therefore treat the original JSON file being read as the safe source to
    correct after such an error. Callback side effects outside the JSON data
    cannot be undone by the library, so callbacks should normally be pure.

    The old value passed to write callbacks has been processed by the normal
    ``parse_json`` method and registered ``parse_converters`` for the old
    path. The processing code deep-copies the old value before calling each
    write's ``condition`` and ``transform_value`` callbacks, so one callback
    cannot mutate the input seen by another callback.

    Automatic-change reporting keeps the existing
    ``ConfigAutoChangeHook.auto_changed()`` signature. When one old value
    produces one or more current values, the hook records one moved old-to-new
    path for each produced current value. When no write is produced, the hook
    records the actual old path as handled old-schema data. When current
    values win, the hook records the actual old path as handled and the
    diagnostic written to ``stderr_file`` lists the old path, the declared
    current paths considered, and the existing current paths that caused the
    conflict. Future implementations may add detailed hook attributes, but
    the summary passed to ``auto_changed()`` must remain backward-compatible.

    Args:
        old_path: Absolute path to the old value in the root configuration
            data object.
        writes: Current value writes to consider as one all-or-nothing
            migration.
    """

    old_path: ConfigPath
    writes: list[RocfValueWrite]


class _MovedValue(NamedTuple):
    """One existing old value found by expanding a ROCF path."""

    actual_path: list[str | int]
    indexes: list[int]
    value: object


class _MoveContext(NamedTuple):
    """Library state shared while applying one batch of ROCF rules."""

    json_data: dict[str, object]
    written_paths: set[str]
    auto_ch_hook: ConfigAutoChangeHook
    stderr_file: TextIO


class _TargetInfo(NamedTuple):
    """One declared write path expanded for one actual old value."""

    path: list[str | int]
    path_text: str
    wrap_prefix: Optional[list[str | int]]


class _PreparedWrite(NamedTuple):
    """One current value prepared before mutating the real JSON data."""

    path: list[str | int]
    path_text: str
    value: object


def _as_dict(value: object) -> Optional[dict[str, object]]:
    """Return ``value`` as a JSON-object dictionary if possible."""
    if isinstance(value, dict):
        return cast(dict[str, object], value)
    return None


def _as_list(value: object) -> Optional[list[object]]:
    """Return ``value`` as a JSON-array list if possible."""
    if isinstance(value, list):
        return cast(list[object], value)
    return None


def _path_text(path: Sequence[str | int]) -> str:
    """Return the path text used in diagnostics and hook callbacks.

    The first dictionary key is rendered as a plain string. Every later
    step (dictionary key or list index) is wrapped in square brackets, so
    a JSON path renders as ``outputs[2][csv_params][delimiter]``. ROCF
    only traverses plain JSON dictionaries and lists, so there is no
    ``.member`` dot syntax here: that style is reserved for cases where a
    path step is known to address a class attribute (for instance inside
    a nested ``Config`` object), which ROCF does not do.
    """
    result = ''
    for part in path:
        if not result and isinstance(part, str):
            result = part
            continue
        result += f'[{part}]'
    return result


def _validate_path(path: ConfigPath, name: str) -> None:
    """Validate a path returned by an application ROCF method."""
    if not path:
        raise ValueError(f'{name} must not be empty')
    if path[0] == '[':
        raise ValueError(f'{name} must start with a dictionary key')
    for part in path:
        if not isinstance(part, str):
            raise TypeError(f'{name} elements must be strings')
        if part.startswith('[') and part != '[':
            raise ValueError(f'{name} element {part} is reserved')


def _list_marker_count(path: ConfigPath) -> int:
    """Return the number of each-list wildcards in ``path``."""
    return sum(1 for part in path if part == '[')


def _conflict_diag(old_path: str, new_path: str, stderr_file: TextIO) -> None:
    """Write the user-facing diagnostic for a current value winning."""
    print('Inconsistent configuration:', file=stderr_file)
    print(f'Both new config parameter {new_path} and old {old_path} '
          'present.', file=stderr_file)
    print(f'Ignoring old parameter {old_path}', file=stderr_file)


def _collect_path_values(data: object, path: ConfigPath,
                         actual: list[str | int],
                         indexes: list[int]) -> list[_MovedValue]:
    """Collect old values reached by expanding one ROCF path."""
    part = path[0]
    rest = path[1:]
    if part == '[':
        list_data = _as_list(data)
        if list_data is None:
            return []
        values = []
        for index, value in enumerate(list_data):
            actual_path = actual + [index]
            list_indexes = indexes + [index]
            if not rest:
                values.append(_MovedValue(actual_path, list_indexes, value))
                continue
            values.extend(_collect_path_values(value, rest, actual_path,
                                               list_indexes))
        return values
    dict_data = _as_dict(data)
    if dict_data is None or part not in dict_data:
        return []
    new_actual = actual + [part]
    if not rest:
        return [_MovedValue(new_actual, indexes, dict_data[part])]
    return _collect_path_values(dict_data[part], rest, new_actual, indexes)


def _target_path(new_path: ConfigPath, indexes: list[int]) -> list[str | int]:
    """Return the current target path for one collected old value."""
    target: list[str | int] = []
    next_index = 0
    for part in new_path:
        if part == '[':
            if indexes:
                target.append(indexes[next_index])
                next_index += 1
            else:
                target.append(0)
        else:
            target.append(part)
    return target


def _delete_path(data: object, path: Sequence[str | int]) -> None:
    """Delete an old actual path after it has been handled."""
    if not path:
        return
    part = path[0]
    rest = path[1:]
    if isinstance(part, int):
        list_data = _as_list(data)
        if list_data is None or part >= len(list_data):
            return
        if rest:
            _delete_path(list_data[part], rest)
        else:
            del list_data[part]
        return
    dict_data = _as_dict(data)
    if dict_data is None or part not in dict_data:
        return
    if rest:
        _delete_path(dict_data[part], rest)
    else:
        del dict_data[part]


def _path_exists(data: object, path: Sequence[str | int]) -> bool:
    """Return whether a current actual path already exists."""
    current = data
    for part in path:
        if isinstance(part, int):
            list_data = _as_list(current)
            if list_data is None or part >= len(list_data):
                return False
            current = list_data[part]
        else:
            dict_data = _as_dict(current)
            if dict_data is None or part not in dict_data:
                return False
            current = dict_data[part]
    return True


def _path_is_prefix(first: Sequence[str | int],
                    second: Sequence[str | int]) -> bool:
    """Return whether ``first`` is an ancestor path of ``second``."""
    if len(first) > len(second):
        return False
    return list(first) == list(second[:len(first)])


def _paths_overlap(first: Sequence[str | int],
                   second: Sequence[str | int]) -> bool:
    """Return whether either actual path is an ancestor of the other."""
    return _path_is_prefix(first, second) or _path_is_prefix(first=second,
                                                             second=first)


def _get_existing_value(data: object,
                        path: Sequence[str | int]) -> tuple[bool, object]:
    """Return whether an actual path exists and its current value."""
    current = data
    for part in path:
        if isinstance(part, int):
            list_data = _as_list(current)
            if list_data is None or part >= len(list_data):
                return False, None
            current = list_data[part]
        else:
            dict_data = _as_dict(current)
            if dict_data is None or part not in dict_data:
                return False, None
            current = dict_data[part]
    return True, current


def _container_for(next_part: str | int) -> object:
    """Return the empty container needed before ``next_part``."""
    if isinstance(next_part, int):
        return []
    return {}


def _require_dict(value: object, path: Sequence[str | int]) \
        -> dict[str, object]:
    """Return a dict or raise when a rule needs a dict path."""
    dict_data = _as_dict(value)
    if dict_data is None:
        msg = f'Path {_path_text(path)} must be a dictionary'
        raise RocfIncompatiblePathError(msg)
    return dict_data


def _require_list(value: object, path: Sequence[str | int]) -> list[object]:
    """Return a list or raise when a rule needs a list path."""
    list_data = _as_list(value)
    if list_data is None:
        msg = f'Path {_path_text(path)} must be a list'
        raise RocfIncompatiblePathError(msg)
    return list_data


def _write_path(data: object, path: Sequence[str | int],
                value: object) -> None:
    """Write a moved, migrated or missing value to a current path."""
    current = data
    for index, part in enumerate(path[:-1]):
        next_part = path[index + 1]
        if isinstance(part, int):
            list_data = _require_list(current, path[:index])
            while len(list_data) <= part:
                list_data.append(_container_for(next_part))
            current = list_data[part]
        else:
            dict_data = _require_dict(current, path[:index])
            if part not in dict_data:
                dict_data[part] = _container_for(next_part)
            current = dict_data[part]
    last = path[-1]
    if isinstance(last, int):
        list_data = _require_list(current, path[:-1])
        while len(list_data) <= last:
            list_data.append(None)
        list_data[last] = value
    else:
        dict_data = _require_dict(current, path[:-1])
        dict_data[last] = value


def _validate_write_shape(old_path: ConfigPath, new_path: ConfigPath) -> None:
    """Validate list wildcard counts for one value-migration write."""
    old_lists = _list_marker_count(old_path)
    new_lists = _list_marker_count(new_path)
    if old_lists == new_lists:
        return
    if old_lists == 0 and new_lists == 1:
        return
    msg = 'ROCF value migrations support equal list wildcard counts, or '
    msg += 'wrapping one non-list old value into one new list'
    raise ValueError(msg)


def _validate_value_migration(migration: RocfValueMigration) -> None:
    """Validate one application-supplied value migration rule."""
    _validate_path(migration.old_path, 'old_path')
    for write in migration.writes:
        _validate_path(write.new_path, 'new_path')
        _validate_write_shape(migration.old_path, write.new_path)


def _wrap_prefix_for(old_path: ConfigPath, new_path: ConfigPath,
                     target: list[str | int]) \
        -> Optional[list[str | int]]:
    """Return the current-list path for a scalar-to-list migration."""
    if _list_marker_count(old_path) != 0:
        return None
    if _list_marker_count(new_path) != 1:
        return None
    for index, part in enumerate(target):
        if isinstance(part, int):
            return target[:index]
    return None


def _target_infos(migration: RocfValueMigration,
                  moved_value: _MovedValue) -> list[_TargetInfo]:
    """Return all declared current paths for one actual old value."""
    infos = []
    seen: set[str] = set()
    for write in migration.writes:
        target = _target_path(write.new_path, moved_value.indexes)
        target_text = _path_text(target)
        if target_text in seen:
            msg = f'More than one ROCF value write targets {target_text}'
            raise RocfConflictError(msg)
        seen.add(target_text)
        wrap_prefix = _wrap_prefix_for(migration.old_path, write.new_path,
                                       target)
        infos.append(_TargetInfo(path=target, path_text=target_text,
                                 wrap_prefix=wrap_prefix))
    return infos


def _append_unique(values: list[str], value: str) -> None:
    """Append one text value if it has not already been collected."""
    if value not in values:
        values.append(value)


def _current_conflicts(context: _MoveContext, moved_value: _MovedValue,
                       infos: list[_TargetInfo]) -> list[str]:
    """Return current paths that make the old value lose."""
    old_actual = moved_value.actual_path
    conflicts: list[str] = []
    for info in infos:
        if info.path_text in context.written_paths:
            msg = f'More than one ROCF value migration wrote {info.path_text}'
            raise RocfConflictError(msg)
        if info.wrap_prefix is not None:
            exists, value = _get_existing_value(context.json_data,
                                                info.wrap_prefix)
            if exists and not _paths_overlap(old_actual, info.wrap_prefix):
                _ = _require_list(value, info.wrap_prefix)
                _append_unique(conflicts, _path_text(info.wrap_prefix))
        if _path_exists(context.json_data, info.path) and not _paths_overlap(
                old_actual, info.path):
            _append_unique(conflicts, info.path_text)
    return conflicts


def _joined_paths(paths: Sequence[str]) -> str:
    """Return path names joined for one user-facing diagnostic line."""
    return ', '.join(paths)


def _value_conflict_diag(old_path: str, declared: list[str],
                         existing: list[str], stderr_file: TextIO) -> None:
    """Write the diagnostic for a value migration current conflict."""
    print('Inconsistent configuration:', file=stderr_file)
    if len(declared) == 1:
        msg = f'Both new config parameter {declared[0]} and old {old_path} '
    else:
        msg = 'Both new config parameter one of '
        msg += f'{_joined_paths(declared)} and old {old_path} '
    print(msg + 'present.', file=stderr_file)
    print('Existing current parameter(s): '
          f'{_joined_paths(existing)}', file=stderr_file)
    print(f'Ignoring old parameter {old_path}', file=stderr_file)


def _prepared_writes(migration: RocfValueMigration, moved_value: _MovedValue,
                     infos: list[_TargetInfo]) -> list[_PreparedWrite]:
    """Return all writes whose conditions accept the old value."""
    prepared = []
    for write, info in zip(migration.writes, infos):
        if not write.condition(deepcopy(moved_value.value)):
            continue
        new_value = write.transform_value(deepcopy(moved_value.value))
        prepared.append(_PreparedWrite(path=info.path,
                                       path_text=info.path_text,
                                       value=new_value))
    return prepared


def _verify_writes(data: dict[str, object], old_path: list[str | int],
                   prepared: list[_PreparedWrite]) -> None:
    """Check write compatibility on a temporary JSON data copy."""
    trial = deepcopy(data)
    _delete_path(trial, old_path)
    for item in prepared:
        _write_path(trial, item.path, item.value)


def _delete_order(values: list[_MovedValue],
                  old_path: ConfigPath) -> list[_MovedValue]:
    """Return collected values in an order safe for deleting old paths."""
    if old_path[-1] == '[':
        return list(reversed(values))
    return values


def _process_one_value_migration(context: _MoveContext,
                                 migration: RocfValueMigration,
                                 moved_value: _MovedValue) -> None:
    """Process one actual old value reached by a value migration."""
    infos = _target_infos(migration, moved_value)
    old_text = _path_text(moved_value.actual_path)
    current_conflicts = _current_conflicts(context, moved_value, infos)
    if current_conflicts:
        _value_conflict_diag(old_text, [info.path_text for info in infos],
                             current_conflicts, context.stderr_file)
        _delete_path(context.json_data, moved_value.actual_path)
        context.auto_ch_hook.old_key_handled(old_text)
        return
    prepared = _prepared_writes(migration, moved_value, infos)
    _verify_writes(context.json_data, moved_value.actual_path, prepared)
    _delete_path(context.json_data, moved_value.actual_path)
    if not prepared:
        context.auto_ch_hook.old_key_handled(old_text)
        return
    for item in prepared:
        _write_path(context.json_data, item.path, item.value)
        context.written_paths.add(item.path_text)
        context.auto_ch_hook.old_path_moved(old_path=old_text,
                                            new_path=item.path_text)


def process_value_migration(json_data: dict[str, object],
                            migration: RocfValueMigration,
                            context: _MoveContext) -> None:
    """Apply one value migration rule to parsed JSON data.

    Args:
        json_data: Root JSON object being normalized. It is passed explicitly
            so the public function signature shows the mutated object.
        migration: Value migration rule to apply.
        context: Shared ROCF processing context for this batch.
    """
    if json_data is not context.json_data:
        raise ValueError('json_data must match context.json_data')
    _validate_value_migration(migration)
    moved = _collect_path_values(json_data, migration.old_path, [], [])
    for moved_value in _delete_order(moved, migration.old_path):
        _process_one_value_migration(context, migration, moved_value)
