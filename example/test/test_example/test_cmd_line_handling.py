#! /usr/local/bin/python3
"""Tests for the shared example command line helper."""

# Copyright (c) 2026 Tom Björkholm
# MIT License

import argparse
from enum import Enum, auto
import pytest
from config_as_json.commontypes import PathOrStr
from example.cmd_line_handling import InputSpec, SetValues
from example.cmd_line_handling import _add_set_arguments, _bool_from_text
from example.cmd_line_handling import _create_argument_parser, _enum_from_text
from example.cmd_line_handling import _dict_kv_token_parser
from example.cmd_line_handling import _json_token_parser
from example.cmd_line_handling import _nested_value_parser, _token_parser
from example.cmd_line_handling import _set_values_from_args, _value_parser
from example.cmd_line_handling import cmd_line_handling


class SampleMode(Enum):
    """Enum used to test enum conversion from command line text."""

    ALPHA = auto()
    BETA = auto()
    GAMMA = auto()


TEST_INPUT_SPECS = [
    InputSpec(name='file_name', single=True, value_type=str),
    InputSpec(name='count', single=True, value_type=int),
    InputSpec(name='ratio', single=True, value_type=float),
    InputSpec(name='enabled', single=True, value_type=bool),
    InputSpec(name='mode', single=True, value_type=SampleMode),
    InputSpec(name='step_values', single=False, value_type=int),
    InputSpec(name='matrix', single=False, value_type=int, nested=True),
    InputSpec(name='flags', single=False, value_type=bool, dict_kv=True),
    InputSpec(name='payload', single=True, value_type=str, json_value=True)
]
"""Input specifications used by the shared helper tests."""


class CommandCallRecorder:
    """Record calls made through the shared command line helper."""

    def __init__(self) -> None:
        """Initialize empty call history."""
        self.set_calls: list[tuple[SetValues, str]] = []
        self.print_calls: list[str] = []

    def set_command(self, set_values: SetValues,
                    config_file: PathOrStr) -> None:
        """Record one set command invocation."""
        self.set_calls.append((dict(set_values), str(config_file)))

    def print_command(self, config_file: PathOrStr) -> None:
        """Record one print command invocation."""
        self.print_calls.append(str(config_file))


@pytest.mark.parametrize('text, expected',
                         [('true', True),
                          ('TRUE', True),
                          ('false', False),
                          ('FaLsE', False)])
def test_bool_from_text_accepts_true_and_false_words(
        text: str, expected: bool) -> None:
    """Convert case-insensitive true and false text to booleans."""
    assert _bool_from_text(text) is expected


def test_bool_from_text_rejects_other_words() -> None:
    """Reject boolean text that is not true or false."""
    with pytest.raises(argparse.ArgumentTypeError) as exc:
        _ = _bool_from_text('yes')
    assert 'true' in str(exc.value)
    assert 'false' in str(exc.value)


def test_enum_from_text_uses_representative_matching() -> None:
    """Accept representative enum spellings and reject missing values."""
    assert _enum_from_text('beta', SampleMode) is SampleMode.BETA
    with pytest.raises(argparse.ArgumentTypeError) as exc:
        _ = _enum_from_text('missing', SampleMode)
    assert 'missing' in str(exc.value)
    assert 'ALPHA' in str(exc.value)
    assert 'BETA' in str(exc.value)
    assert 'GAMMA' in str(exc.value)


def test_value_parser_converts_builtin_types_and_enums() -> None:
    """Return converters matching the declared value type."""
    assert _value_parser(str)('Ada') == 'Ada'
    assert _value_parser(int)('7') == 7
    assert _value_parser(float)('2.5') == pytest.approx(2.5)
    assert _value_parser(bool)('FALSE') is False
    assert _value_parser(SampleMode)('gamma') is SampleMode.GAMMA


def test_nested_value_parser_splits_and_converts_tokens() -> None:
    """Split one CLI token into a list of scalar values."""
    parse_ints = _nested_value_parser(int)
    assert parse_ints('1,2,3') == [1, 2, 3]
    assert parse_ints('42') == [42]
    parse_floats = _nested_value_parser(float)
    assert parse_floats('1.5,2.5') == [pytest.approx(1.5), pytest.approx(2.5)]


def test_nested_value_parser_reports_invalid_scalar_values() -> None:
    """Propagate the inner converter error for bad nested tokens."""
    parse_ints = _nested_value_parser(int)
    with pytest.raises(ValueError):
        _ = parse_ints('1,abc')


def test_token_parser_rejects_nested_single_combination() -> None:
    """Reject the unsupported combination of nested and single."""
    with pytest.raises(ValueError) as exc:
        _ = _token_parser(InputSpec(name='bad', single=True,
                                    value_type=int, nested=True))
    assert 'nested' in str(exc.value)
    assert 'single' in str(exc.value)


def test_dict_kv_token_parser_splits_key_and_value() -> None:
    """Split one key=value token into the typed pair."""
    parse_ints = _dict_kv_token_parser(int)
    assert parse_ints('count=7') == ('count', 7)
    assert parse_ints('label=42') == ('label', 42)
    parse_bools = _dict_kv_token_parser(bool)
    assert parse_bools('enabled=true') == ('enabled', True)
    assert parse_bools('enabled=FALSE') == ('enabled', False)


def test_dict_kv_token_parser_uses_first_separator_only() -> None:
    """Split on the first ``=`` so values may themselves contain ``=``."""
    parse = _dict_kv_token_parser(str)
    assert parse('query=name=ada') == ('query', 'name=ada')


def test_dict_kv_token_parser_rejects_token_without_separator() -> None:
    """Reject a dict_kv token that does not contain ``=``."""
    parse = _dict_kv_token_parser(int)
    with pytest.raises(argparse.ArgumentTypeError) as exc:
        _ = parse('count7')
    assert '=' in str(exc.value)


def test_json_token_parser_returns_python_values() -> None:
    """Parse a JSON-encoded token into the matching Python value."""
    parse = _json_token_parser()
    assert parse('42') == 42
    assert parse('"hello"') == 'hello'
    assert parse('[1,2,3]') == [1, 2, 3]
    assert parse('{"a": 1}') == {'a': 1}


def test_json_token_parser_reports_invalid_json() -> None:
    """Reject a token that is not valid JSON."""
    parse = _json_token_parser()
    with pytest.raises(argparse.ArgumentTypeError):
        _ = parse('not json')


@pytest.mark.parametrize('input_spec, expected_fragment', [
    (InputSpec(name='bad', single=True, value_type=int, dict_kv=True),
     'dict_kv'),
    (InputSpec(name='bad', single=False, value_type=int, json_value=True),
     'json_value'),
    (InputSpec(name='bad', single=False, value_type=int,
               nested=True, dict_kv=True),
     'mutually exclusive'),
    (InputSpec(name='bad', single=True, value_type=int,
               nested=False, json_value=True, dict_kv=True),
     'mutually exclusive'),
])
def test_token_parser_rejects_unsupported_flag_combinations(
        input_spec: InputSpec, expected_fragment: str) -> None:
    """Reject every unsupported combination of input spec flags."""
    with pytest.raises(ValueError) as exc:
        _ = _token_parser(input_spec)
    assert expected_fragment in str(exc.value)


def test_add_set_arguments_adds_single_list_and_nested_options() -> None:
    """Add command line options that parse single values and lists."""
    parser = argparse.ArgumentParser(prog='demo')
    _add_set_arguments(parser, TEST_INPUT_SPECS)
    parsed_args = parser.parse_args([
        '--file-name', 'Ada',
        '--count', '7',
        '--ratio', '2.5',
        '--enabled', 'false',
        '--mode', 'beta',
        '--step-values', '1', '2', '3',
        '--matrix', '1,2', '3,4', '5,6',
        '--flags', 'logging=true', 'debug=false',
        '--payload', '{"k": [1, 2]}'
    ])
    assert parsed_args.file_name == 'Ada'
    assert parsed_args.count == 7
    assert parsed_args.ratio == pytest.approx(2.5)
    assert parsed_args.enabled is False
    assert parsed_args.mode is SampleMode.BETA
    assert parsed_args.step_values == [1, 2, 3]
    assert parsed_args.matrix == [[1, 2], [3, 4], [5, 6]]
    assert parsed_args.flags == [('logging', True), ('debug', False)]
    assert parsed_args.payload == {'k': [1, 2]}


def test_set_values_from_args_collects_only_explicit_values() -> None:
    """Return only values that were set explicitly on the command line."""
    parsed_args = argparse.Namespace(
        file_name='Ada',
        count=None,
        ratio=2.5,
        enabled=None,
        mode=SampleMode.ALPHA,
        step_values=[1, 2],
        matrix=[[7, 8], [9, 10]],
        flags=[('logging', True), ('debug', False)],
        payload={'k': [1, 2]}
    )
    set_values = _set_values_from_args(parsed_args, TEST_INPUT_SPECS)
    assert set_values == {
        'file_name': 'Ada',
        'ratio': 2.5,
        'mode': SampleMode.ALPHA,
        'step_values': [1, 2],
        'matrix': [[7, 8], [9, 10]],
        'flags': {'logging': True, 'debug': False},
        'payload': {'k': [1, 2]}
    }


def test_create_argument_parser_parses_print_and_set_commands() -> None:
    """Build parsers for both supported subcommands."""
    parser = _create_argument_parser('demo', TEST_INPUT_SPECS)
    print_args = parser.parse_args(['print', '--input', 'input.cfg'])
    set_args = parser.parse_args([
        'set',
        '--output', 'output.cfg',
        '--count', '7',
        '--step-values', '1', '2'
    ])
    assert print_args.command == 'print'
    assert print_args.input == 'input.cfg'
    assert set_args.command == 'set'
    assert set_args.output == 'output.cfg'
    assert set_args.count == 7
    assert set_args.step_values == [1, 2]


def test_create_argument_parser_reports_missing_command(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Require the user to choose either print or set."""
    parser = _create_argument_parser('demo', TEST_INPUT_SPECS)
    with pytest.raises(SystemExit) as exc:
        parser.parse_args([])
    _, err = capsys.readouterr()
    assert exc.value.code == 2
    assert 'usage:' in err
    assert 'print' in err
    assert 'set' in err
    assert 'command' in err


def test_create_argument_parser_help_mentions_subcommands_and_options(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Show help for the top level parser and the set subcommand."""
    parser = _create_argument_parser('demo', TEST_INPUT_SPECS)
    with pytest.raises(SystemExit) as top_level:
        parser.parse_args(['--help'])
    out, err = capsys.readouterr()
    assert top_level.value.code == 0
    assert err == ''
    assert 'demo' in out
    assert 'print' in out
    assert 'set' in out
    with pytest.raises(SystemExit) as set_help:
        parser.parse_args(['set', '--help'])
    out, err = capsys.readouterr()
    assert set_help.value.code == 0
    assert err == ''
    assert '--output' in out
    assert '--file-name' in out
    assert '--step-values' in out


def test_cmd_line_handling_routes_print_command() -> None:
    """Call the print command with the requested input file."""
    recorder = CommandCallRecorder()
    cmd_line_handling(
        example_name='demo',
        input_specs=TEST_INPUT_SPECS,
        set_command=recorder.set_command,
        print_command=recorder.print_command,
        args=['print', '--input', 'input.cfg']
    )
    assert recorder.print_calls == ['input.cfg']
    assert not recorder.set_calls


def test_cmd_line_handling_routes_set_command_with_converted_values() -> None:
    """Convert text to Python values before calling the set command."""
    recorder = CommandCallRecorder()
    cmd_line_handling(
        example_name='demo',
        input_specs=TEST_INPUT_SPECS,
        set_command=recorder.set_command,
        print_command=recorder.print_command,
        args=[
            'set',
            '--output', 'output.cfg',
            '--file-name', 'Ada',
            '--count', '7',
            '--ratio', '2.5',
            '--enabled', 'true',
            '--mode', 'beta',
            '--step-values', '1', '2', '3',
            '--matrix', '1,2', '3,4',
            '--flags', 'logging=true', 'debug=false',
            '--payload', '[{"a": 1}]'
        ]
    )
    assert not recorder.print_calls
    assert recorder.set_calls == [({
        'file_name': 'Ada',
        'count': 7,
        'ratio': 2.5,
        'enabled': True,
        'mode': SampleMode.BETA,
        'step_values': [1, 2, 3],
        'matrix': [[1, 2], [3, 4]],
        'flags': {'logging': True, 'debug': False},
        'payload': [{'a': 1}]
    }, 'output.cfg')]


@pytest.mark.parametrize('args, required_name',
                         [(['print'], '--input'),
                          (['set'], '--output')])
def test_cmd_line_handling_requires_input_and_output_files(
        args: list[str], required_name: str,
        capsys: pytest.CaptureFixture[str]) -> None:
    """Require the file option that belongs to each subcommand."""
    recorder = CommandCallRecorder()
    with pytest.raises(SystemExit) as exc:
        cmd_line_handling(
            example_name='demo',
            input_specs=TEST_INPUT_SPECS,
            set_command=recorder.set_command,
            print_command=recorder.print_command,
            args=args
        )
    _, err = capsys.readouterr()
    assert exc.value.code == 2
    assert 'error:' in err
    assert required_name in err
    assert not recorder.set_calls
    assert not recorder.print_calls


def test_cmd_line_handling_rejects_invalid_boolean_text(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Show a useful error when a boolean value is invalid."""
    recorder = CommandCallRecorder()
    with pytest.raises(SystemExit) as exc:
        cmd_line_handling(
            example_name='demo',
            input_specs=TEST_INPUT_SPECS,
            set_command=recorder.set_command,
            print_command=recorder.print_command,
            args=['set',
                  '--output', 'output.cfg',
                  '--enabled', 'maybe']
        )
    _, err = capsys.readouterr()
    assert exc.value.code == 2
    assert '--enabled' in err
    assert 'true' in err
    assert 'false' in err
    assert not recorder.set_calls


def test_cmd_line_handling_rejects_invalid_enum_text(
        capsys: pytest.CaptureFixture[str]) -> None:
    """Show accepted enum names when enum parsing fails."""
    recorder = CommandCallRecorder()
    with pytest.raises(SystemExit) as exc:
        cmd_line_handling(
            example_name='demo',
            input_specs=TEST_INPUT_SPECS,
            set_command=recorder.set_command,
            print_command=recorder.print_command,
            args=['set',
                  '--output', 'output.cfg',
                  '--mode', 'missing']
        )
    _, err = capsys.readouterr()
    assert exc.value.code == 2
    assert '--mode' in err
    assert 'missing' in err
    assert 'ALPHA' in err
    assert 'BETA' in err
    assert 'GAMMA' in err
    assert not recorder.set_calls
