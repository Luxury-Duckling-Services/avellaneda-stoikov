# https://github.com/keanekwa/Optiver-Ready-Trader-Go/blob/main/ASModel.py

# https://medium.com/@degensugarboo/avellaneda-and-stoikov-mm-paper-implementation-b7011b5a7532

# https://math.nyu.edu/~avellane/HighFrequencyTrading.pdf

# https://quant.stackexchange.com/questions/69407/orderbook-liquidity-parameter-avellaneda-stoikov

# https://arxiv.org/pdf/1105.3115.pdf

# https://github.com/hummingbot/hummingbot/tree/master/hummingbot/strategy/avellaneda_market_making

# https://hummingbot.org/strategies/avellaneda-market-making/

import math

# instant volatility:
# https://github.com/hummingbot/hummingbot/blob/master/hummingbot/strategy/__utils__/trailing_indicators/instant_volatility.py

class 

# trading intensity:
# https://github.com/hummingbot/hummingbot/blob/master/hummingbot/strategy/__utils__/trailing_indicators/trading_intensity.pyx

class 

# Avellaneda Stoikov:
# https://medium.com/hummingbot/a-comprehensive-guide-to-avellaneda-stoikovs-market-making-strategy-102d64bf5df6 
# https://stanford.edu/class/msande448/2018/Final/Reports/gr5.pdf

class AvellanedaStoikov:
    def __init__(self, s, q, sigma, gamma, k):
        self.s = s # current market mid price
        self.q = q # quantity of assets in inventory of base asset (could be positive/negative for long/short positions)
        self.sigma = sigma # market volatility
        self.gamma = gamma # inventory risk aversion parameter, small 0.01 = risk neutral, large 1 = risk averse
        self.k = k # order book liquidity parameter, log-linear regression
        # self.T = closing time, T is normalized = 1
        # self.t = current time, t is a time fraction
        
    def reservation_price(self):
        return self.s - self.q * self.gamma * self.sigma * self.sigma * (T - self.t)
    
    def optimal_bid_ask_spread(self):
        return self.gamma * self.sigma * self.sigma * (T - t) + (2/self.gamma) * self.log(1 + self.gamma / self.k)
    
    def optimal_bid(self):
        return self.reservation_price() - self.bid_ask_spread() / 2
       
    def optimal_ask(self):
        return self.reservation_price() + self.bid_ask_spread() / 2


 