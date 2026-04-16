#! /usr/local/bin/python3
# mypy: disable-error-code="no-untyped-def,no-untyped-call"
"""Test the validation framework."""

# Copyright (c) 2024-2026 Tom Björkholm
# MIT License

import sys
from io import StringIO
from typing import Optional, Sequence, TextIO
import pytest
from config_as_json.config import Config
from config_as_json.validator import InvalidConfiguration, \
    InvalidConfigurationValue, StrValidator, Validation, ValidationList, \
    Validator, not_one_of_allowed_values


class ConfigMissingValidationList(Config):
    """Config class used to test missing get_validation_list()."""

    def __init__(self, from_json_data_text: Optional[str] = None,
                 stderr_file: TextIO = sys.stderr) -> None:
        """Construct test config object."""
        self.value = 'alpha'
        super().__init__(from_json_data_text=from_json_data_text,
                         from_json_filename=None, stderr_file=stderr_file)


class EmptyValidationConfig(Config):
    """Config class used as a small helper in validator tests."""

    def __init__(self, from_json_data_text: Optional[str] = None,
                 stderr_file: TextIO = sys.stderr) -> None:
        """Construct test config object."""
        self.value = 'seed'
        super().__init__(from_json_data_text=from_json_data_text,
                         from_json_filename=None, stderr_file=stderr_file)

    def get_validation_list(self, stderr_file: TextIO) -> ValidationList:
        """Get validation list for use when validating the Config object."""
        return []


class UppercaseValidator(Validator):
    """Normalize one string member to upper case."""

    def validate_member(self, config: Config, member_name: str,
                        member_value: object,
                        stderr_file=sys.stderr) -> Optional[object]:
        """Validate one member and return the upper-case value."""
        _ = config
        _ = member_name
        _ = stderr_file
        assert isinstance(member_value, str)
        return member_value.upper()


class PrefixFromNameValidator(Validator):
    """Prefix one member with the normalized name from the config."""

    def validate_member(self, config: Config, member_name: str,
                        member_value: object,
                        stderr_file=sys.stderr) -> Optional[object]:
        """Validate one member and return the prefixed value."""
        assert isinstance(config, ValidationOrderConfig)
        _ = member_name
        _ = stderr_file
        assert isinstance(member_value, str)
        return f'{config.name}:{member_value}'


class WholeConfigSuffixValidator(Validator):
    """Append one suffix to the alias field during whole-config validation."""

    def __init__(self, suffix: str) -> None:
        """Store the suffix to append."""
        self._suffix = suffix

    def validate(self, config: Config, stderr_file=sys.stderr) -> None:
        """Validate the whole config by mutating one member."""
        assert isinstance(config, ValidationOrderConfig)
        _ = stderr_file
        config.alias = config.alias + self._suffix


class IdentityValidator(Validator):
    """Return the validated member unchanged."""

    def validate_member(self, config: Config, member_name: str,
                        member_value: object,
                        stderr_file=sys.stderr) -> Optional[object]:
        """Validate one member and return it unchanged."""
        _ = config
        _ = member_name
        _ = stderr_file
        return member_value


class ReplaceWithNoneValidator(Validator):
    """Replace the validated member with None."""

    def validate_member(self, config: Config, member_name: str,
                        member_value: object,
                        stderr_file=sys.stderr) -> Optional[object]:
        """Validate one member and replace it with None."""
        _ = config
        _ = member_name
        _ = member_value
        _ = stderr_file
        replacement: Optional[object] = None
        return replacement


class ValidationOrderConfig(Config):
    """Config class used to test validation order and write-back."""

    def __init__(self, from_json_data_text: Optional[str] = None,
                 stderr_file: TextIO = sys.stderr) -> None:
        """Construct test config object."""
        self.name = 'alpha'
        self.alias = 'beta'
        super().__init__(from_json_data_text=from_json_data_text,
                         from_json_filename=None, stderr_file=stderr_file)

    def get_validation_list(self, stderr_file: TextIO) -> ValidationList:
        """Get validation list for use when validating the Config object."""
        return [
            Validation(member_names=['name'],
                       validator=UppercaseValidator()),
            Validation(member_names=['alias'],
                       validator=PrefixFromNameValidator()),
            Validation(member_names=None,
                       validator=WholeConfigSuffixValidator('!'))]


class MissingMemberConfig(Config):
    """Config class used to test validation of a missing member."""

    def __init__(self, stderr_file: TextIO) -> None:
        """Construct test config object."""
        self.value = 'alpha'
        super().__init__(from_json_data_text=None, from_json_filename=None,
                         stderr_file=stderr_file)

    def get_validation_list(self, stderr_file: TextIO) -> ValidationList:
        """Get validation list for use when validating the Config object."""
        return [Validation(member_names=['missing'],
                           validator=IdentityValidator())]


class NoneWriteBackConfig(Config):
    """Config class used to test member write-back of None."""

    def __init__(self, stderr_file: TextIO) -> None:
        """Construct test config object."""
        self.value = 'alpha'
        super().__init__(from_json_data_text=None, from_json_filename=None,
                         stderr_file=stderr_file)

    def get_validation_list(self, stderr_file: TextIO) -> ValidationList:
        """Get validation list for use when validating the Config object."""
        return [Validation(member_names=['value'],
                           validator=ReplaceWithNoneValidator())]


class PaletteConfig(Config):
    """Config class used for StrValidator integration tests."""

    def __init__(self, from_json_data_text: Optional[str] = None,
                 stderr_file: TextIO = sys.stderr) -> None:
        """Construct test config object."""
        self.shade = 'GREEN'
        self.accent = 'blu'
        super().__init__(from_json_data_text=from_json_data_text,
                         from_json_filename=None, stderr_file=stderr_file)

    def accent_names(self) -> Sequence[str]:
        """Return the allowed accent names."""
        return ['blue', 'black']

    def get_validation_list(self, stderr_file: TextIO) -> ValidationList:
        """Get validation list for use when validating the Config object."""
        return [
            Validation(member_names=['shade'],
                       validator=StrValidator(
                           ['red', 'green'], ignore_case=True,
                           normalize=True)),
            Validation(member_names=['accent'],
                       validator=StrValidator(
                           self.accent_names, ignore_case=False,
                           best_match=True))]


@pytest.mark.parametrize('validator, member_value, expected',
                         [(StrValidator(['red', 'green'],
                                        ignore_case=False),
                           'red', 'red'),
                          (StrValidator(['red', 'green'],
                                        ignore_case=True),
                           'GREEN', 'GREEN'),
                          (StrValidator(['red', 'green'],
                                        ignore_case=True,
                                        normalize=True),
                           'GREEN', 'green'),
                          (StrValidator(['Alpha'],
                                        ignore_case=False,
                                        best_match=True),
                           'alpha', 'Alpha'),
                          (StrValidator(lambda: ['blue', 'black'],
                                        ignore_case=False,
                                        best_match=True),
                           'blu', 'blue')])
def test_str_validator_ok(capsys, validator, member_value, expected):
    """Test OK cases of StrValidator."""
    cfg = EmptyValidationConfig()
    ret = validator.validate_member(cfg, 'value', member_value, sys.stderr)
    out, err = capsys.readouterr()
    assert ret == expected
    assert out == ''
    assert err == ''


def test_missing_get_validation_list_raises(capsys):
    """Test that direct Config subclasses must implement validation list."""
    with pytest.raises(NotImplementedError) as exc:
        _ = ConfigMissingValidationList(stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert 'Config.get_validation_list() must be implemented' in str(exc.value)
    assert out == ''
    assert 'Config.get_validation_list() must be implemented' in err


def test_validate_applies_member_and_whole_config_in_order(capsys):
    """Test that validation order and write-back work as documented."""
    cfg = ValidationOrderConfig(stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert cfg.name == 'ALPHA'
    assert cfg.alias == 'ALPHA:beta!'
    assert out == ''
    assert err == ''


def test_validate_missing_member_raises_attribute_error(capsys):
    """Test validation failure when a listed member does not exist."""
    with pytest.raises(AttributeError) as exc:
        _ = MissingMemberConfig(stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert 'Member missing not found in Config object' in str(exc.value)
    assert out == ''
    assert 'Member missing not found in Config object' in err


def test_validate_missing_member_uses_supplied_stderr_file(capsys):
    """Test validation failure routing to an explicitly supplied stream."""
    stderr_file = StringIO()
    with pytest.raises(AttributeError) as exc:
        _ = MissingMemberConfig(stderr_file=stderr_file)
    out, err = capsys.readouterr()
    assert 'Member missing not found in Config object' in str(exc.value)
    assert out == ''
    assert err == ''
    assert 'Member missing not found in Config object' in \
        stderr_file.getvalue()


def test_validate_member_can_write_back_none(capsys):
    """Test that a member validator can replace a member with None."""
    cfg = NoneWriteBackConfig(stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert cfg.value is None
    assert out == ''
    assert err == ''


def test_not_one_of_allowed_values_can_suppress_printing(capsys):
    """Test explicit suppression of printing in helper message builder."""
    ret = not_one_of_allowed_values('color', 'orange',
                                    ['red', 'green'], None)
    out, err = capsys.readouterr()
    assert 'Invalid configuration:' in ret
    assert 'orange' in ret
    assert out == ''
    assert err == ''


def test_base_validator_methods_raise_not_implemented(capsys):
    """Test the default Validator methods used without overriding."""
    cfg = EmptyValidationConfig(stderr_file=sys.stderr)
    validator = Validator()
    with pytest.raises(NotImplementedError) as exc:
        validator.validate(cfg, sys.stderr)
    out, err = capsys.readouterr()
    assert 'Validator.validate() must be implemented' in str(exc.value)
    assert out == ''
    assert 'Validator.validate() must be implemented' in err
    with pytest.raises(NotImplementedError) as exc:
        validator.validate_member(cfg, 'value', cfg.value, sys.stderr)
    out, err = capsys.readouterr()
    assert 'Validator.validate_member() must be implemented' in \
        str(exc.value)
    assert out == ''
    assert 'Validator.validate_member() must be implemented' in err


def test_str_validator_rejects_invalid_member_type(capsys):
    """Test that StrValidator rejects non-string values."""
    validator = StrValidator(['red', 'green'], ignore_case=False)
    cfg = EmptyValidationConfig()
    with pytest.raises(InvalidConfiguration) as exc:
        validator.validate_member(cfg, 'value', 42, sys.stderr)
    out, err = capsys.readouterr()
    assert 'Value for value is not a string.' in str(exc.value)
    assert out == ''
    assert 'Value for value is not a string.' in err


def test_str_validator_rejects_disallowed_value(capsys):
    """Test that StrValidator rejects unknown values."""
    validator = StrValidator(['red', 'green'], ignore_case=False)
    cfg = EmptyValidationConfig()
    with pytest.raises(InvalidConfigurationValue) as exc:
        validator.validate_member(cfg, 'value', 'blue', sys.stderr)
    out, err = capsys.readouterr()
    assert 'Value blue for value' in str(exc.value)
    assert out == ''
    assert 'Value blue for value' in err


def test_str_validator_rejects_ambiguous_best_match(capsys):
    """Test that best-match validation rejects ambiguous prefixes."""
    validator = StrValidator(['blue', 'black'],
                             ignore_case=False,
                             best_match=True)
    cfg = EmptyValidationConfig()
    with pytest.raises(InvalidConfigurationValue) as exc:
        validator.validate_member(cfg, 'value', 'bl', sys.stderr)
    out, err = capsys.readouterr()
    assert 'Value bl for value' in str(exc.value)
    assert out == ''
    assert 'Value bl for value' in err


def test_str_validator_cannot_validate_whole_config(capsys):
    """Test that StrValidator is only for member validation."""
    validator = StrValidator(['red'], ignore_case=False)
    cfg = EmptyValidationConfig()
    with pytest.raises(InvalidConfiguration) as exc:
        validator.validate(cfg, sys.stderr)
    out, err = capsys.readouterr()
    assert 'Cannot validate complete Config object' in str(exc.value)
    assert out == ''
    assert 'Cannot validate complete Config object' in err


def test_palette_config_uses_str_validator_on_default_values(capsys):
    """Test StrValidator integration in a derived config class."""
    cfg = PaletteConfig()
    out, err = capsys.readouterr()
    assert cfg.shade == 'green'
    assert cfg.accent == 'blue'
    assert out == ''
    assert err == ''


def test_palette_config_uses_str_validator_on_parsed_json(capsys):
    """Test StrValidator integration when values come from parsed JSON."""
    cfg = PaletteConfig(
        from_json_data_text='{"shade": "Red", "accent": "black"}')
    out, err = capsys.readouterr()
    assert cfg.shade == 'red'
    assert cfg.accent == 'black'
    assert out == ''
    assert err == ''
