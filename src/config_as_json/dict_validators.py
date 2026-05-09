#! /usr/local/bin/python3
"""Implement dictionary validators for config-as-json.

The ``Config`` base class already checks each dict member's keys against the
default; list a member in ``_unchecked_dicts`` when validators here (for
example ``DictKeysValidator``) should own that member's key or value policy
completely instead. See :class:`DictKeysValidator` for the full picture.
"""

# Copyright (c) 2026 Tom Björkholm
# MIT License

import sys
from collections.abc import Hashable, Sequence as SequenceABC
from dataclasses import dataclass
from typing import Callable, Optional, Sequence, TextIO
from config_as_json.config import Config
from config_as_json.validator import InvalidConfiguration, MemberValidator


def _validate_dict_member_value(member_name: str, member_value: object,
                                stderr_file: TextIO) -> dict[Hashable, object]:
    """Validate that one member value is a dict and return it.

    Args:
        member_name: The member name used in any error message.
        member_value: The value to validate.
        stderr_file: The file to write error messages to.

    Returns:
        The validated dict value.

    Raises:
        InvalidConfiguration: If ``member_value`` is not a dict.
    """
    if not isinstance(member_value, dict):
        msg = 'Invalid configuration: '
        msg += f'Value for {member_name} is not a dict.'
        print(msg, file=stderr_file)
        raise InvalidConfiguration(msg)
    return member_value


def _validate_string_keys(keys: Sequence[str], parameter_name: str) -> None:
    """Validate that ``keys`` is a sequence of distinct strings.

    Args:
        keys: The sequence to validate.
        parameter_name: Name used in error messages.

    Raises:
        TypeError: If any entry of ``keys`` is not a ``str``.
        ValueError: If ``keys`` contains a duplicate entry.
    """
    seen: set[str] = set()
    for index, key in enumerate(keys):
        if not isinstance(key, str):
            msg = f'{parameter_name}[{index}] must be a str.'
            raise TypeError(msg)
        if key in seen:
            msg = f'{parameter_name}[{index}]={key!r} duplicates an '
            msg += 'earlier entry.'
            raise ValueError(msg)
        seen.add(key)


def _validate_hashable_keys(keys: Sequence[Hashable],
                            parameter_name: str) -> None:
    """Validate that ``keys`` is a sequence of distinct hashable values.

    Args:
        keys: The sequence to validate.
        parameter_name: Name used in error messages.

    Raises:
        TypeError: If any entry of ``keys`` is not hashable.
        ValueError: If ``keys`` contains a duplicate entry.
    """
    seen: set[Hashable] = set()
    for index, key in enumerate(keys):
        if not isinstance(key, Hashable):
            msg = f'{parameter_name}[{index}] must be hashable.'
            raise TypeError(msg)
        if key in seen:
            msg = f'{parameter_name}[{index}]={key!r} duplicates an '
            msg += 'earlier entry.'
            raise ValueError(msg)
        seen.add(key)


def _validate_bool_argument(value: bool, parameter_name: str) -> None:
    """Validate that a constructor argument is a bool.

    Args:
        value: Value to validate.
        parameter_name: Name used in the error message.

    Raises:
        TypeError: If ``value`` is not a bool.
    """
    if not isinstance(value, bool):
        raise TypeError(f'{parameter_name} must be a bool.')


def _inner_member_name(outer: str, key: Hashable) -> str:
    """Return the inner member name used for a value at ``key`` of ``outer``.

    The convention is ``outer[key]``, mirroring the ``outer[index]`` form
    used by ``ListForEachValidator`` for list elements.

    Args:
        outer: The member name of the surrounding dict member.
        key: The dict key whose value is being validated.

    Returns:
        The combined inner member name.
    """
    return f'{outer}[{key}]'


# pylint: disable-next=too-few-public-methods
class DictKeysValidator(MemberValidator):
    """Validate that a dict's key set conforms to a fixed policy.

    The validator accepts only actual dict values. All keys listed in
    ``mandatory_keys`` must be present in the dict; a missing mandatory key
    is reported as an error. By default, any key in the dict that is neither
    a mandatory key nor an additional allowed key is rejected. The set of
    permitted keys is the union of ``mandatory_keys`` and ``allowed_keys``;
    a key listed in both sequences is harmless.

    When ``allow_extra_dict_keys`` is ``True``, unknown keys are accepted
    after all mandatory keys have been found. This is useful for open
    dictionary shapes where validators should require or validate only a
    selected subset of keys and pass application-specific extras through.

    The validator never modifies the dict and never inspects its values,
    so it is the natural first step in a ``ValidationPlan`` that is later
    followed by per-key value validators such as ``DictForEachValidator``.

    Interaction with :class:`Config` dict checking. The base class
    already enforces a key-set policy for each dict member by matching parsed
    JSON to the default value (unknown keys in the file are not allowed;
    which default keys may be omitted depends on the load path). For a
    fixed closed key set, that is often enough and you do not need this
    validator. Use ``DictKeysValidator`` and list the member in
    ``_unchecked_dicts`` on the :class:`Config` when you need optional keys, a
    different key policy, or when ``DictForEachValidator`` will validate
    values and you must not let the base class reject valid key sets first.
    """

    def __init__(self, mandatory_keys: Sequence[str],
                 allowed_keys: Optional[Sequence[str]] = None,
                 allow_extra_dict_keys: bool = False) -> None:
        """Initialize the validator.

        Args:
            mandatory_keys: Keys that must be present in the dict. May be
                empty if the dict is allowed to be empty (or to contain
                only optional keys).
            allowed_keys: Additional keys that are permitted but not
                required. ``None`` means no optional keys are allowed; the
                dict must contain exactly the mandatory keys unless
                ``allow_extra_dict_keys`` is ``True``.
            allow_extra_dict_keys: Whether keys not listed in
                ``mandatory_keys`` or ``allowed_keys`` should be accepted.

        Raises:
            TypeError: If any entry of ``mandatory_keys`` or
                ``allowed_keys`` is not a ``str``, or if
                ``allow_extra_dict_keys`` is not a bool.
            ValueError: If ``mandatory_keys`` or ``allowed_keys`` contains
                a duplicate entry.
        """
        _validate_string_keys(mandatory_keys, 'mandatory_keys')
        if allowed_keys is not None:
            _validate_string_keys(allowed_keys, 'allowed_keys')
        _validate_bool_argument(allow_extra_dict_keys, 'allow_extra_dict_keys')
        self.mandatory_keys: tuple[str, ...] = tuple(mandatory_keys)
        extra: tuple[str, ...] = tuple(allowed_keys) \
            if allowed_keys is not None else ()
        self.allowed_keys: frozenset[str] = \
            frozenset(self.mandatory_keys) | frozenset(extra)
        self.allow_extra_dict_keys: bool = allow_extra_dict_keys

    def validate_member(self, config: Config, member_name: str,
                        member_value: object,
                        stderr_file: TextIO = sys.stderr) -> Optional[object]:
        """Validate one dict member against the configured key set.

        Mandatory keys are checked first, in their declared order, so the
        first missing mandatory key triggers the error. After that, the
        keys in the dict are checked in their insertion order so that the
        first unknown key triggers the error.

        Args:
            config: The Config object that owns the member.
            member_name: The name of the member to validate.
            member_value: The dict value to validate.
            stderr_file: The file to write error messages to.

        Returns:
            The original dict value if validation succeeds.

        Raises:
            InvalidConfiguration: If the member is not a dict, a mandatory
                key is missing, or an unknown key is present while
                ``allow_extra_dict_keys`` is ``False``.
        """
        _ = config
        validated_value = _validate_dict_member_value(
            member_name=member_name, member_value=member_value,
            stderr_file=stderr_file)
        for mandatory_key in self.mandatory_keys:
            if mandatory_key not in validated_value:
                msg = 'Invalid configuration: '
                msg += f'Mandatory key {mandatory_key!r} is missing '
                msg += f'from {member_name}.'
                print(msg, file=stderr_file)
                raise InvalidConfiguration(msg)
        if self.allow_extra_dict_keys:
            return member_value
        for present_key in validated_value:
            if present_key not in self.allowed_keys:
                msg = 'Invalid configuration: '
                msg += f'Unknown key {present_key!r} in {member_name}.'
                print(msg, file=stderr_file)
                raise InvalidConfiguration(msg)
        return member_value


def accept_all_keys(key: Hashable) -> bool:
    """Return ``True`` for all keys.

    Args:
        key: The key to check.

    Returns:
        ``True`` for all keys.
    """
    _ = key  # pylint: disable=unused-argument
    return True


@dataclass(frozen=True)
class DictRule:
    """Bind a sequence of validators to a set of dict keys.

    A ``DictRule`` is the data shape that ``DictForEachValidator`` uses to
    apply per-key validation. The ``keys`` is either a sequence of hashable
    key values or a callable that receives one key and returns a truthy value
    when the rule should apply.

    If ``keys`` is a sequence, for every key listed in ``keys``,
    every validator in ``validators`` is applied in order, threading the
    normalized return value forward.
    If ``keys`` is a callable, it is called for each key that is present in
    the dict. If the callable returns a truthy value, the validators are
    applied in order to the value at that key, threading the normalized
    return value forward. If the callable returns a falsey value, the
    validators are not applied to the value at that key.
    """

    keys: Sequence[Hashable] | Callable[[Hashable], object]
    validators: Sequence[MemberValidator]

    def __post_init__(self) -> None:
        """Validate that ``keys`` and ``validators`` are well-formed.

        Raises:
            ValueError: If ``keys`` or ``validators`` is empty, or if
                ``keys`` contains a duplicate entry.
            TypeError: If any entry of ``keys`` is not hashable or any
                entry of ``validators`` is not a ``MemberValidator``.
        """
        if not callable(self.keys) and not isinstance(self.keys, SequenceABC):
            msg = 'keys must be a sequence of hashable values or a callable.'
            raise TypeError(msg)
        if len(self.validators) == 0:
            raise ValueError('validators must be non-empty.')
        if callable(self.keys):
            keys: Optional[Sequence[Hashable]] = None
        else:
            assert isinstance(self.keys, SequenceABC)
            keys = self.keys
        if keys is not None:
            if len(keys) == 0:
                msg2 = 'keys must be non-empty sequence when not a callable.'
                raise ValueError(msg2)
            _validate_hashable_keys(keys, 'keys')
        for index, validator in enumerate(self.validators):
            if not isinstance(validator, MemberValidator):
                msg = f'validators[{index}] must be a MemberValidator.'
                raise TypeError(msg)


def _validate_for_each_rules(rules: Sequence[DictRule]) -> None:
    """Validate the ``rules`` argument of DictForEachValidator.

    Args:
        rules: Rules to apply per dict key.

    Raises:
        ValueError: If ``rules`` is empty.
        TypeError: If any entry of ``rules`` is not a ``DictRule``.
    """
    if len(rules) == 0:
        raise ValueError('rules must be non-empty.')
    for index, rule in enumerate(rules):
        if not isinstance(rule, DictRule):
            msg = f'rules[{index}] must be a DictRule.'
            raise TypeError(msg)


# pylint: disable-next=too-few-public-methods
class DictForEachValidator(MemberValidator):
    """Apply per-key validators to specific keys of a dict.

    For each ``DictRule`` in ``rules`` (in declaration order), the
    validator finds that rule's matching keys and applies every validator
    in the rule's ``validators`` (in declaration order) to the value at
    each matching key. A fixed key sequence is iterated in declaration
    order. A key predicate is called for each present dict key, in the
    dict's insertion order, and truthy predicate results select the key.
    Each validator receives the value returned by the previous validator,
    so normalization performed by one inner validator is visible to the
    next one. The dict member is never modified in place; a new dict is
    returned that carries the per-key updates.

    A rule key that is not present in the dict is silently skipped. This
    keeps the validator strictly orthogonal to ``DictKeysValidator``,
    which is the dedicated mechanism for enforcing that mandatory keys
    are present and that unknown keys are rejected.

    Keys that are present in the dict but are not covered by any rule are
    copied through unchanged.

    Inner validator calls receive ``f'{member_name}[{key}]'`` as the
    ``member_name``, so error messages stay precise about which key
    failed. The same convention is used by ``ListForEachValidator`` with
    the index in place of the key.

    Order example::

        ra = DictRule(keys=['a', 'b'], validators=[v1, v2])
        rb = DictRule(keys=['a', 'b', 'c'], validators=[v3, v4])
        v = DictForEachValidator(rules=[ra, rb])

    For a dict whose keys include at least ``'a'``, ``'b'``, and ``'c'``,
    the inner validator calls happen in this order:

        1. ``v1(a)``, ``v2(a)``  -- rule ``ra``, key ``'a'``
        2. ``v1(b)``, ``v2(b)``  -- rule ``ra``, key ``'b'``
        3. ``v3(a)``, ``v4(a)``  -- rule ``rb``, key ``'a'``;
           sees the value left by ``v2(a)``
        4. ``v3(b)``, ``v4(b)``  -- rule ``rb``, key ``'b'``;
           sees the value left by ``v2(b)``
        5. ``v3(c)``, ``v4(c)``  -- rule ``rb``, key ``'c'``

    The iteration is rule-major, then key-within-rule, then
    validator-within-rule. This mirrors ``ListForEachValidator``'s
    iteration shape: outer loop over container children, inner loop over
    the validators that apply to each child.
    """

    def __init__(self, rules: Sequence[DictRule]) -> None:
        """Initialize the validator.

        Args:
            rules: Non-empty sequence of ``DictRule`` entries to apply.

        Raises:
            ValueError: If ``rules`` is empty.
            TypeError: If any entry of ``rules`` is not a ``DictRule``.
        """
        _validate_for_each_rules(rules)
        self.rules: list[DictRule] = list(rules)

    # pylint: disable-next=too-many-arguments,too-many-positional-arguments
    def _run_rule_on_key(self, rule: DictRule, config: Config,
                         member_name: str,
                         member_value: dict[Hashable, object], key: Hashable,
                         stderr_file: TextIO) \
            -> Optional[object]:
        """Run a single rule on a dict member.

        Args:
            rule: The rule to run.
            config: The Config object that owns the member.
            member_name: The name of the outer dict member to validate.
            member_value: The dict value to validate.
            key: The key to validate.
            stderr_file: The file to write error messages to.
        """
        inner_name = _inner_member_name(member_name, key)
        current: object = member_value[key]
        for validator in rule.validators:
            current = validator.validate_member(config=config,
                                                member_name=inner_name,
                                                member_value=current,
                                                stderr_file=stderr_file)
        return current

    def validate_member(self, config: Config, member_name: str,
                        member_value: object,
                        stderr_file: TextIO = sys.stderr) -> Optional[object]:
        """Validate one dict member by delegating to per-key validators.

        Args:
            config: The Config object that owns the member.
            member_name: The name of the outer dict member to validate.
            member_value: The dict value to validate.
            stderr_file: The file to write error messages to.

        Returns:
            A new dict whose values are the values returned by the last
            inner validator for each rule key that was present in the
            input. Keys not covered by any rule are copied through
            unchanged. The new dict preserves the input's key insertion
            order.

        Raises:
            InvalidConfiguration: If the member is not a dict, or a
                supplied validator raised ``InvalidConfiguration``.
            InvalidConfigurationValue: If a supplied validator raised
                ``InvalidConfigurationValue``.
        """
        validated_dict = _validate_dict_member_value(member_name=member_name,
                                                     member_value=member_value,
                                                     stderr_file=stderr_file)
        result: dict[Hashable, object] = dict(validated_dict)
        for rule in self.rules:
            if callable(rule.keys):
                for key in result:
                    if rule.keys(key):
                        result[key] = self._run_rule_on_key(
                            rule=rule, config=config, member_name=member_name,
                            member_value=result, key=key,
                            stderr_file=stderr_file)
            else:
                assert isinstance(rule.keys, SequenceABC)
                for key in rule.keys:
                    if key not in result:
                        continue
                    result[key] = self._run_rule_on_key(
                        rule=rule, config=config, member_name=member_name,
                        member_value=result, key=key, stderr_file=stderr_file)
        return result
