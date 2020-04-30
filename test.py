#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Apr 27 22:26:04 2020

@author: c106763
"""

# https://www.alphavantage.co/support/#api-key

import logging
from yahoo_fin import stock_info as stock
from alpha_vantage import timeseries as tsi
import matplotlib.pyplot as plt
import pandas as pd




max_price = 10000
n_pick = 5
api_key = 'M732SN6UCXRGLSYM'

market_start_time = '9:30AM'
market_start_time = '3:30PM'

b = stock.get_day_gainers()
b = b.sort_values(by='% Change', ascending=False)
b = b[b['Price (Intraday)'] <= max_price/2]
b = b[:n_pick]

list_stocks = b.to_dict('records')


# strategy to sell
# when the stock have moved up to his previous average: sell signal

# strategy to buy
# pick the 5 stocks that has most changed and having price less than thecash available in portfolio



# trading Strategy
# The goal here is to be able to find the sell and buy signals during the day


ts = tsi.TimeSeries(key=api_key, output_format='pandas')
data, meta_data = ts.get_intraday(symbol='MSFT',interval='1min', outputsize='full')
data = data[data.index >= '2020-04-29 00:00:00']
data['4. close'].plot()
plt.title('Intraday Times Series for the MSFT stock (1 min)')
plt.show()
data.to_csv('./data/msft_day.csv', sep=',')


## Generate moving averages
data_msft = pd.DataFrame.from_csv(path='./data/msft_day.csv', sep=',')
data_msft = data_msft.reindex(index=data_msft.index[::-1]) # Reverse for the moving average computation
data_msft['Mavg5'] = data_msft['4. close'].rolling(window=5).mean()
data_msft['Mavg20'] = data_msft['4. close'].rolling(window=20).mean()

# Save moving averages for the day before
prev_short_mavg = data_msft['Mavg5'].shift(1)
prev_long_mavg = data_msft['Mavg20'].shift(1)
 
# Select buying and selling signals: where moving averages cross
buys = data_msft.ix[(data_msft['Mavg5'] <= data_msft['Mavg20']) & (prev_short_mavg >= prev_long_mavg)]
sells = data_msft.ix[(data_msft['Mavg5'] >= data_msft['Mavg20']) & (prev_short_mavg <= prev_long_mavg)]


# The label parameter is useful for the legend
plt.plot(data_msft.index, data_msft['4. close'], label='E-Mini future price')
plt.plot(data_msft.index, data_msft['Mavg5'], label='5-steps moving average')
plt.plot(data_msft.index, data_msft['Mavg20'], label='20-steps moving average')


plt.plot(buys.index, data_msft.ix[buys.index]['4. close'], '^', markersize=10, color='g')
plt.plot(sells.index, data_msft.ix[sells.index]['4. close'], 'v', markersize=10, color='r')


plt.ylabel('E-Mini future price')
plt.xlabel('Date')
plt.legend(loc=0)
plt.show()











