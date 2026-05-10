#! /usr/local/bin/python3
"""Validate that a list of values compares to a reference list of values.

The validator is used to validate that a list of values (which may be
a projected value) compares in the specified way to another list of
values (which might also be a projected value).
"""

# Copyright (c) 2026 Tom Björkholm
# MIT License

from typing import Callable, Optional, TextIO, TYPE_CHECKING
from enum import Enum, auto
from operator import eq, lt
import sys
from config_as_json.validator import WholeConfigValidator
from config_as_json.projected_validators import WholeConfigProjector
if TYPE_CHECKING:
    from config_as_json.config import Config


class ListComparisonKind(Enum):
    """Kind of list comparison."""

    EQUAL = auto()
    """The list of values must be equal to the other list of values.

    For each position in the list of values, the value must be equal to the
    value in the same position in the other list of values, using the
    supplied equality comparison function (which is typically ==).
    """

    EQUAL_IF_SORTED = auto()
    """The sorted list of values must be equal to another sorted list.

    After sorting the lists, using the supplied comparison function, the
    lists must be equal according to the EQUAL rule:
    For each position in the first list of values, the value must be equal
    to the value in the same position in the second list of values, using the
    supplied equality comparison function (which is typically ==).
    """

    SET_EQUAL = auto()
    """All values in one list must also be in the other list.

    The lists must have the same values, regardless of order or multiplicity.
    """

    SUBSET = auto()
    """All values in list A must also be in list B.

    The values in list A must be a subset of the values in list B,
    regardless of order or multiplicity.
    """

    DISJOINT = auto()
    """No values in list A must also be in list B, and vice versa.

    The values in list A must be disjoint from the values in list B,
    regardless of order or multiplicity. No value in either list may appear
    in the other list.
    """


# pylint: disable-next=too-few-public-methods
class ListComparisonValidator(WholeConfigValidator):
    """Validate that a list of values compares to another list of values.

    The validator is used to validate that a list of values (which may be
    a projected value) compares in the specified way to another list of
    values (which might also be a projected value).
    """

    # pylint: disable-next=too-many-arguments,too-many-positional-arguments
    def __init__(self, kind: ListComparisonKind, member_a_name: str,
                 member_b_name: str,
                 a_projector: Optional[WholeConfigProjector] = None,
                 b_projector: Optional[WholeConfigProjector] = None,
                 eq_function: Callable[[object, object], bool] = eq,
                 lt_function: Callable[[object, object], bool] = lt,
                 stderr_file: TextIO = sys.stderr) -> None:
        """Initialize a list comparison validator.

        Args:
            kind: Kind of list comparison.
            member_a_name: Name of the first member to compare.
                           If a_projector is not supplied, this is the name of
                           a member in the Config object, whose value is the
                           list A to compare.
                           If a_projector is supplied, this is the
                           pseudo-member name of the projected value and the
                           name must not be a name of a member in the Config
                           object.
                           The name is used for error messages.
            member_b_name: Name of the second member to compare.
                           If b_projector is not supplied, this is the name of
                           a member in the Config object, whose value is the
                           list B to compare.
                           If b_projector is supplied, this is the
                           pseudo-member name of the projected value and the
                           name must not be a name of a member in the Config
                           object.
                           The name is used for error messages.
            a_projector: Optional projector for the first member (A).
            b_projector: Optional projector for the second member (B).
            eq_function: Function to compare values for equality, which is
                         used to compare the values in the lists. The default
                         is the equality operator.
            lt_function: Function to compare values for less than, which is
                         used to sort the lists in comparisons that work on
                         sorted lists. The default is the less than operator.
            stderr_file: Stream used for user-facing diagnostics.
        """
        # to be implemented here: check the arguments
        # and initialize the instance

    def validate(self, config: 'Config',
                 stderr_file: TextIO = sys.stderr) -> None:
        """Validate how two lists of values compare.

        The validator is used to validate that a list of values (which may be
        a projected value) compares in the specified way to a another list of
        values (which might also be a projected value).

        Args:
            config: The Config object to validate.
            stderr_file: Stream used for user-facing diagnostics.

        Raises:
            InvalidConfiguration: The configuration is invalid.
        """
        # to be implemented here: validate the list of values
        # and the reference list of values
