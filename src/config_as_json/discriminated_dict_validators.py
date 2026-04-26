#! /usr/local/bin/python3
"""Implement validators for discriminated dictionary variants."""

# Copyright (c) 2026 Tom Björkholm
# MIT License

import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Optional, TextIO
from config_as_json.config import Config
from config_as_json.dict_validators import DictForEachValidator, \
    DictKeysValidator, DictRule, _inner_member_name, \
    _validate_dict_member_value, _validate_string_keys
from config_as_json.validator import InvalidConfiguration, MemberValidator


def _validate_variant_rules(rules: Sequence[DictRule]) -> None:
    """Validate the ``rules`` field of ``DictVariant``.

    Args:
        rules: Rules to validate.

    Raises:
        TypeError: If ``rules`` is not a sequence or any entry is not a
            ``DictRule``.
    """
    if not isinstance(rules, Sequence):
        raise TypeError('rules must be a sequence.')
    for index, rule in enumerate(rules):
        if not isinstance(rule, DictRule):
            msg = f'rules[{index}] must be a DictRule.'
            raise TypeError(msg)


@dataclass(frozen=True)
class DictVariant:
    """Describe one allowed dictionary variant.

    The discriminator key handled by ``DiscriminatedDictValidator`` is
    always mandatory and allowed. The keys in this variant are therefore
    the variant-specific keys in addition to that discriminator key.

    Attributes:
        mandatory_keys: Variant-specific keys that must be present.
        allowed_keys: Additional variant-specific keys that are allowed but
            not required. ``None`` means no additional optional keys.
        rules: Per-key validators to apply after the key set has been
            checked. Rules may include the discriminator key if it should
            also be normalized or checked beyond variant selection.
    """

    mandatory_keys: Sequence[str]
    allowed_keys: Optional[Sequence[str]] = None
    rules: Sequence[DictRule] = ()

    def __post_init__(self) -> None:
        """Validate that the variant description is well-formed."""
        _validate_string_keys(self.mandatory_keys, 'mandatory_keys')
        if self.allowed_keys is not None:
            _validate_string_keys(self.allowed_keys, 'allowed_keys')
        _validate_variant_rules(self.rules)


def _validate_discriminator_key(discriminator_key: str) -> None:
    """Validate the discriminator key argument.

    Args:
        discriminator_key: Key whose value chooses the dictionary variant.

    Raises:
        TypeError: If ``discriminator_key`` is not a string.
        ValueError: If ``discriminator_key`` is empty.
    """
    if not isinstance(discriminator_key, str):
        raise TypeError('discriminator_key must be a str.')
    if discriminator_key == '':
        raise ValueError('discriminator_key must be non-empty.')


def _validate_variants(variants: Mapping[object, DictVariant]) -> None:
    """Validate the variants mapping argument.

    Args:
        variants: Mapping from discriminator values to dict variants.

    Raises:
        TypeError: If ``variants`` is not a mapping or one value is not a
            ``DictVariant``.
        ValueError: If ``variants`` is empty.
    """
    if not isinstance(variants, Mapping):
        raise TypeError('variants must be a mapping.')
    if len(variants) == 0:
        raise ValueError('variants must be non-empty.')
    for discriminator_value, variant in variants.items():
        if not isinstance(variant, DictVariant):
            msg = f'variants[{discriminator_value!r}] must be a DictVariant.'
            raise TypeError(msg)


def _validate_optional_discriminator_validator(
        discriminator_validator: Optional[MemberValidator]) -> None:
    """Validate the optional discriminator validator argument."""
    if discriminator_validator is None:
        return
    if not isinstance(discriminator_validator, MemberValidator):
        msg = 'discriminator_validator must be None or a MemberValidator.'
        raise TypeError(msg)


def _variant_mandatory_keys(discriminator_key: str,
                            variant: DictVariant) -> list[str]:
    """Return mandatory keys including the discriminator key once."""
    keys = [discriminator_key]
    for key in variant.mandatory_keys:
        if key != discriminator_key:
            keys.append(key)
    return keys


def _raise_missing_discriminator(member_name: str, discriminator_key: str,
                                 stderr_file: TextIO) -> None:
    """Raise an invalid-configuration error for a missing discriminator."""
    msg = 'Invalid configuration: '
    msg += f'Discriminator key {discriminator_key!r} is missing '
    msg += f'from {member_name}.'
    print(msg, file=stderr_file)
    raise InvalidConfiguration(msg)


def _variant_for_discriminator_value(
        discriminator_name: str, discriminator_value: object,
        variants: Mapping[object, DictVariant],
        stderr_file: TextIO) -> DictVariant:
    """Return the variant selected by one discriminator value.

    Args:
        discriminator_name: Name of the discriminator value in diagnostics.
        discriminator_value: Normalized discriminator value.
        variants: Mapping from discriminator values to variants.
        stderr_file: Stream used for diagnostics.

    Returns:
        The selected variant.

    Raises:
        InvalidConfiguration: If the discriminator value is unhashable or has
            no matching variant.
    """
    try:
        return variants[discriminator_value]
    except TypeError as exc:
        msg = 'Invalid configuration: '
        msg += f'Discriminator value {discriminator_value!r} '
        msg += f'for {discriminator_name} is not usable as a variant key.'
        print(msg, file=stderr_file)
        raise InvalidConfiguration(msg) from exc
    except KeyError as exc:
        allowed_values = ', '.join(str(value) for value in variants)
        msg = 'Invalid configuration: '
        msg += f'Discriminator value {discriminator_value!r} '
        msg += f'for {discriminator_name} has no variant. '
        msg += f'Allowed values: {allowed_values}'
        print(msg, file=stderr_file)
        raise InvalidConfiguration(msg) from exc


class DiscriminatedDictValidator(  # pylint: disable=too-few-public-methods
        MemberValidator):
    """Validate a dictionary using a variant selected by one key.

    This validator is intended for dictionaries whose required and allowed
    keys depend on a discriminator field such as ``'kind'`` or ``'type'``.
    The member must be a dictionary and must contain ``discriminator_key``.
    The discriminator value is optionally validated or normalized by
    ``discriminator_validator`` before variant lookup.

    The ``variants`` mapping is keyed by the discriminator values used after
    that optional discriminator validation. The selected ``DictVariant``
    defines the variant-specific mandatory keys, optional keys, and per-key
    validators.

    Validation never mutates the input dictionary in place. It returns a new
    dictionary carrying any normalized discriminator value and any normalized
    per-key values returned by the selected variant rules.
    """

    def __init__(
            self, discriminator_key: str,
            variants: Mapping[object, DictVariant],
            discriminator_validator: Optional[MemberValidator] = None
            ) -> None:
        """Initialize the discriminated dictionary validator.

        Args:
            discriminator_key: Key whose value chooses the variant. This key
                is always required and allowed independently of the selected
                variant.
            variants: Mapping from normalized discriminator values to the
                variant that applies to that discriminator value.
            discriminator_validator: Optional validator applied to the
                discriminator value before variant lookup. It can normalize
                values, for example from user-facing strings to canonical
                strings or enum values.

        Raises:
            ValueError: If ``discriminator_key`` is empty or ``variants`` is
                empty.
            TypeError: If ``discriminator_key`` is not a string, if
                ``variants`` is not a mapping, if any variant is not a
                ``DictVariant``, or if ``discriminator_validator`` is not
                ``None`` or a ``MemberValidator``.
        """
        _validate_discriminator_key(discriminator_key)
        _validate_variants(variants)
        _validate_optional_discriminator_validator(discriminator_validator)
        self.discriminator_key: str = discriminator_key
        self.variants: dict[object, DictVariant] = dict(variants)
        self.discriminator_validator: Optional[MemberValidator] = \
            discriminator_validator

    def _validate_discriminator(
            self, config: Config, member_name: str,
            member_value: dict[object, object],
            stderr_file: TextIO) -> tuple[dict[object, object], object]:
        """Validate and normalize the discriminator value."""
        if self.discriminator_key not in member_value:
            _raise_missing_discriminator(
                member_name=member_name,
                discriminator_key=self.discriminator_key,
                stderr_file=stderr_file)
        result = dict(member_value)
        discriminator_value = result[self.discriminator_key]
        if self.discriminator_validator is None:
            return result, discriminator_value
        discriminator_name = _inner_member_name(
            member_name, self.discriminator_key)
        discriminator_value = self.discriminator_validator.validate_member(
            config=config, member_name=discriminator_name,
            member_value=discriminator_value, stderr_file=stderr_file)
        result[self.discriminator_key] = discriminator_value
        return result, discriminator_value

    def validate_member(self, config: Config, member_name: str,
                        member_value: object,
                        stderr_file: TextIO = sys.stderr) -> Optional[object]:
        """Validate one dictionary member using the selected variant.

        Args:
            config: The Config object that owns the member.
            member_name: The name of the dictionary member to validate.
            member_value: The dictionary value to validate.
            stderr_file: The file to write error messages to.

        Returns:
            A new dictionary carrying any normalized discriminator value and
            any normalized per-key values returned by the selected variant
            rules.

        Raises:
            InvalidConfiguration: If the member is not a dictionary, the
                discriminator key is missing, the discriminator value has no
                variant, or the selected variant rejects the key set or a
                value.
            InvalidConfigurationValue: If an inner validator rejects a value
                because it is not one of its allowed values.
        """
        validated_dict = _validate_dict_member_value(
            member_name=member_name, member_value=member_value,
            stderr_file=stderr_file)
        result, discriminator_value = self._validate_discriminator(
            config=config, member_name=member_name,
            member_value=validated_dict, stderr_file=stderr_file)
        discriminator_name = _inner_member_name(
            member_name, self.discriminator_key)
        variant = _variant_for_discriminator_value(
            discriminator_name=discriminator_name,
            discriminator_value=discriminator_value,
            variants=self.variants, stderr_file=stderr_file)
        key_validator = DictKeysValidator(
            mandatory_keys=_variant_mandatory_keys(
                self.discriminator_key, variant),
            allowed_keys=variant.allowed_keys)
        key_validator.validate_member(
            config=config, member_name=member_name, member_value=result,
            stderr_file=stderr_file)
        if len(variant.rules) == 0:
            return result
        return DictForEachValidator(variant.rules).validate_member(
            config=config, member_name=member_name, member_value=result,
            stderr_file=stderr_file)
