#! /usr/local/bin/python3
"""Test optional member validator."""

# Copyright (c) 2026 Tom Björkholm
# MIT License

from typing import Optional, TextIO, cast
import sys
import pytest
from config_as_json import Config, MemberValidator, OptionalMemberValidator
from .config_xls_list_transf_name import ConfigXlsListTransfName
from .check_capsys import check_capsys


# pylint: disable-next=too-few-public-methods
class _PrefixValidator(MemberValidator):
    """Validator that prefixes string values for tests."""

    def __init__(self, prefix: str) -> None:
        """Construct prefix validator."""
        self.prefix = prefix
        self.num_calls = 0

    def validate_member(self, config: Config, member_name: str,
                        member_value: object,
                        stderr_file: TextIO = sys.stderr) -> Optional[object]:
        """Prefix the member value."""
        _ = config
        _ = member_name
        _ = stderr_file
        self.num_calls += 1
        assert isinstance(member_value, str)
        return self.prefix + member_value


def test_optional_member_validator_returns_none_without_delegating(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Test that None values bypass the wrapped validator."""
    wrapped = _PrefixValidator(prefix='prefix ')
    validator = OptionalMemberValidator(validator=wrapped)
    cfg = ConfigXlsListTransfName()
    result = validator.validate_member(config=cfg, member_name='x',
                                       member_value=None,
                                       stderr_file=sys.stderr)
    assert result is None
    assert wrapped.num_calls == 0
    check_capsys(capsys=capsys)


def test_optional_member_validator_delegates_non_none_value(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Test that non-None values are validated by the wrapped validator."""
    wrapped = _PrefixValidator(prefix='prefix ')
    validator = OptionalMemberValidator(validator=wrapped)
    cfg = ConfigXlsListTransfName()
    result = validator.validate_member(config=cfg, member_name='x',
                                       member_value='value',
                                       stderr_file=sys.stderr)
    assert result == 'prefix value'
    assert wrapped.num_calls == 1
    check_capsys(capsys=capsys)


def test_optional_member_validator_delegates_to_validator_sequence(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Test that a list of validators is applied in order."""
    first = _PrefixValidator(prefix='a')
    second = _PrefixValidator(prefix='b')
    validator = OptionalMemberValidator(validator=[first, second])
    cfg = ConfigXlsListTransfName()
    result = validator.validate_member(config=cfg, member_name='x',
                                       member_value='value',
                                       stderr_file=sys.stderr)
    assert result == 'bavalue'
    assert first.num_calls == 1
    assert second.num_calls == 1
    check_capsys(capsys=capsys)


def test_optional_member_validator_rejects_empty_list(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Test that an empty validator list is rejected."""
    with pytest.raises(ValueError, match='empty list'):
        OptionalMemberValidator(validator=[])
    check_capsys(capsys=capsys)


def test_optional_member_validator_rejects_non_validator(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Test that invalid validator input is rejected."""
    bad_validator = cast(MemberValidator, 'not a validator')
    with pytest.raises(TypeError, match='str'):
        OptionalMemberValidator(validator=bad_validator)
    check_capsys(capsys=capsys)


def test_optional_member_validator_rejects_list_with_non_validator(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Test that invalid validators in a list are rejected."""
    validators = cast(list[MemberValidator],
                      [_PrefixValidator(prefix='a'), 'not a validator'])
    with pytest.raises(TypeError, match='str'):
        OptionalMemberValidator(validator=validators)
    check_capsys(capsys=capsys)
