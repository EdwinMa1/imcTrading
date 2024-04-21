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
        
    def test_calc_avg_cost_buyer(self):
        own_trades = {'STARFRUIT': [datamodel.Trade(symbol= "STARFRUIT", price = 5000, quantity = 2, buyer = "SUBMISSION", seller = None, timestamp = 1700)]}
        current_position = {'STARFRUIT': [5600, 1]}
        pastPrices = {'avgCost': current_position}
        time = 1800
        calculate_avg_cost(own_trades['STARFRUIT'], pastPrices, time, 'STARFRUIT')
        self.assertEqual(pastPrices, {'avgCost': {'STARFRUIT': [5200, 3]}})
        print(type(pastPrices["avgCost"]))
        # calculate_avg_cost(own_trades['STARFRUIT'], pastPrices, time+100, 'STARFRUIT')
        # self.assertEqual(pastPrices, {'avgCost': {'STARFRUIT': [5200, 3]}})
    
    def test_calc_avg_cost_seller(self):
        own_trades = {'STARFRUIT': [datamodel.Trade(symbol= "STARFRUIT", price = 6200, quantity = 6, buyer = None, seller = "SUBMISSION", timestamp = 1700)]}
        current_position = {'STARFRUIT': [5200, 3]}
        pastPrices = {'avgCost': current_position}
        time = 1800
        calculate_avg_cost(own_trades['STARFRUIT'], pastPrices, time, 'STARFRUIT')
        self.assertEqual(pastPrices, {'avgCost': {'STARFRUIT': [6200, -3]}})

if __name__ == '__main__':
    unittest.main()
# o = datamodel.Observation(dict(), dict())
# s = datamodel.TradingState("", 0, dict(), dict(), dict(), dict(), dict(), o)
# t = Trader()
# t.run(s)