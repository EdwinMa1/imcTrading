from datamodel import OrderDepth, UserId, TradingState, Order
from typing import List
import string
import jsonpickle

POSITION_LIMIT = 20
class Trader:

    def run(self, state: TradingState): # -> (dict[Symbol, Order], int, str)
        # our traderData will store the last 25 mid-prices
        pastPrices = self.parse_traderData(state.traderData)
        # Only method required. It takes all buy and sell orders for all symbols as an input, and outputs a list of orders to be sent
        print("traderData: " + state.traderData)
        print("Observations: " + str(state.observations))
        result = {}
        for product in state.order_depths:
            # if product == "AMETHYSTS":
            #     continue
            # if product == "STARFRUIT":
            #     continue
            order_depth: OrderDepth = state.order_depths[product]
            # initializing the best offers from both sides to be -1 if no offers exist
            best_ask = -1
            best_bid = -1
            best_bid_amount, best_ask_amount = 0, 0

            # strategy to submit trade Orders
            # considering to buy
            if len(order_depth.sell_orders) != 0:
                best_ask, best_ask_amount = list(order_depth.sell_orders.items())[0]
            # considering to sell
            if len(order_depth.buy_orders) != 0:
                best_bid, best_bid_amount = list(order_depth.buy_orders.items())[0]

            midPrice = self.getMidPrice(best_ask, best_bid)
            if product in pastPrices.keys():
                if len(pastPrices[product]) > 25:  # only stores the latest 25
                    pastPrices[product].pop(0)
                pastPrices[product].append(midPrice)
            else:
                pastPrices[product] = [midPrice]
            # if product == "STARFRUIT":
            #     foundExtrema = False
            #     if self.lastIsPeak(pastPrices, product):
            #         print('found')
            #         timeStamp, priceExtrema, peak = state.timestamp - 100, pastPrices[product][-2], True
            #         foundExtrema = True
            #     elif self.lastIsTrough(pastPrices, product):
            #         timeStamp, priceExtrema, peak = state.timestamp - 100, pastPrices[product][-2], False
            #         foundExtrema = True
            #     if foundExtrema:
            #         if "starfruitPeaksAndTroughs" in pastPrices.keys():
            #             pastPrices["starfruitPeaksAndTroughs"].append((timeStamp, priceExtrema, peak))
            #         else:
            #             pastPrices["starfruitPeaksAndTroughs"] = [(timeStamp, priceExtrema, peak)]

                        
            acceptable_price = self.calculate_fair_price(pastPrices, product)  # Participant should calculate this value

            # print("Acceptable price : " + str(acceptable_price))
            # print("Buy Order depth : " + str(
            #     len(order_depth.buy_orders)) + ", Sell order depth : " + str(
            #     len(order_depth.sell_orders)))
            if acceptable_price == -1:
                continue # don't trade this product this iteration


            result[product] = self.order_strategy(state, product, acceptable_price, midPrice, best_ask, best_bid, best_ask_amount, best_bid_amount)
        
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
        return res
            
            
    # converts dictionary of pastPrices into a string which can be parsed as a dict the next iteration
    def convertToStr(self, pastPrices: dict[str, list[int]]) -> str:
        res = jsonpickle.encode(pastPrices)
        return res
    
    
    # calculates fair price valuation based on Moving Averages
    def calculate_fair_price(self, pastPrices: dict, product: str) -> float:
        # initial strategy, calculate MA-3, MA-5, MA-7, MA-8, MA-10, MA-15, and MA-25, then return the median
        # when not enough data for the full MA, exclude that indicator
        # base case for PastPrices having no product
        if product not in pastPrices.keys():
            return -1
        if product == 'AMETHYSTS':
            moving_averages = {25} # consider return 10000, bc centers around this price anyways
        elif product == 'STARFRUIT':
            moving_averages = {5, 8, 15}
        else:
            moving_averages = {8}
        calculated_results = []
        n = len(pastPrices[product])
        sum_prices = 0
        for j in range(n-1,-1,-1):
            i = n-1-j
            sum_prices += pastPrices[product][j]
            if i+1 in moving_averages:
                calculated_results.append(sum_prices / (i + 1))
        if len(calculated_results) == 0:
            return -1
        index = len(calculated_results) // 2
        calculated_results = sorted(calculated_results) 
        return calculated_results[index] # median
       
        
    def lastIsPeak(self, pastPrices, product):        
        n = len(pastPrices[product])
        if n < 3:
            return False
        print('HERE')
        print(pastPrices[product])
        print(pastPrices[product][0]) #WHY CANT I INDEX???
        print('DONE')
        return False
        return pastPrices[product][n-3] < pastPrices[product][n-2] and pastPrices[product][n-2] > pastPrices[product][n-1]
    
    def lastIsTrough(self, pastPrices, product):
        n = len(pastPrices[product])
        if n < 3:
            return False
        
        return False
        return pastPrices[product][n-3] > pastPrices[product][n-2] and pastPrices[product][n-2] < pastPrices[product][n-1]
    
    def evaluateExtrema(self, pastPrices):
        # pastPrices["starfruitPeaksAndTroughs"] 
        # determine up or downtrend, then buy on uptrend for trough, sell on downtrend for peak
        if len(pastPrices["starfruitPeaksAndTroughs"]) >= 6: 
            pass
            
            # if 3 peaks higher than the last 
            # if 3 trough lower than the last
        pass
    
    
    def three_peaks_higher(self, pastPrices):
        i = -5
        highest = -1
        while i < 0: 
            if pastPrices["starfruitPeaksAndTroughs"][i][2]:
                if pastPrices["starfruitPeaksAndTroughs"][i][1] > highest:
                    highest = pastPrices["starfruitPeaksAndTroughs"][i][1]
                else:
                    return False 
            i += 1
        return True
        
    def three_troughs_lower(self, pastPrices):
        i = -5
        lowest = 1000000
        while i < 0:
            if not pastPrices["starfruitPeaksAndTroughs"][i][2]:
                if pastPrices["starfruitPeaksAndTroughs"][i][1] < lowest:
                    lowest = pastPrices["starfruitPeaksAndTroughs"][i][1]
                else:
                    return False
            i += 1
        return True
    
    def order_strategy(self, state, product, acceptable_price, midPrice, best_ask, best_bid, best_ask_amount, best_bid_amount):
        order_depth: OrderDepth = state.order_depths[product]
        orders: List[Order] = []
        try:
            current_position = state.position[product]
        except KeyError:
            current_position = 0
        if product == 'AMETHYSTS':
            i = 0
            while i < len(order_depth.sell_orders) and i < 3:
                ask_price, ask_amount = list(order_depth.sell_orders.items())[i]
                ask_amount = -ask_amount
                if int(ask_price) < acceptable_price:
                    if current_position + ask_amount >= POSITION_LIMIT:
                        orders.append(Order(product, ask_price, POSITION_LIMIT - current_position))
                        current_position = POSITION_LIMIT
                        break
                    orders.append(Order(product, ask_price, ask_amount))
                    i +=1
                    current_position += ask_amount
                else:
                    break
            i = 0
            while i < len(order_depth.buy_orders) and i < 3:
                buy_price, buy_amount = list(order_depth.buy_orders.items())[i]
                if int(buy_price) > acceptable_price:
                    if current_position - buy_amount <= -POSITION_LIMIT:
                        orders.append(Order(product, buy_price, -POSITION_LIMIT - current_position))
                        current_position = -POSITION_LIMIT
                        break
                    orders.append(Order(product, buy_price, -buy_amount))
                    i += 1
                    current_position -= buy_amount
                else:
                    break
            listAmount = 5
            while listAmount > 0:
                if midPrice < acceptable_price:
                    listingPrice = int(min(best_bid + 1, midPrice))
                    if current_position + listAmount < POSITION_LIMIT:
                        orders.append(Order(product, listingPrice, listAmount))
                        current_position += listAmount
                        
                else:
                    listingPrice = int(max(best_ask - 1, midPrice))
                    if current_position - listAmount > -POSITION_LIMIT:
                        orders.append(Order(product, listingPrice, -listAmount))
                        current_position -= listAmount
                        
                listAmount -= 1

        elif product == 'STARFRUIT':
            if len(order_depth.sell_orders) != 0 and int(best_ask) < acceptable_price - 2:
                orders.append(Order(product, best_ask, -best_ask_amount))
            elif len(order_depth.buy_orders) != 0 and int(best_bid) > acceptable_price + 2:
                orders.append(Order(product, best_bid, -best_bid_amount))
            listAmount = 4
            if midPrice < acceptable_price:
                listingPrice = int(min(best_bid + 1, midPrice))
                if current_position + listAmount < POSITION_LIMIT:
                    orders.append(Order(product, listingPrice, listAmount))
                    current_position += listAmount
            elif midPrice > acceptable_price:
                listingPrice = int(max(best_ask - 1, midPrice))
                if current_position - listAmount > -POSITION_LIMIT:
                    orders.append(Order(product, listingPrice, -listAmount))
                    current_position -= listAmount
        return orders
    
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
