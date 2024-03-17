# !pip install binance-connector
# !pip install binance-futures-connector

# https://binance-docs.github.io/apidocs/futures/en/#how-to-manage-a-local-order-book-correctly
# https://github.com/binance/binance-futures-connector-python/blob/main/examples/websocket/um_futures/partial_book_depth.py
# https://github.com/binance/binance-futures-connector-python/blob/main/binance/websocket/um_futures/websocket_client.py

import time
import logging
from binance.lib.utils import config_logging
from binance.websocket.um_futures.websocket_client import UMFuturesWebsocketClient

import json
import csv

config_logging(logging, logging.DEBUG)

with open('historical_ETHUSDT_orderbook_data.csv', 'w') as orderbook:
    writer = csv.writer(orderbook)
    writer.writerow(["Datetime"] + ["bidp" + str(i) for i in range(10)] + ["askp" + str(i) for i in range(10)] + ["bidv" + str(i) for i in range(10)] + ["askv" + str(i) for i in range(10)])

with open('historical_ETHUSDT_kline_data.csv', 'w') as kline:
    writer = csv.writer(kline)
    writer.writerow(["Datetime","Open","High","Low","Close","Volume"])

def message_handler(_,message):
    d = json.loads(message)
    
    f = open("raw_message.txt", "a")
    f.write(message)
    f.write('\n')
    f.close()

    if 'e' in d:
        if d['e'] == 'depthUpdate':
            with open('historical_ETHUSDT_orderbook_data.csv', 'a') as orderbook:
                writer = csv.writer(orderbook)

                data = [ 0 for i in range(41)]
                data[0] = d['T']
                
                for i in range(1 , 11):
                    data[i] = d['b'][i - 1][0]
                    data[i + 10] = d['a'][i - 1][0]
                    data[i + 20] = d['b'][i - 1][1]
                    data[i + 30] = d['a'][i - 1][1]
                
                writer.writerow( data )
        elif d['e'] == "continuous_kline":
            with open('historical_ETHUSDT_kline_data.csv', 'a') as kline:
                writer = csv.writer(kline)
                writer.writerow( [ d['k']['t'] , d['k']['o'] , d['k']['h'] , d['k']['l'] , d['k']['c'] , d['k']['v'] ])

my_client = UMFuturesWebsocketClient(on_message=message_handler)

my_client.partial_book_depth(symbol="ethusdt",level=10,speed=100)
my_client.continuous_kline(pair="ethusdt", contractType="perpetual", interval="1m")
#my_client.kline(symbol="ethusdt", interval="1m")

t = 24 * 60 * 60 + 1

time.sleep(t)

logging.debug("closing ws connection")
my_client.stop()