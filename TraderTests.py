import unittest

o = datamodel.Observation(dict(), dict())
s = datamodel.TradingState("", 0, dict(), dict(), dict(), dict(), dict(), o)
t = Trader()
t.run(s)