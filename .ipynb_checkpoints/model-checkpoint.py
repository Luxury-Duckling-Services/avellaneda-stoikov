# https://github.com/keanekwa/Optiver-Ready-Trader-Go/blob/main/ASModel.py

# https://medium.com/@degensugarboo/avellaneda-and-stoikov-mm-paper-implementation-b7011b5a7532

# https://math.nyu.edu/~avellane/HighFrequencyTrading.pdf

# https://quant.stackexchange.com/questions/69407/orderbook-liquidity-parameter-avellaneda-stoikov

# https://arxiv.org/pdf/1105.3115.pdf

# https://github.com/hummingbot/hummingbot/tree/master/hummingbot/strategy/avellaneda_market_making

# https://hummingbot.org/strategies/avellaneda-market-making/

import math
import numpy as np
from sklearn.linear_model import LinearRegression

# Instant Volatility
# https://github.com/hummingbot/hummingbot/blob/master/hummingbot/strategy/__utils__/trailing_indicators/instant_volatility.py

def volatility(kline_df , time):
    sampling_buffer = kline_df[kline_df['Datetime'] == time]['Close'].to_numpy()
    vol = np.sqrt(np.sum(np.square(np.diff( sampling_buffer ))) / sampling_buffer.size)
    return vol

# Trading intensity
# https://github.com/hummingbot/hummingbot/blob/master/hummingbot/strategy/__utils__/trailing_indicators/trading_intensity.pyx

def trading_intensity(orderbook_df , time):
    end_time = time
    start_time = time - 60000 # 60000 = 1min, 1000 = 1sec
    
    sampling_df = orderbook_df[ ( orderbook_df['Datetime']>= start_time ) & ( orderbook_df['Datetime'] <= end_time ) ].reset_index()
    
    ask_order_price_trading_intensity = []
    bid_order_price_trading_intensity = []
    
    sampling_df = sampling_df[['Datetime','bidp0','askp0']]
    
    for index , row in sampling_df.iterrows():
        if index == 0:
            new_ask_order_indexes = []
            new_ask_order_datetimes = []
            new_ask_order_prices = []
            
            new_bid_order_indexes = []
            new_bid_order_datetimes = []
            new_bid_order_prices = []
            
            continue
            
        # collect ask orders
            
        while len(new_ask_order_prices) > 0:
            if sampling_df.loc[index]['askp0'] > new_ask_order_prices[-1]:
                ask_order_price_trading_intensity.append( [ 
                    ( sampling_df.loc[index]['Datetime'] - new_ask_order_datetimes[-1]) / 1000 ,
                    ( new_ask_order_prices[-1] - 0.5 * ( sampling_df.loc[ new_ask_order_indexes[-1] ]['bidp0'] 
                           + sampling_df.loc[ new_ask_order_indexes[-1] ]['askp0'] ) )
                ] )
                new_ask_order_indexes.pop()
                new_ask_order_datetimes.pop()
                new_ask_order_prices.pop()
            else:
                break
        
        if sampling_df.loc[index]['askp0'] < sampling_df.loc[index - 1]['askp0']:    
            new_ask_order_indexes.append( index )
            new_ask_order_datetimes.append( int( sampling_df.loc[index]['Datetime'] ) )
            new_ask_order_prices.append( sampling_df.loc[index]['askp0'] )
        
        # collect bid orders           
                
        while len(new_bid_order_prices) > 0:
            if sampling_df.loc[index]['bidp0'] < new_bid_order_prices[-1]:
                bid_order_price_trading_intensity.append( [
                    ( sampling_df.loc[index]['Datetime'] - new_bid_order_datetimes[-1] ) / 1000,
                    ( 0.5 * ( sampling_df.loc[ new_bid_order_indexes[-1] ]['bidp0'] 
                           + sampling_df.loc[ new_bid_order_indexes[-1] ]['askp0'] ) - new_bid_order_prices[-1])
                ] )
                new_bid_order_indexes.pop()
                new_bid_order_datetimes.pop()
                new_bid_order_prices.pop()
            else:
                break
        
        if sampling_df.loc[index]['bidp0'] > sampling_df.loc[index - 1]['bidp0']:        
            new_bid_order_indexes.append( index )
            new_bid_order_datetimes.append( int( sampling_df.loc[index]['Datetime'] ) )
            new_bid_order_prices.append( sampling_df.loc[index]['bidp0'] )
        
    delta = np.array( bid_order_price_trading_intensity + ask_order_price_trading_intensity) 
    delta_S = delta[:, 0].reshape(-1, 1)
    delta_t = np.log( delta[:, 1] )
        
    regr = LinearRegression()
    regr.fit(delta_S, delta_t)
    
    return regr.coef_[0]

# Avellaneda Stoikov:
# https://medium.com/hummingbot/a-comprehensive-guide-to-avellaneda-stoikovs-market-making-strategy-102d64bf5df6 
# https://stanford.edu/class/msande448/2018/Final/Reports/gr5.pdf

class AvellanedaStoikov:
    def __init__(self, s, q, sigma, gamma, k , eta , T , t):
        self.s = s # current market mid price
        self.q = q # quantity of assets in inventory of base asset (could be positive/negative for long/short positions)
        self.sigma = sigma # market volatility
        self.gamma = gamma # inventory risk aversion parameter, small 0.01 = risk neutral, large 1 = risk averse
        self.k = k # order book liquidity parameter, log-linear regression
        self.T = T # closing time, T is normalized = 1
        self.t = t # current time, t is a time fraction
        self.eta = eta # shape parameter for order size
        
    def reservation_price(self):
        return self.s - self.q * self.gamma * self.sigma * self.sigma * (self.T - self.t)
    
    def optimal_bid_ask_spread(self):
        return self.gamma * self.sigma * self.sigma * (self.T - self.t) + (2/self.gamma) * np.log(1 + self.gamma / self.k)
    
    def optimal_bid(self):
        return self.reservation_price() - self.optimal_bid_ask_spread() / 2
       
    def optimal_ask(self):
        return self.reservation_price() + self.optimal_bid_ask_spread() / 2

    def bid_size(self, qt, cash):
        if qt < 0:
            return cash / self.optimal_bid()
        elif qt > 0:
            return ( cash / self.optimal_bid() ) * np.exp(-self.eta * qt)

    def ask_size(self, qt , cash):
        if qt > 0:
            return cash / self.optimal_ask()
        elif qt < 0:
            return ( cash / self.optimal_ask() ) * np.exp(-self.eta * qt)