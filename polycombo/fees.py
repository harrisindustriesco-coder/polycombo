"""Polymarket US taker fees (per contract that pays $1), from docs.polymarket.us/fees.

Single market:  fee = 0.0695 * p * (1 - p)
Combo:          fee = p * [0.0695 * (1 - p) + 0.04 * (1 - p)^4]

The exchange rounds each fill (banker's rounding), so real fees can differ by a cent.
Check the fee page if these ever change.
"""
TAKER_THETA = 0.0695
COMBO_EXTRA = 0.04


def taker_fee(p: float) -> float:
    return TAKER_THETA * p * (1 - p)


def combo_fee(p: float) -> float:
    return p * (TAKER_THETA * (1 - p) + COMBO_EXTRA * (1 - p) ** 4)


def net_multiplier(p: float, combo: bool) -> float:
    """Dollars returned per $1 spent (price + fee) if the position wins."""
    fee = combo_fee(p) if combo else taker_fee(p)
    return 1 / (p + fee)
