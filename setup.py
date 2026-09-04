#! /usr/local/bin/python3
"""Setup file specifying build of .whl."""

from setuptools import setup  # type: ignore[import-untyped]

setup(
  name='config-as-json', version='1.7.1',
  description='Read, write, validate, and migrate JSON-backed config classes.',
  author='Tom Björkholm', author_email='klausuler_linnet0q@icloud.com',
  python_requires='>=3.12', packages=['config_as_json'],
  package_dir={'config_as_json': 'src/config_as_json'},
  package_data={'config_as_json': ['py.typed']},
  install_requires=[])
