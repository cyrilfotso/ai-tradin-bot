#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Apr 22 07:33:20 2020

@author: cfo
"""
from datetime import datetime

PORTFOLIO_START_AMOUNT = 1000
TRADING_CYCLE_DURATION_MIN = 5


def get_most_changed(day=None, limit=5):
    """
    Goal: get for the day the stocks having change the most
    """
    if day is None:
        day = datetime.today()
    pass


def get_stock_data(stock_name, api_conf):
    """ 
    Goal: make api call to get stock details for analysis purpose
    """
    pass


def save_portfolio(day=None):
    """
    Goal: at the end of trading cycle | day, persist the portfolio detail into a json
    """
    if day is None:
        day = datetime.today()
    pass


def load_portfolio_data(day=None):
    """
    Goal: load the json saved portfolio of the day into a dict
    """
    if day is None:
        day = datetime.today()
    pass


def process_trading_logic():
    pass

