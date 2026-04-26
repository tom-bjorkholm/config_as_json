#! /usr/local/bin/python3
"""Define validators that validate projected member values."""

# Copyright (c) 2026 Tom Björkholm
# MIT License

import sys
from collections.abc import Callable, Sequence
from typing import Optional, TextIO, TYPE_CHECKING
from config_as_json.validator import MemberValidator
if TYPE_CHECKING:
    from config_as_json.config import Config


def _validate_projector(
        projector: Callable[['Config', str, object, TextIO], object]) -> None:
    """Validate the projector argument.

    Args:
        projector: Callable that computes the value to validate.

    Raises:
        TypeError: If ``projector`` is not callable.
    """
    if not callable(projector):
        raise TypeError('projector must be callable.')


def _validate_optional_source_validator(
        source_validator: Optional[MemberValidator]) -> None:
    """Validate the optional source validator argument.

    Args:
        source_validator: Optional validator for the source member value.

    Raises:
        TypeError: If ``source_validator`` is not ``None`` or a
            ``MemberValidator``.
    """
    if source_validator is None:
        return
    if not isinstance(source_validator, MemberValidator):
        msg = 'source_validator must be None or a MemberValidator.'
        raise TypeError(msg)


def _validate_projected_validators(
        validators: Sequence[MemberValidator]) -> None:
    """Validate validators applied to the projected value.

    Args:
        validators: Validators to apply to the projected value.

    Raises:
        TypeError: If ``validators`` is not a sequence or one entry is not a
            ``MemberValidator``.
        ValueError: If ``validators`` is empty.
    """
    if not isinstance(validators, Sequence):
        raise TypeError('validators must be a sequence.')
    if len(validators) == 0:
        raise ValueError('validators must be non-empty.')
    for index, validator in enumerate(validators):
        if not isinstance(validator, MemberValidator):
            msg = f'validators[{index}] must be a MemberValidator.'
            raise TypeError(msg)


class ProjectedMemberValidator(  # pylint: disable=too-few-public-methods
        MemberValidator):
    """Validate a projected value while keeping the original member value.

    This validator is intended for configuration members whose natural
    validation view is not the stored value itself. A projector function
    computes that validation view from the original member value, and a
    sequence of inner validators is then applied to the projected value.

    ``source_validator`` is an optional validator for the source member value
    before projection. It is useful when the projector benefits from a
    validated or normalized source view. If it is supplied, the value it
    returns is passed to ``projector`` instead of the original member value.

    Projected validators are applied in order. If one projected validator
    returns a normalized or replacement projected value, that returned value
    is passed to the next projected validator. The final projected value is
    discarded when validation succeeds, and the original member value is
    returned.

    Returned replacement values from ``source_validator`` and projected
    validators affect only this validation chain. They do not replace the
    stored member value. The validator does not copy the source or projected
    value, though. In-place mutation done by ``source_validator``, by the
    projector, or by a projected validator can still affect shared mutable
    objects. Validators and projectors that need isolation should return or
    work on detached values.
    """

    def __init__(
            self,
            projector: Callable[['Config', str, object, TextIO], object],
            validators: Sequence[MemberValidator],
            source_validator: Optional[MemberValidator] = None) -> None:
        """Initialize the projected member validator.

        Args:
            projector: Callable that receives the complete config object,
                the member name, the original member value, and the diagnostic
                stream. It returns the projected value to validate.
            validators: Validators to apply to the projected value. They are
                applied in declaration order, and each validator receives the
                value returned by the previous validator.
            source_validator: Optional validator applied to the original
                member value before projection. Its returned value is passed
                to ``projector``.

        Raises:
            ValueError: If ``validators`` is empty.
            TypeError: If ``projector`` is not callable or any validator is
                not a ``MemberValidator``.
        """
        _validate_projector(projector)
        _validate_optional_source_validator(source_validator)
        _validate_projected_validators(validators)
        self.projector: Callable[['Config', str, object, TextIO], object] = \
            projector
        self.validators: list[MemberValidator] = list(validators)
        self.source_validator: Optional[MemberValidator] = \
            source_validator

    def validate_member(self, config: 'Config', member_name: str,
                        member_value: object,
                        stderr_file: TextIO = sys.stderr) -> Optional[object]:
        """Validate one member through a projected value.

        Args:
            config: The Config object that owns the member.
            member_name: The name of the member to validate.
            member_value: The original member value.
            stderr_file: The file to write error messages to.

        Returns:
            The original ``member_value`` when validation succeeds. Returned
            normalized source or projected values affect only this validation
            chain, not the stored config member.

        Raises:
            InvalidConfiguration: If the projector or an inner validator
                detects an invalid configuration.
            InvalidConfigurationValue: If an inner validator rejects a value
                because it is not one of its allowed values.
        """
        source = member_value
        if self.source_validator is not None:
            source = self.source_validator.validate_member(
                config=config, member_name=member_name,
                member_value=source, stderr_file=stderr_file)
        current = self.projector(config, member_name, source, stderr_file)
        for validator in self.validators:
            current = validator.validate_member(
                config=config, member_name=member_name,
                member_value=current, stderr_file=stderr_file)
        return member_value
