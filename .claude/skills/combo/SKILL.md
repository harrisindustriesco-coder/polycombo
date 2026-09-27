---
name: combo
description: Analyze a Polymarket US sports combo (live prices + your estimates)
---
Analyze this Polymarket US combo: {args}

1. For each leg, run `python -m polycombo search "<team>"` (or `games <league>`) and find the
   matching combo-eligible market. Show the question and ask price. If a leg is ambiguous, ask
   which one. If the API fails, ask the user to paste the prices from the app.
2. Ask for the user's own probability per leg if not given, and whether the app showed a combo quote.
3. Run `python -m polycombo check` with `Label=ask:estimate` for every leg, `--quote <quote>` if
   available, and `--bankroll` (default 10).
4. Run `python -m polycombo sim` on the same legs with `--days 1` and `--days 30`, using the
   combined estimate as `--win-prob` and the suggested stake as `--stake`.
5. Report in a short table: combined market chance, user's chance, quote markup, payout after
   fees, EV, suggested stake in dollars, chance of going broke. Name legs with no edge and
   recommend dropping them. Be blunt if it's negative EV.
