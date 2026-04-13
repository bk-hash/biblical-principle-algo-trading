"""
Configuration loader.

Reads config/config.yaml and exposes settings as a nested dictionary.
"""
from __future__ import annotations

import logging
import os
from typing import Any

import yaml

logger = logging.getLogger(__name__)

_DEFAULT_CONFIG_PATH = os.path.join(
    os.path.dirname(__file__), "..", "config", "config.yaml"
)


def load_config(path: str = _DEFAULT_CONFIG_PATH) -> dict[str, Any]:
    """Load YAML configuration file and return as a dict."""
    abs_path = os.path.abspath(path)
    with open(abs_path, "r", encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh)
    logger.debug("Configuration loaded from %s", abs_path)
    return cfg
