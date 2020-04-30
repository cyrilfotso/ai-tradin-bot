#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Apr 25 03:41:13 2020

@author: cfo
"""

# https://www.alphavantage.co/support/#api-key

import time
import logging
import logging.handlers
from yahoo_fin import stock_info as si
from alpha_vantage import timeseries as tsi
import matplotlib.pyplot as plt
from datetime import datetime
from news_reader import process_prediction



log_file = './logs/app.log'
my_logger = logging.getLogger('MyLogger')
my_logger.setLevel(logging.DEBUG)
# Add the log message handler to the logger
handler = logging.handlers.RotatingFileHandler(log_file)

# create formatter
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt='%d-%b-%y %H:%M:%S')
# add formatter to ch
handler.setFormatter(formatter)

my_logger.addHandler(handler)


initial_cash = 10000
n_pick = 5
api_key = 'M732SN6UCXRGLSYM'
api_wait_time = 80

stock_signals = {'buy': {}, 'sell': {}}
market_actions = {'buy': [], 'sell': []}

today = datetime.today()

market_start_time = str(datetime(year=today.year, month=today.month, day=today.day, hour=9, minute=30))
market_end_time = str(datetime(year=today.year, month=today.month, day=today.day, hour=15, minute=30))

market_start_time = '2020-04-30 00:00:00'

market_end_time = '2020-04-30 13:00:00'


def get_day_stocks(limit=5):
    """
    Goal: Get the stock of the day, 
    This will return the top <limit> stock in term of % change
    having they price less than half the max starting price
    """
    b = si.get_day_gainers()
    b = b.sort_values(by='% Change', ascending=False)
    b = b[b['Price (Intraday)'] <= initial_cash/2]
    b = b[:n_pick]
    list_stocks = b.to_dict('records')
    
    return list_stocks


def get_stock_updated_data(symbol, portfolio):
    """
    Goal: get the real time details on a stock using his symbol
    """
    stock_data = {}
    live_price = si.get_live_price(symbol)
    for i in range(len(portfolio['positions'])):
        if portfolio['positions'][i]['Symbol'] == symbol:
            stock_data = portfolio['positions'][i]
            stock_data['Price (Intraday)'] = live_price
    
    return stock_data


def buy_stocks(list_stocks, cash=initial_cash):
    """
    Goal: buy parts of the stocks selected with the cash
    """
    list_prices = [item['Price (Intraday)'] for item in list_stocks]
    min_price = min(list_prices)
    
    while cash >= min_price:
        for i in range(len(list_stocks)):
            if cash >= list_stocks[i]['Price (Intraday)']:
                if 'nbr_part' in list_stocks[i]:
                    list_stocks[i]['nbr_part'] += 1
                else:
                    list_stocks[i]['nbr_part'] = 1
                
                cash -= list_stocks[i]['Price (Intraday)']
    
    portfolio = {'cash': cash, 'positions': list_stocks, 'buy': [], 'sell': [], 'value':{}}
    my_logger.info('portfolio {}'.format(portfolio))
    return portfolio



def buy_specific_stock(portfolio, stock_data):
    """
    Goal: during the day, we may have to buy more part of a specific stock
    """
    cash = portfolio['cash']
    min_price = stock_data['Price (Intraday)']
    while cash >= min_price:
        if cash >= min_price:
            if 'nbr_part' in stock_data:
                stock_data['nbr_part'] += 1
            else:
                stock_data['nbr_part'] = 1
            
            cash -= min_price
    
    portfolio['cash'] = cash
    
    for i in range(len(portfolio['positions'])):
        if portfolio['positions'][i]['Symbol'] == stock_data['Symbol']:
            portfolio['positions'][i]['Price (Intraday)'] = min_price
            portfolio['positions'][i]['nbr_part'] = stock_data['nbr_part']
    
    
    market_actions['buy'].append(stock_data)    
    my_logger.info('buy {}'.format(stock_data))
    my_logger.info('portfolio {}'.format(portfolio))
    
    return portfolio
    


def sel_specific_stock(portfolio, stock_data):
    """
    Goal: during the day, we may have to buy more part of a specific stock
    """
    sell_price = stock_data['Price (Intraday)']
    
    for i in range(len(portfolio['positions'])):
        if portfolio['positions'][i]['Symbol'] == stock_data['Symbol']:
            stock_data['nbr_part'] = portfolio['positions'][i]['nbr_part']
            stock_data['buy_price'] = portfolio['positions'][i]['Price (Intraday)']
            stock_data['sell_price'] = sell_price
            
            portfolio['cash'] += portfolio['positions'][i]['nbr_part']*sell_price
            
            portfolio['positions'][i]['Price (Intraday)'] = sell_price
            portfolio['positions'][i]['nbr_part'] = 0
    
    market_actions['sell'].append(stock_data)
    return portfolio


def process_portfolio_value(portfolio):
    """
    Goal: evaluate the total value of a portfolio at a certain time
    """
    actions_value = 0
    for item in portfolio['positions']:
        actions_value += item['nbr_part']*item['Price (Intraday)']
        
    total_value = actions_value + portfolio['cash']
    
    portfolio['value'] = {'total_value': total_value, 'cash': portfolio['cash'], 'actions_value': actions_value}
    return portfolio
    

def get_nlp_prediction(symbol):
    """
    Goal: process the real time nlp prediction on the stock symbol movement (up or down)
    We already have the model trained, so we will just call the helper to get updated headers 
    then process the prediction  
    Will return :
        1: if the stock is predicted to go up
        0: if the stock is predicted to go down
    """
    predict = process_prediction(symbol)
    return predict[0]


def run_strategy(portfolio, nlp_enabled=True):
    """
    Goal: run our strategy at a trading moment
    """    
    for item in portfolio['positions']:
        symbol = item['Symbol']
        print('stock: ', symbol)
        try:
            ts = tsi.TimeSeries(key=api_key, output_format='pandas')
            data, meta_data = ts.get_intraday(symbol=symbol,interval='1min', outputsize='full')
            data = data[data.index >= market_start_time]
            # plots
            if len(data) > 0:
                plt.figure()
                data['4. close'].plot()
                plt.title('Intraday Times Series for the {} stock (1 min)'.format(symbol))
                plt.show()
                        
            # Generate moving averages
            data = data.reindex(index=data.index[::-1]) # Reverse for the moving average computation
            data['Mavg5'] = data['4. close'].rolling(window=5).mean()
            data['Mavg20'] = data['4. close'].rolling(window=20).mean()
            
            # Save moving averages for the day before
            prev_short_mavg = data['Mavg5'].shift(1)
            prev_long_mavg = data['Mavg20'].shift(1)
            
            # Select buying and selling signals: where moving averages cross
            buys = data.ix[(data['Mavg5'] <= data['Mavg20']) & (prev_short_mavg >= prev_long_mavg)]
            buys['key'] = buys.index
            sells = data.ix[(data['Mavg5'] >= data['Mavg20']) & (prev_short_mavg <= prev_long_mavg)]
            sells['key'] = sells.index
            
            # decide to sell or buy
            # 1- sellprocess
            sells_actions = sells.to_dict('records')
            for action in sells_actions:
                key = str(action['key'])+'_'+symbol
                if key in stock_signals['sell']:
                    pass
                else:
                    stock_data = get_stock_updated_data(symbol, portfolio)
                    if nlp_enabled:
                        prediton_value = get_nlp_prediction(symbol)
                        if prediton_value == 0:
                            portfolio = sel_specific_stock(portfolio, stock_data)
                        else:
                            lod_data = 'skipp selling because prediction value for {} is {}: going lower'.format(symbol, prediton_value)
                            my_logger.info(lod_data)
                    else: # nlp not enabled
                        portfolio = sel_specific_stock(portfolio, stock_data)
                    
                    stock_signals['sell'][key] = {'action': True, 'date': str(datetime.now())}
                    
            
            # 2- buy process
            buys_actions = buys.to_dict('records')
            for action in buys_actions:
                key = str(action['key'])+'_'+symbol
                if key in stock_signals['buy']:
                    pass
                else:
                    stock_data = get_stock_updated_data(symbol, portfolio)
                    if nlp_enabled:
                        prediton_value = get_nlp_prediction(symbol)
                        if prediton_value == 1:
                            portfolio = buy_specific_stock(portfolio, stock_data)
                        else:
                            lod_data = 'skipp buying because prediction value for {} is {}: going lower'.format(symbol, prediton_value)                        
                            my_logger.info(lod_data)
                    else: # nlp disabled
                        portfolio = buy_specific_stock(portfolio, stock_data)
                        
                    stock_signals['buy'][key] = {'action': True, 'date': str(datetime.now())}
            
            # plot for that trading moment
            # The label parameter is useful for the legend
            plt.plot(data.index, data['4. close'], label='E-Mini future price')
            plt.plot(data.index, data['Mavg5'], label='5-steps moving average')
            plt.plot(data.index, data['Mavg20'], label='20-steps moving average')
            
            
            plt.plot(buys.index, data.ix[buys.index]['4. close'], '^', markersize=10, color='g')
            plt.plot(sells.index, data.ix[sells.index]['4. close'], 'v', markersize=10, color='r')
            
            plt.ylabel('E-Mini future price {}'.format(symbol))
            plt.xlabel('Date')
            plt.legend(loc=0)
            plt.show()
            time.sleep(1)
        except Exception as e:
            print('error on stock: ', symbol, str(e))
            
    return portfolio



if __name__ == "__main__":
    day_list_stocks = get_day_stocks()
    portfolio = buy_stocks(day_list_stocks)
    portfolio = process_portfolio_value(portfolio)
    current_time = str(datetime.now())

    while current_time <= market_end_time:
        portfolio = run_strategy(portfolio, nlp_enabled=True)
        portfolio = process_portfolio_value(portfolio)
        my_logger.info('datetime: {}, protfolio data: {}'.format(datetime.now(), portfolio['value']))        
        time.sleep(api_wait_time)
        current_time = str(datetime.now())
#        break
    










