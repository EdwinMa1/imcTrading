import unittest
import Trader
import datamodel

class TestTrader(unittest.TestCase):

    def test_upper(self):
        self.assertEqual('foo'.upper(), 'FOO')


if __name__ == '__main__':
    unittest.main()
o = datamodel.Observation(dict(), dict())
s = datamodel.TradingState("", 0, dict(), dict(), dict(), dict(), dict(), o)
t = Trader()
t.run(s)