"""Pure game-economy helpers.

Everything in this module is free of tkinter (and of any other UI)
dependencies, which keeps the numbers easy to reason about and easy
to unit-test without opening a window.
"""

from typing import Mapping

# How much more expensive every next building of the same type is.
BUILDING_COST_GROWTH = 1.15

# Cost of the first manual click upgrade and the growth per level.
CLICK_UPGRADE_BASE_COST = 50
CLICK_UPGRADE_GROWTH = 1.5

# Money earned while the game was closed is capped at 8 hours.
OFFLINE_EARNINGS_CAP_SECONDS = 8 * 60 * 60


def building_cost(base_cost: float, owned: int,
                  growth: float = BUILDING_COST_GROWTH) -> int:
    """Return the price of the next copy of a building."""
    if owned < 0:
        raise ValueError("owned buildings cannot be negative")
    # Round, not truncate: 100 * 1.15 is 114.999... in binary floats.
    return int(round(base_cost * (growth ** owned)))


def click_upgrade_cost(level: int) -> int:
    """Return the price of the next manual click upgrade.

    ``level`` is the number of click upgrades already bought, so the
    first upgrade starts at :data:`CLICK_UPGRADE_BASE_COST`.
    """
    level = max(1, level)
    return int(round(CLICK_UPGRADE_BASE_COST * (CLICK_UPGRADE_GROWTH ** (level - 1))))


def bulk_cost(base_cost: float, owned: int, count: int,
              growth: float = BUILDING_COST_GROWTH) -> int:
    """Return the total price of the next ``count`` copies of a building.

    Buying in bulk is priced exactly like buying one copy at a time, so
    the player never pays extra for the convenience.
    """
    if owned < 0:
        raise ValueError("owned buildings cannot be negative")
    if count < 0:
        raise ValueError("cannot buy a negative number of buildings")
    return sum(
        building_cost(base_cost, owned + offset, growth)
        for offset in range(count)
    )


def max_affordable(base_cost: float, owned: int, budget: float, limit: int,
                   growth: float = BUILDING_COST_GROWTH) -> int:
    """Return how many copies of a building ``budget`` can pay for.

    The answer is capped at ``limit``, the batch size the player picked,
    and priced exactly like :func:`bulk_cost`, so a player who cannot
    afford the whole batch still gets the copies they *can* afford.
    """
    if owned < 0:
        raise ValueError("owned buildings cannot be negative")
    if budget < 0:
        raise ValueError("cannot spend a negative budget")
    if limit < 0:
        raise ValueError("cannot buy a negative number of buildings")

    count = 0
    total = 0
    while count < limit:
        price = building_cost(base_cost, owned + count, growth)
        if total + price > budget:
            break
        total += price
        count += 1
    return count


def total_cps(buildings: Mapping[str, Mapping[str, float]],
              multiplier: float = 1.0) -> float:
    """Sum the output of every owned building, then apply a multiplier."""
    base = sum(b.get("owned", 0) * b.get("cps", 0.0) for b in buildings.values())
    return base * multiplier


def offline_earnings(cps: float, elapsed_seconds: float,
                     cap: float = OFFLINE_EARNINGS_CAP_SECONDS) -> float:
    """Cookies produced while the game was closed, limited by ``cap``."""
    if cps <= 0 or elapsed_seconds <= 0:
        return 0.0
    return cps * min(elapsed_seconds, cap)


_SUFFIXES = (
    (1_000_000_000_000, "T"),
    (1_000_000_000, "B"),
    (1_000_000, "M"),
    (1_000, "K"),
)


def format_number(value: float) -> str:
    """Format a counter for the UI: ``1234.5`` becomes ``1.23K``."""
    sign = "-" if value < 0 else ""
    magnitude = abs(value)
    for index, (threshold, suffix) in enumerate(_SUFFIXES):
        if magnitude < threshold:
            continue
        scaled = magnitude / threshold
        # 999_999 must render as "1M", not "1000K".
        while scaled >= 999.995 and index > 0:
            index -= 1
            threshold, suffix = _SUFFIXES[index]
            scaled = magnitude / threshold
        rendered = f"{scaled:.2f}".rstrip("0").rstrip(".")
        return f"{sign}{rendered}{suffix}"
    if float(magnitude).is_integer():
        return f"{sign}{magnitude:,.0f}"
    return f"{sign}{magnitude:,.1f}"
