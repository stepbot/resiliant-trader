##############################
    # Robinhood API based on https://github.com/Jamonek/Robinhood.git
##############################

import getpass
import requests

import numpy as np

class Robinhood:
    """wrapper class for fetching/parsing Robinhood endpoints"""
    endpoints = {
        "login": "https://api.robinhood.com/api-token-auth/",
        "logout": "https://api.robinhood.com/api-token-logout/",
        "investment_profile": "https://api.robinhood.com/user/investment_profile/",
        "accounts": "https://api.robinhood.com/accounts/",
        "ach_iav_auth": "https://api.robinhood.com/ach/iav/auth/",
        "ach_relationships": "https://api.robinhood.com/ach/relationships/",
        "ach_transfers": "https://api.robinhood.com/ach/transfers/",
        "applications": "https://api.robinhood.com/applications/",
        "dividends": "https://api.robinhood.com/dividends/",
        "edocuments": "https://api.robinhood.com/documents/",
        "instruments": "https://api.robinhood.com/instruments/",
        "margin_upgrades": "https://api.robinhood.com/margin/upgrades/",
        "markets": "https://api.robinhood.com/markets/",
        "notifications": "https://api.robinhood.com/notifications/",
        "orders": "https://api.robinhood.com/orders/",
        "password_reset": "https://api.robinhood.com/password_reset/request/",
        "portfolios": "https://api.robinhood.com/portfolios/",
        "positions": "https://api.robinhood.com/positions/",
        "quotes": "https://api.robinhood.com/quotes/",
        "historicals": "https://api.robinhood.com/quotes/historicals/",
        "document_requests": "https://api.robinhood.com/upload/document_requests/",
        "user": "https://api.robinhood.com/user/",
        "watchlists": "https://api.robinhood.com/watchlists/",
        "news": "https://api.robinhood.com/midlands/news/",
        "fundamentals": "https://api.robinhood.com/fundamentals/",
    }

    session = None

    username = None

    password = None

    headers = None

    auth_token = None

    ##############################
    #Logging in and initializing
    ##############################

    def __init__(self):
        self.session = requests.session()
        self.headers = {
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "en;q=1, fr;q=0.9, de;q=0.8, ja;q=0.7, nl;q=0.6, it;q=0.5",
            "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
            "X-Robinhood-API-Version": "1.0.0",
            "Connection": "keep-alive",
            "User-Agent": "Robinhood/823 (iPhone; iOS 7.1.2; Scale/2.00)"
        }
        self.session.headers = self.headers

    ##############################
    #GET DATA
    ##############################

    def get_historical_quote(
            self,
            stock,
            interval,
            span
        ):
        """fetch historical data for stock
        Note: valid interval/span configs
            interval = 5minute | 10minute + span = day, week
            interval = day + span = year
            interval = week
            TODO: NEEDS TESTS
        Args:
            stock (str): stock ticker
            interval (str): resolution of data
            span (str): length of data
        Returns:
            (:obj:`ndarray`) values returned from `historicals` endpoint
            columns: open_price, low_price, high_price, close_price, mean_price, volume
        """

        params = {
            'symbols': stock,
            'interval': interval,
            'span': span,
            'bounds': 'regular'
        }
        res = self.session.get(
            self.endpoints['historicals'],
            params=params
        )

        rawHistoricals = ((res.json()['results'])[0])['historicals']

        numpyHistoricals = np.zeros((len(rawHistoricals),6))

        ii = 0


        for bar in rawHistoricals:
            numpyHistoricals[ii,0] = float(bar['open_price'])
            numpyHistoricals[ii,1] = float(bar['low_price'])
            numpyHistoricals[ii,2] = float(bar['high_price'])
            numpyHistoricals[ii,3] = float(bar['close_price'])
            numpyHistoricals[ii,4] = (float(bar['open_price'])+float(bar['low_price'])+float(bar['high_price'])+float(bar['close_price']))/4
            numpyHistoricals[ii,5] = float(bar['volume'])
            ii = ii+1


        return numpyHistoricals
