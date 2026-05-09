#! /usr/local/bin/python3
"""Shared helpers for validator-related tests."""

# Copyright (c) 2024-2026 Tom Björkholm
# MIT License

import sys
from typing import Optional, TextIO
import pytest
from config_as_json.config import Config
from config_as_json.validator import ValidationPlan, MemberValidationStep, \
    MemberValidator


class EmptyValidationConfig(Config):
    """Config class used as a small helper in validator tests."""

    def __init__(self, from_json_data_text: Optional[str] = None,
                 stderr_file: TextIO = sys.stderr) -> None:
        """Construct test config object."""
        self.value = 'seed'
        super().__init__(from_json_data_text=from_json_data_text,
                         from_json_filename=None, stderr_file=stderr_file)

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Get validation plan for use when validating the Config object."""
        _ = stderr_file
        return []


class SingleMemberValidationConfig(Config):
    """Config class used to test one member validator in integration."""

    def __init__(self, member_name: str, member_value: object,
                 validator: MemberValidator,
                 from_json_data_text: Optional[str] = None) -> None:
        """Construct one-member config object with injected validation."""
        self._member_name = member_name
        self._validator = validator
        setattr(self, member_name, member_value)
        super().__init__(from_json_data_text=from_json_data_text,
                         from_json_filename=None, stderr_file=sys.stderr)

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Get validation plan for use when validating the Config object."""
        _ = stderr_file
        return [MemberValidationStep(member_names=[self._member_name],
                                     validator=self._validator)]


def assert_validate_member_ok(capsys: pytest.CaptureFixture[str],
                              validator: MemberValidator, member_value: object,
                              expected: object) -> None:
    """Assert that one member validation succeeds without stderr output."""
    cfg = EmptyValidationConfig()
    ret = validator.validate_member(cfg, 'value', member_value, sys.stderr)
    out, err = capsys.readouterr()
    assert ret == expected
    assert out == ''
    assert err == ''


def assert_validate_member_failure(capsys: pytest.CaptureFixture[str],
                                   validator: MemberValidator,
                                   member_value: object,
                                   exc_type: type[Exception], message: str
                                   ) -> None:
    """Assert that one member validation fails with one error message."""
    cfg = EmptyValidationConfig()
    with pytest.raises(exc_type) as exc:
        validator.validate_member(cfg, 'value', member_value, sys.stderr)
    out, err = capsys.readouterr()
    assert message in str(exc.value)
    assert out == ''
    assert message in err
