from datamodel import OrderDepth, UserId, TradingState, Order
from typing import List
import string
import jsonpickle

POSITION_LIMIT = 20
class Trader:

    def run(self, state: TradingState): # -> (dict[Symbol, Order], int, str)
        # our traderData will store the last 25 mid-prices
        pastPrices = parse_traderData(state.traderData)
        print(state.market_trades)
        print(state.own_trades)

        # Only method required. It takes all buy and sell orders for all symbols as an input, and outputs a list of orders to be sent
        print("traderData: " + state.traderData)
        print("Observations: " + str(state.observations))
        result = {}
        for product in state.order_depths:
            # if product == "AMETHYSTS":
            #     continue
            # if product == "STARFRUIT":
            #     continue
            # if product == "ORCHIDS":
            #     continue
            if product in {"CHOCOLATE", "STRAWBERRIES","ROSES","", "COCONUT", "COCONUT_COUPON"}:
                continue
            # if product not in {"STARFRUIT"}:
            #     continue
            if product in state.own_trades.keys():
                calculate_avg_cost(state.own_trades[product], pastPrices, state.timestamp, product)
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

            midPrice = getMidPrice(best_ask, best_bid)
            if product in pastPrices.keys():
                if len(pastPrices[product]) > 25:  # only stores the latest 25
                    pastPrices[product].pop(0)
                pastPrices[product].append(midPrice)
            else:
                pastPrices[product] = [midPrice]


            extremaKey = product + "PeaksAndTroughs"
            tradeNow = False
            if product != "AMETHYSTS":
                save_sup_and_res(order_depth, product, pastPrices)
                foundExtrema = False
                if lastIsPeak(pastPrices, product):
                    timeStamp, priceExtrema, peak = state.timestamp - 100, pastPrices[product][-2], True
                    foundExtrema = True
                elif lastIsTrough(pastPrices, product):
                    timeStamp, priceExtrema, peak = state.timestamp - 100, pastPrices[product][-2], False
                    foundExtrema = True
                if foundExtrema:
                    if extremaKey in pastPrices.keys():
                        pastPrices[extremaKey].append((timeStamp, priceExtrema, peak))
                        if len(pastPrices[extremaKey]) > 10:
                            pastPrices[extremaKey].pop(0)
                    else:
                        pastPrices[extremaKey] = [(timeStamp, priceExtrema, peak)]
                    tradeNow = True


            acceptable_price = calculate_fair_price(pastPrices, product, extremaKey)  # Participant should calculate this value

            # print("Acceptable price : " + str(acceptable_price))
            # print("Buy Order depth : " + str(
            #     len(order_depth.buy_orders)) + ", Sell order depth : " + str(
            #     len(order_depth.sell_orders)))
            if acceptable_price == -1:
                continue # don't trade this product this iteration


            result[product] = order_strategy(state, product, acceptable_price, midPrice, best_ask, best_bid, best_ask_amount, best_bid_amount, tradeNow, pastPrices, extremaKey)
        
        traderData = convertToStr(pastPrices)  # String value holding Trader state data required. It will be delivered as TradingState.traderData on next execution.
        # print(state)
        conversions = 0
        return result, conversions, traderData
    
# gets the middle value between both sides of a bid-ask spread, i.e. the current price valuation, returns -1 if no spread exists
def getMidPrice(best_ask: int, best_bid: int) -> float:
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
def parse_traderData(traderData: str) -> dict:
    if traderData == "":
        return dict()
    res = jsonpickle.decode(traderData)
    return res
        
        
# converts dictionary of pastPrices into a string which can be parsed as a dict the next iteration
def convertToStr(pastPrices: dict[str, list[int]]) -> str:
    res = jsonpickle.encode(pastPrices)
    return res


# calculates fair price valuation based on Moving Averages
def calculate_fair_price(pastPrices: dict, product: str, extremaKey: str) -> float:
    # initial strategy, calculate MA-3, MA-5, MA-7, MA-8, MA-10, MA-15, and MA-25, then return the median
    # when not enough data for the full MA, exclude that indicator
    # base case for PastPrices having no product
    if product not in pastPrices.keys():
        return -1
    if product == 'AMETHYSTS':
        moving_averages = {25} # consider return 10000, bc centers around this price anyways
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
        return calculated_results[index]  # median
    if product == 'STARFRUIT':
        midPrice = pastPrices[product + "_res"][0] + pastPrices[product + "_sup"][0]
        midPrice /= 2
        return midPrice + pastPrices[product+"Broke"] # + evaluateExtrema(pastPrices, product, extremaKey) * 2
    else:
        return 0

def calculate_avg_cost(prevTrades, pastPrices, timestamp, product):
    for trade in prevTrades:
        if timestamp != trade.timestamp + 100:
            break
        if trade.buyer == 'SUBMISSION':
            quant = trade.quantity
        else:
            # trade.seller == 'SUBMISSION'
            quant = -trade.quantity
        if "avgCost" not in pastPrices.keys():
            pos = {product: [trade.price, quant]}
            pastPrices["avgCost"] = pos
        elif product not in pastPrices["avgCost"].keys():
            pos = {product: [trade.price, quant]}
            pastPrices["avgCost"] = pos
        else:
            avg_cost, amnt = pastPrices["avgCost"][product] 
            new_pos = quant + amnt
            # ignore realized profit
            if new_pos == 0:
                del pastPrices["avgCost"][product]
            elif new_pos > 0 > amnt:
                #flip from short to long
                pastPrices["avgCost"][product] = [trade.price, new_pos]
            elif new_pos < 0 < amnt:
                # flip from long to short
                pastPrices["avgCost"][product] = [trade.price, new_pos]
            elif abs(amnt) > abs(quant):
                # makes lesser positions cancel
                pastPrices["avgCost"][product] = [avg_cost, new_pos]
            else:
                new_avg_cost = (amnt * avg_cost + quant * trade.price) / new_pos
                pastPrices["avgCost"][product] = [new_avg_cost, new_pos]

                
            
def save_sup_and_res(order_depth, product, pastPrices):
    key1 = product + "_res"
    key2 = product + "_sup"
    def adjust_strength_score(key, bot_orders):
        found = False
        for i, prices in enumerate(bot_orders):
            if key in pastPrices.keys():
                if pastPrices[key][0] == prices:
                    pastPrices[key][1] += 1 - i
                    found = True
                    break
            else:
                pastPrices[key] = [prices, 1]
                found = True
                break
        if not found:
            pastPrices[key][1] -= 3

        if pastPrices[key][1] <= 0:
            if len(bot_orders) == 0:
                return
            new_price = list(bot_orders)[0]
            if 'res' in key:
                if new_price < pastPrices[key][0]:
                    pastPrices[product + 'Broke'] -= 2
                else:
                    pastPrices[product+'Broke'] += 3
            if 'sup' in key:
                if new_price < pastPrices[key][0]:
                    pastPrices[product + 'Broke'] -= 3
                else:
                    pastPrices[product + 'Broke'] += 2
            pastPrices[key] = [new_price, 1]
   
    if (product + 'Broke') not in pastPrices.keys(): 
        pastPrices[product+'Broke'] = 0
    adjust_strength_score(key1, order_depth.sell_orders.keys())
    adjust_strength_score(key2, order_depth.buy_orders.keys())
    if pastPrices[product + 'Broke'] < 0:
        pastPrices[product + 'Broke'] += 4
    elif pastPrices[product + 'Broke'] > 0:
        pastPrices[product + 'Broke'] -= 4


def lastIsPeak(pastPrices, product):        
    n = len(pastPrices[product])
    if n < 3:
        return False
    return pastPrices[product][-3] < pastPrices[product][-2] and pastPrices[product][-2] > pastPrices[product][-1]

def lastIsTrough(pastPrices, product):
    n = len(pastPrices[product])
    if n < 3:
        return False
    return pastPrices[product][-3] > pastPrices[product][-2] and pastPrices[product][-2] < pastPrices[product][-1]

def evaluateExtrema(pastPrices, product, extremaKey):
    # determine up or downtrend, then buy on uptrend for trough, sell on downtrend for peak
    if extremaKey in pastPrices.keys() and len(pastPrices[extremaKey]) >= 6:         
        # uptrend
        if three_peaks_higher(pastPrices, extremaKey) and three_troughs_higher(pastPrices, extremaKey):
            return 1
        if last_four_increasing(pastPrices, product):
            return 1
        # downtrend
        elif three_troughs_lower(pastPrices, extremaKey) and three_peaks_lower(pastPrices, extremaKey):
            return -1
        if last_four_decreasing(pastPrices, product):
            return -1
    return 0

def last_four_increasing(pastPrices, product):
    for i in range(len(pastPrices[product]) - 2, len(pastPrices[product]) - 6, -1):
        if not pastPrices[product][i] < pastPrices[product][i+1]:
            return False
    return True
            
def last_four_decreasing(pastPrices, product):
    for i in range(len(pastPrices[product]) - 2, len(pastPrices[product]) - 6, -1):
        if not pastPrices[product][i] > pastPrices[product][i + 1]:
            return False
    return True
    
def three_peaks_higher(pastPrices, extremaKey):
    i = -6
    highest = -1
    while i < 0: 
        if pastPrices[extremaKey][i][2]:
            if pastPrices[extremaKey][i][1] > highest:
                highest = pastPrices[extremaKey][i][1]
            else:
                return False 
        i += 1
    return True
    
def three_troughs_higher(pastPrices, extremaKey):
    i = -6
    highest = -1
    while i < 0:
        if not pastPrices[extremaKey][i][2]:
            if pastPrices[extremaKey][i][1] > highest:
                highest = pastPrices[extremaKey][i][1]
            else:
                return False
        i += 1
    return True
    
def three_peaks_lower(pastPrices, extremaKey):
    i = -6
    lowest = 1000000
    while i < 0:
        if pastPrices[extremaKey][i][2]:
            if pastPrices[extremaKey][i][1] < lowest:
                lowest = pastPrices[extremaKey][i][1]
            else:
                return False
        i += 1
    return True
    
def three_troughs_lower(pastPrices, extremaKey):
    i = -6
    lowest = 1000000
    while i < 0:
        if not pastPrices[extremaKey][i][2]:
            if pastPrices[extremaKey][i][1] < lowest:
                lowest = pastPrices[extremaKey][i][1]
            else:
                return False
        i += 1
    return True

def order_strategy(state, product, acceptable_price, midPrice, best_ask, best_bid, best_ask_amount, best_bid_amount, tradeNow, pastPrices, extremaKey):
    order_depth: OrderDepth = state.order_depths[product]
    true_orders = []
    try:
        current_position = state.position[product]
    except KeyError:
        current_position = 0
    if product == 'AMETHYSTS':
        orders: List[Order] = []
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
                i += 1
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
        true_orders.extend(prevent_limit_exceed(orders, state, product, pastPrices))

    elif product == 'STARFRUIT':
        orders: List[Order] = []
        try:
            avg_cost, amnt = pastPrices['avgCost'][product]
        except KeyError:
            amnt = 0
            avg_cost = -1
        try:
            if pastPrices[product+'_res'][1] > 4 and pastPrices[product+'_sup'][1] > 4:
                if amnt == 0 and best_ask < acceptable_price:
                    orders.append(Order(product, best_ask, -best_ask_amount // 3))
                    current_position -= best_ask_amount
                if amnt == 0 and best_bid > acceptable_price:
                    orders.append(Order(product, best_bid, -best_bid_amount // 3))
                    current_position -= best_bid_amount
                if acceptable_price < avg_cost - 10 or (amnt < 0 and acceptable_price < avg_cost-5):
                    #buy
                    if current_position -(amnt+1)//4 <= POSITION_LIMIT:
                        orders.append(Order(product, int(acceptable_price), -(amnt)//4+1))
                        current_position += -(amnt+1)//4 +1
                if acceptable_price > avg_cost + 10 or (amnt > 0 and acceptable_price < avg_cost+5):
                    #sell
                    if current_position -(amnt+1)//4 >= -POSITION_LIMIT:
                        orders.append(Order(product, int(acceptable_price), -(amnt)//4-1))
                        current_position += -(amnt)//4 -1
        except KeyError:
            pass
        for listAmount in range(6, 3, -1):
            if avg_cost != -1 and avg_cost < acceptable_price + 6:
                if current_position - listAmount >= -POSITION_LIMIT:
                    orders.append(Order(product, int(acceptable_price+listAmount/1.5), -listAmount))
                    current_position -= listAmount
                    
            if avg_cost != -1 and avg_cost > acceptable_price - 6:
                if current_position + listAmount <= POSITION_LIMIT:
                    orders.append(Order(product, int(acceptable_price-listAmount/1.5), listAmount))
                    current_position += listAmount
        if extremaKey in pastPrices.keys():
            if evaluateExtrema(pastPrices, product, extremaKey) > 0 and  \
                    (not pastPrices[extremaKey][-1][2] or last_four_decreasing(pastPrices, product)):
                if current_position + POSITION_LIMIT // 5 <= POSITION_LIMIT:
                    orders.append(Order(product, min(acceptable_price, best_ask-1), POSITION_LIMIT // 5))
                    current_position += POSITION_LIMIT // 5
            if evaluateExtrema(pastPrices, product, extremaKey) < 0 and \
                    ( pastPrices[extremaKey][-1][2] or last_four_increasing(pastPrices, product)):
                # trading down on peak
                if current_position - POSITION_LIMIT // 5 >= -POSITION_LIMIT:
                    orders.append(Order(product, max(acceptable_price, best_bid+1), -POSITION_LIMIT // 5))
                    current_position -= POSITION_LIMIT // 5
            if pastPrices[product+"Broke"] > 1 and  \
                    (not pastPrices[extremaKey][-1][2] or last_four_decreasing(pastPrices, product)):
                if current_position + pastPrices[product+"Broke"] <= POSITION_LIMIT:
                    orders.append(Order(product, pastPrices[product+'_sup'][0] + 1, int(pastPrices[product+"Broke"])))
                    current_position += pastPrices[product+"Broke"]
            if pastPrices[product+"Broke"] < -1 and \
                    ( pastPrices[extremaKey][-1][2] or last_four_increasing(pastPrices, product)):
                if current_position + pastPrices[product+"Broke"] >= -POSITION_LIMIT:
                    orders.append(Order(product, pastPrices[product+'_res'][0]- 1, int(pastPrices[product+"Broke"])))
                    current_position += pastPrices[product+"Broke"]
        true_orders.extend(prevent_limit_exceed(orders, state, product, pastPrices))
    else:
        orders: List[Order] = []
        try:
            avg_cost, amnt = pastPrices['avgCost'][product]
        except KeyError:
            amnt = 0
            avg_cost = -1
        try:
            if pastPrices[product + '_res'][1] > 4 and pastPrices[product + '_sup'][1] > 4:
                if amnt == 0 and best_ask < acceptable_price:
                    orders.append(Order(product, best_ask, -best_ask_amount // 3))
                    current_position -= best_ask_amount
                if amnt == 0 and best_bid > acceptable_price:
                    orders.append(Order(product, best_bid, -best_bid_amount // 3))
                    current_position -= best_bid_amount
                if acceptable_price < avg_cost - 10 or (
                        amnt < 0 and acceptable_price < avg_cost - 5):
                    # buy
                    if current_position - (amnt + 1) // 4 <= POSITION_LIMIT:
                        orders.append(Order(product, int(acceptable_price), -(amnt) // 4 + 1))
                        current_position += -(amnt + 1) // 4 + 1
                if acceptable_price > avg_cost + 10 or (
                        amnt > 0 and acceptable_price < avg_cost + 5):
                    # sell
                    if current_position - (amnt + 1) // 4 >= -POSITION_LIMIT:
                        orders.append(Order(product, int(acceptable_price), -(amnt) // 4 - 1))
                        current_position += -(amnt) // 4 - 1
        except KeyError:
            pass
        for listAmount in range(6, 3, -1):
            if avg_cost != -1 and avg_cost < acceptable_price + 6:
                if current_position - listAmount >= -POSITION_LIMIT:
                    orders.append(
                        Order(product, int(acceptable_price + listAmount / 1.5), -listAmount))
                    current_position -= listAmount

            if avg_cost != -1 and avg_cost > acceptable_price - 6:
                if current_position + listAmount <= POSITION_LIMIT:
                    orders.append(
                        Order(product, int(acceptable_price - listAmount / 1.5), listAmount))
                    current_position += listAmount
        if extremaKey in pastPrices.keys():
            if evaluateExtrema(pastPrices, product, extremaKey) > 0 and \
                    (not pastPrices[extremaKey][-1][2] or last_four_decreasing(pastPrices,
                                                                               product)):
                if current_position + POSITION_LIMIT // 5 <= POSITION_LIMIT:
                    orders.append(
                        Order(product, min(acceptable_price, best_ask - 1), POSITION_LIMIT // 5))
                    current_position += POSITION_LIMIT // 5
            if evaluateExtrema(pastPrices, product, extremaKey) < 0 and \
                    (pastPrices[extremaKey][-1][2] or last_four_increasing(pastPrices, product)):
                # trading down on peak
                if current_position - POSITION_LIMIT // 5 >= -POSITION_LIMIT:
                    orders.append(
                        Order(product, max(acceptable_price, best_bid + 1), -POSITION_LIMIT // 5))
                    current_position -= POSITION_LIMIT // 5
            if pastPrices[product + "Broke"] > 1 and \
                    (not pastPrices[extremaKey][-1][2] or last_four_decreasing(pastPrices,
                                                                               product)):
                if current_position + pastPrices[product + "Broke"] <= POSITION_LIMIT:
                    orders.append(Order(product, pastPrices[product + '_sup'][0] + 1,
                                        int(pastPrices[product + "Broke"])))
                    current_position += pastPrices[product + "Broke"]
            if pastPrices[product + "Broke"] < -1 and \
                    (pastPrices[extremaKey][-1][2] or last_four_increasing(pastPrices, product)):
                if current_position + pastPrices[product + "Broke"] >= -POSITION_LIMIT:
                    orders.append(Order(product, pastPrices[product + '_res'][0] - 1,
                                        int(pastPrices[product + "Broke"])))
                    current_position += pastPrices[product + "Broke"]
        true_orders.extend(prevent_limit_exceed(orders, state, product, pastPrices))
    return true_orders
    
def prevent_limit_exceed(orders, state, product, pastPrices):
    """return true order list"""
    if product in state.position.keys():
        true_position = state.position[product]
    else:
        true_position = 0
    kept_orders = []
    total_long = 0
    longs = []
    total_short = 0
    shorts = []
    for order in orders:
        if order.quantity > 0:
            total_long += order.quantity
            longs.append([order.price, order.quantity])
        elif order.quantity < 0:
            total_short -= order.quantity
            shorts.append([order.price, order.quantity])
    if true_position + total_long <= POSITION_LIMIT and true_position - total_short >= -POSITION_LIMIT:
        return orders
    longs = sorted(longs, reverse = True)
    shorts = sorted(shorts)
    if true_position + total_long <= POSITION_LIMIT and true_position - total_short < -POSITION_LIMIT:
        for price, quant in shorts:
            if true_position - total_short - (quant // 2) >= -POSITION_LIMIT:
                kept_orders.append(Order(product, price, int(quant//2)))
            elif true_position - total_short - quant >= -POSITION_LIMIT:
                pass
            else:
                kept_orders.append(Order(product, price, quant))
        for price, quant in longs:
            kept_orders.append(Order(product, price, quant))
    elif true_position + total_long > POSITION_LIMIT and true_position - total_short >= -POSITION_LIMIT:
        for price, quant in longs:
            if true_position + total_long - (quant // 2) <= POSITION_LIMIT:
                kept_orders.append(Order(product, price, int(quant // 2)))
            elif true_position + total_long - quant <= POSITION_LIMIT:
                pass
            else:
                kept_orders.append(Order(product, price, quant))
        for price, quant in shorts:
            kept_orders.append(Order(product, price, quant))
    elif true_position + total_long > POSITION_LIMIT and true_position - total_short < -POSITION_LIMIT:
        i = 0
        j = 0
        while i < len(shorts) and j < len(longs):
            if shorts[i][0] < longs[j][0]:
                pass
            else:
                kept_orders.append(Order(product, shorts[i][0], shorts[i][1]))
                kept_orders.append(Order(product, longs[i][0], longs[i][0]))
            i += 1
            j += 1
        total_short, total_long = 0, 0
        for order in kept_orders:
            if order.quantity > 0:
                total_long += order.quantity
            elif order.quantity < 0:
                total_short -= order.quantity
        if true_position + total_long > POSITION_LIMIT or true_position - total_short < -POSITION_LIMIT:
            kept_orders = kept_orders[2:]
    return kept_orders
            
    
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
