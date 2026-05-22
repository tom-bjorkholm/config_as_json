#! /usr/local/bin/python3
"""Test the initial-data copy and nested auto-wrap features of Config."""

# Copyright (c) 2026 Tom Björkholm
# MIT License

import sys
from dataclasses import dataclass
from typing import Optional, TextIO, cast, override
import pytest
from pytest import CaptureFixture
from config_as_json import Config, ConfigNesting, ConfigNestingKind, \
    NestedConfigs, PathOrStr, ValidationPlan


class NSubA:  # pylint: disable=too-few-public-methods
    """Framework-neutral sub-section A."""

    def __init__(self) -> None:
        """Initialize neutral A with defaults."""
        self.a1param: str = 'aa'
        self.a2param: int = 4
        self.a3param: Optional[str] = None


class NSubB:  # pylint: disable=too-few-public-methods
    """Framework-neutral sub-section B with argument-taking constructor."""

    def __init__(self, b1param: bool = False, b3param: int = 1) -> None:
        """Initialize neutral B with optional argument-driven defaults."""
        self.b1param: bool = b1param
        self.b2param: Optional[str] = 'bbb'
        self.b3param: int = b3param


class NConfigSimple:  # pylint: disable=too-few-public-methods
    """Neutral top-level config with no constructor arguments."""

    def __init__(self) -> None:
        """Initialize neutral top-level config with None nested defaults."""
        self.c1: str = 'something'
        self.suba: Optional[NSubA] = None
        self.subb: Optional[NSubB] = None


class NConfigEager:  # pylint: disable=too-few-public-methods
    """Neutral top-level config with non-None nested defaults."""

    def __init__(self, c1: str, b1p: bool, b3p: int) -> None:
        """Initialize neutral top-level config with eager nested defaults."""
        self.c1: str = c1
        self.suba: Optional[NSubA] = NSubA()
        self.subb: Optional[NSubB] = NSubB(b1param=b1p, b3param=b3p)


class MySubA(NSubA, Config):
    """Bridge for ``NSubA`` that also derives from :class:`Config`."""

    def __init__(self, from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 stderr_file: TextIO = sys.stderr) -> None:
        """Construct the bridge for ``NSubA``."""
        NSubA.__init__(self)
        Config.__init__(self, from_json_data_text=from_json_data_text,
                        from_json_filename=from_json_filename,
                        stderr_file=stderr_file)

    @override
    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Return an empty validation plan for the bridge."""
        _ = stderr_file
        return []


class MySubB(NSubB, Config):
    """Bridge for ``NSubB`` that also derives from :class:`Config`."""

    def __init__(self, from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 stderr_file: TextIO = sys.stderr) -> None:
        """Construct the bridge for ``NSubB`` using neutral defaults."""
        NSubB.__init__(self)
        Config.__init__(self, from_json_data_text=from_json_data_text,
                        from_json_filename=from_json_filename,
                        stderr_file=stderr_file)

    @override
    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Return an empty validation plan for the bridge."""
        _ = stderr_file
        return []


class MyConfigSimple(NConfigSimple, Config):
    """Bridge for ``NConfigSimple`` using multiple inheritance."""

    def __init__(self, from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 stderr_file: TextIO = sys.stderr) -> None:
        """Construct the simple bridge config."""
        NConfigSimple.__init__(self)
        Config.__init__(self, from_json_data_text=from_json_data_text,
                        from_json_filename=from_json_filename,
                        stderr_file=stderr_file)

    @override
    def nested_configs(self) -> NestedConfigs:
        """Return nested Config declarations for the simple bridge."""
        return {
            'suba': ConfigNesting(kind=ConfigNestingKind.OPTIONAL_MEMBER,
                                  config_type=MySubA),
            'subb': ConfigNesting(kind=ConfigNestingKind.OPTIONAL_MEMBER,
                                  config_type=MySubB)
        }

    @override
    def _omit_none_from_json(self) -> list[str]:
        """Return optional members omitted while their value is ``None``."""
        return ['suba', 'subb']

    @override
    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Return an empty validation plan for the bridge."""
        _ = stderr_file
        return []


class MyConfigEager(NConfigEager, Config):
    """Bridge for ``NConfigEager`` that copies a supplied neutral instance."""

    # pylint: disable-next=super-init-not-called
    def __init__(self, *, neutral: Optional[NConfigEager] = None,
                 from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 stderr_file: TextIO = sys.stderr) -> None:
        """Construct the eager bridge config from a neutral source."""
        if neutral is None:
            neutral = NConfigEager(c1='example', b1p=False, b3p=1)
        Config.copy_initial_data(neutral, self)
        Config.__init__(self, from_json_data_text=from_json_data_text,
                        from_json_filename=from_json_filename,
                        stderr_file=stderr_file)

    @override
    def nested_configs(self) -> NestedConfigs:
        """Return nested Config declarations for the eager bridge."""
        return {
            'suba': ConfigNesting(kind=ConfigNestingKind.OPTIONAL_MEMBER,
                                  config_type=MySubA),
            'subb': ConfigNesting(kind=ConfigNestingKind.OPTIONAL_MEMBER,
                                  config_type=MySubB)
        }

    @override
    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Return an empty validation plan for the bridge."""
        _ = stderr_file
        return []


def test_copy_init_from_object(capsys: CaptureFixture[str]) -> None:
    """Plain-object source values are copied onto the bridge target."""
    target = MyConfigSimple(stderr_file=sys.stderr)
    source = NConfigSimple()
    source.c1 = 'copied'
    Config.copy_initial_data(source, target)
    out, err = capsys.readouterr()
    assert out == ''
    assert err == ''
    assert target.c1 == 'copied'


def test_copy_init_from_mapping(capsys: CaptureFixture[str]) -> None:
    """Mapping source values are copied onto the bridge target."""
    target = MyConfigSimple(stderr_file=sys.stderr)
    Config.copy_initial_data({'c1': 'mapped'}, target)
    out, err = capsys.readouterr()
    assert out == ''
    assert err == ''
    assert target.c1 == 'mapped'


def test_copy_map_skips_private() -> None:
    """Private mapping keys are skipped just like private object attributes."""
    target = MyConfigSimple(stderr_file=sys.stderr)
    Config.copy_initial_data({'c1': 'mapped', '_private': 'hidden'}, target)
    assert target.c1 == 'mapped'
    assert not hasattr(target, '_private')


@dataclass
class DataclassSource:
    """Dataclass form of a flat neutral source."""

    c1: str = 'dataclass'
    suba: Optional[NSubA] = None
    subb: Optional[NSubB] = None


def test_copy_init_from_dataclass(capsys: CaptureFixture[str]) -> None:
    """Dataclass source values are copied onto the bridge target."""
    target = MyConfigSimple(stderr_file=sys.stderr)
    Config.copy_initial_data(DataclassSource(c1='from-dataclass'), target)
    out, err = capsys.readouterr()
    assert out == ''
    assert err == ''
    assert target.c1 == 'from-dataclass'


def test_copy_init_skips_extras() -> None:
    """Private names and callable attributes are not copied."""
    target = MyConfigSimple(stderr_file=sys.stderr)

    class WithExtras:  # pylint: disable=too-few-public-methods
        """Source that hides private and callable attributes."""

        def __init__(self) -> None:
            """Build the test source."""
            self.c1: str = 'visible'
            self._private = 'hidden'
            self.helper = lambda: 'not-copied'
    Config.copy_initial_data(WithExtras(), target)
    assert target.c1 == 'visible'
    assert not hasattr(target, '_private')
    assert not hasattr(target, 'helper')


def test_copy_init_extra_attr_raises() -> None:
    """Extra source attribute raises when target schema is established."""
    target = MyConfigSimple(stderr_file=sys.stderr)

    class WithExtra:  # pylint: disable=too-few-public-methods
        """Source whose ``unknown`` attribute is not declared on target."""

        def __init__(self) -> None:
            """Build the test source with one unexpected attribute."""
            self.c1: str = 'fine'
            self.unknown: int = 99
    with pytest.raises(TypeError) as exc:
        Config.copy_initial_data(WithExtra(), target)
    assert 'unknown' in str(exc.value)
    assert 'MyConfigSimple' in str(exc.value)


def test_copy_init_no_schema() -> None:
    """When target has no public attributes the source defines the schema."""

    class BareTarget(Config):  # pylint: disable=too-few-public-methods
        """Bridge that defers schema setup to ``copy_initial_data``."""

        def __init__(self, source: object) -> None:
            """Use ``copy_initial_data`` to seed the schema."""
            Config.copy_initial_data(source, self)
            Config.__init__(self, from_json_data_text=None,
                            from_json_filename=None, stderr_file=sys.stderr)

        @override
        def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
            """Return an empty validation plan."""
            _ = stderr_file
            return []
    cfg = BareTarget({'c1': 'late', 'count': 3})
    assert getattr(cfg, 'c1') == 'late'
    assert getattr(cfg, 'count') == 3


def test_copy_init_bad_source() -> None:
    """Sources that are not mappings or objects are rejected."""
    target = MyConfigSimple(stderr_file=sys.stderr)
    with pytest.raises(TypeError):
        Config.copy_initial_data(42, target)


def test_copy_init_non_str_key() -> None:
    """Mapping keys must be strings."""
    target = MyConfigSimple(stderr_file=sys.stderr)
    bad_source = cast(dict[object, object], {7: 'value'})
    with pytest.raises(TypeError) as exc:
        Config.copy_initial_data(bad_source, target)
    assert 'must be a string' in str(exc.value)


def test_simple_bridge_default() -> None:
    """The MI bridge keeps None nested defaults when the neutral has them."""
    cfg = MyConfigSimple(stderr_file=sys.stderr)
    assert cfg.c1 == 'something'
    assert cfg.suba is None
    assert cfg.subb is None


def test_simple_bridge_round_trip(capsys: CaptureFixture[str]) -> None:
    """JSON round-trip uses the bridge types for nested members."""
    cfg = MyConfigSimple(stderr_file=sys.stderr)
    cfg.suba = MySubA(stderr_file=sys.stderr)
    cfg.suba.a1param = 'xyz'
    json_text = cfg.as_json_string(stderr_file=sys.stderr)
    again = MyConfigSimple(from_json_data_text=json_text,
                           stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert out == ''
    assert err == ''
    assert isinstance(again.suba, MySubA)
    assert again.suba.a1param == 'xyz'
    assert again.subb is None


def test_eager_wraps_neutrals(capsys: CaptureFixture[str]) -> None:
    """A neutral instance hands off non-None nested neutrals to the bridge."""
    cfg = MyConfigEager(neutral=NConfigEager(c1='hello', b1p=True, b3p=4),
                        stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert out == ''
    assert err == ''
    assert cfg.c1 == 'hello'
    assert isinstance(cfg.suba, MySubA)
    assert isinstance(cfg.subb, MySubB)
    assert cfg.subb.b1param is True
    assert cfg.subb.b3param == 4


def test_eager_round_trip(capsys: CaptureFixture[str]) -> None:
    """A bridge built from a neutral instance round-trips through JSON."""
    cfg = MyConfigEager(neutral=NConfigEager(c1='hello', b1p=True, b3p=4),
                        stderr_file=sys.stderr)
    json_text = cfg.as_json_string(stderr_file=sys.stderr)
    again = MyConfigEager(from_json_data_text=json_text,
                          stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert out == ''
    assert err == ''
    assert again.c1 == 'hello'
    assert isinstance(again.suba, MySubA)
    assert isinstance(again.subb, MySubB)
    assert again.subb.b1param is True
    assert again.subb.b3param == 4


def test_eager_default_neutral() -> None:
    """The eager bridge falls back to a hard-coded default neutral."""
    cfg = MyConfigEager(stderr_file=sys.stderr)
    assert cfg.c1 == 'example'
    assert isinstance(cfg.suba, MySubA)
    assert isinstance(cfg.subb, MySubB)
    assert cfg.subb.b1param is False
    assert cfg.subb.b3param == 1


class NSection:  # pylint: disable=too-few-public-methods
    """Neutral section used to exercise the list and dict wrap kinds."""

    def __init__(self) -> None:
        """Initialize the neutral section with one scalar attribute."""
        self.label: str = 'plain'


class MySection(NSection, Config):
    """Bridge over ``NSection``."""

    def __init__(self, from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 stderr_file: TextIO = sys.stderr) -> None:
        """Construct the section bridge."""
        NSection.__init__(self)
        Config.__init__(self, from_json_data_text=from_json_data_text,
                        from_json_filename=from_json_filename,
                        stderr_file=stderr_file)

    @override
    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Return an empty validation plan."""
        _ = stderr_file
        return []


class ListBridge(Config):
    """Bridge with a LIST_ELEMENT nested member containing neutrals."""

    def __init__(self, *, items: Optional[list[object]] = None,
                 from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 stderr_file: TextIO = sys.stderr) -> None:
        """Construct the list bridge with optional initial items."""
        self.items: list[object] = [] if items is None else items
        Config.__init__(self, from_json_data_text=from_json_data_text,
                        from_json_filename=from_json_filename,
                        stderr_file=stderr_file)

    @override
    def nested_configs(self) -> NestedConfigs:
        """Return nested Config declarations for the list bridge."""
        return {
            'items': ConfigNesting(kind=ConfigNestingKind.LIST_ELEMENT,
                                   config_type=MySection)
        }

    @override
    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Return an empty validation plan."""
        _ = stderr_file
        return []


def test_list_wraps_neutrals() -> None:
    """LIST_ELEMENT default that contains neutrals is wrapped per element."""
    n1 = NSection()
    n1.label = 'one'
    n2 = NSection()
    n2.label = 'two'
    cfg = ListBridge(items=[n1, n2], stderr_file=sys.stderr)
    assert all(isinstance(item, MySection) for item in cfg.items)
    labels = [cast(MySection, item).label for item in cfg.items]
    assert labels == ['one', 'two']


def test_list_keeps_bridges() -> None:
    """Already-bridge list elements are not re-wrapped."""
    section = MySection(stderr_file=sys.stderr)
    section.label = 'kept'
    items: list[object] = [section]
    cfg = ListBridge(items=items, stderr_file=sys.stderr)
    assert cfg.items is items
    assert cfg.items[0] is section


def test_list_bad_default_type(capsys: CaptureFixture[str]) -> None:
    """Non-list LIST_ELEMENT defaults are left for validation to reject."""
    with pytest.raises(TypeError, match='must be a list'):
        _ = ListBridge(items=cast(list[object], 'not-a-list'),
                       stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert out == ''
    assert 'Nested Config member items must be a list' in err


class DictBridge(Config):
    """Bridge with a DICT_VALUE nested member containing neutrals."""

    def __init__(self, *, sections: Optional[dict[str, object]] = None,
                 from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 stderr_file: TextIO = sys.stderr) -> None:
        """Construct the dict bridge with optional initial sections."""
        self.sections: dict[str, object] = {} if sections is None \
            else sections
        Config.__init__(self, from_json_data_text=from_json_data_text,
                        from_json_filename=from_json_filename,
                        stderr_file=stderr_file)

    @override
    def nested_configs(self) -> NestedConfigs:
        """Return nested Config declarations for the dict bridge."""
        return {
            'sections': ConfigNesting(kind=ConfigNestingKind.DICT_VALUE,
                                      config_type=MySection)
        }

    @override
    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Return an empty validation plan."""
        _ = stderr_file
        return []


def test_dict_value_wraps() -> None:
    """DICT_VALUE default with neutrals is wrapped per value."""
    n1 = NSection()
    n1.label = 'first'
    cfg = DictBridge(sections={'a': n1}, stderr_file=sys.stderr)
    section_a = cfg.sections['a']
    assert isinstance(section_a, MySection)
    assert section_a.label == 'first'


def test_dict_value_keeps_bridges() -> None:
    """Already-bridge dict values are not re-wrapped or copied."""
    section = MySection(stderr_file=sys.stderr)
    section.label = 'kept'
    sections: dict[str, object] = {'a': section}
    cfg = DictBridge(sections=sections, stderr_file=sys.stderr)
    assert cfg.sections is sections
    assert cfg.sections['a'] is section


def test_dict_value_bad_default(capsys: CaptureFixture[str]) -> None:
    """Non-dict DICT_VALUE defaults are left for validation to reject."""
    with pytest.raises(TypeError, match='must be a dict'):
        _ = DictBridge(sections=cast(dict[str, object], ['not-a-dict']),
                       stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert out == ''
    assert 'Nested Config member sections must be a dict' in err


class DictByKeyBridge(Config):
    """Bridge with a DICT_VALUE_BY_KEY member mixing scalars and configs."""

    def __init__(self, *, mixed: Optional[dict[str, object]] = None,
                 from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 stderr_file: TextIO = sys.stderr) -> None:
        """Construct the dict-by-key bridge with optional initial values."""
        self.mixed: dict[str, object] = {} if mixed is None else mixed
        Config.__init__(self, from_json_data_text=from_json_data_text,
                        from_json_filename=from_json_filename,
                        stderr_file=stderr_file)

    @override
    def nested_configs(self) -> NestedConfigs:
        """Return nested Config declarations for the dict-by-key bridge."""
        return {
            'mixed': [
                ConfigNesting(
                    kind=ConfigNestingKind.DICT_VALUE_BY_KEY,
                    config_type=MySection, discriminator_key='section')
            ]
        }

    @override
    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Return an empty validation plan."""
        _ = stderr_file
        return []


def test_dict_by_key_wraps() -> None:
    """DICT_VALUE_BY_KEY wraps only keys with a matching declaration."""
    neutral_section = NSection()
    neutral_section.label = 'kept-key'
    cfg = DictByKeyBridge(
        mixed={'section': neutral_section, 'note': 'plain-string'},
        stderr_file=sys.stderr)
    assert isinstance(cfg.mixed['section'], MySection)
    assert cfg.mixed['note'] == 'plain-string'


def test_by_key_keeps_bridge() -> None:
    """DICT_VALUE_BY_KEY preserves existing bridges and undeclared values."""
    section = MySection(stderr_file=sys.stderr)
    section.label = 'typed'
    mixed: dict[str, object] = {'section': section, 'note': 'plain-string'}
    cfg = DictByKeyBridge(mixed=mixed, stderr_file=sys.stderr)
    assert cfg.mixed is mixed
    assert cfg.mixed['section'] is section
    assert cfg.mixed['note'] == 'plain-string'


def test_by_key_bad_default_type(capsys: CaptureFixture[str]) -> None:
    """Bad DICT_VALUE_BY_KEY defaults are left for validation to reject."""
    with pytest.raises(TypeError, match='must be a dict'):
        _ = DictByKeyBridge(mixed=cast(dict[str, object], ['not-a-dict']),
                            stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert out == ''
    assert 'Nested Config member mixed must be a dict' in err


def test_wrap_rejects_extra(capsys: CaptureFixture[str]) -> None:
    """A neutral source with an unexpected attribute raises during wrap."""

    class WithExtraAttr:  # pylint: disable=too-few-public-methods
        """Neutral that has an attribute the bridge does not declare."""

        def __init__(self) -> None:
            """Build the bad neutral that adds ``oops`` next to ``label``."""
            self.label: str = 'plain'
            self.oops: int = 1
    with pytest.raises(TypeError) as exc:
        _ = ListBridge(items=[WithExtraAttr()], stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert out == ''
    assert 'oops' in err
    assert 'MySection' in str(exc.value)
