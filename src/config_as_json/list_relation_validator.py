#! /usr/local/bin/python3
"""Validate that one list-like value has a relation to another.

The validator is used to validate that a list-like value (which may be
a projected value) has the specified relation to another list-like value
(which might also be a projected value).
"""

# Copyright (c) 2026 Tom Björkholm
# MIT License

import sys
from collections.abc import Sequence as SequenceABC
from enum import Enum, auto
from operator import eq, lt
from typing import Callable, Optional, TextIO, TYPE_CHECKING, cast
from config_as_json.member_path import member_path
from config_as_json.validator import InvalidConfiguration, WholeConfigValidator
from config_as_json.projected_validators import WholeConfigProjector
if TYPE_CHECKING:
    from config_as_json.config import Config


_DEFAULT_LT_COMPARATOR: Callable[[object, object], bool] = \
    cast(Callable[[object, object], bool], lt)


def _validate_relation_kind(kind: object) -> 'ListRelationKind':
    """Validate and return one list relation kind.

    Args:
        kind: Relation kind supplied to the constructor.

    Returns:
        ``kind`` after it has been proven to be a ``ListRelationKind``.

    Raises:
        TypeError: If ``kind`` is not a ``ListRelationKind``.
    """
    if not isinstance(kind, ListRelationKind):
        raise TypeError('kind must be a ListRelationKind.')
    return kind


def _validate_member_name(member_name: object, parameter_name: str) -> str:
    """Validate and return one relation member or pseudo-member name.

    Args:
        member_name: Name supplied to the constructor.
        parameter_name: Parameter name used in error messages.

    Returns:
        ``member_name`` after it has been proven to be non-empty str.

    Raises:
        TypeError: If ``member_name`` is not a str.
        ValueError: If ``member_name`` is empty.
    """
    if not isinstance(member_name, str):
        raise TypeError(f'{parameter_name} must be a str.')
    if member_name == '':
        raise ValueError(f'{parameter_name} must be non-empty.')
    return member_name


def _validate_optional_projector(
        projector: Optional[WholeConfigProjector],
        parameter_name: str) -> Optional[WholeConfigProjector]:
    """Validate and return an optional whole-config projector.

    Args:
        projector: Optional projector supplied to the constructor.
        parameter_name: Parameter name used in error messages.

    Returns:
        ``projector`` after it has been proven to be ``None`` or callable.

    Raises:
        TypeError: If ``projector`` is not ``None`` and not callable.
    """
    if projector is None:
        return None
    if not callable(projector):
        raise TypeError(f'{parameter_name} must be None or callable.')
    return projector


def _validate_comparator(comparator: object, parameter_name: str) \
        -> Callable[[object, object], bool]:
    """Validate and return one relation element comparator.

    Args:
        comparator: Comparator supplied to the constructor.
        parameter_name: Parameter name used in error messages.

    Returns:
        ``comparator`` after it has been proven to be callable.

    Raises:
        TypeError: If ``comparator`` is not callable.
    """
    if not callable(comparator):
        raise TypeError(f'{parameter_name} must be callable.')
    return cast(Callable[[object, object], bool], comparator)


def _print_and_raise_type_error(message: str, stderr_file: TextIO) -> None:
    """Print one type error message and raise ``TypeError``.

    Args:
        message: Message to print and raise.
        stderr_file: Stream used for user-facing diagnostics.

    Raises:
        TypeError: Always raised with ``message``.
    """
    print(message, file=stderr_file)
    raise TypeError(message)


def _print_and_raise_key_error(message: str, stderr_file: TextIO) -> None:
    """Print one key error message and raise ``KeyError``.

    Args:
        message: Message to print and raise.
        stderr_file: Stream used for user-facing diagnostics.

    Raises:
        KeyError: Always raised with ``message``.
    """
    print(message, file=stderr_file)
    raise KeyError(message)


def _print_and_raise_invalid(message: str, stderr_file: TextIO) -> None:
    """Print one invalid-configuration message and raise it.

    Args:
        message: Message to print and raise.
        stderr_file: Stream used for user-facing diagnostics.

    Raises:
        InvalidConfiguration: Always raised with ``message``.
    """
    print(message, file=stderr_file)
    raise InvalidConfiguration(message)


def _materialized_sequence(member_name: str, value: object,
                           stderr_file: TextIO) -> list[object]:
    """Validate and materialize one relation value as a list.

    Args:
        member_name: The reported path of the member, used in
            diagnostics.
        value: Value to validate and materialize.
        stderr_file: Stream used for user-facing diagnostics.

    Returns:
        The relation value as a newly materialized list.

    Raises:
        TypeError: If ``value`` is not a sequence, or if it is ``str``,
            ``bytes``, or ``bytearray``.
    """
    if isinstance(value, (str, bytes, bytearray)) or \
            not isinstance(value, SequenceABC):
        msg = 'Invalid configuration: '
        msg += f'Value for {member_name} must be a sequence, '
        msg += 'but not str, bytes, or bytearray.'
        _print_and_raise_type_error(msg, stderr_file)
    sequence = cast(SequenceABC[object], value)
    return list(sequence)


def _contains_equal(values: list[object], value: object,
                    eq_comparator: Callable[[object, object], bool]) -> bool:
    """Return whether ``values`` contains an equal value.

    Args:
        values: Values to search.
        value: Value to find.
        eq_comparator: Function used to compare values.

    Returns:
        ``True`` if an equal value was found.
    """
    return any(eq_comparator(candidate, value) for candidate in values)


def _is_distinct_subset(values_a: list[object], values_b: list[object],
                        eq_comparator: Callable[[object, object], bool]) \
        -> bool:
    """Return whether distinct values in A are found in B.

    Args:
        values_a: Candidate subset values.
        values_b: Candidate superset values.
        eq_comparator: Function used to compare values.

    Returns:
        ``True`` if every distinct value in ``values_a`` occurs in
        ``values_b``.
    """
    checked: list[object] = []
    for value in values_a:
        if _contains_equal(checked, value, eq_comparator):
            continue
        checked.append(value)
        if not _contains_equal(values_b, value, eq_comparator):
            return False
    return True


def _is_multiset_equal(values_a: list[object], values_b: list[object],
                       eq_comparator: Callable[[object, object], bool]) \
        -> bool:
    """Return whether two values contain equal values with equal counts.

    Args:
        values_a: First value sequence.
        values_b: Second value sequence.
        eq_comparator: Function used to compare values.

    Returns:
        ``True`` if every value in ``values_a`` can be paired with exactly
        one equal value in ``values_b``.
    """
    if len(values_a) != len(values_b):
        return False
    matched_b = [False] * len(values_b)
    for value_a in values_a:
        found_index: Optional[int] = None
        for index, value_b in enumerate(values_b):
            if not matched_b[index] and eq_comparator(value_a, value_b):
                found_index = index
                break
        if found_index is None:
            return False
        matched_b[found_index] = True
    return True


def _is_disjoint(values_a: list[object], values_b: list[object],
                 eq_comparator: Callable[[object, object], bool]) -> bool:
    """Return whether no value from A occurs in B.

    Args:
        values_a: First value sequence.
        values_b: Second value sequence.
        eq_comparator: Function used to compare values.

    Returns:
        ``True`` if no value in one sequence is equal to a value in the
        other sequence.
    """
    for value_a in values_a:
        if _contains_equal(values_b, value_a, eq_comparator):
            return False
    return True


class ListRelationKind(Enum):
    """Relation to require between two list-like values."""

    EQUAL = auto()
    """The two values must be equal as ordered sequences.

    The sequences must have the same length. For each position, the value in
    sequence A must be equal to the value in the same position in sequence B
    according to the supplied equality comparator.
    """

    MULTISET_EQUAL = auto()
    """The two values must contain the same elements with the same counts.

    Order is ignored, but duplicates are significant. For example,
    ``['a', 'a', 'b']`` and ``['a', 'b', 'a']`` satisfy this relation, while
    ``['a', 'b']`` and ``['a', 'a', 'b']`` do not.
    """

    SET_EQUAL = auto()
    """Each distinct value in either sequence must occur in the other.

    Order and duplicates are ignored. For example, ``['a', 'a']`` and
    ``['a']`` satisfy this relation.
    """

    SUBSET = auto()
    """Each distinct value in sequence A must occur in sequence B.

    Order and duplicates are ignored. Sequence B may contain additional
    values. For example, ``['a', 'a']`` is a subset of ``['a', 'b']``.
    """

    DISJOINT = auto()
    """No value in sequence A may also occur in sequence B.

    Order and duplicates inside either sequence are ignored. The relation
    fails if any value in one sequence is equal to a value in the other
    sequence.
    """


# pylint: disable-next=too-few-public-methods
class ListRelationValidator(WholeConfigValidator):
    """Validate that one list-like value has a relation to another.

    Each side of the relation is either read from a named ``Config`` member or
    computed by a projector. A value read from a config member is expected to
    be a finite sequence represented by that member, but not a ``str``,
    ``bytes``, or ``bytearray``. A projected value may be any finite
    sequence except ``str``, ``bytes``, or ``bytearray``. The validator
    conceptually materializes both values as lists before applying the
    relation.

    All element comparisons use ``eq_comparator``. ``lt_comparator`` is
    used for relation kinds or diagnostics that need a stable ordering
    of values.
    """

    # pylint: disable-next=too-many-arguments
    def __init__(self, kind: ListRelationKind, member_a_name: str,
                 member_b_name: str, *,
                 a_projector: Optional[WholeConfigProjector] = None,
                 b_projector: Optional[WholeConfigProjector] = None,
                 eq_comparator: Callable[[object, object], bool] = eq,
                 lt_comparator: Callable[[object, object], bool] =
                 _DEFAULT_LT_COMPARATOR) -> None:
        """Initialize a list relation validator.

        Args:
            kind: Relation to require between the two values.
            member_a_name: Name of the first member to compare.
                If ``a_projector`` is not supplied, this is the name of a
                member in the ``Config`` object whose value is sequence A.
                If ``a_projector`` is supplied, this is the pseudo-member
                name of the projected value. The name is used for error
                messages.
            member_b_name: Name of the second member to compare.
                If ``b_projector`` is not supplied, this is the name of a
                member in the ``Config`` object whose value is sequence B.
                If ``b_projector`` is supplied, this is the pseudo-member
                name of the projected value. The name is used for error
                messages.
            a_projector: Optional projector for sequence A.
            b_projector: Optional projector for sequence B.
            eq_comparator: Function used to decide whether two element values
                are equal. The default is the equality operator.
            lt_comparator: Function used when a relation or diagnostic needs
                to order element values. The default is the less-than
                operator.

        Raises:
            TypeError: If a constructor argument has an invalid type.
            ValueError: If a member name is empty.
        """
        self.kind: ListRelationKind = _validate_relation_kind(kind)
        self.member_a_name: str = _validate_member_name(member_a_name,
                                                        'member_a_name')
        self.member_b_name: str = _validate_member_name(member_b_name,
                                                        'member_b_name')
        self.a_projector: Optional[WholeConfigProjector] = \
            _validate_optional_projector(a_projector, 'a_projector')
        self.b_projector: Optional[WholeConfigProjector] = \
            _validate_optional_projector(b_projector, 'b_projector')
        self.eq_comparator: Callable[[object, object], bool] = \
            _validate_comparator(eq_comparator, 'eq_comparator')
        self.lt_comparator: Callable[[object, object], bool] = \
            _validate_comparator(lt_comparator, 'lt_comparator')

    # pylint: disable-next=too-many-arguments
    def _relation_value(self, config: 'Config', local_name: str,
                        reported_name: str,
                        projector: Optional[WholeConfigProjector],
                        stderr_file: TextIO) -> list[object]:
        """Return one materialized relation value.

        Args:
            config: The Config object to validate.
            local_name: Real member name or pseudo-member name, as it is
                named on ``config``.
            reported_name: The same name as diagnostics report it, which is
                the path for reaching it from the top level.
            projector: Optional projector for the relation value.
            stderr_file: Stream used for user-facing diagnostics.

        Returns:
            The relation value as a list.

        Raises:
            KeyError: The member is missing and no projector was supplied.
            TypeError: The relation value is not a sequence, or it is
                ``str``, ``bytes``, or ``bytearray``.
        """
        if projector is None:
            if not hasattr(config, local_name):
                msg = 'Invalid configuration: '
                msg += f'Member {reported_name} not found in Config object.'
                _print_and_raise_key_error(msg, stderr_file)
            value = getattr(config, local_name)
        else:
            value = projector(config, stderr_file)
        return _materialized_sequence(reported_name, value, stderr_file)

    def _relation_holds(self, values_a: list[object],
                        values_b: list[object]) -> bool:
        """Return whether the configured relation holds.

        Args:
            values_a: Sequence A materialized as a list.
            values_b: Sequence B materialized as a list.

        Returns:
            ``True`` if the configured relation holds.
        """
        if self.kind == ListRelationKind.EQUAL:
            return len(values_a) == len(values_b) and all(
                self.eq_comparator(value_a, value_b)
                for value_a, value_b in zip(values_a, values_b))
        if self.kind == ListRelationKind.MULTISET_EQUAL:
            return _is_multiset_equal(values_a, values_b, self.eq_comparator)
        if self.kind == ListRelationKind.SET_EQUAL:
            return _is_distinct_subset(values_a, values_b,
                                       self.eq_comparator) and \
                _is_distinct_subset(values_b, values_a, self.eq_comparator)
        if self.kind == ListRelationKind.SUBSET:
            return _is_distinct_subset(values_a, values_b, self.eq_comparator)
        return _is_disjoint(values_a, values_b, self.eq_comparator)

    def validate(self, config: 'Config', stderr_file: TextIO = sys.stderr, *,
                 member_name: Optional[str] = None) -> None:
        """Validate the configured relation between two list-like values.

        If no projector is supplied for a side, that side is read from the
        named ``Config`` member. If a projector is supplied, the projector
        receives the complete ``Config`` object and the diagnostic stream, and
        its returned value is used as that side of the relation.

        Both relation values must be finite sequences, but not ``str``,
        ``bytes``, or ``bytearray``. Rejecting those scalar text and binary
        types keeps accidental character-by-character comparison from being
        treated as a valid configuration relation.

        Args:
            config: The Config object to validate.
            stderr_file: Stream used for user-facing diagnostics.
            member_name: Dotted and indexed path for reaching ``config``
                by traversing nested attributes from the top level of the
                complete ``validate()`` operation, such as
                ``outputs[1].section``. ``None`` means that ``config`` is the
                top level and not a member of anything.

        Raises:
            KeyError: A side has no projector and the named member is not
                present in ``config``.
            TypeError: One relation value is not a sequence, or it is
                ``str``, ``bytes``, or ``bytearray``.
            InvalidConfiguration: The relation does not hold.
        """
        reported_a = member_path(member_name, self.member_a_name)
        reported_b = member_path(member_name, self.member_b_name)
        values_a = self._relation_value(config=config,
                                        local_name=self.member_a_name,
                                        reported_name=reported_a,
                                        projector=self.a_projector,
                                        stderr_file=stderr_file)
        values_b = self._relation_value(config=config,
                                        local_name=self.member_b_name,
                                        reported_name=reported_b,
                                        projector=self.b_projector,
                                        stderr_file=stderr_file)
        if not self._relation_holds(values_a, values_b):
            msg = 'Invalid configuration: '
            msg += f'Relation {self.kind.name} does not hold between '
            msg += f'{reported_a} and {reported_b}.'
            _print_and_raise_invalid(msg, stderr_file)
