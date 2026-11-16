"""Tests for the save-file schema and its legacy handling."""

import pytest

from save import SAVE_VERSION, deserialize_state, serialize_state


def make_state(**overrides):
    state = {
        "cookies": 120.5,
        "click_power": 12.0,
        "click_level": 4,
        "cps_multiplier": 1.1,
        "buildings": {"Cursor": 10, "Grandma": 2},
        "upgrades": {"double_click": True, "click_x5": False},
        "timestamp": 1_700_000_000.0,
    }
    state.update(overrides)
    return state


class TestSerializeState:
    def test_writes_current_version(self):
        assert serialize_state(**make_state())["version"] == SAVE_VERSION

    def test_keeps_all_game_values(self):
        data = serialize_state(**make_state())

        assert data["cookies"] == 120.5
        assert data["click_power"] == 12.0
        assert data["click_level"] == 4
        assert data["cps_multiplier"] == 1.1
        assert data["buildings"] == {"Cursor": 10, "Grandma": 2}
        assert data["upgrades"] == {"double_click": True, "click_x5": False}
        assert data["timestamp"] == 1_700_000_000.0


class TestDeserializeState:
    def test_roundtrip_preserves_the_state(self):
        original = serialize_state(**make_state())

        assert deserialize_state(original) == original

    def test_rejects_non_object_saves(self):
        with pytest.raises(ValueError):
            deserialize_state(["not", "a", "save"])

    def test_empty_save_falls_back_to_fresh_game_values(self):
        state = deserialize_state({})

        assert state["cookies"] == 0.0
        assert state["click_power"] == 1.0
        assert state["click_level"] == 1
        assert state["cps_multiplier"] == 1.0
        assert state["buildings"] == {}
        assert state["upgrades"] == {}
        assert state["timestamp"] is None

    def test_legacy_save_without_click_level_gets_level_one(self):
        legacy = {
            "cookies": 900,
            "click_power": 10,
            "cps_multiplier": 1.1,
            "buildings": {"Cursor": 5},
            "upgrades": {"double_click": True},
            "timestamp": 1_700_000_000.0,
        }

        state = deserialize_state(legacy)

        assert state["click_level"] == 1
        assert state["cookies"] == 900
        assert state["click_power"] == 10
        assert state["version"] == SAVE_VERSION

    def test_negative_cookies_are_clamped(self):
        assert deserialize_state({"cookies": -500})["cookies"] == 0

    def test_invalid_numbers_use_defaults(self):
        state = deserialize_state(
            {"cookies": "many", "click_power": None, "click_level": "x"}
        )

        assert state["cookies"] == 0.0
        assert state["click_power"] == 1.0
        assert state["click_level"] == 1

    def test_string_numbers_are_coerced(self):
        state = deserialize_state({"cookies": "42", "click_level": "3"})

        assert state["cookies"] == 42.0
        assert state["click_level"] == 3

    def test_building_counts_are_sanitized(self):
        state = deserialize_state(
            {"buildings": {"Cursor": "3", "Mine": -7, "Farm": "lots"}}
        )

        assert state["buildings"] == {"Cursor": 3, "Mine": 0, "Farm": 0}

    def test_malformed_buildings_are_dropped(self):
        assert deserialize_state({"buildings": ["Cursor"]})["buildings"] == {}

    def test_upgrade_flags_accept_strings(self):
        state = deserialize_state(
            {"upgrades": {"double_click": "true", "click_x5": "false"}}
        )

        assert state["upgrades"] == {"double_click": True, "click_x5": False}

    def test_missing_or_zero_timestamp_disables_offline_progress(self):
        assert deserialize_state({})["timestamp"] is None
        assert deserialize_state({"timestamp": 0})["timestamp"] is None
        assert deserialize_state({"timestamp": "nope"})["timestamp"] is None

    def test_unknown_fields_are_ignored(self):
        state = deserialize_state({"cookies": 5, "cheat_engine": True})

        assert "cheat_engine" not in state
