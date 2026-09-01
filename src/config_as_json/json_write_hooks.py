#! /usr/local/bin/python3
"""Implement the public write-side JSON conversion hook API.

A ``Config`` subclass overrides ``serialize_converters()`` to declare how
selected Python values should be converted into JSON-compatible data before
``json.dumps()`` is called. ``Config.as_json_string()`` invokes
:func:`apply_serialize_converters` once the data dictionary owned by the
current Config object has been assembled and all declared nested Config
objects have already serialized themselves.

The implementation is intentionally small: built-in fallback conversions
cover only ``Enum`` and ``IntEnum`` members (converted to their member
names). Everything else is the responsibility of explicit converters
declared by the application. The motivating problem case is ``IntEnum``,
which Python's JSON encoder treats as ``int`` and therefore never offers to
``default()``; the write-side hook runs before ``json.dumps()`` and
sidesteps that issue.
"""

# Copyright (c) 2026 Tom Björkholm
# MIT License

from copy import deepcopy
from enum import Enum
from typing import Callable, NamedTuple, Optional, Sequence, TextIO
from config_as_json.commontypes import ConfigPath, JsonType, json_types
from config_as_json.member_path import member_path
from config_as_json.validator import InvalidConfiguration


type SerializeSelector = str | ConfigPath
"""Select values that should use one write-side converter.

A plain string is a recursive dictionary key selector. For example,
``'format'`` applies to every dictionary member named ``format`` in data owned
by the current ``Config`` object.

A ``ConfigPath`` is an absolute path selector. For example,
``('outputs', '[', 'format')`` applies only to that path. The one-element path
``('format',)`` means the root key ``format``; it is not the same as the plain
string selector ``'format'``.

Applications must not return both a recursive key selector and a path selector
that ends with the same dictionary key. For example, returning both
``'format'`` and ``('outputs', '[', 'format')`` is a selector conflict even if
the current configuration data does not contain that path. The implementation
should detect such conflicts when it checks ``serialize_converters()`` and
raise ``SerializeSelectorError``. A path ending in ``'['`` targets list
elements, not a dictionary key, so it does not conflict with a recursive key
selector.

For symmetry, the implementation also rejects a path selector that passes
through a key that is itself a recursive key selector. This is conservative;
future versions may extend write hooks to also describe converters for a
class-object member that is itself a member of an outer class object, which
would relax this rule.

Declared nested ``Config`` objects form ownership boundaries. Parent
converters do not apply inside nested objects; each nested object uses only
its own write-side converters.
"""


class SerializeConverter(NamedTuple):
    """Describe one write-side conversion from Python data to JSON data.

    A converter is selected by a ``SerializeSelector`` returned from
    ``serialize_converters()``. Explicit converters override built-in
    conversions such as enum-name serialization.

    ``None`` values pass through unchanged. This lets validation and
    omit-when-None handling decide whether ``None`` is allowed or omitted.

    If ``value_type`` is not ``None``, every matched non-``None`` value must
    be an instance of that type before ``func`` is called. If the value has
    another type, serialization should raise a path-aware
    ``JsonWriteHookError``. This rule applies to both absolute path selectors
    and recursive key-name selectors.

    If ``value_type`` is ``None``, no pre-conversion type check is performed
    and the conversion function is responsible for accepting the matched
    value.

    The conversion function is called with the matched value, the current
    path text, the current ``stderr_file``, and the keyword arguments from
    ``args``. The intended call shape is
    ``func(value, path_text=path_text, stderr_file=stderr_file, **args)``.

    ``path_text`` is for diagnostics and should not be parsed as a selector.
    It uses the same style as member names passed to member validators: list
    indexes and dictionary keys are appended in square brackets, for example
    ``matrix[3]`` and ``csv_params[delimiter]``.

    The conversion result must be recursively JSON-compatible. Valid output
    is ``None``, ``int``, ``float``, ``str``, ``bool``, a list of valid
    values, or a dictionary with string keys and valid values. Invalid output
    raises a path-aware ``JsonWriteHookError`` before ``json.dumps()`` is
    called. Explicit converter output is checked as-is. Built-in fallback
    conversions are not applied to the converter return value, so returning
    ``{'mode': SomeEnum.FAST}`` is invalid. Return a JSON-compatible value
    such as ``{'mode': 'FAST'}`` instead.

    If ``func`` raises ``JsonWriteHookError``, it propagates unchanged.
    Other exceptions from ``func`` are wrapped in ``JsonWriteHookError``
    with selector and path context.

    Attributes:
        value_type: Optional expected Python type before conversion.
        func: Callable that converts a Python value to JSON-compatible data.
        args: Keyword arguments passed to ``func``.
    """

    value_type: Optional[type[object]]
    func: Callable[..., JsonType]
    args: dict[str, object]


class JsonWriteHookError(InvalidConfiguration):
    """Raised when write-side JSON conversion cannot produce valid JSON."""


class SerializeSelectorError(ValueError):
    """Raised when write-side conversion selectors are not valid together.

    This exception reports programming errors in ``serialize_converters()``
    declarations, such as invalid selector types, invalid ``ConfigPath``
    syntax, or a recursive key selector that conflicts with a path selector
    ending in or passing through the same dictionary key. It also reports
    selectors that would cross child-owned nested ``Config`` ownership
    boundaries.

    Selector declarations are checked before conversion starts as far as
    possible. Data-dependent traversal errors, such as a path selector that
    reaches a list where it needs a dictionary, are detected while traversing
    the actual data and also raise this exception.
    """


type SerializeConverters = dict[SerializeSelector, SerializeConverter]
"""Write-side conversion rules for rich Python values before JSON write."""


# The intermediate selector path used during traversal. Each step is either
# a dictionary key (any string not starting with '[') or the literal '['
# marker that stands for "this step descended into a list element".
type _SelectorPath = tuple[str, ...]

# Lookups built from the converter mapping. Path converters are keyed by the
# exact ``_SelectorPath`` they target; recursive key converters are keyed by
# the dictionary key name.
type _PathConverters = dict[_SelectorPath, SerializeConverter]
type _RecKeyConverters = dict[str, SerializeConverter]


# ----------------------------------------------------------------------
# Selector validation
# ----------------------------------------------------------------------


def _is_path_selector(selector: SerializeSelector) -> bool:
    """Return whether ``selector`` is a path (tuple), not a recursive key."""
    return isinstance(selector, tuple)


def _selector_repr(selector: SerializeSelector) -> str:
    """Return a human-friendly representation of one selector."""
    if isinstance(selector, str):
        return repr(selector)
    return str(selector)


def _validate_one_selector(selector: SerializeSelector) -> None:
    """Validate the shape of one selector returned from the hook.

    Recursive key selectors must be non-empty strings that do not start with
    ``'['``. Path selectors follow the same rules as ROCF paths: non-empty
    tuple of strings, first element must be a dictionary key, intermediate
    ``'['`` markers are allowed, and any other element starting with ``'['``
    is reserved.
    """
    if isinstance(selector, str):
        if not selector:
            raise SerializeSelectorError(
                'Recursive key selector must not be the empty string')
        if selector.startswith('['):
            raise SerializeSelectorError(
                f'Recursive key selector {selector!r} must not start with '
                "'['")
        return
    if not isinstance(selector, tuple):
        raise SerializeSelectorError(
            'Selector must be a str or a ConfigPath tuple; got '
            f'{type(selector).__name__}')
    if not selector:
        raise SerializeSelectorError('Path selector must not be empty')
    if selector[0] == '[':
        raise SerializeSelectorError(
            f'Path selector {selector} must start with a dictionary key')
    for part in selector:
        if not isinstance(part, str):
            raise SerializeSelectorError(
                f'Path selector {selector} element must be a str; got '
                f'{type(part).__name__}')
        if part.startswith('[') and part != '[':
            raise SerializeSelectorError(
                f'Path selector {selector} element {part!r} is reserved')


def _split_selectors(converters: SerializeConverters) \
        -> tuple[_RecKeyConverters, _PathConverters]:
    """Validate selectors and split them into rec-key and path mappings."""
    rec_key: _RecKeyConverters = {}
    paths: _PathConverters = {}
    for selector, converter in converters.items():
        if not isinstance(converter, SerializeConverter):
            raise SerializeSelectorError(
                f'Converter for {_selector_repr(selector)} must be a '
                'SerializeConverter')
        _validate_one_selector(selector)
        if isinstance(selector, str):
            rec_key[selector] = converter
        else:
            paths[selector] = converter
    return rec_key, paths


def _check_rec_vs_path_conflicts(rec_key: _RecKeyConverters,
                                 paths: _PathConverters) -> None:
    """Reject recursive-key vs path selector conflicts.

    A path selector may neither end with a key that is also a recursive-key
    selector, nor pass through such a key in an intermediate step.
    """
    for path in paths.keys():
        last = path[-1]
        if last != '[' and last in rec_key:
            raise SerializeSelectorError(
                f'Path selector {path} ends in key {last!r} which is also '
                'a recursive-key selector')
        # pylint: disable-next=line-too-long
        # Intermediate steps must not pass through a recursive-key target. A
        # future relaxation could allow rec-key conversion of a Config
        # member that contains other rec-key targets, but for now we reject
        # the combination.
        for step in path[:-1]:
            if step != '[' and step in rec_key:
                raise SerializeSelectorError(
                    f'Path selector {path} passes through key {step!r} '
                    'which is also a recursive-key selector')


def _path_matches_or_extends(p: _SelectorPath,
                             reference: _SelectorPath) -> bool:
    """Return whether ``p`` is equal to or a descendant of ``reference``.

    In ``reference``, the literal ``'['`` step matches either ``'['`` in
    ``p`` (list iteration) or any non-``'['`` dictionary key in ``p`` (a
    dictionary value). This extended meaning is only used when matching a
    traversal selector path against a child-owned-path boundary. Plain
    path-selector matching uses identical tuple equality.
    """
    if len(p) < len(reference):
        return False
    for p_step, ref_step in zip(p[:len(reference)], reference):
        if ref_step == '[':
            continue
        if p_step != ref_step:
            return False
    return True


def _check_child_boundaries(paths: _PathConverters,
                            child_owned: Sequence[ConfigPath]) -> None:
    """Reject path selectors that cross child-owned subtree boundaries."""
    for path in paths.keys():
        for cop in child_owned:
            if _path_matches_or_extends(path, cop):
                raise SerializeSelectorError(
                    f'Path selector {path} targets or descends into the '
                    f'child-owned subtree {cop}')
            if _path_matches_or_extends(cop, path):
                raise SerializeSelectorError(
                    f'Path selector {path} is an ancestor of the '
                    f'child-owned subtree {cop}')


# Recursive-key selectors do not need an up-front boundary check against
# child_owned_paths: the parent-owned walk never descends into child-owned
# subtrees, so a recursive key whose name happens to also exist deep inside
# a child-owned subtree is silently ignored.


# ----------------------------------------------------------------------
# Path text helpers
# ----------------------------------------------------------------------


def _append_path_text(prefix: str, step: str | int) -> str:
    """Append one dict-key or list-index step to a path-text string.

    Returns the top-level name unchanged when ``prefix`` is empty and the
    step is a string. For all other cases the step is wrapped in square
    brackets, matching the member-name convention used by the member
    validators.
    """
    if not prefix and isinstance(step, str):
        return step
    return f'{prefix}[{step}]'


def _reported_at(path_text: str, member_name: Optional[str]) -> str:
    """Return what a diagnostic calls one place in the written JSON data.

    ``path_text`` addresses the JSON data of one Config object, so the
    reported place is the path of that object with the place inside it
    appended. The top level of a whole configuration is not a member of
    anything and has no name, so it is called ``<root>``.
    """
    if not path_text:
        return '<root>' if member_name is None else member_name
    return member_path(member_name, path_text)


# ----------------------------------------------------------------------
# JSON compatibility verification
# ----------------------------------------------------------------------


def _check_json_compatible(value: object, path_text: str,
                           member_name: Optional[str]) -> None:
    """Recursively verify that a value is JSON-compatible.

    Accepted leaf types are ``None``, ``bool``, ``int``, ``float`` and
    ``str``. Containers must be a ``list`` of compatible values or a
    ``dict`` with string keys mapping to compatible values. A
    ``JsonWriteHookError`` is raised on the first violation.

    ``bool`` is intentionally accepted as a leaf even though it is a
    subclass of ``int``; ``json.dumps`` writes booleans as ``true``/
    ``false`` and we treat them as JSON-native.
    """
    if value is None or isinstance(value, (bool, int, float, str)):
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _check_json_compatible(item, _append_path_text(path_text, index),
                                   member_name)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            where = _reported_at(path_text, member_name)
            if not isinstance(key, str):
                raise JsonWriteHookError(
                    f'Dictionary key at {where} must be a '
                    f'str; got {type(key).__name__}')
            if key.startswith('['):
                raise JsonWriteHookError(
                    f'Dictionary key {key!r} at {where} '
                    "must not start with '['")
            _check_json_compatible(item, _append_path_text(path_text, key),
                                   member_name)
        return
    raise JsonWriteHookError(
        f'Value at {_reported_at(path_text, member_name)} has non-JSON type '
        f'{type(value).__name__}')


# ----------------------------------------------------------------------
# Converter dispatch
# ----------------------------------------------------------------------


# pylint: disable-next=too-many-arguments
def _apply_one_converter(value: object, converter: SerializeConverter,
                         path_text: str, selector: SerializeSelector,
                         stderr_file: TextIO, *,
                         member_name: Optional[str]) -> JsonType:
    """Apply one converter to ``value`` and wrap unexpected errors.

    ``None`` always passes through unchanged. The optional ``value_type``
    pre-check raises ``JsonWriteHookError`` instead of trusting the user
    converter to be defensive.
    """
    if value is None:
        return None
    where = _reported_at(path_text, member_name)
    if converter.value_type is not None and \
            not isinstance(value, converter.value_type):
        raise JsonWriteHookError(
            f'Value at {where} for selector '
            f'{_selector_repr(selector)} has type '
            f'{type(value).__name__}; expected '
            f'{converter.value_type.__name__}')
    try:
        result = converter.func(value, path_text=path_text,
                                stderr_file=stderr_file, **converter.args)
    except JsonWriteHookError:
        raise
    except Exception as exc:  # pylint: disable=broad-exception-caught
        raise JsonWriteHookError(
            f'Converter for {_selector_repr(selector)} at '
            f'{where} raised {type(exc).__name__}: {exc}') from exc
    _check_json_compatible(result, path_text, member_name)
    return result


def _builtin_fallback(value: object) -> object:
    """Apply the built-in fallback conversion to one value.

    Only Enum/IntEnum members are converted, to their symbolic ``name``.
    Other values are returned unchanged.
    """
    if isinstance(value, Enum):
        return value.name
    return value


def _is_inside_child_owned(selector_path: _SelectorPath,
                           child_owned: Sequence[ConfigPath]) -> bool:
    """Return whether ``selector_path`` is at or below a child-owned path."""
    for cop in child_owned:
        if _path_matches_or_extends(selector_path, cop):
            return True
    return False


def _has_path_inside(selector_path: _SelectorPath,
                     paths: _PathConverters) -> tuple[bool, bool]:
    """Return whether any path selector targets inside ``selector_path``.

    The two booleans say whether such a path expects a dict next or a list
    next at ``selector_path``. They are used to raise
    ``SerializeSelectorError`` when the actual data has the wrong container
    type at this point.
    """
    expects_dict = False
    expects_list = False
    depth = len(selector_path)
    for path in paths.keys():
        if len(path) <= depth:
            continue
        if path[:depth] != selector_path:
            continue
        next_step = path[depth]
        if next_step == '[':
            expects_list = True
        else:
            expects_dict = True
    return expects_dict, expects_list


class _WalkContext(NamedTuple):
    """Bundle the read-only walk parameters threaded through traversal."""

    rec_key: _RecKeyConverters
    paths: _PathConverters
    child_owned: Sequence[ConfigPath]
    stderr_file: TextIO
    member_name: Optional[str]


def _convert_dict(value: dict[str, object], selector_path: _SelectorPath,
                  path_text: str, ctx: _WalkContext) -> dict[str, JsonType]:
    """Convert one parent-owned dictionary value."""
    result: dict[str, JsonType] = {}
    for key, item in value.items():
        where = _reported_at(path_text, ctx.member_name)
        if not isinstance(key, str):
            raise JsonWriteHookError(
                f'Dictionary key at {where} must be a '
                f'str; got {type(key).__name__}')
        if key.startswith('['):
            raise JsonWriteHookError(
                f'Dictionary key {key!r} at {where} '
                "must not start with '['")
        child_selector = selector_path + (key,)
        child_text = _append_path_text(path_text, key)
        if _is_inside_child_owned(child_selector, ctx.child_owned):
            result[key] = _passthrough_child(item, child_text, ctx)
            continue
        # An exact path-selector match at the child position takes
        # precedence over recursive key selectors. Declaration-time checks
        # prevent both from targeting the same value, but path selectors
        # may also target the same name as a different key elsewhere; the
        # exact match wins here.
        if child_selector in ctx.paths:
            converter = ctx.paths[child_selector]
            result[key] = _apply_one_converter(value=item, converter=converter,
                                               path_text=child_text,
                                               selector=child_selector,
                                               stderr_file=ctx.stderr_file,
                                               member_name=ctx.member_name)
            continue
        if key in ctx.rec_key:
            converter = ctx.rec_key[key]
            result[key] = _apply_one_converter(value=item, converter=converter,
                                               path_text=child_text,
                                               selector=key,
                                               stderr_file=ctx.stderr_file,
                                               member_name=ctx.member_name)
            continue
        result[key] = _convert_value(value=item, selector_path=child_selector,
                                     path_text=child_text, ctx=ctx)
    return result


def _convert_list(value: list[object], selector_path: _SelectorPath,
                  path_text: str, ctx: _WalkContext) -> list[JsonType]:
    """Convert one parent-owned list value."""
    child_selector = selector_path + ('[',)
    inside_child = _is_inside_child_owned(child_selector, ctx.child_owned)
    result: list[JsonType] = []
    for index, item in enumerate(value):
        child_text = _append_path_text(path_text, index)
        if inside_child:
            result.append(_passthrough_child(item, child_text, ctx))
            continue
        if child_selector in ctx.paths:
            result.append(_apply_one_converter(
                value=item, converter=ctx.paths[child_selector],
                path_text=child_text, selector=child_selector,
                stderr_file=ctx.stderr_file, member_name=ctx.member_name))
            continue
        result.append(_convert_value(value=item, selector_path=child_selector,
                                     path_text=child_text, ctx=ctx))
    return result


def _passthrough_child(value: object, path_text: str,
                       ctx: '_WalkContext') -> JsonType:
    """Return a child-owned value as-is after a JSON-compatibility check.

    Child-owned subtrees have already been produced by the child object's
    own ``as_json_string()``, so they must already be JSON-compatible. The
    check protects us against programming mistakes and produces a clear
    error rather than a cryptic ``json.dumps`` failure. A diagnostic names
    the child by its path, like every other diagnostic here.
    """
    _check_json_compatible(value, path_text, ctx.member_name)
    assert isinstance(value, json_types)
    return value


def _convert_value(value: object, selector_path: _SelectorPath, path_text: str,
                   ctx: _WalkContext) -> JsonType:
    """Convert one value, recursing into containers as needed."""
    expects_dict, expects_list = _has_path_inside(selector_path, ctx.paths)
    where = _reported_at(path_text, ctx.member_name)
    if isinstance(value, dict):
        if expects_list:
            raise SerializeSelectorError(
                f'Path selector expects a list at '
                f'{where} but data has a dict')
        return _convert_dict(value=value, selector_path=selector_path,
                             path_text=path_text, ctx=ctx)
    if isinstance(value, list):
        if expects_dict:
            raise SerializeSelectorError(
                f'Path selector expects a dict at '
                f'{where} but data has a list')
        return _convert_list(value=value, selector_path=selector_path,
                             path_text=path_text, ctx=ctx)
    if expects_dict or expects_list:
        raise SerializeSelectorError(
            f'Path selector expects a container at '
            f'{where} but data has '
            f'{type(value).__name__}')
    fallback = _builtin_fallback(value)
    if fallback is not None and \
            not isinstance(fallback, (bool, int, float, str)):
        raise JsonWriteHookError(
            f'Value at {where} has non-JSON type '
            f'{type(value).__name__}; declare a SerializeConverter or use '
            'a JSON-compatible value')
    assert isinstance(fallback, json_types)
    return fallback


# ----------------------------------------------------------------------
# Public entry point
# ----------------------------------------------------------------------


def apply_serialize_converters(data: dict[str, object],
                               converters: SerializeConverters,
                               stderr_file: TextIO,
                               child_owned_paths: Sequence[ConfigPath] = (), *,
                               member_name: Optional[str]) \
                                   -> dict[str, JsonType]:
    """Return JSON-compatible data after write-side conversions.

    ``Config.as_json_string()`` should call this function after validation
    and after nested ``Config`` members have been converted to their own
    JSON data, but before calling ``json.dumps()``. The function owns
    selector checking, converter dispatch, built-in fallback conversions
    such as enum-name serialization, and recursive JSON-compatibility
    checks.

    The function returns a new converted tree. The passed-in tree is never
    mutated.

    The initial built-in fallback conversions are ``Enum`` and ``IntEnum``
    members to their member names. Everything else outside explicit
    converters must already be JSON-compatible.

    A path selector that reaches a missing dictionary key is a no-op. A
    path selector that reaches the wrong container type raises
    ``SerializeSelectorError``. For example, expecting a dictionary key
    where the actual data has a list is an error, while an absent key in an
    existing dictionary is not.

    A recursive key-name selector walks parent-owned dictionaries and
    lists. It skips child-owned subtrees automatically because the walk
    never descends into them.

    ``child_owned_paths`` describes nested ``Config`` subtrees that are
    present in ``data`` only because the child object already serialized
    itself. The function passes those subtrees through unchanged. In a
    child-owned path the literal ``'['`` step matches either a list
    element or a dictionary value at that point, which lets a parent
    describe ``LIST_ELEMENT`` and ``DICT_VALUE`` nested-config kinds with
    the same notation.

    Dictionary keys that start with ``'['`` are rejected. ``'['`` is
    reserved by ``ConfigPath`` for list iteration and is not allowed as a
    literal data key.

    Args:
        data: Root data dictionary owned by the current ``Config`` object.
        converters: Explicit converters returned by
            ``Config.serialize_converters()``.
        stderr_file: Stream passed through to converter functions.
        child_owned_paths: Paths to nested ``Config`` subtrees owned by
            child objects. Selectors that would convert those subtrees,
            their descendants, or an ancestor container containing them
            are invalid.
        member_name: Dotted and indexed path for reaching the ``Config``
            object owning ``data`` by traversing nested attributes from the
            top level of the complete ``as_json_string()`` operation, such
            as ``outputs[1].section``. ``None`` means that the object is
            the top level and not a member of anything. A diagnostic names
            the place it is about by that path with the place inside
            ``data`` appended, and calls the top level ``<root>``. The
            ``path_text`` handed to a converter function stays relative to
            ``data``, because a selector is relative to it too.

    Returns:
        A JSON-compatible dictionary ready to pass to ``json.dumps()``.

    Raises:
        SerializeSelectorError: The selector declarations are invalid or
            ambiguous, or a selector crosses a child-owned path boundary.
        JsonWriteHookError: A matched value has the wrong type, a
            converter raises an error that should be wrapped with path
            context, or a conversion result is not JSON-compatible.
    """
    if not isinstance(data, dict):
        raise JsonWriteHookError(
            f'Root data must be a dict; got {type(data).__name__}')
    if not isinstance(converters, dict):
        raise SerializeSelectorError(
            'serialize_converters() must return a dict mapping selectors '
            'to SerializeConverter objects')
    child_owned = tuple(child_owned_paths)
    for cop in child_owned:
        _validate_one_selector(cop)
    rec_key, paths = _split_selectors(converters)
    _check_rec_vs_path_conflicts(rec_key=rec_key, paths=paths)
    _check_child_boundaries(paths=paths, child_owned=child_owned)
    # We always produce a new tree so callers can rely on the input not
    # being mutated. ``deepcopy`` is conservative but keeps the converter
    # API simple: converter functions may safely keep references to the
    # values they receive without worrying about hidden aliasing.
    working = deepcopy(data)
    ctx = _WalkContext(rec_key=rec_key, paths=paths, child_owned=child_owned,
                       stderr_file=stderr_file, member_name=member_name)
    return _convert_dict(value=working, selector_path=(), path_text='',
                         ctx=ctx)
