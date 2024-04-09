from datamodel import OrderDepth, UserId, TradingState, Order
from typing import List
import string
import jsonpickle


class Trader:

    def run(self, state: TradingState): # -> (dict[Symbol, Order], int, str)
        # our traderData will store the last 25 mid-prices
        pastPrices = self.parse_traderData(state.traderData)
        # Only method required. It takes all buy and sell orders for all symbols as an input, and outputs a list of orders to be sent
        print("traderData: " + state.traderData)
        print("Observations: " + str(state.observations))
        result = {}
        for product in state.order_depths:
            
            order_depth: OrderDepth = state.order_depths[product]
            orders: List[Order] = []

            # initializing the best offers from both sides to be -1 if no offers exist
            best_ask = -1
            best_bid = -1

            # strategy to submit trade Orders
            # considering to buy
            if len(order_depth.sell_orders) != 0:
                best_ask, best_ask_amount = list(order_depth.sell_orders.items())[0]
            # considering to sell
            if len(order_depth.buy_orders) != 0:
                best_bid, best_bid_amount = list(order_depth.buy_orders.items())[0]
                
            midPrice = self.getMidPrice(best_ask, best_bid)
            if product in pastPrices.keys():
                if len(pastPrices[product]) >= 25:  # only stores the latest 25
                    pastPrices[product].pop(0)
                pastPrices[product].append(midPrice)
            else:
                pastPrices[product] = [midPrice]
            
            acceptable_price = self.calculate_fair_price(pastPrices, product)  # Participant should calculate this value
            
            print("Acceptable price : " + str(acceptable_price))
            print("Buy Order depth : " + str(
                len(order_depth.buy_orders)) + ", Sell order depth : " + str(
                len(order_depth.sell_orders)))
            if acceptable_price == -1:
                continue # don't trade this product this iteration
            
            if len(order_depth.sell_orders) != 0 and int(best_ask) < acceptable_price:
                print("BUY", str(-best_ask_amount) + "x", best_ask)
                orders.append(Order(product, best_ask, -best_ask_amount))
            if len(order_depth.buy_orders) != 0 and int(best_bid) > acceptable_price:
                print("SELL", str(best_bid_amount) + "x", best_bid)
                orders.append(Order(product, best_bid, -best_bid_amount))

            result[product] = orders
        
        traderData = self.convertToStr(pastPrices)  # String value holding Trader state data required. It will be delivered as TradingState.traderData on next execution.

        conversions = 1
        return result, conversions, traderData
    
    # gets the middle value between both sides of a bid-ask spread, i.e. the current price valuation, returns -1 if no spread exists
    def getMidPrice(self, best_ask: int, best_bid: int) -> float:
        if best_ask == -1 and best_bid == -1:
            return -1 # no midPrice Exists
        else:
            if best_ask == -1:
                return best_bid
            elif best_bid == -1:
                return best_ask
            else:
                return (best_bid + best_ask) / 2
    
    
    # generators dictionary of last 25 prices from all the symbols, key symbol, value list of prices
    def parse_traderData(self, traderData: str) -> dict:
        if traderData == "":
            return dict()
        res = jsonpickle.decode(traderData)
        print(type(res))
        print(res)
        return res
            
            
    # converts dictionary of pastPrices into a string which can be parsed as a dict the next iteration
    def convertToStr(self, pastPrices: dict[str, list[int]]) -> str:
        res = jsonpickle.encode(pastPrices)
        print(type(res))
        print(res)
        return res
    
    
    # calculates fair price valuation based on Moving Averages
    def calculate_fair_price(self, pastPrices: dict, product: str) -> float:
        # initial strategy, calculate MA-3, MA-5, MA-7, MA-8, MA-10, MA-15, and MA-25, then return the median
        # when not enough data for the full MA, exclude that indicator
        # base case for PastPrices having no product
        if product not in pastPrices.keys():
            return -1
        if product == 'AMETHYSTS':
            moving_averages = {8, 10, 25}
        elif product == 'STARFRUIT':
            moving_averages = {3, 7, 15}
        else:
            moving_averages = {8}
        calculated_results = []
        n = len(pastPrices[product])
        sum_prices = 0
        for i in range(n):
            sum_prices += pastPrices[product][i]
            if i+1 in moving_averages:
                calculated_results.append(sum_prices / (i + 1))
        if len(calculated_results) == 0:
            return -1
        index = len(calculated_results) // 2
        calculated_results = sorted(calculated_results) 
        return calculated_results[index] # median
       
        
        #default
        # return 10
    
    
"""
Need to implement parsing function + converting function
We are only submitting trader.py
AWS lambda prevents us from consistently storing certain things like dictionaries in memory,
 hence we need traderData string which is passed to the next iteration every iteration
Possible problems:
 1. how will our trades affect the market...is this even a worry on such a large scale?
 2. We did not implement the strategies for submitting the actual orders, its currently set up to trade the best offers that meet our acceptable price
    a. * How do we address position limits? *
    b. Canceled orders not considered
    c. Is there any sort of time race against competitors
    d. If we change this preset strategy, should we prioritize trading as much that meet our acceptable price, or only the best, or something in between?
 3. Is our algorithm efficient, could it be better?
"""
