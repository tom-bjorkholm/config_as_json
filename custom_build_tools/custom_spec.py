
"""Repository-specific build specification for common_build_tools."""

from pathlib import Path
from typing import Optional
from build_spec import BuildInformation, BuildSpec


PYTHON_LAYOUT_INITIAL_EXCLUDES = [
    Path('test'),
    Path('example')
]


def strip_generated_markdown_whitespace(_build_spec: BuildSpec,
                                        build_information: BuildInformation) \
        -> None:
    """Strip trailing whitespace from generated markdown files."""
    doc_folder = build_information['project_root'] / 'doc'
    for markdown_file in sorted(doc_folder.glob('*.md')):
        strip_trailing_whitespace(markdown_file)


def strip_trailing_whitespace(path: Path) -> None:
    """Strip trailing whitespace from text file lines."""
    original_text = path.read_text(encoding='utf-8')
    stripped_text = ''.join(
        f'{line.rstrip()}\n' for line in original_text.splitlines()
    )
    if stripped_text != original_text:
        path.write_text(stripped_text, encoding='utf-8')


def custom_spec() -> Optional[BuildSpec]:
    """Return custom build spec for this repository."""
    excludes = PYTHON_LAYOUT_INITIAL_EXCLUDES
    return BuildSpec(readme_summary_max_skipped=200,
                     python_layout_exclude_folders=excludes,
                     custom_final=[strip_generated_markdown_whitespace])
