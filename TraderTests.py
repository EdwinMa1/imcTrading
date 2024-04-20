import unittest
from Trader import *
import datamodel

class TestTrader(unittest.TestCase):

    def test_json_traderdata(self):
        shouldEqual = dict()
        shouldEqual['He'] = 21
        shouldEqual['She'] = [12, 16, 40]
        shouldEqual['okay'] = 'FOO'
        res = '{"He": 21, "She": [12, 16, 40], "okay": "FOO"}'
        self.assertEqual(parse_traderData(""), dict())
        self.assertEqual(convertToStr(shouldEqual), res)
        # self.assertEqual(parse_traderData("{He: 21, She: [12, 16, 40], okay: 'FOO'}"), shouldEqual) 
        self.assertEqual(parse_traderData(res), shouldEqual) 
    
    def test_sup_res_stores_in_pastPrices(self):
        pastPrices = {"Fruit1": [50, 2]}
        o = datamodel.OrderDepth({40: 3}, {53: 1, 55: 8})
        save_sup_and_res(o, 'FRUIT1', pastPrices)
        self.assertEqual(pastPrices, {"Fruit1": [50, 2], "FRUIT1_res": [53, 1], "FRUIT1_sup": [40, 1]})
        
        o = datamodel.OrderDepth({40: 3}, {55: 8})
        save_sup_and_res(o, 'FRUIT1', pastPrices)
        self.assertEqual(pastPrices, {"Fruit1": [50, 2], "FRUIT1_res": [55, 1], "FRUIT1_sup": [40, 2]})
        
        o = datamodel.OrderDepth({42:10, 40: 3}, {55: 8})
        save_sup_and_res(o, 'FRUIT1', pastPrices)
        self.assertEqual(pastPrices,
                         {"Fruit1": [50, 2], "FRUIT1_res": [55, 2], "FRUIT1_sup": [40, 2]})
        o = datamodel.OrderDepth({42: 10}, {55: 8})
        save_sup_and_res(o, 'FRUIT1', pastPrices)
        self.assertEqual(pastPrices,
                         {"Fruit1": [50, 2], "FRUIT1_res": [55, 3], "FRUIT1_sup": [42, 1]})


if __name__ == '__main__':
    unittest.main()
# o = datamodel.Observation(dict(), dict())
# s = datamodel.TradingState("", 0, dict(), dict(), dict(), dict(), dict(), o)
# t = Trader()
# t.run(s)