from datamodel import OrderDepth, UserId, TradingState, Order
from typing import List
import string


class Trader:

    def run(self, state: TradingState): # -> (dict[Symbol, Order], int, str)
        # our traderData will store the last 25 midprices
        # Only method required. It takes all buy and sell orders for all symbols as an input, and outputs a list of orders to be sent
        print("traderData: " + state.traderData)
        print("Observations: " + str(state.observations))
        result = {}
        for product in state.order_depths:
            order_depth: OrderDepth = state.order_depths[product]
            orders: List[Order] = []
            acceptable_price = 10  # Participant should calculate this value
            print("Acceptable price : " + str(acceptable_price))
            print("Buy Order depth : " + str(
                len(order_depth.buy_orders)) + ", Sell order depth : " + str(
                len(order_depth.sell_orders)))
            
            #initializing the best offers from both sides to be -1 if no offers exist
            best_ask = -1 
            best_bid = -1
            if len(order_depth.sell_orders) != 0:
                best_ask, best_ask_amount = list(order_depth.sell_orders.items())[0]
                if int(best_ask) < acceptable_price:
                    print("BUY", str(-best_ask_amount) + "x", best_ask)
                    orders.append(Order(product, best_ask, -best_ask_amount))

            if len(order_depth.buy_orders) != 0:
                best_bid, best_bid_amount = list(order_depth.buy_orders.items())[0]
                if int(best_bid) > acceptable_price:
                    print("SELL", str(best_bid_amount) + "x", best_bid)
                    orders.append(Order(product, best_bid, -best_bid_amount))
            midPrice = self.getMidPrice(best_ask, best_bid) 

            result[product] = orders

        traderData = "SAMPLE"  # String value holding Trader state data required. It will be delivered as TradingState.traderData on next execution.

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
    