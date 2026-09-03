#! /usr/local/bin/python3
"""Optional validator."""

# Copyright (c) 2026 Tom Björkholm
# MIT License

from typing import Optional, TextIO
import sys
from config_as_json.config import Config
from config_as_json.validator import MemberValidator, MemberValidatorSequence


def _validate_mvalidator(validator: MemberValidator | list[MemberValidator]) \
        -> MemberValidator:
    """Validate a MemberValidator or list of MemberValidators."""
    if isinstance(validator, list):
        if not validator:
            msg1 = 'Expected non-empty list of MemberValidators, '
            msg1 += 'but got empty list instead.'
            raise ValueError(msg1)
        if not all(isinstance(v, MemberValidator) for v in validator):
            msg2 = 'Expected list of MemberValidators, '
            msg2 += 'but got list with elements of type other than '
            msg2 += 'MemberValidator. Found elements of type '
            msg2 += ', '.join(type(v).__name__ for v in validator)
            raise TypeError(msg2)
        return MemberValidatorSequence(validators=validator)
    if not isinstance(validator, MemberValidator):
        msg3 = 'Expected MemberValidator or list of MemberValidators, '
        msg3 += f'but got type {type(validator).__name__} instead.'
        raise TypeError(msg3)
    return validator


# pylint: disable-next=too-few-public-methods
class OptionalMemberValidator(MemberValidator):
    """Validate an optional member."""

    def __init__(self,
                 validator: MemberValidator | list[MemberValidator]) -> None:
        """Construct validator for an optional member.

        Args:
            validator: Validator or list of validators to use for the
                       value if it is not None.
        Raises:
            TypeError: If ``validator`` is not a MemberValidator or
                       list of MemberValidators.
            ValueError: If ``validator`` is an empty list.
        """
        self.validator: MemberValidator = _validate_mvalidator(validator)

    def validate_member(self, config: Config, member_name: str,
                        member_value: object,
                        stderr_file: TextIO = sys.stderr) -> Optional[object]:
        """Validate one member if it is not None.

        Args:
            config: The Config object that owns the member.
            member_name: The reported dotted and indexed path of the
                member to validate.
            member_value: The member value to validate.
            stderr_file: The file to write error messages to.

        Returns:
            None if ``member_value`` is None. Otherwise, the result of
            validating ``member_value`` using the supplied validator(s),
            that may normalize the value.

        Raises:
            The same exceptions as the supplied validator(s).
        """
        if member_value is None:
            return None
        return self.validator.validate_member(config=config,
                                              member_name=member_name,
                                              member_value=member_value,
                                              stderr_file=stderr_file)
