#! /usr/local/bin/python3
"""Test factory functions for nested Config members."""

# Copyright (c) 2026 Tom Björkholm
# MIT License

import json
import sys
from typing import Optional, TextIO, Type, cast, override
import pytest
from pytest import CaptureFixture
from config_as_json import Config, ConfigFactory, ConfigNesting, \
    ConfigNestingKind, NestedConfigs, PathOrStr, ValidationPlan


def _empty_plan(stderr_file: TextIO) -> ValidationPlan:
    """Return an empty validation plan and consume the diagnostic stream."""
    _ = stderr_file
    return []


class FactoryOutputConfig(Config):
    """Nested configuration used by factory-function tests."""

    def __init__(self, from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 stderr_file: TextIO = sys.stderr,
                 construction_label: str = 'type',
                 member_name: Optional[str] = None) -> None:
        """Construct one output configuration."""
        self.name = 'default-output'
        self.format_name = 'CSV'
        self._construction_label = construction_label
        super().__init__(from_json_data_text=from_json_data_text,
                         from_json_filename=from_json_filename,
                         stderr_file=stderr_file, member_name=member_name)

    def construction_label(self) -> str:
        """Return which construction path created this object."""
        return self._construction_label

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Return validation steps for this nested test configuration."""
        return _empty_plan(stderr_file)


class FactoryOutputSubclass(FactoryOutputConfig):
    """Nested configuration subclass returned by a factory test."""


class WrongOutputConfig(Config):
    """Different Config type with the same JSON shape as the expected type."""

    def __init__(self, from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 stderr_file: TextIO = sys.stderr,
                 member_name: Optional[str] = None) -> None:
        """Construct a wrong-type nested configuration."""
        self.format_name = 'CSV'
        self.name = 'wrong-output'
        super().__init__(from_json_data_text=from_json_data_text,
                         from_json_filename=from_json_filename,
                         stderr_file=stderr_file, member_name=member_name)

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Return validation steps for this wrong-type configuration."""
        return _empty_plan(stderr_file)


# pylint: disable-next=too-few-public-methods
class TrackingFactory:
    """Factory that records how Config called it."""

    def __init__(self, construction_label: str = 'factory',
                 output_type: Type[FactoryOutputConfig]
                 = FactoryOutputConfig) -> None:
        """Construct a recording factory."""
        self._construction_label = construction_label
        self._output_type = output_type
        self.json_texts: list[Optional[str]] = []
        self.filenames: list[Optional[PathOrStr]] = []
        self.stderr_files: list[TextIO] = []
        self.member_names: list[Optional[str]] = []

    def __call__(self, *, from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 stderr_file: TextIO = sys.stderr,
                 member_name: Optional[str] = None) -> Config:
        """Record the call and construct the configured nested type."""
        self.json_texts.append(from_json_data_text)
        self.filenames.append(from_json_filename)
        self.stderr_files.append(stderr_file)
        self.member_names.append(member_name)
        return self._output_type(from_json_data_text=from_json_data_text,
                                 from_json_filename=from_json_filename,
                                 stderr_file=stderr_file,
                                 construction_label=self._construction_label,
                                 member_name=member_name)


# pylint: disable-next=too-few-public-methods
class WrongTypeFactory:
    """Factory that returns a Config object with the wrong runtime type."""

    def __call__(self, *, from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 stderr_file: TextIO = sys.stderr,
                 member_name: Optional[str] = None) -> Config:
        """Construct a Config object that is not the declared config_type."""
        return WrongOutputConfig(from_json_data_text=from_json_data_text,
                                 from_json_filename=from_json_filename,
                                 stderr_file=stderr_file,
                                 member_name=member_name)


class FactoryParentConfig(Config):
    """Parent configuration with a factory-enabled nested member."""

    def __init__(self, from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 stderr_file: TextIO = sys.stderr,
                 factory_function: Optional[ConfigFactory] = None,
                 member_name: Optional[str] = None) -> None:
        """Construct a parent configuration with one nested member."""
        self.output = FactoryOutputConfig(stderr_file=stderr_file)
        self._factory_function = factory_function
        super().__init__(from_json_data_text=from_json_data_text,
                         from_json_filename=from_json_filename,
                         stderr_file=stderr_file, member_name=member_name)

    @override
    def nested_configs(self) -> NestedConfigs:
        """Return nested Config declarations."""
        output_nesting = ConfigNesting(kind=ConfigNestingKind.MEMBER,
                                       config_type=FactoryOutputConfig,
                                       factory_function=self._factory_function)
        return {'output': output_nesting}

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Return validation steps for this parent configuration."""
        return _empty_plan(stderr_file)


class OptionalFactoryParentConfig(Config):
    """Parent configuration with a factory-enabled optional nested member."""

    def __init__(self, from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 stderr_file: TextIO = sys.stderr,
                 factory_function: Optional[ConfigFactory] = None,
                 member_name: Optional[str] = None) -> None:
        """Construct a parent configuration with one optional nested member."""
        self.output: Optional[FactoryOutputConfig] = None
        self._factory_function = factory_function
        super().__init__(from_json_data_text=from_json_data_text,
                         from_json_filename=from_json_filename,
                         stderr_file=stderr_file, member_name=member_name)

    @override
    def nested_configs(self) -> NestedConfigs:
        """Return nested Config declarations."""
        output_nesting = ConfigNesting(kind=ConfigNestingKind.OPTIONAL_MEMBER,
                                       config_type=FactoryOutputConfig,
                                       factory_function=self._factory_function)
        return {'output': output_nesting}

    @override
    def _omit_none_from_json(self) -> list[str]:
        """Return optional members omitted while their value is None."""
        return ['output']

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Return validation steps for this parent configuration."""
        return _empty_plan(stderr_file)


class ListFactoryParentConfig(Config):
    """Parent configuration with factory-enabled nested list elements."""

    def __init__(self, from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 stderr_file: TextIO = sys.stderr,
                 factory_function: Optional[ConfigFactory] = None,
                 member_name: Optional[str] = None) -> None:
        """Construct a parent configuration with nested list elements."""
        self.outputs: list[FactoryOutputConfig] = []
        self._factory_function = factory_function
        super().__init__(from_json_data_text=from_json_data_text,
                         from_json_filename=from_json_filename,
                         stderr_file=stderr_file, member_name=member_name)

    @override
    def nested_configs(self) -> NestedConfigs:
        """Return nested Config declarations."""
        output_nesting = ConfigNesting(kind=ConfigNestingKind.LIST_ELEMENT,
                                       config_type=FactoryOutputConfig,
                                       factory_function=self._factory_function)
        return {'outputs': output_nesting}

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Return validation steps for this parent configuration."""
        return _empty_plan(stderr_file)


class DictFactoryParentConfig(Config):
    """Parent configuration with factory-enabled nested dict values."""

    def __init__(self, from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 stderr_file: TextIO = sys.stderr,
                 factory_function: Optional[ConfigFactory] = None,
                 member_name: Optional[str] = None) -> None:
        """Construct a parent configuration with nested dict values."""
        self.outputs: dict[str, FactoryOutputConfig] = {}
        self._factory_function = factory_function
        super().__init__(from_json_data_text=from_json_data_text,
                         from_json_filename=from_json_filename,
                         stderr_file=stderr_file, member_name=member_name)

    @override
    def nested_configs(self) -> NestedConfigs:
        """Return nested Config declarations."""
        output_nesting = ConfigNesting(kind=ConfigNestingKind.DICT_VALUE,
                                       config_type=FactoryOutputConfig,
                                       factory_function=self._factory_function)
        return {'outputs': output_nesting}

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Return validation steps for this parent configuration."""
        return _empty_plan(stderr_file)


class DictByKeyFactoryParentConfig(Config):
    """Parent configuration with a factory-enabled keyed dict value."""

    def __init__(self, from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 stderr_file: TextIO = sys.stderr,
                 factory_function: Optional[ConfigFactory] = None,
                 member_name: Optional[str] = None) -> None:
        """Construct a parent config with selected nested dict values."""
        self.outputs: dict[str, object] = {
            'typed': FactoryOutputConfig(stderr_file=stderr_file),
            'factory': FactoryOutputConfig(stderr_file=stderr_file),
            'plain': 'keep'
        }
        self._factory_function = factory_function
        super().__init__(from_json_data_text=from_json_data_text,
                         from_json_filename=from_json_filename,
                         stderr_file=stderr_file, member_name=member_name)

    @override
    def nested_configs(self) -> NestedConfigs:
        """Return nested Config declarations."""
        typed_nest = ConfigNesting(kind=ConfigNestingKind.DICT_VALUE_BY_KEY,
                                   config_type=FactoryOutputConfig,
                                   discriminator_key='typed')
        fact_nest = ConfigNesting(kind=ConfigNestingKind.DICT_VALUE_BY_KEY,
                                  config_type=FactoryOutputConfig,
                                  discriminator_key='factory',
                                  factory_function=self._factory_function)
        return {
            'outputs': [typed_nest, fact_nest]
        }

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Return validation steps for this parent configuration."""
        return _empty_plan(stderr_file)


def _json_text() -> str:
    """Return JSON with one nested output configuration."""
    return '{"output": {"format_name": "TXT", "name": "from-json"}}'


def _list_json_text() -> str:
    """Return JSON with two nested output configurations."""
    return ('{"outputs": [{"format_name": "TXT", "name": "first"}, '
            '{"format_name": "CSV", "name": "second"}]}')


def _dict_json_text() -> str:
    """Return JSON with two nested output configurations in a dict."""
    return ('{"outputs": {"first": {"format_name": "TXT", '
            '"name": "first"}, "second": {"format_name": "CSV", '
            '"name": "second"}}}')


def _dict_by_key_json_text() -> str:
    """Return JSON with selected nested output configurations in a dict."""
    return ('{"outputs": {"typed": {"format_name": "TXT", '
            '"name": "typed"}, "factory": {"format_name": "CSV", '
            '"name": "factory"}, "plain": "keep"}}')


def _expected_json() -> dict[str, object]:
    """Return the expected JSON-compatible data after parsing."""
    return {
        'output': {
            'format_name': 'TXT',
            'name': 'from-json'
        }
    }


def _list_expected_json() -> dict[str, object]:
    """Return expected JSON-compatible data for nested list parsing."""
    return {
        'outputs': [{
            'format_name': 'TXT',
            'name': 'first'
        }, {
            'format_name': 'CSV',
            'name': 'second'
        }]
    }


def _dict_expected_json() -> dict[str, object]:
    """Return expected JSON-compatible data for nested dict parsing."""
    return {
        'outputs': {
            'first': {
                'format_name': 'TXT',
                'name': 'first'
            },
            'second': {
                'format_name': 'CSV',
                'name': 'second'
            }
        }
    }


def _dict_by_key_expected_json() -> dict[str, object]:
    """Return expected JSON-compatible data for keyed dict parsing."""
    return {
        'outputs': {
            'factory': {
                'format_name': 'CSV',
                'name': 'factory'
            },
            'plain': 'keep',
            'typed': {
                'format_name': 'TXT',
                'name': 'typed'
            }
        }
    }


def _json_data_from_config(config: Config,
                           capsys: CaptureFixture[str]) -> dict[str, object]:
    """Serialize one config and verify that it was silent."""
    loaded = json.loads(config.as_json_string(stderr_file=sys.stderr,
                                              member_name=None))
    out, err = capsys.readouterr()
    assert out == ''
    assert err == ''
    return cast(dict[str, object], loaded)


def test_factory_constructs_member(capsys: CaptureFixture[str]) -> None:
    """Test that a factory can construct a mandatory nested member."""
    factory = TrackingFactory()
    cfg = FactoryParentConfig(from_json_data_text=_json_text(),
                              factory_function=factory, stderr_file=sys.stderr)
    json_text = factory.json_texts[0]
    assert json_text is not None
    json_data = _json_data_from_config(cfg, capsys)
    assert factory.filenames == [None]
    assert factory.stderr_files == [sys.stderr]
    assert json.loads(json_text) == _expected_json()['output']
    assert cfg.output.construction_label() == 'factory'
    assert json_data == _expected_json()


def test_factory_default_constructor(capsys: CaptureFixture[str]) -> None:
    """Test that omitting factory_function keeps the current behavior."""
    cfg = FactoryParentConfig(from_json_data_text=_json_text(),
                              stderr_file=sys.stderr)
    json_data = _json_data_from_config(cfg, capsys)
    assert cfg.output.construction_label() == 'type'
    assert json_data == _expected_json()


def test_factory_returns_subclass(capsys: CaptureFixture[str]) -> None:
    """Test that a factory may return a subclass of config_type."""
    factory = TrackingFactory(construction_label='subclass',
                              output_type=FactoryOutputSubclass)
    cfg = FactoryParentConfig(from_json_data_text=_json_text(),
                              factory_function=factory, stderr_file=sys.stderr)
    json_data = _json_data_from_config(cfg, capsys)
    assert isinstance(cfg.output, FactoryOutputSubclass)
    assert cfg.output.construction_label() == 'subclass'
    assert json_data == _expected_json()


def test_optional_factory_skips_null(capsys: CaptureFixture[str]) -> None:
    """Test that optional JSON null does not call the factory."""
    factory = TrackingFactory()
    cfg = OptionalFactoryParentConfig(from_json_data_text='{"output": null}',
                                      factory_function=factory,
                                      stderr_file=sys.stderr)
    json_data = _json_data_from_config(cfg, capsys)
    assert cfg.output is None
    assert not factory.json_texts
    assert json_data == {}


def test_optional_factory_constructs(capsys: CaptureFixture[str]) -> None:
    """Test that optional JSON objects are constructed with the factory."""
    factory = TrackingFactory()
    cfg = OptionalFactoryParentConfig(from_json_data_text=_json_text(),
                                      factory_function=factory,
                                      stderr_file=sys.stderr)
    json_data = _json_data_from_config(cfg, capsys)
    assert cfg.output is not None
    assert cfg.output.construction_label() == 'factory'
    assert len(factory.json_texts) == 1
    assert json_data == _expected_json()


def test_list_factory_constructs(capsys: CaptureFixture[str]) -> None:
    """Test that a factory constructs every nested list element."""
    factory = TrackingFactory()
    cfg = ListFactoryParentConfig(from_json_data_text=_list_json_text(),
                                  factory_function=factory,
                                  stderr_file=sys.stderr)
    json_data = _json_data_from_config(cfg, capsys)
    json_texts = [text for text in factory.json_texts if text is not None]
    assert factory.filenames == [None, None]
    assert factory.stderr_files == [sys.stderr, sys.stderr]
    assert [json.loads(text) for text in json_texts] == \
        _list_expected_json()['outputs']
    assert [output.construction_label() for output in cfg.outputs] == \
        ['factory', 'factory']
    assert json_data == _list_expected_json()


def test_dict_factory_constructs(capsys: CaptureFixture[str]) -> None:
    """Test that a factory constructs every nested dict value."""
    factory = TrackingFactory()
    cfg = DictFactoryParentConfig(from_json_data_text=_dict_json_text(),
                                  factory_function=factory,
                                  stderr_file=sys.stderr)
    json_data = _json_data_from_config(cfg, capsys)
    json_texts = [text for text in factory.json_texts if text is not None]
    expected_outputs = cast(dict[str, object],
                            _dict_expected_json()['outputs'])
    assert factory.filenames == [None, None]
    assert factory.stderr_files == [sys.stderr, sys.stderr]
    assert [json.loads(text) for text in json_texts] == [
        expected_outputs['first'], expected_outputs['second']]
    assert [output.construction_label()
            for output in cfg.outputs.values()] == ['factory', 'factory']
    assert json_data == _dict_expected_json()


def test_by_key_factory_constructs(capsys: CaptureFixture[str]) -> None:
    """Test that a factory constructs one selected keyed dict value."""
    factory = TrackingFactory()
    cfg = DictByKeyFactoryParentConfig(
        from_json_data_text=_dict_by_key_json_text(), factory_function=factory,
        stderr_file=sys.stderr)
    json_data = _json_data_from_config(cfg, capsys)
    json_texts = [text for text in factory.json_texts if text is not None]
    typed = cast(FactoryOutputConfig, cfg.outputs['typed'])
    factory_output = cast(FactoryOutputConfig, cfg.outputs['factory'])
    expected_outputs = cast(dict[str, object],
                            _dict_by_key_expected_json()['outputs'])
    assert factory.filenames == [None]
    assert factory.stderr_files == [sys.stderr]
    assert [json.loads(text) for text in json_texts] == [
        expected_outputs['factory']]
    assert typed.construction_label() == 'type'
    assert factory_output.construction_label() == 'factory'
    assert cfg.outputs['plain'] == 'keep'
    assert json_data == _dict_by_key_expected_json()


def test_factory_must_be_callable() -> None:
    """Test that a non-callable factory declaration fails visibly."""
    bad_factory = cast(ConfigFactory, 'not-callable')
    with pytest.raises(TypeError, match='factory_function must be callable'):
        FactoryParentConfig(factory_function=bad_factory,
                            stderr_file=sys.stderr)


def test_factory_base_call_raises() -> None:
    """Test direct call of the ConfigFactory protocol placeholder."""
    factory = cast(ConfigFactory, object())
    with pytest.raises(NotImplementedError):
        ConfigFactory.__call__(factory, from_json_data_text=None,
                               from_json_filename=None, stderr_file=sys.stderr,
                               member_name=None)


def test_factory_return_type_checked(capsys: CaptureFixture[str]) -> None:
    """Test that factory results must match config_type."""
    with pytest.raises(TypeError, match='factory for output must return'):
        FactoryParentConfig(from_json_data_text=_json_text(),
                            factory_function=WrongTypeFactory(),
                            stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert out == ''
    assert 'Nested Config factory for output must return' in err


def test_list_factory_bad_return(capsys: CaptureFixture[str]) -> None:
    """Test that list factory results must match config_type."""
    with pytest.raises(TypeError, match='outputs\\[0\\] must return'):
        ListFactoryParentConfig(from_json_data_text=_list_json_text(),
                                factory_function=WrongTypeFactory(),
                                stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert out == ''
    assert 'Nested Config factory for outputs[0] must return' in err


def test_dict_factory_bad_return(capsys: CaptureFixture[str]) -> None:
    """Test that dict factory results must match config_type."""
    with pytest.raises(TypeError, match='outputs\\[first\\] must return'):
        DictFactoryParentConfig(from_json_data_text=_dict_json_text(),
                                factory_function=WrongTypeFactory(),
                                stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert out == ''
    assert 'Nested Config factory for outputs[first] must return' in err


def test_by_key_factory_bad_return(capsys: CaptureFixture[str]) -> None:
    """Test that keyed dict factory results must match config_type."""
    with pytest.raises(TypeError, match='outputs\\[factory\\] must return'):
        DictByKeyFactoryParentConfig(
            from_json_data_text=_dict_by_key_json_text(),
            factory_function=WrongTypeFactory(), stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert out == ''
    assert 'Nested Config factory for outputs[factory] must return' in err


def test_factory_checks_member_type(capsys: CaptureFixture[str]) -> None:
    """Test that validate still checks current members against config_type."""
    cfg = FactoryParentConfig(factory_function=TrackingFactory(),
                              stderr_file=sys.stderr)
    cfg.output = cast(FactoryOutputConfig, WrongOutputConfig())
    with pytest.raises(TypeError, match='output must be FactoryOutputConfig'):
        cfg.validate(stderr_file=sys.stderr, member_name=None)
    out, err = capsys.readouterr()
    assert out == ''
    assert 'Nested Config member output must be FactoryOutputConfig' in err
