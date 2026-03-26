"""Tests for the config loader."""
import os
import pytest
from src.config_loader import load_config


class TestConfigLoader:
    def test_loads_without_error(self):
        cfg = load_config()
        assert isinstance(cfg, dict)

    def test_has_expected_sections(self):
        cfg = load_config()
        assert "trading" in cfg
        assert "data" in cfg
        assert "strategies" in cfg

    def test_initial_capital_is_positive(self):
        cfg = load_config()
        assert cfg["trading"]["initial_capital"] > 0

    def test_risk_per_trade_between_0_and_100(self):
        cfg = load_config()
        pct = cfg["trading"]["max_risk_per_trade_pct"]
        assert 0 < pct <= 100

    def test_max_drawdown_between_0_and_100(self):
        cfg = load_config()
        dd = cfg["trading"]["max_drawdown_pct"]
        assert 0 < dd <= 100

    def test_default_symbols_non_empty(self):
        cfg = load_config()
        assert len(cfg["data"]["default_symbols"]) > 0
