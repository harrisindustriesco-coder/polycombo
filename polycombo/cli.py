"""polycombo: honest calculator for Polymarket US sports combos.

Examples:
  python -m polycombo games nfl
  python -m polycombo search "lakers"
  python -m polycombo market <market-slug>
  python -m polycombo check Lakers=0.55:0.60 Chiefs=0.62:0.66 --quote 0.36 --bankroll 10
  python -m polycombo reality --mult 10 --prob 0.9
  python -m polycombo sim --legs 0.55 0.60 0.50 0.62 --days 1
"""
from __future__ import annotations

import argparse
import sys

from .combo import Leg, analyze, simulate, required_edge
from .fees import combo_fee, net_multiplier


def _leg(s: str) -> Leg:
    """'0.55' or '0.55:0.62' (price:your_estimate) or 'Lakers=0.55:0.62'."""
    label = ""
    if "=" in s:
        label, s = s.split("=", 1)
    if ":" in s:
        p, e = s.split(":", 1)
        return Leg(float(p), float(e), label)
    return Leg(float(s), None, label)


def _pct(x):
    return "n/a" if x is None else f"{x:.0%}"


def cmd_check(a):
    r = analyze([_leg(x) for x in a.legs], quote=a.quote)
    print(f"Legs: {len(r.legs)}")
    for i, l in enumerate(r.legs, 1):
        est = f"  you {l.estimate:.0%}  edge {l.edge:+.0%}" if l.estimate is not None else ""
        print(f"  {i}. {l.label or 'leg'}: market {l.price:.0%}{est}")
    print(f"Legs combined price:  ${r.fair_price:.3f}  (market chance {r.market_prob:.1%})")
    if r.markup is not None:
        print(f"RFQ quote:            ${r.price:.3f}  ({r.markup:+.0%} vs combined)")
    print(f"Fee per contract:     ${r.fee:.4f}")
    print(f"Payout if it hits:    {r.multiplier:.2f}x your money, fees included")
    print(f"  $10 in -> ${10 * r.multiplier:,.2f} back")
    if r.your_prob is not None:
        print(f"Your chance:          {r.your_prob:.1%}")
        print(f"Expected value:       {r.ev_per_dollar:+.1%} per $1")
        print(f"Suggested stake:      {r.kelly_fraction:.1%} of bankroll = "
              f"${a.bankroll * r.kelly_fraction:.2f} of ${a.bankroll:.2f} (quarter-Kelly, 5% cap)")
    for w in r.warnings:
        print(f"! {w}")


def cmd_reality(a):
    price = 1 / a.mult
    real_mult = net_multiplier(price, combo=True)
    need = required_edge(a.mult, a.prob)
    ev = a.prob * a.mult - 1
    print(f"A {a.mult:g}x combo costs about ${price:.2f} per $1 contract, so the market gives it "
          f"about a {price:.0%} chance.")
    print(f"After Polymarket US combo fees (${combo_fee(price):.4f}/contract) it actually pays "
          f"{real_mult:.2f}x, not {a.mult:g}x.")
    print(f"You want {a.prob:.0%}. That means being {need:.1f}x more accurate than the market.")
    print(f"If that were real, expected return would be {ev:+.0%} per bet.")
    if ev > 1:
        days, bank = 0, 10.0
        while bank < 1e9 and days < 1000:
            bank *= 1 + ev
            days += 1
        print(f"Compounded daily, $10 would pass $1 billion in about {days} days.")
    print("No public strategy, bot, or tipster has this. Treat any claim of it as a scam.")


def cmd_sim(a):
    r = analyze([Leg(p) for p in a.legs], quote=a.quote)
    win = a.win_prob if a.win_prob is not None else r.market_prob
    s = simulate(win, r.multiplier, start=a.start, days=a.days, bets_per_day=a.per_day,
                 stake_fraction=a.stake, target=a.target, runs=a.runs, seed=a.seed)
    how = "whole bankroll each bet" if a.stake is None else f"{a.stake:.0%} of bankroll each bet"
    print(f"{s.runs:,} runs, {s.days} day(s), {a.per_day} bet(s)/day, {how}")
    print(f"Win chance per combo {win:.1%}, payout {r.multiplier:.2f}x after fees")
    print(f"Reached ${s.target:,.0f}:  {s.p_hit_target:.1%}")
    print(f"Ended up:           {s.p_up:.1%}")
    print(f"Went broke:         {s.p_bust:.1%}")
    print(f"Median final:       ${s.median_final:,.2f}")


def _print_events(events):
    if not events:
        print("No events found.")
    for e in events:
        print(f"\n{e['title']}  ({e['start'] or 'time n/a'})")
        for m in e["markets"]:
            sides = "  ".join(f"{s['name']} {_pct(s['price'])}" for s in m["sides"] if s["name"])
            print(f"  - {m['question']}\n      bid {_pct(m['bid'])} / ask {_pct(m['ask'])}"
                  f"{'  | ' + sides if sides else ''}\n      slug: {m['slug']}")


def cmd_search(a):
    from . import polymarket_us as pm
    _print_events(pm.search(a.query, a.limit, combo_only=not a.all))


def cmd_games(a):
    from . import polymarket_us as pm
    _print_events(pm.league_events(a.league, a.limit))


def cmd_market(a):
    from . import polymarket_us as pm
    b = pm.bbo(a.slug)
    print(f"{b['slug']}  [{b['state']}]")
    print(f"  bid {_pct(b['bid'])}  ask {_pct(b['ask'])}  last {_pct(b['last'])}")
    print("  Use the ask as the leg price: it's what you'd actually pay.")


def main(argv=None):
    p = argparse.ArgumentParser(prog="polycombo", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("check", help="analyze a combo")
    c.add_argument("legs", nargs="+", help="price, price:estimate, or Label=price:estimate")
    c.add_argument("--quote", type=float, default=None,
                   help="combo price the app/RFQ quoted you (0-1), if you have one")
    c.add_argument("--bankroll", type=float, default=10.0)
    c.set_defaults(fn=cmd_check)

    r = sub.add_parser("reality", help="what a payout target + win rate would require")
    r.add_argument("--mult", type=float, default=10)
    r.add_argument("--prob", type=float, default=0.9)
    r.set_defaults(fn=cmd_reality)

    s = sub.add_parser("sim", help="Monte Carlo a combo strategy")
    s.add_argument("--legs", type=float, nargs="+", required=True)
    s.add_argument("--quote", type=float, default=None)
    s.add_argument("--win-prob", type=float, default=None,
                   help="true win chance; defaults to market-implied")
    s.add_argument("--start", type=float, default=10.0)
    s.add_argument("--target", type=float, default=None)
    s.add_argument("--days", type=int, default=30)
    s.add_argument("--per-day", type=int, default=1)
    s.add_argument("--stake", type=float, default=None, help="fraction per bet; omit = all-in")
    s.add_argument("--runs", type=int, default=10_000)
    s.add_argument("--seed", type=int, default=None)
    s.set_defaults(fn=cmd_sim)

    q = sub.add_parser("search", help="search Polymarket US (combo-eligible markets by default)")
    q.add_argument("query")
    q.add_argument("--limit", type=int, default=10)
    q.add_argument("--all", action="store_true", help="include markets not eligible for combos")
    q.set_defaults(fn=cmd_search)

    g = sub.add_parser("games", help="upcoming games for a league (nfl, nba, mlb, nhl, ...)")
    g.add_argument("league")
    g.add_argument("--limit", type=int, default=20)
    g.set_defaults(fn=cmd_games)

    m = sub.add_parser("market", help="best bid/ask for one market slug")
    m.add_argument("slug")
    m.set_defaults(fn=cmd_market)

    a = p.parse_args(argv)
    try:
        a.fn(a)
    except (ValueError, LookupError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    except OSError as e:
        print(f"network error reaching Polymarket US: {e}", file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
