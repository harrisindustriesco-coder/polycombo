# polycombo (Polymarket US)

Honest analysis tool for sports combos on Polymarket US (the CFTC-regulated US exchange).
Pure Python 3.9+, standard library only. Reads the public gateway (https://gateway.polymarket.us);
no account, no API key, no order placement.

## Commands
- `python -m polycombo games nfl`: upcoming games + prices (leagues: nfl, nba, mlb, nhl, ...)
- `python -m polycombo search "lakers"`: combo-eligible markets matching a query (`--all` for every market)
- `python -m polycombo market <slug>`: best bid/ask for one market
- `python -m polycombo check Lakers=0.55:0.60 Chiefs=0.62:0.66 --quote 0.36 --bankroll 10`: combo odds, fees, markup, EV, stake
- `python -m polycombo reality --mult 10 --prob 0.9`: what a payout target + win rate would require
- `python -m polycombo sim --legs 0.55 0.60 0.50 0.62 --days 1`: Monte Carlo outcomes
- Tests: `python -m unittest discover -s tests`

Leg format: `price`, `price:your_estimate`, or `Label=price:your_estimate` (0 to 1).
Use the ASK as the leg price (what you'd pay). For same-game legs, label them `Game/Leg`
(e.g. `LALBOS/Lakers ML`) so the tool can warn about correlation.

## How Polymarket US combos work (from docs.polymarket.us)
- 2 to 10 legs. Pays $1/contract only if every leg wins; one loss zeroes it.
- Priced by RFQ: market makers quote the combo. The quote can exceed the legs multiplied together;
  `--quote` measures that markup.
- Combo taker fee per contract: p * [0.0695 * (1-p) + 0.04 * (1-p)^4]. Single-market taker fee: 0.0695 * p * (1-p).
  Formulas live in `polycombo/fees.py`. Re-check https://docs.polymarket.us/fees if numbers look off.

## Rules for Claude working in this repo
- Never add code that places orders, uses API keys, or touches the authenticated API (api.polymarket.us).
  Analysis only.
- Never call a combo "high probability" when its combined price is low. Always show the combined
  chance next to the payout.
- If the user asks for a strategy that turns $X into 10X with 90% odds, run `reality` and explain it.
  Don't build anything that implies it's achievable.
- Stake sizing is quarter-Kelly capped at 5% of bankroll. Don't raise the cap unless the user explicitly
  asks, and warn if they do.
- If the live API response shape differs from what `polymarket_us.py` expects, fix the parser and add a
  test case with the real shape in `tests/`.
