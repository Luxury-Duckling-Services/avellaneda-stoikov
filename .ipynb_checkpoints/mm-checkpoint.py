# !pip install backtrader
# !pip install yfinance --upgrade --no-cache-dir
# !pip install ipympl
# !pip install ipywidgets

import datetime
from model import volatility
from model import trading_intensity
from model import AvellanedaStoikov
import pandas as pd
import numpy as np

orderbook_df = pd.read_csv ('Data/historical_ETHUSDT_orderbook_data.csv')
kline_full_df = pd.read_csv('Data/historical_ETHUSDT_kline_data.csv')

kline_next_df = kline_full_df.copy()
kline_next_df['Datetime'] = kline_next_df['Datetime'].apply(lambda x: datetime.datetime.fromtimestamp(int(x) / 1000) )    

kline_reduced_array = []

for datetime in np.unique( kline_full_df['Datetime'].tolist() ):
    kline_reduced_array.append( kline_next_df[kline_full_df['Datetime'] == datetime].tail(1) )

kline_next_df = pd.concat(kline_reduced_array, axis=0)

kline_next_df.set_index('Datetime', inplace=True)

kline_next_df.head()

kline_next_df.tail()

kline_full_df.head()

orderbook_df.head()

# parameters to change

k_multiplier = 1000
risk_aversion = 0.1

import datetime
import backtrader as bt
import yfinance as yf

from backtrader import Order

def str_to_timestamp( s ):
    return int( datetime.datetime.strptime(s, '%Y-%m-%d %H:%M:%S').timestamp() * 1000 )

orderbook_timestamp = orderbook_df['Datetime'].tolist()

def smallest_timestamp_before( t ):
    for i in range(len(orderbook_timestamp)):
        if orderbook_timestamp[i] > t:
            return int(orderbook_timestamp[i-1])

def time_percentage( t ):
    start_time = kline_full_df.iloc[1]['Datetime']
    end_time = kline_full_df.iloc[-1]['Datetime']
    time_diff = end_time - start_time
    return (t - start_time ) /(end_time - start_time)

class MAstrategy(bt.Strategy):
    def __init__(self):
        self.orders = []

    def next(self):
        time = str_to_timestamp( str( self.datas[0].datetime.date() ) + " " + str( self.data.datetime.time() )   )  
        start_time = kline_full_df.iloc[1]['Datetime']
        end_time = kline_full_df.iloc[-1]['Datetime']
        
        if start_time >= time:
            return

        if end_time <= time:
            return
        
        ask_price_at_time = orderbook_df[orderbook_df["Datetime"] == smallest_timestamp_before(  time	)].iloc[0] ['askp0']
        bid_price_at_time = orderbook_df[orderbook_df["Datetime"] == smallest_timestamp_before(  time	)].iloc[0] ['bidp0']
        
        s = 0.5 * ( ask_price_at_time + bid_price_at_time )

        sigma = volatility(kline_full_df , time)

        k = trading_intensity(orderbook_df , time)

        eta = 0.005
        
        gamma = risk_aversion

        qt = self.position.size
        
        AS = AvellanedaStoikov(s, qt, sigma, gamma, k * k_multiplier , eta , 1 , time_percentage(time) )

        if k > 0 :
            for order in self.orders:
                self.broker.cancel(order)
            self.log('Buy Limit Create, %.2f' % AS.optimal_bid())
            order = self.buy(exectype=Order.Limit, price=AS.optimal_bid() , size=AS.bid_size(qt , self.stats.broker.value[0] * 0.5) )
            self.log('Sell Limit Create, %.2f' % AS.optimal_ask())
            order = self.sell(exectype=Order.Limit, price=AS.optimal_ask() , size=AS.bid_size(qt , self.stats.broker.value[0] * 0.5) )
            self.log('Account Value, %.2f' % self.stats.broker.value[0] )
 
	# outputting information
    def log(self, txt):
        dt = str( self.datas[0].datetime.date() ) + " " + str( self.data.datetime.time() )
        print('%s, %s' % (dt, txt))
    
    def notify_order(self, order):
        if order.status == order.Completed:
            if order.isbuy():
                self.log(
                "Executed Limit BUY (Price: %.2f, Value: %.2f, Commission %.2f)" %
                (order.executed.price, order.executed.value, order.executed.comm))
            else:
                self.log(
                "Executed Limit SELL (Price: %.2f, Value: %.2f, Commission %.2f)" %
                (order.executed.price, order.executed.value, order.executed.comm))
            self.bar_executed = len(self)
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log("Order was canceled/margin/rejected")

cerebro = bt.Cerebro()
cerebro.addstrategy(MAstrategy)
cerebro.broker.setcash(10000)
cerebro.broker.setcommission(commission=0.000 , leverage=10)
data = bt.feeds.PandasData(dataname=kline_next_df )
cerebro.adddata(data)
   
print('<START> Brokerage account: $%.2f' % cerebro.broker.getvalue())
cerebro.run()
print('<FINISH> Brokerage account: $%.2f' % cerebro.broker.getvalue())
%matplotlib inline
# Plot the strategy
img = cerebro.plot(style='candlestick',loc='grey', grid=False, iplot=False) #You can leave inside the paranthesis empty

img[0][0].savefig('Data/plot_k_multiplier{}_risk_aversion{}.png'.format(k_multiplier , risk_aversion))