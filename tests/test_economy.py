"""Tests for the UI-free economy helpers."""

import pytest

from economy import (
    BUILDING_COST_GROWTH,
    CLICK_UPGRADE_BASE_COST,
    OFFLINE_EARNINGS_CAP_SECONDS,
    building_cost,
    bulk_cost,
    click_upgrade_cost,
    format_number,
    max_affordable,
    offline_earnings,
    total_cps,
)


class TestBuildingCost:
    def test_first_copy_costs_the_base_price(self):
        assert building_cost(15, 0) == 15

    def test_price_grows_with_every_owned_copy(self):
        assert building_cost(100, 1) == 115
        assert building_cost(100, 2) == int(100 * BUILDING_COST_GROWTH ** 2)

    def test_custom_growth_rate_is_supported(self):
        assert building_cost(200, 3, growth=2.0) == 1600

    def test_negative_owned_count_is_rejected(self):
        with pytest.raises(ValueError):
            building_cost(15, -1)


class TestBulkCost:
    def test_buying_nothing_costs_nothing(self):
        assert bulk_cost(15, 0, 0) == 0

    def test_batch_price_is_the_sum_of_single_prices(self):
        expected = sum(building_cost(100, owned) for owned in range(3))
        assert bulk_cost(100, 0, 3) == expected

    def test_price_accounts_for_copies_already_owned(self):
        expected = sum(building_cost(15, owned) for owned in range(5, 15))
        assert bulk_cost(15, 5, 10) == expected

    def test_negative_owned_count_is_rejected(self):
        with pytest.raises(ValueError):
            bulk_cost(15, -1, 1)

    def test_negative_batch_size_is_rejected(self):
        with pytest.raises(ValueError):
            bulk_cost(15, 0, -5)


class TestMaxAffordable:
    def test_an_empty_purse_buys_nothing(self):
        assert max_affordable(15, 0, 0, limit=10) == 0

    def test_a_purse_below_the_first_price_buys_nothing(self):
        assert max_affordable(15, 0, 14, limit=10) == 0

    def test_an_exact_budget_buys_the_whole_batch(self):
        budget = bulk_cost(15, 0, 3)

        assert max_affordable(15, 0, budget, limit=10) == 3

    def test_a_short_budget_buys_the_affordable_part(self):
        # 15 + 17 = 32, the third copy costs 20 on top.
        assert max_affordable(15, 0, 51, limit=10) == 2

    def test_the_selected_batch_size_is_never_exceeded(self):
        assert max_affordable(15, 0, 10 ** 9, limit=100) == 100

    def test_copies_already_owned_are_priced_in(self):
        budget = bulk_cost(15, 5, 2)

        assert max_affordable(15, 5, budget, limit=10) == 2

    def test_negative_arguments_are_rejected(self):
        with pytest.raises(ValueError):
            max_affordable(15, -1, 100, limit=10)
        with pytest.raises(ValueError):
            max_affordable(15, 0, -1, limit=10)
        with pytest.raises(ValueError):
            max_affordable(15, 0, 100, limit=-1)


class TestClickUpgradeCost:
    def test_first_upgrade_costs_the_base_price(self):
        assert click_upgrade_cost(1) == CLICK_UPGRADE_BASE_COST

    def test_levels_below_one_are_clamped(self):
        assert click_upgrade_cost(0) == click_upgrade_cost(1)

    def test_cost_follows_the_growth_curve(self):
        assert click_upgrade_cost(2) == 75
        assert click_upgrade_cost(4) == 169


class TestTotalCps:
    def test_no_buildings_means_no_income(self):
        assert total_cps({}) == 0

    def test_sums_owned_buildings(self):
        buildings = {
            "Cursor": {"owned": 10, "cps": 0.1},
            "Grandma": {"owned": 2, "cps": 1.0},
        }
        assert total_cps(buildings) == pytest.approx(3.0)

    def test_multiplier_is_applied_to_the_sum(self):
        buildings = {"Farm": {"owned": 1, "cps": 8.0}}
        assert total_cps(buildings, multiplier=1.5) == pytest.approx(12.0)


class TestOfflineEarnings:
    def test_no_income_means_no_offline_progress(self):
        assert offline_earnings(0, 3600) == 0

    def test_negative_elapsed_time_is_ignored(self):
        assert offline_earnings(10, -50) == 0

    def test_short_absences_are_paid_in_full(self):
        assert offline_earnings(10, 60) == pytest.approx(600)

    def test_long_absences_are_capped_at_eight_hours(self):
        assert offline_earnings(10, 10 ** 6) == pytest.approx(
            10 * OFFLINE_EARNINGS_CAP_SECONDS
        )


class TestFormatNumber:
    @pytest.mark.parametrize(
        "value, expected",
        [
            (0, "0"),
            (7, "7"),
            (999, "999"),
            (12.34, "12.3"),
            (1_000, "1K"),
            (1_234, "1.23K"),
            (1_500, "1.5K"),
            (999_999, "1M"),
            (1_234_567, "1.23M"),
            (2_500_000_000, "2.5B"),
            (1_000_000_000_000, "1T"),
            (-2_500, "-2.5K"),
        ],
    )
    def test_compact_rendering(self, value, expected):
        assert format_number(value) == expected

    @pytest.mark.parametrize(
        "value, expected",
        [
            # Rounding must not produce "1000K" or "1000M" at the boundary.
            (999_994, "999.99K"),
            (999_995, "1M"),
            (999_994_999, "999.99M"),
            (999_995_000, "1B"),
        ],
    )
    def test_values_near_a_suffix_boundary_round_up(self, value, expected):
        assert format_number(value) == expected
