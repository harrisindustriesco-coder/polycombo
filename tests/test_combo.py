import unittest

from polycombo import Leg, analyze, simulate, required_edge, taker_fee, combo_fee
from polycombo import polymarket_us as pm


class TestFees(unittest.TestCase):
    def test_taker_fee_matches_docs(self):
        # Docs: max at $0.50 is $1.74 per 100 contracts
        self.assertAlmostEqual(taker_fee(0.5) * 100, 1.74, places=2)

    def test_combo_fee_higher_than_single(self):
        self.assertGreater(combo_fee(0.1), taker_fee(0.1))


class TestCombo(unittest.TestCase):
    def test_fair_price(self):
        r = analyze([Leg(0.5), Leg(0.5)])
        self.assertAlmostEqual(r.fair_price, 0.25)
        self.assertLess(r.multiplier, 4.0)  # fees reduce the 4x

    def test_quote_markup_flagged(self):
        r = analyze([Leg(0.5), Leg(0.5)], quote=0.30)
        self.assertAlmostEqual(r.markup, 0.2)
        self.assertTrue(any("above the legs" in w for w in r.warnings))

    def test_no_edge_zero_stake(self):
        r = analyze([Leg(0.5, 0.5), Leg(0.5, 0.5)])
        self.assertLess(r.ev_per_dollar, 0)
        self.assertEqual(r.kelly_fraction, 0.0)

    def test_edge_capped_stake(self):
        r = analyze([Leg(0.4, 0.6), Leg(0.5, 0.6)])
        self.assertGreater(r.ev_per_dollar, 0)
        self.assertLessEqual(r.kelly_fraction, 0.05)

    def test_leg_limit(self):
        with self.assertRaises(ValueError):
            analyze([Leg(0.9)] * 11)

    def test_required_edge(self):
        self.assertAlmostEqual(required_edge(10, 0.9), 9.0)

    def test_sim_all_in_10x_mostly_busts(self):
        s = simulate(0.1, 10.0, start=10, days=1, runs=20000, seed=1)
        self.assertAlmostEqual(s.p_bust, 0.9, delta=0.01)


class TestParsing(unittest.TestCase):
    """Shapes taken from docs.polymarket.us API reference."""

    def test_parse_event(self):
        e = {"title": "Lakers vs Celtics", "slug": "lal-bos", "startTime": "2026-10-01T02:00:00Z",
             "markets": [{"slug": "lal-bos-ml", "question": "Who wins?",
                          "bestBidQuote": {"value": "0.45", "currency": "USD"},
                          "bestAskQuote": {"value": "0.47", "currency": "USD"},
                          "marketSides": [{"description": "Lakers", "price": "0.47"},
                                          {"description": "Celtics", "price": {"value": "0.55"}}]}]}
        out = pm.parse_event(e)
        m = out["markets"][0]
        self.assertEqual(m["ask"], 0.47)
        self.assertEqual(m["sides"][1], {"name": "Celtics", "price": 0.55})

    def test_missing_fields_dont_crash(self):
        m = pm.parse_market({"slug": "x"})
        self.assertIsNone(m["ask"])
        self.assertEqual(m["sides"], [])


if __name__ == "__main__":
    unittest.main()
