#! /usr/local/bin/python3
"""Test that application code without ``member_name`` works, and warns.

Every place where this package calls into code of the application with
``member_name`` reads the signature of what it is about to call first. Code
that does not accept the argument is called without it, and is warned once
about what to change. The configuration is then handled exactly as the
version before the whole path existed handled it, and its diagnostics name
plain member names.

Each old-style class is declared inside the test function that is about it,
because the warning is issued once per function and per class for the whole
process.
"""

# Copyright (c) 2026 Tom Björkholm
# MIT License

import sys
from io import StringIO
from pathlib import Path
from typing import Optional, TextIO, override
from config_as_json.commontypes import PathOrStr
from config_as_json.config import Config
from config_as_json.config_auto_change_hook import ConfigAutoChangeHook
from config_as_json.config_factory import MatchConfig, \
    config_factory_from_json
from config_as_json.config_nesting import ConfigNesting, ConfigNestingKind, \
    NestedConfigs
from config_as_json.hexadecimal_number import HexadecimalNumber
from config_as_json.migrate_cfg import migrate_cfg
from config_as_json.validator import ValidationPlan, ValidationStep, \
    WholeConfigValidationStep, WholeConfigValidator
from .member_name_compat_tools import HOLDER_JSON, PlainHolder, PlainLeaf, \
    deprecations
from .member_path_test_configs import Leaf

LEAF_JSON = '{"kind": "parsed"}'
"""JSON for one nested leaf configuration."""


def test_old_validate() -> None:
    """An old-style validate override works, and warns once per class."""

    class OldValidate(Config):
        """A configuration written before ``member_name`` existed."""

        def __init__(self) -> None:
            """Construct the configuration holding its default value."""
            self.value = 'seed'
            super().__init__(from_json_data_text=None, from_json_filename=None)

        @override
        def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
            """Return no validation plan of its own."""
            _ = stderr_file
            return []

        # pylint: disable-next=arguments-differ
        def validate(self,  # type: ignore[override]
                     stderr_file: TextIO) -> None:
            """Validate the configuration the way an old version did."""
            _ = stderr_file
            self.value = 'validated'

    messages = deprecations(OldValidate)
    assert len(messages) == 1
    assert 'OldValidate.validate' in messages[0]
    assert deprecations(OldValidate) == []
    assert OldValidate().value == 'validated'


def test_old_parse_json() -> None:
    """An old-style parse_json override works, and warns once per class."""

    class OldParse(Config):
        """A configuration written before ``member_name`` existed."""

        def __init__(self, from_json_data_text: Optional[str] = None) -> None:
            """Construct the configuration from the given JSON text."""
            self.kind = 'seed'
            super().__init__(from_json_data_text=from_json_data_text,
                             from_json_filename=None)

        @override
        def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
            """Return no validation plan of its own."""
            _ = stderr_file
            return []

        # pylint: disable-next=arguments-differ
        def parse_json(self,  # type: ignore[override]
                       from_json_text: str, ok_to_use_defaults: bool = False,
                       stderr_file: TextIO = sys.stderr) -> None:
            """Parse the JSON text the way an old version did."""
            super().parse_json(from_json_text, ok_to_use_defaults,
                               stderr_file=stderr_file)

    messages = deprecations(lambda: OldParse(from_json_data_text=LEAF_JSON))
    assert len(messages) == 1
    assert 'OldParse.parse_json' in messages[0]
    assert deprecations(lambda: OldParse(from_json_data_text=LEAF_JSON)) == []
    assert OldParse(from_json_data_text=LEAF_JSON).kind == 'parsed'


def test_old_read(tmp_path: Path) -> None:
    """An old-style read override works, and warns once per class."""
    filename = tmp_path / 'old.json'
    filename.write_text(LEAF_JSON, encoding='UTF-8')

    class OldRead(Config):
        """A configuration written before ``member_name`` existed."""

        def __init__(self, from_json_filename: Optional[PathOrStr]) -> None:
            """Construct the configuration from the given JSON file."""
            self.kind = 'seed'
            super().__init__(from_json_data_text=None,
                             from_json_filename=from_json_filename)

        @override
        def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
            """Return no validation plan of its own."""
            _ = stderr_file
            return []

        # pylint: disable-next=arguments-differ
        def read(self,  # type: ignore[override]
                 from_json_filename: PathOrStr,
                 ok_to_use_defaults: bool = False,
                 stderr_file: TextIO = sys.stderr) -> None:
            """Read the JSON file the way an old version did."""
            super().read(from_json_filename, ok_to_use_defaults,
                         stderr_file=stderr_file)

    messages = deprecations(lambda: OldRead(filename))
    assert len(messages) == 1
    assert 'OldRead.read' in messages[0]
    assert OldRead(filename).kind == 'parsed'


def test_old_as_json_string(tmp_path: Path) -> None:
    """An old-style as_json_string override works, and warns once."""

    class OldWrite(Config):
        """A configuration written before ``member_name`` existed."""

        def __init__(self) -> None:
            """Construct the configuration holding its default value."""
            self.kind = 'seed'
            super().__init__(from_json_data_text=None, from_json_filename=None)

        @override
        def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
            """Return no validation plan of its own."""
            _ = stderr_file
            return []

        # pylint: disable-next=arguments-differ
        def as_json_string(self,  # type: ignore[override]
                           stderr_file: TextIO) -> str:
            """Serialize the configuration the way an old version did."""
            return super().as_json_string(stderr_file=stderr_file)

    written = tmp_path / 'written.json'
    cfg = OldWrite()
    messages = deprecations(lambda: cfg.write(to_json_filename=written))
    assert len(messages) == 1
    assert 'OldWrite.as_json_string' in messages[0]
    assert '"kind": "seed"' in written.read_text(encoding='UTF-8')


def test_old_nested_class() -> None:
    """An old-style nested class is constructed, and warns once per class."""

    class OldNested(Config):
        """A nested configuration written before ``member_name`` existed."""

        def __init__(self, from_json_data_text: Optional[str] = None,
                     from_json_filename: Optional[PathOrStr] = None,
                     stderr_file: TextIO = sys.stderr) -> None:
            """Construct one nested configuration the old way."""
            self.kind = 'seed'
            super().__init__(from_json_data_text=from_json_data_text,
                             from_json_filename=from_json_filename,
                             stderr_file=stderr_file)

        @override
        def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
            """Return no validation plan of its own."""
            _ = stderr_file
            return []

    class OldHolder(Config):
        """A configuration holding one old-style nested configuration."""

        def __init__(self, from_json_data_text: Optional[str] = None,
                     member_name: Optional[str] = None) -> None:
            """Construct one holder of the old-style nested configuration."""
            self.part = OldNested()
            super().__init__(from_json_data_text=from_json_data_text,
                             from_json_filename=None, member_name=member_name)

        @override
        def nested_configs(self) -> NestedConfigs:
            """Return the one nested Config declaration."""
            return {'part': ConfigNesting(kind=ConfigNestingKind.MEMBER,
                                          config_type=OldNested)}

        @override
        def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
            """Return no validation plan of its own."""
            _ = stderr_file
            return []

    messages = deprecations(lambda: OldHolder(from_json_data_text=HOLDER_JSON))
    assert len(messages) == 1
    assert 'OldNested.__init__' in messages[0]
    parsed = OldHolder(from_json_data_text=HOLDER_JSON)
    assert isinstance(parsed.part, OldNested)
    assert parsed.part.kind == 'parsed'


def test_old_factory() -> None:
    """An old-style factory function is called, and warns once."""

    def old_factory(*, from_json_data_text: Optional[str] = None,
                    from_json_filename: Optional[PathOrStr] = None,
                    stderr_file: TextIO = sys.stderr) -> Config:
        """Construct one nested configuration the old way."""
        return PlainLeaf(from_json_data_text=from_json_data_text,
                         from_json_filename=from_json_filename,
                         stderr_file=stderr_file)

    class FactoryHolder(Config):
        """A configuration whose nested member has an old-style factory."""

        def __init__(self, from_json_data_text: Optional[str] = None,
                     member_name: Optional[str] = None) -> None:
            """Construct one holder using the old-style factory."""
            self.part = PlainLeaf()
            super().__init__(from_json_data_text=from_json_data_text,
                             from_json_filename=None, member_name=member_name)

        @override
        def nested_configs(self) -> NestedConfigs:
            """Return the one nested Config declaration."""
            return {'part': ConfigNesting(
                kind=ConfigNestingKind.MEMBER, config_type=PlainLeaf,
                factory_function=old_factory)}  # type: ignore[arg-type]

        @override
        def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
            """Return no validation plan of its own."""
            _ = stderr_file
            return []

    def action() -> Config:
        """Construct one holder, which uses the old-style factory."""
        return FactoryHolder(from_json_data_text=HOLDER_JSON)

    messages = deprecations(action)
    assert len(messages) == 1
    assert 'old_factory' in messages[0]
    assert deprecations(action) == []
    assert isinstance(FactoryHolder(from_json_data_text=HOLDER_JSON).part,
                      PlainLeaf)


def test_old_validation_step() -> None:
    """An old-style validation step is applied, and warns once per class."""
    # pylint: disable-next=too-few-public-methods
    class OldStep(ValidationStep):
        """A validation step written before ``member_name`` existed."""

        # pylint: disable-next=arguments-differ
        def apply(self, config: Config,  # type: ignore[override]
                  stderr_file: TextIO = sys.stderr) -> None:
            """Refuse nothing, and record that the step was applied."""
            _ = stderr_file
            assert isinstance(config, PlainLeaf)
            config.kind = 'stepped'

    class StepConfig(PlainLeaf):
        """A configuration validated by the old-style validation step."""

        @override
        def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
            """Return the one old-style validation step."""
            _ = stderr_file
            return [OldStep()]

    messages = deprecations(StepConfig)
    assert len(messages) == 1
    assert 'OldStep.apply' in messages[0]
    assert deprecations(StepConfig) == []
    assert StepConfig().kind == 'stepped'


def test_old_whole_validator() -> None:
    """An old-style whole-config validator is called, and warns once."""
    # pylint: disable-next=too-few-public-methods
    class OldWhole(WholeConfigValidator):
        """A whole-config validator written before the path existed."""

        # pylint: disable-next=arguments-differ
        def validate(self, config: Config,  # type: ignore[override]
                     stderr_file: TextIO = sys.stderr) -> None:
            """Refuse nothing, and record that the validator was called."""
            _ = stderr_file
            assert isinstance(config, PlainLeaf)
            config.kind = 'checked'

    class WholeConfig(PlainLeaf):
        """A configuration validated by the old-style validator."""

        @override
        def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
            """Return the one old-style whole-config validation step."""
            _ = stderr_file
            return [WholeConfigValidationStep(validator=OldWhole())]

    messages = deprecations(WholeConfig)
    assert len(messages) == 1
    assert 'OldWhole.validate' in messages[0]
    assert deprecations(WholeConfig) == []
    assert WholeConfig().kind == 'checked'


def test_old_class_from_factory() -> None:
    """``config_factory_from_json`` constructs an old-style class."""

    class OldMatched(Config):
        """A configuration written before ``member_name`` existed."""

        def __init__(self, from_json_data_text: Optional[str] = None,
                     from_json_filename: Optional[PathOrStr] = None,
                     auto_ch_hook: Optional[ConfigAutoChangeHook] = None,
                     stderr_file: TextIO = sys.stderr) -> None:
            """Construct the configuration the old way."""
            self.kind = 'seed'
            super().__init__(from_json_data_text=from_json_data_text,
                             from_json_filename=from_json_filename,
                             auto_ch_hook=auto_ch_hook,
                             stderr_file=stderr_file)

        @override
        def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
            """Return no validation plan of its own."""
            _ = stderr_file
            return []

    def make() -> Config:
        """Construct the matched configuration through the factory."""
        matchers = [MatchConfig(match_func=lambda text, stderr: True,
                                config_class=OldMatched)]
        return config_factory_from_json(match_configs=matchers,
                                        auto_ch_hook=ConfigAutoChangeHook(),
                                        from_json_data_text=LEAF_JSON,
                                        stderr_file=sys.stderr)

    messages = deprecations(make)
    assert len(messages) == 1
    assert 'OldMatched.__init__' in messages[0]
    assert deprecations(make) == []
    made = make()
    assert isinstance(made, OldMatched)
    assert made.kind == 'parsed'


def test_old_class_migrated(tmp_path: Path) -> None:
    """``migrate_cfg`` migrates a file of an old-style class."""
    infile = tmp_path / 'old.json'
    infile.write_text(LEAF_JSON, encoding='UTF-8')
    outfile = tmp_path / 'new.json'

    class OldMigrated(Config):
        """A configuration written before ``member_name`` existed."""

        def __init__(self, from_json_data_text: Optional[str] = None,
                     from_json_filename: Optional[PathOrStr] = None,
                     auto_ch_hook: Optional[ConfigAutoChangeHook] = None,
                     stderr_file: TextIO = sys.stderr) -> None:
            """Construct the configuration the old way."""
            self.kind = 'seed'
            super().__init__(from_json_data_text=from_json_data_text,
                             from_json_filename=from_json_filename,
                             auto_ch_hook=auto_ch_hook,
                             stderr_file=stderr_file)

        @override
        def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
            """Return no validation plan of its own."""
            _ = stderr_file
            return []

    def migrate() -> int:
        """Migrate the old configuration file to the new file."""
        return migrate_cfg(infile=infile, outfile=outfile,
                           config_class=OldMigrated, stderr_file=sys.stderr)

    messages = deprecations(migrate)
    assert len(messages) == 1
    assert 'OldMigrated.__init__' in messages[0]
    assert '"kind": "parsed"' in outfile.read_text(encoding='UTF-8')


def test_old_bridge_class() -> None:
    """An old-style bridge class wraps a neutral default value, and warns."""
    # pylint: disable-next=too-few-public-methods
    class Neutral:
        """A value of the application that is no configuration object."""

        def __init__(self) -> None:
            """Initialize the neutral value."""
            self.kind = 'neutral'

    class OldBridge(Config):
        """A bridge class written before ``member_name`` existed."""

        def __init__(self, from_json_data_text: Optional[str] = None,
                     from_json_filename: Optional[PathOrStr] = None,
                     stderr_file: TextIO = sys.stderr) -> None:
            """Construct one bridge configuration the old way."""
            self.kind = 'seed'
            super().__init__(from_json_data_text=from_json_data_text,
                             from_json_filename=from_json_filename,
                             stderr_file=stderr_file)

        @override
        def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
            """Return no validation plan of its own."""
            _ = stderr_file
            return []

    class BridgeHolder(Config):
        """A configuration whose nested default value is a neutral value."""

        def __init__(self, member_name: Optional[str] = None) -> None:
            """Construct one holder of the neutral default value."""
            self.part: object = Neutral()
            super().__init__(from_json_data_text=None, from_json_filename=None,
                             member_name=member_name)

        @override
        def nested_configs(self) -> NestedConfigs:
            """Return the one nested Config declaration."""
            return {'part': ConfigNesting(kind=ConfigNestingKind.MEMBER,
                                          config_type=OldBridge)}

        @override
        def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
            """Return no validation plan of its own."""
            _ = stderr_file
            return []

    messages = deprecations(BridgeHolder)
    assert len(messages) == 1
    assert 'OldBridge.__init__' in messages[0]
    wrapped = BridgeHolder().part
    assert isinstance(wrapped, OldBridge)
    assert wrapped.kind == 'neutral'


def test_old_radix_class() -> None:
    """An old-style written-number class is constructed by its factory."""

    class OldHex(HexadecimalNumber):
        """A hexadecimal value written before ``member_name`` existed."""

        # pylint: disable-next=too-many-arguments
        def __init__(self, from_json_data_text: Optional[str] = None,
                     from_json_filename: Optional[PathOrStr] = None,
                     auto_ch_hook: Optional[ConfigAutoChangeHook] = None,
                     stderr_file: TextIO = sys.stderr, *,
                     value: Optional[int | str] = None,
                     prefix: Optional['HexadecimalNumber.Prefix'] = None,
                     digits: int = 0) -> None:
            """Construct one hexadecimal value the old way."""
            super().__init__(from_json_data_text, from_json_filename,
                             auto_ch_hook, stderr_file, value=value,
                             prefix=prefix, digits=digits)

    factory = OldHex.factory(OldHex.Prefix.ZERO_X, 4, 0)

    class MaskConfig(Config):
        """A configuration with one hexadecimal value in it."""

        def __init__(self, from_json_data_text: Optional[str] = None,
                     member_name: Optional[str] = None) -> None:
            """Construct one configuration holding the declared default."""
            self.mask = OldHex(value=0, prefix=OldHex.Prefix.ZERO_X, digits=4)
            super().__init__(from_json_data_text=from_json_data_text,
                             from_json_filename=None, member_name=member_name)

        @override
        def nested_configs(self) -> NestedConfigs:
            """Return the one nested Config declaration."""
            return {'mask': ConfigNesting(kind=ConfigNestingKind.MEMBER,
                                          config_type=OldHex,
                                          factory_function=factory)}

        @override
        def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
            """Return no validation plan of its own."""
            _ = stderr_file
            return []

    json_text = '{"mask": {"hex_str": "1f"}}'

    def action() -> Config:
        """Construct one configuration, which uses the old-style class."""
        return MaskConfig(from_json_data_text=json_text)

    messages = deprecations(action)
    assert len(messages) == 1
    assert 'OldHex.__init__' in messages[0]
    assert deprecations(action) == []
    assert MaskConfig(from_json_data_text=json_text).mask.get() == 0x1f


def test_warning_says_what_to_change() -> None:
    """The warning names the method, the argument, and the loss it causes."""

    class OldNamed(PlainHolder):
        """A configuration written before ``member_name`` existed."""

        # pylint: disable-next=arguments-differ
        def validate(self,  # type: ignore[override]
                     stderr_file: TextIO) -> None:
            """Validate nothing, the way an old version did."""
            _ = stderr_file

    messages = deprecations(OldNamed)
    assert len(messages) == 1
    message = messages[0]
    assert 'OldNamed.validate() does not accept the member_name' in message
    assert "Add 'member_name: Optional[str] = None' to it" in message
    assert 'outputs[1].kind' in message
    assert 'future major release' in message


def test_old_style_loses_the_path() -> None:
    """A diagnostic below an old-style override names a shorter path.

    The old-style override is not told the path of the object it validates,
    so the objects nested in it are told nothing about the levels above it.
    The leaf below it reports ``leaf.kind`` where a new-style holder would
    have made it report ``mid.leaf.kind``. That is the documented price of
    not accepting the argument.
    """

    class OldMiddle(Config):
        """A configuration written before ``member_name`` existed."""

        def __init__(self, stderr_file: TextIO = sys.stderr) -> None:
            """Construct one holder of the leaf configuration."""
            self.leaf = Leaf(stderr_file=stderr_file)
            super().__init__(from_json_data_text=None, from_json_filename=None,
                             stderr_file=stderr_file)

        @override
        def nested_configs(self) -> NestedConfigs:
            """Return the one nested Config declaration."""
            return {'leaf': ConfigNesting(kind=ConfigNestingKind.MEMBER,
                                          config_type=Leaf)}

        @override
        def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
            """Return no validation plan of its own."""
            _ = stderr_file
            return []

        # pylint: disable-next=arguments-differ
        def validate(self,  # type: ignore[override]
                     stderr_file: TextIO) -> None:
            """Validate the nested member the way an old version did."""
            super().validate(stderr_file=stderr_file)

    class NewTop(Config):
        """A configuration holding the old-style configuration."""

        def __init__(self, stderr_file: TextIO = sys.stderr) -> None:
            """Construct one holder of the old-style configuration."""
            self.mid = OldMiddle(stderr_file=stderr_file)
            super().__init__(from_json_data_text=None, from_json_filename=None,
                             stderr_file=stderr_file, member_name=None)

        @override
        def nested_configs(self) -> NestedConfigs:
            """Return the one nested Config declaration."""
            return {'mid': ConfigNesting(kind=ConfigNestingKind.MEMBER,
                                         config_type=OldMiddle)}

        @override
        def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
            """Return no validation plan of its own."""
            _ = stderr_file
            return []

    stderr = StringIO()

    def build_and_validate() -> None:
        """Construct the configuration and validate it once."""
        top = NewTop(stderr_file=stderr)
        top.mid.leaf.kind = 'legacy'
        top.validate(stderr_file=stderr, member_name=None)

    assert len(deprecations(build_and_validate)) == 1
    assert 'Warning: leaf.kind still uses a legacy format' in stderr.getvalue()
    assert 'mid.leaf.kind' not in stderr.getvalue()
