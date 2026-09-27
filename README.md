# polycombo for Polymarket US

Honest calculator for Polymarket US sports combos. It pulls live prices, shows your real combined odds,
what you'd actually get paid after Polymarket US combo fees, how much the combo quote is marked up,
whether you have any edge, how much to bet, and what repeating the bet does to a $10 bankroll.
It reads public data only and never places orders.

## Set up
1. Unzip and `cd polycombo` (Python 3.9+, nothing to install).
2. Run `claude` in the folder. Claude Code reads `CLAUDE.md` automatically.

## In Claude Code
- `/slate nfl`: tonight's games and prices
- `/combo Lakers ML, Chiefs ML`: live prices, your estimates, fees, stake size, simulation
- `/reality 10x at 90%`: checks whether a goal is possible

These also ship as Claude Skills (`.claude/skills/slate`, `.claude/skills/combo`,
`.claude/skills/reality`) with the same behavior, for clients that discover skills instead of
slash commands.

## Or run directly
```
python -m polycombo games nba
python -m polycombo search "chiefs"
python -m polycombo check Lakers=0.55:0.60 Chiefs=0.62:0.66 --quote 0.36 --bankroll 10
python -m polycombo reality --mult 10 --prob 0.9
python -m polycombo sim --legs 0.55 0.6 0.5 0.6 --days 1
python -m unittest discover -s tests
```
Leg format: `price` or `price:your_estimate` (0 to 1). Use the ask price.
`--quote` is the combo price the app shows you (in dollars per contract, e.g. 0.36).

Polymarket US availability varies by state. Only bet what you can afford to lose.
