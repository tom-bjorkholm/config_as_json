#! /usr/local/bin/python3
"""Test projected member validators."""

# Copyright (c) 2026 Tom Björkholm
# MIT License

import sys
from typing import Optional, TextIO
import pytest
from config_as_json.config import Config
from config_as_json.dict_validators import DictKeysValidator
from config_as_json.list_validators import ListIsOrderedValidator, \
    ListSizeValidator
from config_as_json.projected_validators import ProjectedMemberValidator, \
    ProjectedWholeConfigValidator
from config_as_json.validator import InvalidConfiguration, \
    InvalidConfigurationValue, MemberValidationStep, MemberValidator, \
    StrValidator, ValidationPlan, WholeConfigValidationStep, \
    WholeConfigValidator
from .validator_test_helpers import EmptyValidationConfig, \
    assert_validate_member_failure, assert_validate_member_ok


# pylint: disable-next=too-few-public-methods
class _RecordingProjector:
    """Projector that records the context it received."""

    def __init__(self, projected_value: object) -> None:
        """Store the value returned by the projector."""
        self.projected_value: object = projected_value
        self.calls: list[tuple[Config, str, object, TextIO]] = []

    def __call__(self, config: Config, member_name: str, member_value: object,
                 stderr_file: TextIO) -> object:
        """Record one projector call and return the stored value."""
        self.calls.append((config, member_name, member_value, stderr_file))
        return self.projected_value


# pylint: disable-next=too-few-public-methods
class _RecordingWholeProjector:
    """Whole-config projector that records the context it received."""

    def __init__(self, projected_value: object) -> None:
        """Store the value returned by the projector."""
        self.projected_value: object = projected_value
        self.calls: list[tuple[Config, TextIO]] = []

    def __call__(self, config: Config, stderr_file: TextIO) -> object:
        """Record one projector call and return the stored value."""
        self.calls.append((config, stderr_file))
        return self.projected_value


# pylint: disable-next=too-few-public-methods
class _RecordingValidator(MemberValidator):
    """Validator that records its input and returns a configured value."""

    def __init__(self, name: str, recording: list[tuple[str, str, object]],
                 replacement: object) -> None:
        """Store the recording destination and replacement value."""
        self.name: str = name
        self.recording: list[tuple[str, str, object]] = recording
        self.replacement: object = replacement

    def validate_member(self, config: Config, member_name: str,
                        member_value: object,
                        stderr_file: TextIO = sys.stderr) -> Optional[object]:
        """Record the validation call and return the replacement value."""
        _ = config, stderr_file
        self.recording.append((self.name, member_name, member_value))
        return self.replacement


# pylint: disable-next=too-few-public-methods
class _AppendValidator(MemberValidator):
    """Validator that mutates a list in place for aliasing tests."""

    def __init__(self, item: object) -> None:
        """Store the item to append."""
        self.item: object = item

    def validate_member(self, config: Config, member_name: str,
                        member_value: object,
                        stderr_file: TextIO = sys.stderr) -> Optional[object]:
        """Append one item to the supplied list and return it."""
        _ = config, member_name, stderr_file
        assert isinstance(member_value, list)
        member_value.append(self.item)
        return member_value


# pylint: disable-next=too-few-public-methods
class _FailingValidator(MemberValidator):
    """Validator that always rejects the projected value."""

    def validate_member(self, config: Config, member_name: str,
                        member_value: object,
                        stderr_file: TextIO = sys.stderr) -> Optional[object]:
        """Raise ``InvalidConfiguration`` for one projected value."""
        _ = config, member_value
        msg = 'Invalid configuration: projected value failed for '
        msg += f'{member_name}.'
        print(msg, file=stderr_file)
        raise InvalidConfiguration(msg)


class ProjectedValidationConfig(Config):
    """Config class used to test projected validators through ``Config``."""

    def __init__(self, validator: MemberValidator,
                 from_json_data_text: Optional[str] = None) -> None:
        """Construct one config object with route data."""
        self._validator = validator
        self.routes: list[dict[str, object]] = [{
            'name': 'api',
            'port': 8080
        }, {
            'name': 'admin',
            'port': 9090
        }]
        super().__init__(from_json_data_text=from_json_data_text,
                         from_json_filename=None, stderr_file=sys.stderr)

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Get validation plan for use when validating the Config object."""
        _ = stderr_file
        return [
            MemberValidationStep(member_names=['routes'],
                                 validator=self._validator)
        ]


class WholeProjectedValidationConfig(Config):
    """Config class used to test whole-config projected validators."""

    def __init__(self, validator: Optional[WholeConfigValidator],
                 from_json_data_text: Optional[str] = None) -> None:
        """Construct one config object with route data."""
        self._validator = validator
        self.routes: list[dict[str, object]] = [{
            'name': 'api',
            'port': 8080
        }, {
            'name': 'admin',
            'port': 9090
        }]
        super().__init__(from_json_data_text=from_json_data_text,
                         from_json_filename=None, stderr_file=sys.stderr)

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Get validation plan for use when validating the Config object."""
        _ = stderr_file
        if self._validator is None:
            return []
        return [WholeConfigValidationStep(validator=self._validator)]


def project_names(config: Config, member_name: str, member_value: object,
                  stderr_file: TextIO) -> object:
    """Project a list of route dictionaries to their route names."""
    _ = config, member_name, stderr_file
    assert isinstance(member_value, list)
    route_names: list[object] = []
    for route in member_value:
        assert isinstance(route, dict)
        route_names.append(route['name'])
    return route_names


def project_mode(config: Config, member_name: str, member_value: object,
                 stderr_file: TextIO) -> object:
    """Project a dict member to its ``mode`` value."""
    _ = config, member_name, stderr_file
    assert isinstance(member_value, dict)
    return member_value['mode']


def project_limits(config: Config, member_name: str, member_value: object,
                   stderr_file: TextIO) -> object:
    """Project a dict member to its nested ``limits`` dict."""
    _ = config, member_name, stderr_file
    assert isinstance(member_value, dict)
    return member_value['limits']


def identity_projector(config: Config, member_name: str, member_value: object,
                       stderr_file: TextIO) -> object:
    """Return the original member value as the projected value."""
    _ = config, member_name, stderr_file
    return member_value


def failing_projector(config: Config, member_name: str, member_value: object,
                      stderr_file: TextIO) -> object:
    """Raise ``InvalidConfiguration`` during projection."""
    _ = config, member_value
    msg = 'Invalid configuration: cannot project '
    msg += f'{member_name}.'
    print(msg, file=stderr_file)
    raise InvalidConfiguration(msg)


def project_whole_route_names(config: Config, stderr_file: TextIO) -> object:
    """Project a whole config to the names of its routes."""
    _ = stderr_file
    assert isinstance(config, WholeProjectedValidationConfig)
    route_config = config
    return [route['name'] for route in route_config.routes]


def project_whole_mode(config: Config, stderr_file: TextIO) -> object:
    """Return a scalar projected value from the whole config."""
    _ = config, stderr_file
    return 'slow'


def failing_whole_projector(config: Config, stderr_file: TextIO) -> object:
    """Raise ``InvalidConfiguration`` during whole-config projection."""
    _ = config
    msg = 'Invalid configuration: cannot project whole config.'
    print(msg, file=stderr_file)
    raise InvalidConfiguration(msg)


def make_unique_names_validator() -> ProjectedMemberValidator:
    """Create a validator that checks route names through a projection."""
    return ProjectedMemberValidator(projector=project_names,
                                    validators=[
                                        ListIsOrderedValidator(
                                            str, is_ordered=False,
                                            unique_values=True)])


@pytest.mark.parametrize(
    'projector, validators, source_validator, exc_type, message',
    [(object(), [ListSizeValidator(0, 1)
                 ], None, TypeError, 'projector must be callable'),
     (project_names, None, None, TypeError, 'validators must be a sequence'),
     (project_names, [], None, ValueError, 'validators must be non-empty'),
     (project_names, [], ListSizeValidator(
         0, 1), ValueError, 'validators must be non-empty'),
     (project_names, [object()], None, TypeError,
      'validators[0] must be a MemberValidator'),
     (project_names, [ListSizeValidator(0, 1)], object(), TypeError,
      'source_validator must be None or a MemberValidator')])
def test_projected_member_validator_init_rejects_invalid_arguments(
        projector: object, validators: object, source_validator: object,
        exc_type: type[Exception], message: str) -> None:
    """Test constructor validation."""
    with pytest.raises(exc_type) as exc:
        ProjectedMemberValidator(
            projector=projector,  # type: ignore[arg-type]
            validators=validators,  # type: ignore[arg-type]
            source_validator=source_validator)  # type: ignore[arg-type]
    assert message in str(exc.value)


def test_projected_member_validator_init_stores_arguments() -> None:
    """Test that constructor arguments are exposed on the validator."""
    validator = ListSizeValidator(0, 2)
    source_validator = ListSizeValidator(0, 2)
    projected = ProjectedMemberValidator(projector=project_names,
                                         validators=[validator],
                                         source_validator=source_validator)
    assert projected.projector is project_names
    assert projected.validators == [validator]
    assert projected.source_validator is source_validator


def test_projected_member_validator_validates_projected_list_and_keeps_source(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Validate a projected list while returning the original list."""
    validator = make_unique_names_validator()
    routes = [{'name': 'api'}, {'name': 'admin'}]
    cfg = EmptyValidationConfig()
    result = validator.validate_member(cfg, 'value', routes, sys.stderr)
    out, err = capsys.readouterr()
    assert result is routes
    assert routes == [{'name': 'api'}, {'name': 'admin'}]
    assert out == ''
    assert err == ''


def test_projected_member_validator_rejects_invalid_projected_list(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Reject a projected list when an inner validator rejects it."""
    validator = make_unique_names_validator()
    assert_validate_member_failure(capsys, validator, [{
        'name': 'api'
    }, {
        'name': 'api'
    }], InvalidConfiguration, 'duplicates the value at index 0')


def test_projected_member_validator_validates_projected_scalar(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Validate a projected scalar and keep the original dict."""
    validator = ProjectedMemberValidator(projector=project_mode,
                                         validators=[
                                             StrValidator(
                                                 allowed_values=['fast'],
                                                 ignore_case=True,
                                                 normalize=True)])
    settings = {'mode': 'FAST', 'limit': 3}
    assert_validate_member_ok(capsys, validator, settings, settings)
    assert settings == {'mode': 'FAST', 'limit': 3}


def test_projected_member_validator_validates_projected_dict(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Validate a projected nested dict and keep the outer dict."""
    validator = ProjectedMemberValidator(projector=project_limits,
                                         validators=[
                                             DictKeysValidator(
                                                 mandatory_keys=['min', 'max'],
                                                 allowed_keys=None)])
    settings = {'name': 'cache', 'limits': {'min': 1, 'max': 5}}
    assert_validate_member_ok(capsys, validator, settings, settings)
    assert settings == {'name': 'cache', 'limits': {'min': 1, 'max': 5}}


def test_projected_member_validator_uses_source_validator_before_projector(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Let the source validator normalize before projection."""
    recording: list[tuple[str, str, object]] = []
    projector = _RecordingProjector('projected')
    validator = ProjectedMemberValidator(
        projector=projector,
        source_validator=_RecordingValidator('source', recording,
                                             'normalized-source'),
        validators=[
            _RecordingValidator('projected', recording, 'normalized-projected')
        ])
    assert_validate_member_ok(capsys, validator, 'original', 'original')
    assert recording == [('source', 'value', 'original'),
                         ('projected', 'value', 'projected')]
    assert projector.calls[0][2] == 'normalized-source'


def test_projected_member_validator_chains_normalized_values(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Pass each normalized projected value to the next validator."""
    recording: list[tuple[str, str, object]] = []
    validator = ProjectedMemberValidator(
        projector=_RecordingProjector('zero'),
        validators=[
            _RecordingValidator('first', recording, 'one'),
            _RecordingValidator('second', recording, 'two')])
    assert_validate_member_ok(capsys, validator, 'original', 'original')
    assert recording == [('first', 'value', 'zero'),
                         ('second', 'value', 'one')]


def test_projected_member_validator_passes_context_to_projector(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Pass config, member name, member value, and stderr to projector."""
    cfg = EmptyValidationConfig()
    member_value = ['original']
    projector = _RecordingProjector(['projected'])
    validator = ProjectedMemberValidator(projector=projector,
                                         validators=[ListSizeValidator(1, 1)])
    result = validator.validate_member(config=cfg, member_name='value',
                                       member_value=member_value,
                                       stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert result is member_value
    assert projector.calls == [(cfg, 'value', member_value, sys.stderr)]
    assert out == ''
    assert err == ''


def test_projected_member_validator_propagates_source_failure(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Propagate an invalid configuration raised by the source validator."""
    projector = _RecordingProjector(['projected'])
    validator = ProjectedMemberValidator(projector=projector,
                                         source_validator=_FailingValidator(),
                                         validators=[ListSizeValidator(1, 1)])
    assert_validate_member_failure(capsys, validator, ['original'],
                                   InvalidConfiguration,
                                   'projected value failed for value')
    assert not projector.calls


def test_projected_member_validator_propagates_projector_failure(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Propagate an invalid configuration raised by the projector."""
    validator = ProjectedMemberValidator(projector=failing_projector,
                                         validators=[ListSizeValidator(1, 1)])
    assert_validate_member_failure(capsys, validator, ['original'],
                                   InvalidConfiguration,
                                   'cannot project value')


def test_projected_member_validator_propagates_inner_failure(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Propagate an invalid configuration raised by an inner validator."""
    validator = ProjectedMemberValidator(projector=identity_projector,
                                         validators=[_FailingValidator()])
    assert_validate_member_failure(capsys, validator, ['original'],
                                   InvalidConfiguration,
                                   'projected value failed for value')


def test_projected_member_validator_propagates_allowed_value_failure(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Propagate ``InvalidConfigurationValue`` from an inner validator."""
    validator = ProjectedMemberValidator(
        projector=project_mode,
        validators=[StrValidator(allowed_values=['fast'], ignore_case=False)])
    assert_validate_member_failure(
        capsys, validator, {'mode': 'slow'}, InvalidConfigurationValue,
        'Value slow for value is not one of the allowed values')


def test_projected_member_validator_can_expose_in_place_mutation(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Document that shared projected objects are not defensively copied."""
    validator = ProjectedMemberValidator(
        projector=identity_projector, validators=[_AppendValidator('mutated')])
    values = ['original']
    cfg = EmptyValidationConfig()
    result = validator.validate_member(cfg, 'value', values, sys.stderr)
    out, err = capsys.readouterr()
    assert result is values
    assert values == ['original', 'mutated']
    assert out == ''
    assert err == ''


def test_projected_member_validator_integration_uses_parsed_json(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Test integration through ``Config.validate()`` and parsed JSON."""
    config = ProjectedValidationConfig(make_unique_names_validator(),
                                       from_json_data_text='{"routes": ['
                                       '{"name": "api", "port": 8080}, '
                                       '{"name": "admin", "port": 9090}]}')
    out, err = capsys.readouterr()
    assert config.routes == [{'name': 'api', 'port': 8080},
                             {'name': 'admin', 'port': 9090}]
    assert out == ''
    assert err == ''


@pytest.mark.parametrize(
    'projector, pseudo_member_name, validators, exc_type, message',
    [(object(), 'projected', [ListSizeValidator(0, 1)], TypeError,
      'projector must be callable'),
     (project_whole_route_names, object(), [ListSizeValidator(0, 1)],
      TypeError, 'pseudo_member_name must be a str'),
     (project_whole_route_names, '', [ListSizeValidator(0, 1)], ValueError,
      'pseudo_member_name must be non-empty'),
     (project_whole_route_names, 'projected', None, TypeError,
      'validators must be a sequence'),
     (project_whole_route_names, 'projected', [], ValueError,
      'validators must be non-empty'),
     (project_whole_route_names, 'projected', [object()], TypeError,
      'validators[0] must be a MemberValidator')])
def test_whole_proj_rejects_bad_init(
        projector: object, pseudo_member_name: object, validators: object,
        exc_type: type[Exception], message: str) -> None:
    """Test whole-config projected validator constructor validation."""
    with pytest.raises(exc_type) as exc:
        ProjectedWholeConfigValidator(
            projector=projector,  # type: ignore[arg-type]
            pseudo_member_name=pseudo_member_name,  # type: ignore[arg-type]
            validators=validators)  # type: ignore[arg-type]
    assert message in str(exc.value)


def test_whole_proj_stores_args() -> None:
    """Test that constructor arguments are exposed on the validator."""
    validator = ListSizeValidator(0, 2)
    projected = ProjectedWholeConfigValidator(
        projector=project_whole_route_names, pseudo_member_name='route_names',
        validators=[validator])
    assert projected.projector is project_whole_route_names
    assert projected.pseudo_member_name == 'route_names'
    assert projected.validators == [validator]


def test_whole_proj_validates_list(capsys: pytest.CaptureFixture[str]) -> None:
    """Validate a whole-config projection through member validators."""
    validator = ProjectedWholeConfigValidator(
        projector=project_whole_route_names, pseudo_member_name='route_names',
        validators=[ListSizeValidator(1, 3)])
    config = WholeProjectedValidationConfig(validator=None)
    validator.validate(config, sys.stderr)
    out, err = capsys.readouterr()
    assert out == ''
    assert err == ''


def test_whole_proj_chains_values(capsys: pytest.CaptureFixture[str]) -> None:
    """Pass each normalized projected value to the next validator."""
    recording: list[tuple[str, str, object]] = []
    validator = ProjectedWholeConfigValidator(
        projector=_RecordingWholeProjector('zero'),
        pseudo_member_name='whole_view',
        validators=[
            _RecordingValidator('first', recording, 'one'),
            _RecordingValidator('second', recording, 'two')])
    config = WholeProjectedValidationConfig(validator=None)
    validator.validate(config, sys.stderr)
    out, err = capsys.readouterr()
    assert recording == [('first', 'whole_view', 'zero'),
                         ('second', 'whole_view', 'one')]
    assert out == ''
    assert err == ''


def test_whole_proj_passes_context(capsys: pytest.CaptureFixture[str]) -> None:
    """Pass config and stderr to the whole-config projector."""
    projector = _RecordingWholeProjector(['projected'])
    validator = ProjectedWholeConfigValidator(
        projector=projector, pseudo_member_name='whole_view',
        validators=[ListSizeValidator(1, 1)])
    config = WholeProjectedValidationConfig(validator=None)
    validator.validate(config=config, stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert projector.calls == [(config, sys.stderr)]
    assert out == ''
    assert err == ''


def test_whole_proj_projector_fails(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Propagate an invalid configuration raised by the projector."""
    validator = ProjectedWholeConfigValidator(
        projector=failing_whole_projector, pseudo_member_name='whole_view',
        validators=[ListSizeValidator(1, 1)])
    config = WholeProjectedValidationConfig(validator=None)
    with pytest.raises(InvalidConfiguration) as exc:
        validator.validate(config, sys.stderr)
    out, err = capsys.readouterr()
    assert 'cannot project whole config' in str(exc.value)
    assert out == ''
    assert 'cannot project whole config' in err


def test_whole_proj_inner_fails(capsys: pytest.CaptureFixture[str]) -> None:
    """Propagate an invalid configuration raised by an inner validator."""
    validator = ProjectedWholeConfigValidator(
        projector=_RecordingWholeProjector(['projected']),
        pseudo_member_name='whole_view', validators=[_FailingValidator()])
    config = WholeProjectedValidationConfig(validator=None)
    with pytest.raises(InvalidConfiguration) as exc:
        validator.validate(config, sys.stderr)
    out, err = capsys.readouterr()
    assert 'projected value failed for whole_view' in str(exc.value)
    assert out == ''
    assert 'projected value failed for whole_view' in err


def test_whole_proj_value_fails(capsys: pytest.CaptureFixture[str]) -> None:
    """Propagate ``InvalidConfigurationValue`` from an inner validator."""
    validator = ProjectedWholeConfigValidator(
        projector=project_whole_mode, pseudo_member_name='mode',
        validators=[StrValidator(allowed_values=['fast'], ignore_case=False)])
    config = WholeProjectedValidationConfig(validator=None)
    with pytest.raises(InvalidConfigurationValue) as exc:
        validator.validate(config, sys.stderr)
    out, err = capsys.readouterr()
    assert 'Value slow for mode is not one of the allowed values' in \
        str(exc.value)
    assert out == ''
    assert 'Value slow for mode is not one of the allowed values' in err


def test_whole_proj_exposes_mutation(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Document that shared projected objects are not defensively copied."""
    projected_value = ['original']
    validator = ProjectedWholeConfigValidator(
        projector=_RecordingWholeProjector(projected_value),
        pseudo_member_name='whole_view',
        validators=[_AppendValidator('mutated')])
    config = WholeProjectedValidationConfig(validator=None)
    validator.validate(config, sys.stderr)
    out, err = capsys.readouterr()
    assert projected_value == ['original', 'mutated']
    assert out == ''
    assert err == ''


def test_whole_proj_uses_json(capsys: pytest.CaptureFixture[str]) -> None:
    """Test whole-config projected validation through ``Config``."""
    validator = ProjectedWholeConfigValidator(
        projector=project_whole_route_names, pseudo_member_name='route_names',
        validators=[ListIsOrderedValidator(str, is_ordered=False,
                                           unique_values=True)])
    config = WholeProjectedValidationConfig(
        validator=validator,
        from_json_data_text='{"routes": ['
        '{"name": "api", "port": 8080}, '
        '{"name": "admin", "port": 9090}]}')
    out, err = capsys.readouterr()
    assert config.routes == [{'name': 'api', 'port': 8080},
                             {'name': 'admin', 'port': 9090}]
    assert out == ''
    assert err == ''


def test_whole_proj_rejects_json(capsys: pytest.CaptureFixture[str]) -> None:
    """Reject an invalid whole-config projection during config parsing."""
    validator = ProjectedWholeConfigValidator(
        projector=project_whole_route_names, pseudo_member_name='route_names',
        validators=[ListIsOrderedValidator(str, is_ordered=False,
                                           unique_values=True)])
    with pytest.raises(InvalidConfiguration) as exc:
        WholeProjectedValidationConfig(
            validator=validator,
            from_json_data_text='{"routes": ['
            '{"name": "api", "port": 8080}, '
            '{"name": "api", "port": 9090}]}')
    out, err = capsys.readouterr()
    assert 'duplicates the value at index 0' in str(exc.value)
    assert out == ''
    assert 'duplicates the value at index 0' in err
