#! /usr/local/bin/python3
"""Test ok_to_use_defaults for Config objects built by factories.

A nested factory that accepts ``ok_to_use_defaults`` gets it. One that does
not is called without it, parses strictly, and is warned about once. The
class selected by ``config_factory_from_json``, and the class of a
``RadixNumber.factory()``, are constructed with the keyword when their
constructor accepts it, and else from their class defaults, which the JSON
data is then parsed into.
"""

# Copyright (c) 2026 Tom Björkholm
# MIT License

import json
import sys
from pathlib import Path
from typing import Callable, Optional, TextIO, TypedDict, Unpack
import pytest
from pytest import CaptureFixture
import config_as_json._deprecated_support as depr_mod
from config_as_json.commontypes import JsonPath, PathOrStr
from config_as_json.config import Config
from config_as_json.config_auto_change_hook import ConfigAutoChangeHook
from config_as_json.config_errors import ConfigMissingKey
from config_as_json.config_factory import config_factory_from_json, \
    JsonValueMatcher, MatchConfig
from config_as_json.config_nesting import ConfigFactory, ConfigNesting, \
    ConfigNestingKind, NestedConfigs
from config_as_json.hexadecimal_number import HexadecimalNumber
from config_as_json.validator import InvalidConfiguration, ValidationPlan, \
    WholeConfigValidationStep, WholeConfigValidator
from .member_name_compat_tools import deprecations


class Item(Config):
    """Item whose constructor does not accept ok_to_use_defaults."""

    def __init__(self, from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 auto_ch_hook: Optional[ConfigAutoChangeHook] = None,
                 stderr_file: TextIO = sys.stderr, *,
                 member_name: Optional[str] = None) -> None:
        """Construct with the class defaults, size 1."""
        self.name = 'item'
        self.size = 1
        super().__init__(from_json_data_text, from_json_filename, auto_ch_hook,
                         stderr_file, member_name=member_name)

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Return no validation."""
        _ = stderr_file
        return []


# pylint: disable-next=too-few-public-methods
class NameValidator(WholeConfigValidator):
    """Reject an empty name."""

    def validate(self, config: Config, stderr_file: TextIO = sys.stderr, *,
                 member_name: Optional[str] = None) -> None:
        """Raise InvalidConfiguration when the name is empty."""
        _ = member_name
        assert isinstance(config, BlankItem)
        if not config.name:
            msg = 'Empty name'
            print(msg, file=stderr_file)
            raise InvalidConfiguration(msg)


class BlankItem(Config):
    """Item whose defaults are not valid on their own."""

    # pylint: disable-next=too-many-arguments
    def __init__(self, from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 auto_ch_hook: Optional[ConfigAutoChangeHook] = None,
                 stderr_file: TextIO = sys.stderr, *,
                 member_name: Optional[str] = None,
                 ok_to_use_defaults: bool = False) -> None:
        """Construct with an empty name, and forward ok_to_use_defaults."""
        self.name = ''
        self.size = 1
        super().__init__(from_json_data_text, from_json_filename, auto_ch_hook,
                         stderr_file, member_name=member_name,
                         ok_to_use_defaults=ok_to_use_defaults)

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Return the name validation."""
        _ = stderr_file
        return [WholeConfigValidationStep(validator=NameValidator())]


class StrictBlankItem(BlankItem):
    """BlankItem whose constructor does not accept ok_to_use_defaults."""

    def __init__(self, from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 auto_ch_hook: Optional[ConfigAutoChangeHook] = None,
                 stderr_file: TextIO = sys.stderr, *,
                 member_name: Optional[str] = None) -> None:
        """Construct without ok_to_use_defaults."""
        super().__init__(from_json_data_text, from_json_filename, auto_ch_hook,
                         stderr_file, member_name=member_name)


# pylint: disable-next=too-few-public-methods
class RecordingFactory:
    """Factory recording the ok_to_use_defaults it is called with."""

    def __init__(self) -> None:
        """Construct with nothing recorded."""
        self.flags: list[bool] = []

    def __call__(self, *, from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 stderr_file: TextIO = sys.stderr,
                 member_name: Optional[str] = None,
                 ok_to_use_defaults: bool = False) -> Config:
        """Record the flag and construct a BlankItem."""
        self.flags.append(ok_to_use_defaults)
        return BlankItem(from_json_data_text, from_json_filename,
                         stderr_file=stderr_file, member_name=member_name,
                         ok_to_use_defaults=ok_to_use_defaults)


class _FactoryKeywords(TypedDict, total=False):
    """Keyword arguments that the library passes to a factory."""

    from_json_data_text: Optional[str]
    from_json_filename: Optional[PathOrStr]
    stderr_file: TextIO
    member_name: Optional[str]
    ok_to_use_defaults: bool


def kwargs_factory(**kwargs: Unpack[_FactoryKeywords]) -> Config:
    """Construct a BlankItem, forwarding every keyword argument."""
    return BlankItem(**kwargs)


def _always(json_text: str, stderr_file: TextIO) -> bool:
    """Match any JSON text."""
    _ = json_text, stderr_file
    return True


def picking_factory(*, from_json_data_text: Optional[str] = None,
                    from_json_filename: Optional[PathOrStr] = None,
                    stderr_file: TextIO = sys.stderr,
                    member_name: Optional[str] = None,
                    ok_to_use_defaults: bool = False) -> Config:
    """Construct an Item through config_factory_from_json."""
    return config_factory_from_json(
        match_configs=[MatchConfig(match_func=_always, config_class=Item)],
        auto_ch_hook=ConfigAutoChangeHook(),
        from_json_filename=from_json_filename,
        from_json_data_text=from_json_data_text, stderr_file=stderr_file,
        member_name=member_name, ok_to_use_defaults=ok_to_use_defaults)


_HELD = json.dumps({'name': 'held', 'size': 7})
"""JSON data of the current nested objects, whose size is not the default."""


class Holder(Config):
    """Configuration holding items built by a factory, in two kinds."""

    def __init__(self, factory: ConfigFactory,
                 item_type: type[Item | BlankItem] = BlankItem) -> None:
        """Construct holding items of size 7."""
        self._factory = factory
        self._item_type = item_type
        self.member = item_type(_HELD)
        self.items = [item_type(_HELD)]
        super().__init__(None, None)

    def nested_configs(self) -> NestedConfigs:
        """Return the MEMBER and LIST_ELEMENT declarations."""
        return {'member': self._nesting(ConfigNestingKind.MEMBER),
                'items': self._nesting(ConfigNestingKind.LIST_ELEMENT)}

    def _nesting(self, kind: ConfigNestingKind) -> ConfigNesting:
        """Return one declaration built by the factory."""
        return ConfigNesting(kind=kind, config_type=self._item_type,
                             factory_function=self._factory)

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Return no validation."""
        _ = stderr_file
        return []


_PARTIAL = json.dumps({'member': {'name': 'm'},
                       'items': [{'name': 'i', 'size': 3}, {'name': 'j'}]})
"""Holder JSON data lacking the size of the member and the second item."""

_COMPLETE = json.dumps({'member': {'name': 'm', 'size': 2},
                        'items': [{'name': 'i', 'size': 3}]})
"""Holder JSON data lacking nothing."""


def _assert_quiet(capsys: CaptureFixture[str]) -> None:
    """Assert that nothing was written to stdout or stderr."""
    out, err = capsys.readouterr()
    assert out == ''
    assert err == ''


@pytest.mark.parametrize('factory, item_type', [
    (RecordingFactory(), BlankItem), (kwargs_factory, BlankItem),
    (picking_factory, Item)])
def test_factory_keeps(capsys: CaptureFixture[str], factory: ConfigFactory,
                       item_type: type[Item | BlankItem]) -> None:
    """Test that a factory accepting the flag keeps the class defaults.

    A factory never parses in place, so a kept size is the class default
    1, and not the size 7 of the current nested objects. The kept paths
    are prefixed by the path of the nested object in the parent.
    """
    cfg = Holder(factory, item_type)
    member = cfg.member
    assert deprecations(lambda: cfg.parse_json(_PARTIAL, True)) == []
    assert cfg.member is not member
    assert (cfg.member.name, cfg.member.size) == ('m', 1)
    assert [(i.name, i.size) for i in cfg.items] == [('i', 3), ('j', 1)]
    assert sorted(cfg.kept_value_paths()) == [('items', 1, 'size'),
                                              ('member', 'size')]
    _assert_quiet(capsys)


@pytest.mark.parametrize('ok_to_use_defaults', [True, False])
def test_factory_flag(capsys: CaptureFixture[str],
                      ok_to_use_defaults: bool) -> None:
    """Test that a factory gets the flag only when it is true."""
    factory = RecordingFactory()
    cfg = Holder(factory)
    cfg.parse_json(_COMPLETE, ok_to_use_defaults)
    assert factory.flags == [ok_to_use_defaults] * 2
    assert not cfg.kept_value_paths()
    _assert_quiet(capsys)


def test_factory_no_keyword(capsys: CaptureFixture[str]) -> None:
    """Test that a factory without the keyword parses strictly.

    It is warned about once, and a partial nested object is an error.
    """

    def old_factory(*, from_json_data_text: Optional[str] = None,
                    from_json_filename: Optional[PathOrStr] = None,
                    stderr_file: TextIO = sys.stderr,
                    member_name: Optional[str] = None) -> Config:
        """Construct an Item, without accepting ok_to_use_defaults."""
        return Item(from_json_data_text, from_json_filename,
                    stderr_file=stderr_file, member_name=member_name)
    cfg = Holder(old_factory, Item)  # type: ignore[arg-type]
    messages = deprecations(lambda: cfg.parse_json(_COMPLETE, True))
    assert len(messages) == 1
    assert 'old_factory() does not accept the ok_to_use_defaults' \
        in messages[0]
    assert 'will stop working in a future major release' in messages[0]
    assert (cfg.member.name, cfg.member.size) == ('m', 2)
    assert deprecations(lambda: cfg.parse_json(_COMPLETE, True)) == []
    with pytest.raises(ConfigMissingKey) as exc_info:
        cfg.parse_json(_PARTIAL, True, stderr_file=sys.stderr)
    assert exc_info.value.json_path == ('member', 'size')
    out, err = capsys.readouterr()
    assert out == ''
    assert 'No value for' in err


def test_factory_lacks_both(capsys: CaptureFixture[str]) -> None:
    """Test that a factory lacking both keywords is warned about twice."""

    def older_factory(*, from_json_data_text: Optional[str] = None,
                      from_json_filename: Optional[PathOrStr] = None,
                      stderr_file: TextIO = sys.stderr) -> Config:
        """Construct an Item, accepting neither keyword."""
        return Item(from_json_data_text, from_json_filename,
                    stderr_file=stderr_file)
    cfg = Holder(older_factory, Item)  # type: ignore[arg-type]
    messages = deprecations(lambda: cfg.parse_json(_COMPLETE, True))
    assert len(messages) == 2
    assert 'does not accept the member_name' in messages[0]
    assert 'does not accept the ok_to_use_defaults' in messages[1]
    _assert_quiet(capsys)


def test_strict_no_inspect(capsys: CaptureFixture[str],
                           monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that a strict parse never checks the factory for the flag."""
    asked: list[str] = []
    original = depr_mod._signature_takes  # pylint: disable=protected-access

    def recorded(func: Callable[..., object], name: str) -> bool:
        """Record the keyword asked about, and answer as before."""
        asked.append(name)
        return original(func, name)

    def old_factory(*, from_json_data_text: Optional[str] = None,
                    from_json_filename: Optional[PathOrStr] = None,
                    stderr_file: TextIO = sys.stderr,
                    member_name: Optional[str] = None) -> Config:
        """Construct an Item, without accepting ok_to_use_defaults."""
        return Item(from_json_data_text, from_json_filename,
                    stderr_file=stderr_file, member_name=member_name)
    monkeypatch.setattr(depr_mod, '_signature_takes', recorded)
    cfg = Holder(old_factory, Item)  # type: ignore[arg-type]
    assert deprecations(lambda: cfg.parse_json(_COMPLETE)) == []
    assert 'ok_to_use_defaults' not in asked
    assert (cfg.member.name, cfg.member.size) == ('m', 2)
    _assert_quiet(capsys)


def _from_json(item_type: type[Config], source: str, tmp_path: Path,
               hook: ConfigAutoChangeHook,
               ok_to_use_defaults: bool = True) -> Config:
    """Construct item_type through config_factory_from_json.

    Args:
        item_type: The class that the factory selects.
        source: ``'text'`` or ``'file'``, which input to construct from.
        tmp_path: Directory for the JSON file.
        hook: Automatic-change hook given to the factory.
        ok_to_use_defaults: The flag given to the factory.

    Returns:
        The constructed object.
    """
    text = '{"name": "x"}'
    filename = tmp_path / 'item.cfg'
    filename.write_text(text, encoding='UTF-8')
    matcher = MatchConfig(match_func=JsonValueMatcher('name', 'x'),
                          config_class=item_type)
    return config_factory_from_json(
        match_configs=[matcher], auto_ch_hook=hook,
        from_json_filename=filename if source == 'file' else None,
        from_json_data_text=text if source == 'text' else None,
        stderr_file=sys.stderr, ok_to_use_defaults=ok_to_use_defaults)


@pytest.mark.parametrize('item_type', [Item, BlankItem])
@pytest.mark.parametrize('source', ['text', 'file'])
def test_from_json_keeps(capsys: CaptureFixture[str], tmp_path: Path,
                         item_type: type[Item | BlankItem],
                         source: str) -> None:
    """Test that config_factory_from_json keeps the class defaults.

    BlankItem gets the keyword, so its invalid defaults are never validated
    on their own. Item is constructed from its defaults and then parsed.
    Either way the object gets the hook given to the factory.
    """
    hook = ConfigAutoChangeHook()
    cfg = _from_json(item_type, source, tmp_path, hook)
    assert isinstance(cfg, item_type)
    assert (cfg.name, cfg.size) == ('x', 1)
    assert cfg.kept_value_paths() == [('size',)]
    assert cfg.auto_change_hook() is hook
    _assert_quiet(capsys)


def test_from_json_invalid(capsys: CaptureFixture[str],
                           tmp_path: Path) -> None:
    """Test that defaults are validated alone without the keyword."""
    with pytest.raises(InvalidConfiguration):
        _from_json(StrictBlankItem, 'text', tmp_path, ConfigAutoChangeHook())
    out, err = capsys.readouterr()
    assert out == ''
    assert 'Empty name' in err


@pytest.mark.parametrize('item_type', [Item, BlankItem])
def test_from_json_strict(capsys: CaptureFixture[str], tmp_path: Path,
                          item_type: type[Item | BlankItem]) -> None:
    """Test that config_factory_from_json is strict without the flag."""
    with pytest.raises(ConfigMissingKey):
        _from_json(item_type, 'text', tmp_path, ConfigAutoChangeHook(),
                   ok_to_use_defaults=False)
    out, err = capsys.readouterr()
    assert out == ''
    assert 'No value for' in err


class NoDefaultsHex(HexadecimalNumber):
    """HexadecimalNumber whose constructor lacks ok_to_use_defaults."""

    # pylint: disable-next=too-many-arguments
    def __init__(self, from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 auto_ch_hook: Optional[ConfigAutoChangeHook] = None,
                 stderr_file: TextIO = sys.stderr, *,
                 value: Optional[int | str] = None,
                 prefix: Optional[HexadecimalNumber.Prefix] = None,
                 digits: int = 0, member_name: Optional[str] = None) -> None:
        """Construct without ok_to_use_defaults."""
        super().__init__(from_json_data_text, from_json_filename, auto_ch_hook,
                         stderr_file, value=value, prefix=prefix,
                         digits=digits, member_name=member_name)


def _hex_factory(hex_type: type[HexadecimalNumber]) -> ConfigFactory:
    """Return a factory of hex_type values defaulting to 0x001f."""
    return hex_type.factory(HexadecimalNumber.Prefix.ZERO_X, 4, 0x1f)


class MaskHolder(Config):
    """Configuration holding one hexadecimal value built by a factory."""

    def __init__(self, hex_type: type[HexadecimalNumber]) -> None:
        """Construct holding a mask of value 0x001f."""
        self._factory = _hex_factory(hex_type)
        self._hex_type = hex_type
        mask = self._factory()
        assert isinstance(mask, HexadecimalNumber)
        self.mask = mask
        super().__init__(None, None)

    def nested_configs(self) -> NestedConfigs:
        """Return the mask declaration built by the factory."""
        return {'mask': ConfigNesting(kind=ConfigNestingKind.MEMBER,
                                      config_type=self._hex_type,
                                      factory_function=self._factory)}

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Return no validation."""
        _ = stderr_file
        return []


@pytest.mark.parametrize('hex_type', [HexadecimalNumber, NoDefaultsHex])
def test_radix_nested(capsys: CaptureFixture[str],
                      hex_type: type[HexadecimalNumber]) -> None:
    """Test that a radix factory keeps the value of the factory."""
    cfg = MaskHolder(hex_type)
    cfg.mask.set(5)
    assert deprecations(lambda: cfg.parse_json('{"mask": {}}', True)) == []
    assert isinstance(cfg.mask, hex_type)
    assert (cfg.mask.get(), cfg.mask.hex_str) == (0x1f, '0x001f')
    assert cfg.kept_value_paths() == [('mask', 'hex_str')]
    with pytest.raises(ConfigMissingKey):
        cfg.parse_json('{"mask": {}}', stderr_file=sys.stderr)
    out, err = capsys.readouterr()
    assert out == ''
    assert 'No value for' in err


@pytest.mark.parametrize('hex_type', [HexadecimalNumber, NoDefaultsHex])
@pytest.mark.parametrize('source', ['text', 'file'])
def test_radix_direct(capsys: CaptureFixture[str], tmp_path: Path,
                      hex_type: type[HexadecimalNumber], source: str) -> None:
    """Test a radix factory called with the flag and either JSON source."""
    filename = tmp_path / 'mask.cfg'
    filename.write_text('{}', encoding='UTF-8')
    factory = _hex_factory(hex_type)
    mask = factory(from_json_data_text='{}' if source == 'text' else None,
                   from_json_filename=filename if source == 'file' else None,
                   ok_to_use_defaults=True)
    assert isinstance(mask, hex_type)
    assert mask.hex_str == '0x001f'
    kept: list[JsonPath] = [('hex_str',)]
    assert mask.kept_value_paths() == kept
    _assert_quiet(capsys)
