#! /usr/local/bin/python3
"""Teach dicts where selected keys are nested Config objects.

Example 35 showed ``ConfigNestingKind.DICT_VALUE``. That shape is useful
when every value in a dictionary has the same nested ``Config`` type.

This example teaches ``ConfigNestingKind.DICT_VALUE_BY_KEY``. That shape is
useful when one dictionary contains a few well-known nested configuration
objects and also some ordinary JSON values. The dictionary key decides
whether a value is handled as a nested ``Config`` object:

- ``participants`` is a ``ReportOutputConfig``
- ``audit`` is a ``WebhookOutputConfig``
- ``owner`` and ``max_attempts`` are plain JSON values

The ``audit`` value is constructed with a factory when JSON is read. That
shows how a keyed nested value can use application-specific construction
logic while the rest of the dictionary still stays simple.
"""

# Copyright (c) 2026 Tom Björkholm
# MIT License

import json
import sys
from typing import Optional, TextIO, cast
from config_as_json import Config, ConfigNesting, ConfigNestingKind, \
    JsonType, MemberValidationStep, NestedConfigs, PathOrStr, StrValidator, \
    ValidationPlan
from .cmd_line_handling import InputSpec, SetValues, cmd_line_handling
from .e34_list_nested_configs import ReportOutputConfig


class WebhookOutputConfig(Config):
    """Configuration for one webhook report delivery."""

    def __init__(self, from_json_data_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 stderr_file: TextIO = sys.stderr,
                 created_by_factory: bool = False) -> None:
        """Initialize one webhook output configuration.

        Args:
            from_json_data_text: Optional JSON text to parse directly.
            from_json_filename: Optional path to a JSON file to read.
            stderr_file: Stream used for user-facing diagnostics.
            created_by_factory: Whether the example factory made this object.
        """
        # These public attributes are the settings that will be written to
        # JSON. The private flag is only here so the example can demonstrate
        # that the factory was actually used while reading JSON.
        self.url: str = 'https://example.invalid/audit'
        self.method: str = 'POST'
        self.timeout_seconds: int = 30
        self._created_by_factory = created_by_factory
        super().__init__(from_json_data_text=from_json_data_text,
                         from_json_filename=from_json_filename,
                         stderr_file=stderr_file)

    def created_by_factory(self) -> bool:
        """Return whether the example factory constructed this object."""
        return self._created_by_factory

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Return validation steps for one webhook output."""
        _ = stderr_file
        return [MemberValidationStep(
            member_names=['method'],
            validator=StrValidator(['POST', 'PUT'], ignore_case=True,
                                   normalize=True))]


def _webhook_output_factory(*, from_json_data_text: Optional[str] = None,
                            from_json_filename: Optional[PathOrStr] = None,
                            stderr_file: TextIO = sys.stderr) -> Config:
    """Construct the webhook nested Config for DICT_VALUE_BY_KEY.

    Args:
        from_json_data_text: Optional JSON text to parse directly.
        from_json_filename: Optional path to a JSON file to read.
        stderr_file: Stream used for user-facing diagnostics.

    Returns:
        The webhook output configuration created by this factory.
    """
    # The factory has the same call shape as the nested Config constructor.
    # Here it only sets a teaching flag, but a real application could choose
    # a subclass, inject dependencies, or translate old construction rules.
    return WebhookOutputConfig(from_json_data_text=from_json_data_text,
                               from_json_filename=from_json_filename,
                               stderr_file=stderr_file,
                               created_by_factory=True)


def _default_reports(stderr_file: TextIO) -> dict[str, object]:
    """Create the default mixed dictionary for the example.

    Args:
        stderr_file: Stream used for user-facing diagnostics.

    Returns:
        A dictionary with two nested Config values and two plain values.
    """
    participant_report = ReportOutputConfig(stderr_file=stderr_file)
    audit_report = WebhookOutputConfig(stderr_file=stderr_file)
    return {
        'participants': participant_report,
        'audit': audit_report,
        'owner': 'training-team',
        'max_attempts': 3
    }


class ExampleConfig36(Config):
    """Configuration with selected nested Config values in one dict."""

    def get_validation_plan(self, stderr_file: TextIO) -> ValidationPlan:
        """Return validation steps for the top-level configuration."""
        _ = stderr_file
        return []

    def __init__(self, from_json_text: Optional[str] = None,
                 from_json_filename: Optional[PathOrStr] = None,
                 stderr_file: TextIO = sys.stderr) -> None:
        """Initialize the course report configuration.

        Args:
            from_json_text: Optional JSON text to parse directly.
            from_json_filename: Optional path to a JSON file to read.
            stderr_file: Stream used for user-facing diagnostics.
        """
        self.course_name: str = 'python-intro'
        # The dictionary deliberately mixes nested Config objects and plain
        # JSON values. That is exactly the situation DICT_VALUE_BY_KEY is
        # meant for.
        self.reports_by_key: dict[str, object] = _default_reports(
            stderr_file=stderr_file)
        participant_nesting = ConfigNesting(
            kind=ConfigNestingKind.DICT_VALUE_BY_KEY,
            config_type=ReportOutputConfig, discriminator_key='participants')
        audit_nesting = ConfigNesting(kind=ConfigNestingKind.DICT_VALUE_BY_KEY,
                                      config_type=WebhookOutputConfig,
                                      discriminator_key='audit',
                                      factory_function=_webhook_output_factory)
        # The _nested_configs key is still the public member name:
        # ``reports_by_key``. The value is a list because two different keys
        # inside that one dictionary are nested Config objects.
        #
        # For DICT_VALUE_BY_KEY, discriminator_key names the dictionary key.
        # It is not a field inside the nested object. The keys not listed
        # here, such as ``owner`` and ``max_attempts``, are written and read
        # as ordinary JSON values.
        self._nested_configs: NestedConfigs = {
            'reports_by_key': [participant_nesting, audit_nesting]
        }
        super().__init__(from_json_data_text=from_json_text,
                         from_json_filename=from_json_filename,
                         stderr_file=stderr_file)


def _cmd_report_from_json_value(report_data: JsonType) -> ReportOutputConfig:
    """Construct the participant report from command-line JSON.

    Args:
        report_data: JSON-shaped value describing the report.

    Returns:
        A ``ReportOutputConfig`` parsed from ``report_data``.

    Raises:
        ValueError: ``report_data`` is not a JSON object.
    """
    if not isinstance(report_data, dict):
        raise ValueError('reports_by_key[participants] must be an object.')
    return ReportOutputConfig(from_json_data_text=json.dumps(report_data))


def _cmd_webhook_from_json_value(
        webhook_data: JsonType) -> WebhookOutputConfig:
    """Construct the audit webhook from command-line JSON.

    Args:
        webhook_data: JSON-shaped value describing the webhook.

    Returns:
        A ``WebhookOutputConfig`` parsed from ``webhook_data``.

    Raises:
        ValueError: ``webhook_data`` is not a JSON object.
    """
    if not isinstance(webhook_data, dict):
        raise ValueError('reports_by_key[audit] must be an object.')
    webhook = _webhook_output_factory(
        from_json_data_text=json.dumps(webhook_data))
    return cast(WebhookOutputConfig, webhook)


def _cmd_reports_by_key_from_json(value: JsonType) -> dict[str, object]:
    """Construct the mixed report dictionary from command-line JSON.

    Args:
        value: JSON-shaped value supplied for ``reports_by_key``.

    Returns:
        A dictionary where known keys have been turned into Config objects.

    Raises:
        ValueError: The value is not a JSON object, or a known nested key does
            not contain a JSON object.
    """
    if not isinstance(value, dict):
        raise ValueError('reports_by_key must be a JSON object.')
    reports: dict[str, object] = {}
    for report_key, report_data in value.items():
        if not isinstance(report_key, str):
            raise ValueError('reports_by_key keys must be strings.')
        if report_key == 'participants':
            reports[report_key] = _cmd_report_from_json_value(report_data)
        elif report_key == 'audit':
            reports[report_key] = _cmd_webhook_from_json_value(report_data)
        else:
            reports[report_key] = report_data
    return reports


def _apply_set_value(config: ExampleConfig36, key: str, value: object) -> None:
    """Apply one command-line value to the example configuration.

    Args:
        config: Configuration object receiving the value.
        key: Command-line key being applied.
        value: Command-line value.

    Raises:
        ValueError: The command-line helper supplied an unknown key.
    """
    if key == 'course_name':
        config.course_name = cast(str, value)
        return
    if key == 'reports_by_key':
        config.reports_by_key = _cmd_reports_by_key_from_json(
            cast(JsonType, value))
        return
    raise ValueError(f'Invalid key: {key}')


def e36_dict_by_key_set(set_values: SetValues, config_file: PathOrStr) \
        -> None:
    """Create configuration, apply overrides, and store it.

    Args:
        set_values: Values that should differ from the defaults.
        config_file: Path where to write the configuration file.
    """
    config = ExampleConfig36()
    for key, value in set_values.items():
        _apply_set_value(config=config, key=key, value=value)
    config.write(to_json_filename=config_file)
    print(f'Configuration written to {config_file}')


def _plain_value_text(value: object) -> str:
    """Return stable text for one plain JSON value."""
    return json.dumps(value, sort_keys=True)


def _report_output_lines(report: ReportOutputConfig) -> list[str]:
    """Return printable lines for the participant report."""
    return [
        f'Participants report name: {report.name}',
        f'Participants report file: {report.file_name}',
        f'Participants report format: {report.output_format}',
        f'Participants report encoding: {report.encoding}']


def _webhook_output_lines(webhook: WebhookOutputConfig) -> list[str]:
    """Return printable lines for the audit webhook."""
    factory_text = 'yes' if webhook.created_by_factory() else 'no'
    return [
        f'Audit webhook URL: {webhook.url}',
        f'Audit webhook method: {webhook.method}',
        f'Audit webhook timeout: {webhook.timeout_seconds}',
        f'Audit webhook created by factory: {factory_text}']


def _print_report_value(report_key: str, report_value: object) -> None:
    """Print one value from the mixed report dictionary."""
    if isinstance(report_value, ReportOutputConfig):
        for line in _report_output_lines(report_value):
            print(line)
    elif isinstance(report_value, WebhookOutputConfig):
        for line in _webhook_output_lines(report_value):
            print(line)
    else:
        print(f'Plain value {report_key}: {_plain_value_text(report_value)}')


def e36_dict_by_key_print(config_file: PathOrStr) -> None:
    """Read a configuration file and show keyed nested dict values.

    Args:
        config_file: Path to the configuration file to read.
    """
    config = ExampleConfig36(from_json_filename=config_file)
    print(f'Configuration read from {config_file}')
    print(f'Course name: {config.course_name}')
    print(f'Dictionary entry count: {len(config.reports_by_key)}')
    for report_key in sorted(config.reports_by_key):
        _print_report_value(report_key, config.reports_by_key[report_key])


INPUT_SPECS = [
    InputSpec(name='course_name', single=True, value_type=str),
    # One JSON value is the clearest command-line representation for this
    # mixed dictionary. The library feature is the _nested_configs
    # declaration above, not the command-line syntax.
    InputSpec(name='reports_by_key', single=True, value_type=str,
              json_value=True)
]
"""Command line values that the example exposes for ``set``."""


def main(args: Optional[list[str]] = None) -> None:
    """Run the example command line interface.

    Args:
        args: Optional replacement for ``sys.argv[1:]``, mainly for tests.
    """
    cmd_line_handling(example_name='e36_dict_by_key_nested_configs',
                      input_specs=INPUT_SPECS, set_command=e36_dict_by_key_set,
                      print_command=e36_dict_by_key_print, args=args)


if __name__ == '__main__':
    main()
    sys.exit(0)
