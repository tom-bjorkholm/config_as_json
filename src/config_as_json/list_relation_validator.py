#! /usr/local/bin/python3
"""Validate that one list-like value has a relation to another.

The validator is used to validate that a list-like value (which may be
a projected value) has the specified relation to another list-like value
(which might also be a projected value).
"""

# Copyright (c) 2026 Tom Björkholm
# MIT License

import sys
from enum import Enum, auto
from operator import eq, lt
from typing import Callable, Optional, TextIO, TYPE_CHECKING, cast
from config_as_json.validator import WholeConfigValidator
from config_as_json.projected_validators import WholeConfigProjector
if TYPE_CHECKING:
    from config_as_json.config import Config


_DEFAULT_LT_COMPARATOR: Callable[[object, object], bool] = \
    cast(Callable[[object, object], bool], lt)


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
        # to be implemented here: check the arguments
        # and initialize the instance

    def validate(self, config: 'Config',
                 stderr_file: TextIO = sys.stderr) -> None:
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

        Raises:
            KeyError: A side has no projector and the named member is not
                present in ``config``.
            TypeError: One relation value is not a non-string sequence.
            InvalidConfiguration: The relation does not hold.
        """
        # to be implemented here: validate the relation values
