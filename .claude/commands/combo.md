---
description: Analyze a Polymarket US sports combo (live prices + your estimates)
argument-hint: <legs, e.g. "Lakers ML, Chiefs ML, Yankees ML">
---
Analyze this Polymarket US combo: $ARGUMENTS

1. For each leg, run `python -m polycombo search "<team>"` (or `games <league>`) and find the matching combo-eligible market. Show the question and ask price. If a leg is ambiguous, ask which one. If the API fails, ask me to paste the prices from the app.
2. Ask me for my own probability per leg if I haven't given one, and whether the app showed me a combo quote.
3. Run `python -m polycombo check` with `Label=ask:estimate` for every leg, `--quote <quote>` if I have one, and `--bankroll` (default 10).
4. Run `python -m polycombo sim` on the same legs with `--days 1` and `--days 30`, using my combined estimate as `--win-prob` and the suggested stake as `--stake`.
5. Report in a short table: combined market chance, my chance, quote markup, payout after fees, EV, suggested stake in dollars, chance of going broke. Name legs with no edge and recommend dropping them. Be blunt if it's negative EV.
