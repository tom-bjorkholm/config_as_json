#! /usr/local/bin/python3
"""Define application configuration classes that serialize to JSON.

The package centers on :class:`config_as_json.config.Config`. Applications
derive their own configuration classes, declare supported settings as
instance attributes, and use the library to read, validate, migrate, and
write JSON configuration files.
"""

# Copyright (c) 2026 Tom Björkholm
# MIT License
