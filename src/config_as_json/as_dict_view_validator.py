#! /usr/local/bin/python3
"""Validate a member value through a dictionary-shaped view."""

# Copyright (c) 2024-2026 Tom Björkholm
# MIT License

import sys
from collections.abc import Callable, Hashable, Sequence
from typing import Optional, TextIO, TYPE_CHECKING, cast
from config_as_json.validator import InvalidConfiguration, MemberValidator
from config_as_json.dict_validators import DictForEachValidator, DictRule, \
    _validate_for_each_rules
if TYPE_CHECKING:
    from config_as_json.config import Config


def public_attrs_to_dict(config: 'Config', member_name: str,
                         member_value: object, stderr_file: TextIO) \
                             -> dict[Hashable, object]:
    """Project public object attributes to a dictionary.

    This helper is the explicit opt-in conversion for the common case where
    an application class stores its configuration data in normal public
    instance attributes. The intended dictionary view contains every
    non-callable entry in ``vars(member_value)`` whose name does not start
    with ``'_'``.

    The projected dictionary is intended to be a shallow copy. Replacing a
    value in the projected dictionary should not replace the corresponding
    attribute on ``member_value``. If an attribute value is itself mutable,
    validators that mutate that shared value in place may still affect the
    original object.

    Args:
        config: The configuration object that owns ``member_name``.
        member_name: The name of the member being projected.
        member_value: The non-dict object to project.
        stderr_file: The stream used for diagnostics.

    Returns:
        A dictionary-shaped validation view of ``member_value``.

    Raises:
        InvalidConfiguration: If ``member_value`` cannot be projected from
            public attributes.
    """
    _ = config
    try:
        attributes = vars(member_value)
    except TypeError as exc:
        msg = 'Invalid configuration: '
        msg += f'Value for {member_name} cannot be projected to a dict '
        msg += 'from public attributes.'
        print(msg, file=stderr_file)
        raise InvalidConfiguration(msg) from exc
    return {key: value for key, value in attributes.items()
            if not key.startswith('_') and not callable(value)}


def _validate_non_dict_type(non_dict_type: object) -> type[object]:
    """Validate and return the accepted non-dict runtime type."""
    if not isinstance(non_dict_type, type):
        raise TypeError('non_dict_type must be a type.')
    if issubclass(non_dict_type, dict):
        msg = 'non_dict_type may not be dict or a dict subclass.'
        raise TypeError(msg)
    return non_dict_type


def _validate_to_dict(to_dict: object) -> Callable[
        ['Config', str, object, TextIO], dict[Hashable, object]]:
    """Validate and return the dictionary-view projector."""
    if not callable(to_dict):
        raise TypeError('to_dict must be callable.')
    return cast(Callable[
        ['Config', str, object, TextIO], dict[Hashable, object]], to_dict)


def _validate_rules(rules: object) -> list[DictRule]:
    """Validate and return dictionary rules for the view."""
    if not isinstance(rules, Sequence):
        raise TypeError('rules must be a sequence.')
    if len(rules) != 0:
        _validate_for_each_rules(rules)
    return list(rules)


def _validate_validators(validators: Optional[Sequence[MemberValidator]]) \
        -> list[MemberValidator]:
    """Validate and return whole-dict validators for the view."""
    if validators is None:
        return []
    if not isinstance(validators, Sequence):
        raise TypeError('validators must be None or a sequence.')
    for index, validator in enumerate(validators):
        if not isinstance(validator, MemberValidator):
            msg = f'validators[{index}] must be a MemberValidator.'
            raise TypeError(msg)
    return list(validators)


def _ensure_work_exists(rules: Sequence[DictRule],
                        validators: Sequence[MemberValidator]) -> None:
    """Validate that the validator has at least one operation to run."""
    if len(rules) == 0 and len(validators) == 0:
        msg = 'rules must be non-empty when validators is None or empty.'
        raise ValueError(msg)


def _raise_invalid_member_type(member_name: str, member_value: object,
                               non_dict_type: type[object],
                               stderr_file: TextIO) -> None:
    """Raise an invalid-configuration error for an unsupported value type."""
    msg = 'Invalid configuration: '
    msg += f'Value for {member_name} is not a dict or '
    msg += f'{non_dict_type.__name__}.'
    _ = member_value
    print(msg, file=stderr_file)
    raise InvalidConfiguration(msg)


def _validate_projected_dict(member_name: str, projected: object,
                             stderr_file: TextIO) \
        -> dict[Hashable, object]:
    """Validate and return one projected dictionary view."""
    if not isinstance(projected, dict):
        msg = 'Invalid configuration: '
        msg += f'Dictionary view for {member_name} is not a dict.'
        print(msg, file=stderr_file)
        raise InvalidConfiguration(msg)
    return projected


def _validate_dict_view_step(
        validator: MemberValidator, config: 'Config', member_name: str,
        member_value: dict[Hashable, object],
        stderr_file: TextIO) -> dict[Hashable, object]:
    """Run one dict-view validator and require a dict result."""
    result = validator.validate_member(config, member_name, member_value,
                                       stderr_file)
    return _validate_projected_dict(member_name=member_name, projected=result,
                                    stderr_file=stderr_file)


def _validation_chain(rules: Sequence[DictRule],
                      validators: Sequence[MemberValidator]) \
        -> list[MemberValidator]:
    """Return the complete validation chain for one dictionary view."""
    result: list[MemberValidator] = list(validators)
    if len(rules) != 0:
        result.append(DictForEachValidator(rules))
    return result


# pylint: disable-next=too-few-public-methods
class AsDictViewValidator(MemberValidator):
    """Validate a member value through a dictionary-shaped view.

    ``AsDictViewValidator`` handles a member whose runtime value may be either
    a real ``dict`` or one application-defined object type that can be
    projected to a ``dict``. The same dictionary validators and dictionary
    rules are applied to both representations, so application code can define
    one validation policy for the dictionary-shaped data.

    The class is a convenience adapter for the common case where dictionary
    validation mainly consists of a list of ``DictRule`` objects. Conceptually
    it branches on the member value type, uses ``to_dict`` only for the
    non-dict representation, applies the optional whole-dict validators, and
    finally applies a ``DictForEachValidator`` built from ``rules``.

    The member value must be either an actual ``dict`` or an instance of
    ``non_dict_type``. Other mapping implementations are not accepted by this
    validator. Keeping the contract limited to ``dict`` avoids ambiguity
    about how replacement values from validators should be stored.

    If the member value is a ``dict``, validators and rules are applied to the
    dictionary value. Replacement values returned by validators and rules are
    returned from ``validate_member`` and are therefore stored back into the
    configuration member by ``MemberValidationStep``.

    If the member value is an instance of ``non_dict_type``, ``to_dict`` is
    called to produce a dictionary view, and validators and rules are applied
    to that view. Replacement values returned while validating the projected
    view are used only inside this validation chain. The original object is
    returned from ``validate_member`` and remains the stored configuration
    member. In-place mutation may still affect shared mutable objects if the
    projector exposes them.
    """

    def __init__(self, non_dict_type: type[object], rules: Sequence[DictRule],
                 to_dict: Callable[['Config', str, object, TextIO],
                                   dict[Hashable, object]],
                 validators: Optional[Sequence[MemberValidator]] = None) \
            -> None:
        """Initialize the as-dict-view validator.

        Args:
            non_dict_type: The accepted application-defined object type when
                the member value is not a ``dict``. This type may not be
                ``dict`` or a subclass of ``dict``.
            rules: Dictionary rules applied to the dictionary view after
                ``validators`` have run. This keeps the common
                ``DictForEachValidator`` use case concise.
            to_dict: Callable that receives the complete config object, the
                member name, the non-dict member value, and the diagnostic
                stream. It returns the dictionary view to validate.
                ``public_attrs_to_dict`` is a candidate when the view should
                be the object's public instance attributes.
            validators: Optional sequence of whole-dict validators to apply
                to the dictionary view before applying ``rules``. Each
                validator receives the value returned by the previous
                validator.

        Raises:
            TypeError: If ``non_dict_type`` is not a type, is ``dict`` or a
                subclass of ``dict``, if ``to_dict`` is not callable, or if
                any validator is not a ``MemberValidator``.
            ValueError: If both ``rules`` is empty and ``validators`` is None
                or empty.
        """
        self.non_dict_type: type[object] = \
            _validate_non_dict_type(non_dict_type)
        self.to_dict: Callable[
            ['Config', str, object, TextIO], dict[Hashable, object]] = \
            _validate_to_dict(to_dict)
        self.rules: list[DictRule] = _validate_rules(rules)
        whole_validators = _validate_validators(validators)
        _ensure_work_exists(self.rules, whole_validators)
        self.validators: list[MemberValidator] = \
            _validation_chain(self.rules, whole_validators)

    def _validate_dict_view(
            self, config: 'Config', member_name: str,
            dict_view: dict[Hashable, object], stderr_file: TextIO) \
            -> Optional[object]:
        """Validate one dictionary view and return its normalized value."""
        current: dict[Hashable, object] = dict_view
        for validator in self.validators:
            current = _validate_dict_view_step(
                validator=validator, config=config, member_name=member_name,
                member_value=current, stderr_file=stderr_file)
        return current

    def validate_member(self, config: 'Config', member_name: str,
                        member_value: object,
                        stderr_file: TextIO = sys.stderr) -> Optional[object]:
        """Validate one member through a dictionary-shaped view.

        Args:
            config: The configuration object that owns ``member_name``.
            member_name: The name of the member to validate.
            member_value: The member value to validate.
            stderr_file: The file to write error messages to.

        Returns:
            The normalized dictionary if ``member_value`` is a ``dict``.
            The original ``member_value`` if it is an instance of
            ``non_dict_type`` and its dictionary view validates.

        Raises:
            InvalidConfiguration: If ``member_value`` is neither a ``dict``
                nor an instance of ``non_dict_type``, if projection fails, if
                the projector does not return a ``dict``, or if a validator
                rejects the dictionary view.
            InvalidConfigurationValue: If an inner validator rejects a value
                because it is not one of its allowed values.
        """
        if isinstance(member_value, dict):
            return self._validate_dict_view(config=config,
                                            member_name=member_name,
                                            dict_view=member_value,
                                            stderr_file=stderr_file)
        if not isinstance(member_value, self.non_dict_type):
            _raise_invalid_member_type(member_name=member_name,
                                       member_value=member_value,
                                       non_dict_type=self.non_dict_type,
                                       stderr_file=stderr_file)
        dict_view = self.to_dict(config, member_name, member_value,
                                 stderr_file)
        validated = _validate_projected_dict(member_name=member_name,
                                             projected=dict_view,
                                             stderr_file=stderr_file)
        _ = self._validate_dict_view(config=config, member_name=member_name,
                                     dict_view=validated,
                                     stderr_file=stderr_file)
        return member_value
