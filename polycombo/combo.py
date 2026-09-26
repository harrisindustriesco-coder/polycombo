"""Core math for Polymarket US combos.

A Polymarket US combo is one contract built from 2-10 legs. It pays $1 per contract only if
every leg resolves your way; one losing leg zeroes it. Its price comes from market makers via
RFQ (request for quote), so the quoted price can be worse than the legs' prices multiplied together.

Leg prices here are YES prices (0-1), best read as the ask: what you'd actually pay.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import List, Optional

from .fees import combo_fee, net_multiplier, taker_fee

MIN_LEGS, MAX_LEGS = 2, 10


@dataclass
class Leg:
    price: float                      # market price of the side you're taking, 0-1
    estimate: Optional[float] = None  # YOUR probability estimate, 0-1 (optional)
    label: str = ""

    def __post_init__(self):
        if not 0 < self.price < 1:
            raise ValueError(f"price must be between 0 and 1, got {self.price}")
        if self.estimate is not None and not 0 <= self.estimate <= 1:
            raise ValueError(f"estimate must be between 0 and 1, got {self.estimate}")

    @property
    def edge(self) -> Optional[float]:
        return None if self.estimate is None else self.estimate - self.price


@dataclass
class ComboReport:
    legs: List[Leg]
    fair_price: float              # legs multiplied together
    price: float                   # price actually used (RFQ quote if given)
    fee: float                     # fee per contract
    markup: Optional[float]        # quote vs fair price (only if a quote was given)
    multiplier: float              # $ back per $1 spent, fees included, if it hits
    market_prob: float
    your_prob: Optional[float]
    ev_per_dollar: Optional[float]
    kelly_fraction: Optional[float]
    warnings: List[str] = field(default_factory=list)


def analyze(legs: List[Leg], quote: Optional[float] = None, kelly_scale: float = 0.25,
            kelly_cap: float = 0.05) -> ComboReport:
    if not legs:
        raise ValueError("need at least one leg")
    is_combo = len(legs) >= MIN_LEGS
    if len(legs) > MAX_LEGS:
        raise ValueError(f"Polymarket US combos allow at most {MAX_LEGS} legs")
    if quote is not None and not 0 < quote < 1:
        raise ValueError(f"quote must be between 0 and 1, got {quote}")

    fair = math.prod(l.price for l in legs)
    price = quote if quote is not None else fair
    fee = combo_fee(price) if is_combo else taker_fee(price)
    mult = net_multiplier(price, is_combo)
    markup = (quote / fair - 1) if quote is not None else None

    warnings: List[str] = []
    if markup is not None and markup > 0.05:
        warnings.append(f"The quote is {markup:.0%} above the legs' combined price. "
                        "That gap is the market maker's margin, and it comes out of your payout.")

    your_prob = math.prod(l.estimate for l in legs) if all(l.estimate is not None for l in legs) else None
    ev = kelly = None
    if your_prob is not None:
        ev = your_prob * mult - 1
        b = mult - 1
        full_kelly = (your_prob * b - (1 - your_prob)) / b if b > 0 else 0.0
        kelly = max(0.0, min(kelly_cap, full_kelly * kelly_scale))
        if full_kelly <= 0:
            warnings.append("Negative expected value at your own estimates, after fees: bet $0.")
        for l in legs:
            if l.edge is not None and l.edge <= 0:
                warnings.append(f"Leg '{l.label or l.price}' has no edge "
                                f"(your {l.estimate:.0%} vs market {l.price:.0%}). Drop it.")
        if your_prob > 2.5 * fair and your_prob > 0.2:
            warnings.append("Your combined estimate is far above the market's. That usually means "
                            "the estimates are overconfident, not that the market is wrong.")
        if _same_game_hint(legs):
            warnings.append("Legs from the same game are correlated, so multiplying them can be "
                            "off in either direction.")
    else:
        warnings.append(f"No estimates given. At market prices, expected value is "
                        f"{fair * mult - 1:+.1%} per $1 (fees and markup only, no edge).")

    if len(legs) >= 4:
        warnings.append(f"{len(legs)} legs: every extra leg multiplies the chance of losing.")

    return ComboReport(legs, fair, price, fee, markup, mult, fair, your_prob, ev, kelly,
                       [w for w in warnings if w])


def _same_game_hint(legs: List[Leg]) -> bool:
    labels = [l.label.split("/")[0].strip().lower() for l in legs if "/" in l.label]
    return len(labels) != len(set(labels))


def required_edge(target_multiplier: float, target_prob: float) -> float:
    """How many times more accurate than the market you'd need to be.

    A combo returning `target_multiplier` is priced at about 1/target_multiplier.
    """
    return target_prob * target_multiplier


@dataclass
class SimResult:
    runs: int
    days: int
    start: float
    median_final: float
    p_bust: float
    p_hit_target: float
    p_up: float
    target: float


def simulate(win_prob: float, multiplier: float, start: float = 10.0, days: int = 30,
             bets_per_day: int = 1, stake_fraction: Optional[float] = None,
             target: Optional[float] = None, runs: int = 10_000, min_bet: float = 1.0,
             seed: Optional[int] = None) -> SimResult:
    """Monte Carlo of repeating a combo. stake_fraction=None means all-in every time."""
    rng = random.Random(seed)
    target = target if target is not None else start * 10
    finals, busts, hits = [], 0, 0
    for _ in range(runs):
        bank, hit = start, False
        for _ in range(days * bets_per_day):
            if bank < min_bet:
                break
            stake = bank if stake_fraction is None else max(min_bet, bank * stake_fraction)
            stake = min(stake, bank)
            bank -= stake
            if rng.random() < win_prob:
                bank += stake * multiplier
            if bank >= target:
                hit = True
        finals.append(bank)
        busts += bank < min_bet
        hits += hit
    finals.sort()
    return SimResult(runs, days, start, finals[len(finals) // 2], busts / runs, hits / runs,
                     sum(f > start for f in finals) / runs, target)
