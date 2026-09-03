#! /usr/local/bin/python3
"""Implement per-element validators for list members."""

# Copyright (c) 2024-2026 Tom Björkholm
# MIT License

import sys
from typing import Optional, Sequence, TextIO
from config_as_json._list_validator_common import _validate_list_member_value
from config_as_json.config import Config
from config_as_json.dict_validators import DictKeysValidator
from config_as_json.validator import InvalidConfiguration, MemberValidator


def _check_element_validators(
        element_validators: Sequence[MemberValidator]) -> None:
    """Validate the ``element_validators`` argument of ListForEachValidator.

    Args:
        element_validators: Validators to apply to each list element.

    Raises:
        ValueError: If ``element_validators`` is empty.
        TypeError: If any entry is not a ``MemberValidator``.
    """
    if len(element_validators) == 0:
        raise ValueError('element_validators must be non-empty.')
    for index, validator in enumerate(element_validators):
        if not isinstance(validator, MemberValidator):
            msg = f'element_validators[{index}] must be a MemberValidator.'
            raise TypeError(msg)


def _check_element_type_arg(element_type: Optional[type[object]]) -> None:
    """Validate the ``element_type`` argument of ListForEachValidator.

    Args:
        element_type: Optional required runtime type of each list element.

    Raises:
        TypeError: If ``element_type`` is not ``None`` and not a ``type``.
    """
    if element_type is None:
        return
    if not isinstance(element_type, type):
        raise TypeError('element_type must be a type or None.')


# pylint: disable-next=too-few-public-methods
class ListForEachValidator(MemberValidator):
    """Apply a sequence of inner validators to each element of a list.

    This validator is the general composition mechanism for list members.
    It iterates the outer list and delegates all per-element work to the
    ``element_validators`` sequence. It has no opinion about what an
    element is: every inner validator is a ``MemberValidator`` and can
    therefore be any of the built-in validators or a user-defined one.

    Typical use cases include, but are not restricted to:

    - Lists of lists (a matrix) where each inner list is checked with
      other list validators such as ``ListSizeValidator`` or
      ``ListValueValidator``.
    - Lists of dicts where each element is checked with the built-in
      ``DictKeysValidator`` and ``DictForEachValidator`` (or any
      user-defined ``MemberValidator``) used as inner element
      validators.
    - Lists of scalar values where each element is checked or normalized
      by a user-defined validator. For example a custom ``MemberValidator``
      may spell-check each string, convert each string to upper case, or
      apply any other per-element rule that the built-in scalar list
      validators do not cover.

    Because ``ListForEachValidator`` is itself a ``MemberValidator``, one
    instance can be an element validator of another, so nesting is not
    limited to a single inner layer.

    The member value must be a list. For each element, in order:

    1. If ``element_type`` was provided, the element must be an instance of
       that type.
    2. Every validator in ``element_validators`` is invoked on the element,
       in order. Each validator receives the value returned by the previous
       validator, so normalization performed by one inner validator is
       visible to the next one.
    3. The final value returned for that element is collected into a new
       list that is returned from ``validate_member``.

    When an inner validator is invoked, ``member_name`` is the outer member
    name with the element index appended in square brackets, for example
    ``'matrix[3]'``. The validator's error messages therefore stay precise
    about which element failed. The ``member_name`` is built as the
    configuration structure is traversed. The top level member name starts
    the string as a plain string. When "indexing" into a list or dict the
    index is appended in square brackets. When going into a class member
    a dot and the member name is appended.

    List-level size or ordering checks are intentionally not part of this
    class. Use a separate ``ListSizeValidator`` (or any other list
    validator) as an earlier or later step in the ``ValidationPlan``.
    """

    def __init__(self, element_validators: Sequence[MemberValidator],
                 element_type: Optional[type[object]] = None) -> None:
        """Initialize the validator.

        Args:
            element_validators: Non-empty sequence of validators to apply
                to each list element, in order. Each entry must be a
                ``MemberValidator``.
            element_type: Optional required runtime type of each list
                element. If ``None``, the type check is skipped and the
                inner validators are solely responsible for type checks.

        Raises:
            ValueError: If ``element_validators`` is empty.
            TypeError: If any entry of ``element_validators`` is not a
                ``MemberValidator``, or if ``element_type`` is not ``None``
                and not a ``type``.
        """
        _check_element_validators(element_validators)
        _check_element_type_arg(element_type)
        self.element_validators: list[MemberValidator] = \
            list(element_validators)
        self.element_type: Optional[type[object]] = element_type

    def _validate_element_type(self, member_name: str, index: int,
                               element: object, stderr_file: TextIO) -> None:
        """Check one element's type when ``element_type`` is configured.

        Args:
            member_name: The reported path of the outer member, used in
                error messages.
            index: The index of the element in the outer list.
            element: The element to type-check.
            stderr_file: The file to write error messages to.

        Raises:
            InvalidConfiguration: If ``element`` is not an instance of
                ``self.element_type``.
        """
        if self.element_type is None:
            return
        if isinstance(element, self.element_type):
            return
        msg = 'Invalid configuration: '
        msg += f'Value at {member_name}[{index}] has type '
        msg += f'{type(element).__name__}; expected '
        msg += f'{self.element_type.__name__}.'
        print(msg, file=stderr_file)
        raise InvalidConfiguration(msg)

    def validate_member(self, config: Config, member_name: str,
                        member_value: object,
                        stderr_file: TextIO = sys.stderr) -> Optional[object]:
        """Validate one list member by delegating to the inner validators.

        Args:
            config: The Config object that owns the member.
            member_name: The reported path of the outer list member to
                validate.
            member_value: The list value to validate.
            stderr_file: The file to write error messages to.

        Returns:
            A new list whose elements are the values returned by the last
            inner validator for each element. The caller's list is never
            modified in place.

        Raises:
            InvalidConfiguration: If the member is not a list, an element
                has the wrong runtime type, or a supplied validator raised
                ``InvalidConfiguration``.
            InvalidConfigurationValue: If a supplied validator raised
                ``InvalidConfigurationValue``.
        """
        raw_list = _validate_list_member_value(member_name=member_name,
                                               member_value=member_value,
                                               stderr_file=stderr_file)
        result: list[object] = []
        for index, element in enumerate(raw_list):
            self._validate_element_type(member_name=member_name, index=index,
                                        element=element,
                                        stderr_file=stderr_file)
            element_name = f'{member_name}[{index}]'
            current: object = element
            for validator in self.element_validators:
                current = validator.validate_member(config=config,
                                                    member_name=element_name,
                                                    member_value=current,
                                                    stderr_file=stderr_file)
            result.append(current)
        return result


# pylint: disable-next=too-few-public-methods
class ListOfDictsKeysValidator(MemberValidator):
    """Validate the keys of every dict element in a list member.

    This is the dedicated predefined validator for the common "list of
    dictionaries with a fixed key policy" shape. It is equivalent to using a
    ``ListForEachValidator`` with ``element_type=dict`` and one inner
    ``DictKeysValidator``. Pass ``allow_extra_dict_keys=True`` for an open
    dict shape where each element must contain selected mandatory keys but
    may also carry application-specific extra keys.
    """

    def __init__(self, mandatory_keys: Sequence[str],
                 allowed_keys: Optional[Sequence[str]] = None,
                 allow_extra_dict_keys: bool = False) -> None:
        """Initialize the validator.

        Args:
            mandatory_keys: Keys that must be present in every dict element.
            allowed_keys: Additional keys that are permitted but not required.
            allow_extra_dict_keys: Whether keys not listed in
                ``mandatory_keys`` or ``allowed_keys`` should be accepted.

        Raises:
            TypeError: If any key entry is not a string.
            ValueError: If a key sequence contains duplicates.
        """
        self._validator = ListForEachValidator(
            element_validators=[DictKeysValidator(
                mandatory_keys=mandatory_keys, allowed_keys=allowed_keys,
                allow_extra_dict_keys=allow_extra_dict_keys)],
            element_type=dict)

    def validate_member(self, config: Config, member_name: str,
                        member_value: object,
                        stderr_file: TextIO = sys.stderr) -> Optional[object]:
        """Validate one list-of-dicts member against the configured keys.

        Args:
            config: The Config object that owns the member.
            member_name: The reported path of the list member to validate.
            member_value: The list value to validate.
            stderr_file: The file to write error messages to.

        Returns:
            A new list containing the validated dict elements.

        Raises:
            InvalidConfiguration: If the member is not a list, one element is
                not a dict, one dict misses a mandatory key, or one dict has
                an unknown key while ``allow_extra_dict_keys`` is ``False``.
        """
        return self._validator.validate_member(config=config,
                                               member_name=member_name,
                                               member_value=member_value,
                                               stderr_file=stderr_file)
