#! /usr/local/bin/python3
"""Test discriminated dictionary validators."""

# Copyright (c) 2026 Tom Björkholm
# MIT License

import sys
from typing import Any, Optional, TextIO, cast
import pytest
from config_as_json.config import Config
from config_as_json.dict_validators import DictRule
from config_as_json.discriminated_dict_validators import DictVariant, \
    DiscriminatedDictValidator
from config_as_json.validator import IntFloatValidator, \
    InvalidConfiguration, InvalidConfigurationValue, MemberValidator, \
    StrValidator, ValidationPlan, MemberValidationStep
from .validator_test_helpers import EmptyValidationConfig, \
    assert_validate_member_failure


# pylint: disable-next=too-few-public-methods
class _ConstantValidator(MemberValidator):
    """Return one constant value from ``validate_member``."""

    def __init__(self, value: object) -> None:
        """Store the value to return."""
        self.value: object = value

    def validate_member(self, config: Config, member_name: str,
                        member_value: object,
                        stderr_file: TextIO = sys.stderr) -> Optional[object]:
        """Return the stored constant value."""
        _ = config, member_name, member_value, stderr_file
        return self.value


class DictMemberValidationConfig(Config):
    """Config class used to test dict validators through ``Config``."""

    def __init__(self, validator: MemberValidator,
                 from_json_data_text: Optional[str] = None) -> None:
        """Construct one dict-member config object."""
        self._validator = validator
        self._unchecked_dicts = ['value']
        self.value: dict[str, object] = {'kind': 'disk', 'path': 'local.json'}
        super().__init__(from_json_data_text=from_json_data_text,
                         from_json_filename=None, stderr_file=sys.stderr)

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Get validation plan for use when validating the Config object."""
        _ = stderr_file
        return [
            MemberValidationStep(member_names=['value'],
                                 validator=self._validator)
        ]


def make_export_target_validator() -> DiscriminatedDictValidator:
    """Create a representative discriminated dict validator."""
    file_variant = DictVariant(
        mandatory_keys=['path'], allowed_keys=['format'],
        rules=[
            DictRule(keys=['path'],
                     validators=[
                         StrValidator(
                             allowed_values=['local.json', 'local.parquet'],
                             ignore_case=False)
                     ]),
            DictRule(keys=['format'],
                     validators=[
                         StrValidator(allowed_values=['ndjson', 'parquet'],
                                      ignore_case=True, normalize=True)])])
    topic_variant = DictVariant(
        mandatory_keys=['topic'], allowed_keys=['max_batch'],
        rules=[
            DictRule(keys=['topic'],
                     validators=[
                         StrValidator(allowed_values=['audit', 'events'],
                                      ignore_case=True, normalize=True)
                     ]),
            DictRule(keys=['max_batch'],
                     validators=[
                         IntFloatValidator(min_value=1, max_value=1000,
                                           allowed_values=None)])])
    return DiscriminatedDictValidator(discriminator_key='kind',
                                      variants={
                                          'disk': file_variant,
                                          'topic': topic_variant
                                      },
                                      discriminator_validator=StrValidator(
                                          allowed_values=['disk', 'topic'],
                                          ignore_case=True, normalize=True))


def validate_member(validator: MemberValidator, member_value: object,
                    capsys: pytest.CaptureFixture[str]) -> object:
    """Validate a member value and assert that no diagnostics were printed."""
    cfg = EmptyValidationConfig()
    result = validator.validate_member(cfg, 'value', member_value, sys.stderr)
    out, err = capsys.readouterr()
    assert out == ''
    assert err == ''
    return result


@pytest.mark.parametrize(
    'mandatory_keys, allowed_keys, rules, exc_type, message',
    [(['path', 7], None, (), TypeError, 'mandatory_keys[1] must be a str'),
     (['path', 'path'], None,
      (), ValueError, "mandatory_keys[1]='path' duplicates an earlier entry"),
     (['path'], ['format', 7], (), TypeError, 'allowed_keys[1] must be a str'),
     (['path'], ['format', 'format'],
      (), ValueError, "allowed_keys[1]='format' duplicates an earlier entry"),
     (['path'], None, None, TypeError, 'rules must be a sequence'),
     (['path'], None, [object()], TypeError, 'rules[0] must be a DictRule')])
def test_dict_variant_init_rejects_invalid_arguments(
        mandatory_keys: list[object], allowed_keys: Optional[list[object]],
        rules: object, exc_type: type[Exception], message: str) -> None:
    """Test DictVariant constructor validation."""
    with pytest.raises(exc_type) as exc:
        DictVariant(mandatory_keys=cast(Any, mandatory_keys),
                    allowed_keys=cast(Any, allowed_keys),
                    rules=cast(Any, rules))
    assert message in str(exc.value)


def test_dict_variant_init_rejects_non_bool_extra_policy() -> None:
    """allow_extra_dict_keys must be a bool."""
    with pytest.raises(TypeError) as exc:
        DictVariant(mandatory_keys=[], allow_extra_dict_keys=cast(Any, 'yes'))
    assert 'allow_extra_dict_keys must be a bool' in str(exc.value)


def test_dict_variant_init_accepts_empty_rules() -> None:
    """A variant may validate only the selected key set."""
    variant = DictVariant(mandatory_keys=[], allowed_keys=None)
    assert not list(variant.mandatory_keys)
    assert variant.allowed_keys is None
    assert not list(variant.rules)
    assert variant.allow_extra_dict_keys is False


@pytest.mark.parametrize(
    'discriminator_key, variants, discriminator_validator, exc_type, message',
    [(7, {
        'file': DictVariant([])
    }, None, TypeError, 'discriminator_key must be a str'),
     ('', {
         'file': DictVariant([])
     }, None, ValueError, 'discriminator_key must be non-empty'),
     ('kind', [], None, TypeError, 'variants must be a mapping'),
     ('kind', {}, None, ValueError, 'variants must be non-empty'),
     ('kind', {
         'file': object()
     }, None, TypeError, "variants['file'] must be a DictVariant"),
     ('kind', {
         'file': DictVariant([])
     }, object(), TypeError,
      'discriminator_validator must be None or a MemberValidator')])
def test_discriminated_dict_validator_init_rejects_invalid_arguments(
        discriminator_key: object, variants: object,
        discriminator_validator: object, exc_type: type[Exception],
        message: str) -> None:
    """Test DiscriminatedDictValidator constructor validation."""
    with pytest.raises(exc_type) as exc:
        DiscriminatedDictValidator(
            discriminator_key=cast(Any, discriminator_key),
            variants=cast(Any, variants),
            discriminator_validator=cast(Any, discriminator_validator))
    assert message in str(exc.value)


def test_discriminated_dict_validator_init_stores_arguments() -> None:
    """Test that constructor arguments are exposed on the validator."""
    variant = DictVariant(mandatory_keys=[])
    discriminator_validator = StrValidator(allowed_values=['file'],
                                           ignore_case=True, normalize=True)
    validator = DiscriminatedDictValidator(
        discriminator_key='kind', variants={'file': variant},
        discriminator_validator=discriminator_validator)
    assert validator.discriminator_key == 'kind'
    assert validator.variants == {'file': variant}
    assert validator.discriminator_validator is discriminator_validator


def test_discriminated_dict_validator_normalizes_values_without_mutation(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Normalize discriminator and variant values in a returned dict."""
    validator = make_export_target_validator()
    member_value = {
        'kind': 'DISK',
        'path': 'local.parquet',
        'format': 'NDJSON'
    }
    result = validate_member(validator, member_value, capsys)
    assert result == {
        'kind': 'disk',
        'path': 'local.parquet',
        'format': 'ndjson'
    }
    assert member_value == {
        'kind': 'DISK',
        'path': 'local.parquet',
        'format': 'NDJSON'
    }


def test_discriminated_dict_validator_accepts_other_variant(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Select the topic variant and normalize its values."""
    validator = make_export_target_validator()
    result = validate_member(validator, {
        'kind': 'TOPIC',
        'topic': 'EVENTS',
        'max_batch': 50
    }, capsys)
    assert result == {'kind': 'topic', 'topic': 'events', 'max_batch': 50}


def test_discriminated_dict_validator_accepts_omitted_optional_key(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Accept a selected variant when optional keys are absent."""
    validator = make_export_target_validator()
    result = validate_member(validator, {
        'kind': 'topic',
        'topic': 'audit'
    }, capsys)
    assert result == {'kind': 'topic', 'topic': 'audit'}


def test_discriminated_dict_validator_accepts_variant_with_only_kind(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Accept a variant that has no variant-specific keys."""
    validator = DiscriminatedDictValidator(
        discriminator_key='kind',
        variants={'ping': DictVariant(mandatory_keys=[])})
    result = validate_member(validator, {'kind': 'ping'}, capsys)
    assert result == {'kind': 'ping'}


def test_discriminated_dict_validator_allows_kind_in_mandatory_keys(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Including the discriminator key in a variant is harmless."""
    validator = DiscriminatedDictValidator(
        discriminator_key='kind',
        variants={'disk': DictVariant(mandatory_keys=['kind', 'path'])})
    result = validate_member(validator, {
        'kind': 'disk',
        'path': 'local.json'
    }, capsys)
    assert result == {'kind': 'disk', 'path': 'local.json'}


def test_discriminated_dict_validator_accepts_discriminator_rule(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Allow selected variant rules to apply to the discriminator key."""
    validator = DiscriminatedDictValidator(
        discriminator_key='kind',
        variants={
            'disk':
            DictVariant(mandatory_keys=[],
                        rules=[
                            DictRule(
                                keys=['kind'],
                                validators=[_ConstantValidator('stored-disk')])
                        ])
        })
    result = validate_member(validator, {'kind': 'disk'}, capsys)
    assert result == {'kind': 'stored-disk'}


def test_discriminated_dict_validator_accepts_variant_extra_keys(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Allow unknown keys when the selected variant opens its key policy."""
    validator = DiscriminatedDictValidator(discriminator_key='kind',
                                           variants={
                                               'disk':
                                               DictVariant(
                                                   mandatory_keys=['path'],
                                                   allow_extra_dict_keys=True)
                                           })
    result = validate_member(validator, {
        'kind': 'disk',
        'path': 'local.json',
        'owner': 'ops'
    }, capsys)
    assert result == {'kind': 'disk', 'path': 'local.json', 'owner': 'ops'}


def test_discriminated_dict_validator_open_variant_still_requires_keys(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Open variant policy must still reject a missing mandatory key."""
    validator = DiscriminatedDictValidator(discriminator_key='kind',
                                           variants={
                                               'disk':
                                               DictVariant(
                                                   mandatory_keys=['path'],
                                                   allow_extra_dict_keys=True)
                                           })
    assert_validate_member_failure(
        capsys, validator, {
            'kind': 'disk',
            'owner': 'ops'
        }, InvalidConfiguration, "Mandatory key 'path' is missing from value")


def test_discriminated_dict_validator_rejects_missing_discriminator(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Reject a dict that has no discriminator key."""
    validator = make_export_target_validator()
    assert_validate_member_failure(
        capsys, validator, {'path': 'local.json'}, InvalidConfiguration,
        "Discriminator key 'kind' is missing from value")


def test_discriminated_dict_validator_rejects_unknown_discriminator(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Reject a discriminator value without a matching variant."""
    validator = DiscriminatedDictValidator(
        discriminator_key='kind',
        variants={'file': DictVariant(mandatory_keys=[])})
    assert_validate_member_failure(
        capsys, validator, {'kind': 'queue'}, InvalidConfiguration,
        "Discriminator value 'queue' for value[kind] has no variant")


def test_discriminated_dict_validator_rejects_unhashable_discriminator(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Reject normalized discriminator values that cannot be mapping keys."""
    validator = DiscriminatedDictValidator(
        discriminator_key='kind',
        variants={'file': DictVariant(mandatory_keys=[])},
        discriminator_validator=_ConstantValidator(['file']))
    assert_validate_member_failure(
        capsys, validator, {'kind': 'file'}, InvalidConfiguration,
        "Discriminator value ['file'] for value[kind] is not usable")


def test_discriminated_dict_validator_rejects_invalid_discriminator_value(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Reject a discriminator value rejected by the discriminator validator."""
    validator = make_export_target_validator()
    assert_validate_member_failure(
        capsys, validator, {
            'kind': 'smtp',
            'path': 'local.json'
        }, InvalidConfigurationValue,
        'Value smtp for value[kind] is not one of the allowed values')


def test_discriminated_dict_validator_rejects_missing_variant_key(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Reject a selected variant with a missing mandatory key."""
    validator = make_export_target_validator()
    assert_validate_member_failure(
        capsys, validator, {'kind': 'disk'}, InvalidConfiguration,
        "Mandatory key 'path' is missing from value")


def test_discriminated_dict_validator_rejects_unknown_variant_key(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Reject keys not allowed by the selected variant."""
    validator = make_export_target_validator()
    assert_validate_member_failure(capsys, validator, {
        'kind': 'disk',
        'path': 'local.json',
        'topic': 'audit'
    }, InvalidConfiguration, "Unknown key 'topic' in value")


def test_discriminated_dict_validator_rejects_variant_value(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Reject values using the selected variant's rules."""
    validator = make_export_target_validator()
    assert_validate_member_failure(
        capsys, validator, {
            'kind': 'topic',
            'topic': 'audit',
            'max_batch': 1001
        }, InvalidConfiguration,
        'Value 1001 for value[max_batch] is greater than maximum 1000')


def test_discriminated_dict_validator_rejects_non_dict(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Reject non-dict member values."""
    validator = make_export_target_validator()
    assert_validate_member_failure(capsys, validator, ['kind', 'file'],
                                   InvalidConfiguration,
                                   'Value for value is not a dict')


def test_discriminated_dict_validator_integration_uses_parsed_json(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Test integration through ``Config.validate()`` and parsed JSON."""
    validator = make_export_target_validator()
    config = DictMemberValidationConfig(
        validator,
        from_json_data_text='{"value": {"kind": "TOPIC", '
        '"topic": "EVENTS", "max_batch": 7}}')
    out, err = capsys.readouterr()
    assert config.value == {'kind': 'topic', 'topic': 'events', 'max_batch': 7}
    assert out == ''
    assert err == ''
