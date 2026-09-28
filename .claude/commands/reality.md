---
description: Reality-check a money goal (e.g. $10 to $100 in 24h at 90%)
argument-hint: <goal, e.g. "10x at 90%">
---
Reality-check this goal: $ARGUMENTS

Work out the multiplier and win probability being asked for, then run
`python -m polycombo reality --mult <m> --prob <p>` and
`python -m polycombo sim --legs <prices that multiply to about 1/m> --days 1 --runs 20000`.
Explain in plain English what Polymarket US prices say the real odds are, how fees shrink the payout, what edge the goal would require, and what the simulation shows. Then suggest a realistic alternative using `check`.
