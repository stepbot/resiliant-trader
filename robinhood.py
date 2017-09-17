##############################
    # Robinhood API based on https://github.com/Jamonek/Robinhood.git
    # refence available at https://github.com/sanko/Robinhood.git
##############################

import getpass
import requests
from datetime import datetime

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

    def login_prompt(self): #pragma: no cover
        """Prompts user for username and password and calls login()."""
        username = input("Username: ")
        password = getpass.getpass()
        return self.login(username=username, password=password)

    def login(
            self,
            username,
            password,
            mfa_code=None
        ):
        """save and test login info for Robinhood accounts
        Args:
            username (str): username
            password (str): password
        Returns:
            (bool): received valid auth token
        """
        self.username = username
        self.password = password
        payload = {
            'password': self.password,
            'username': self.username
        }

        if mfa_code:
            payload['mfa_code'] = mfa_code

        try:
            res = self.session.post(
                self.endpoints['login'],
                data=payload
            )
            res.raise_for_status()
            data = res.json()
        except requests.exceptions.HTTPError:
            raise RH_exception.LoginFailed()

        if 'mfa_required' in data.keys():           #pragma: no cover
            raise RH_exception.TwoFactorRequired()  #requires a second call to enable 2FA

        if 'token' in data.keys():
            self.auth_token = data['token']
            self.headers['Authorization'] = 'Token ' + self.auth_token
            return True

        return False

    def logout(self):
        """logout from Robinhood
        Returns:
            (:obj:`requests.request`) result from logout endpoint
        """
        flag = False
        try:
            req = self.session.post(self.endpoints['logout'])
            req.raise_for_status()

        except requests.exceptions.HTTPError as err_msg:
            warnings.warn('Failed to log out ' + repr(err_msg))

        self.headers['Authorization'] = None
        self.auth_token = None

        if req.status_code == 200:
            flag = True

        return flag

    ##############################
    #GET DATA
    ##############################
    def marketOpenCheck(self):
        canTrade = True
        now = datetime.utcnow()

        url = self.endpoints['markets']
        marketData = (self.get_url(url)['results'])
        for market in marketData:
            marketTimeData = self.get_url(market['todays_hours'])
            status = marketTimeData['is_open']
            if status == 'false':
                canTrade = False
            else:
                openTime = marketTimeData['opens_at']
                openTimeObject = datetime.strptime(openTime,'%Y-%m-%dT%H:%M:%SZ')
                closeTime = marketTimeData['closes_at']
                closeTimeObject= datetime.strptime(closeTime,'%Y-%m-%dT%H:%M:%SZ')
            if now < openTimeObject:
                canTrade = False
            if now > closeTimeObject:
                canTrade = False
        return canTrade



    def instruments(self, stock):
        """fetch instruments endpoint
        Args:
            stock (str): stock ticker
        Returns:
            (:obj:`dict`): JSON contents from `instruments` endpoint
        """
        res = self.session.get(
            self.endpoints['instruments'],
            params={'query': stock.upper()}
        )
        res.raise_for_status()
        res = res.json()

        # if requesting all, return entire object so may paginate with ['next']
        if (stock == ""):
            return res

        return res['results']

    def get_url(self, url):
        """flat wrapper for fetching URL directly"""
        return self.session.get(url).json()

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

    def quote_data(self, stock=''):
        """fetch stock quote
        Args:
            stock (str): stock ticker, prompt if blank
        Returns:
            (:obj:`dict`): JSON contents from `quotes` endpoint
        """
        url = None
        if stock.find(',') == -1:
            url = str(self.endpoints['quotes']) + str(stock) + "/"
        else:
            url = str(self.endpoints['quotes']) + "?symbols=" + str(stock)
        #Check for validity of symbol
        try:
            req = requests.get(url)
            req.raise_for_status()
            data = req.json()
        except requests.exceptions.HTTPError:
            raise NameError('Invalid Symbol: ' + stock) #TODO: custom exception

        return data



    def ask_price(self, stock=''):
        """get asking price for a stock
        Note:
            queries `quote` endpoint, dict wrapper
        Args:
            stock (str): stock ticker
        Returns:
            (float): ask price
        """
        data = self.quote_data(stock)
        return float(data['ask_price'])

    def bid_price(self, stock=''):
        """get bid price for a stock
        Note:
            queries `quote` endpoint, dict wrapper
        Args:
            stock (str): stock ticker
        Returns:
            (float): bid price
        """
        data = self.quote_data(stock)
        return float(data['bid_price'])

    def get_account(self):
        """fetch account information
        Returns:
            (:obj:`dict`): `accounts` endpoint payload
        """
        res = self.session.get(self.endpoints['accounts'])
        res.raise_for_status()  #auth required
        res = res.json()
        return res['results'][0]

    ##############################
    # PORTFOLIOS DATA
    ##############################

    def portfolios(self):
        """Returns the user's portfolio data."""
        req = self.session.get(self.endpoints['portfolios'])
        req.raise_for_status()
        return req.json()['results'][0]

    def adjusted_equity_previous_close(self):
        """wrapper for portfolios
        get `adjusted_equity_previous_close` value
        """
        return float(self.portfolios()['adjusted_equity_previous_close'])

    def equity(self):
        """wrapper for portfolios
        get `equity` value
        """
        return float(self.portfolios()['equity'])

    ##############################
    # POSITIONS DATA
    ##############################

    def securities_owned(self):
        """
        Returns a list of symbols of securities of which there are more
        than zero shares in user's portfolio.
        """
        return self.session.get(self.endpoints['positions']+'?nonzero=true').json()

    ##############################
    #PLACE ORDER
    ##############################

    def check_order_status(self,url):
        orderOutcomeDictionary = {
            'queued':'unresolved',
            'unconfirmed':'unresolved',
            'confirmed':'unresolved',
            'partially_filled':'unresolved',
            'filled':'success',
            'rejected':'failure',
            'canceled':'failure',
            'failed':'failure'
        }
        orderResponse = self.get_url(url)
        return orderOutcomeDictionary[orderResponse['state']]




    def place_immediate_market_order(self,instrument,symbol,time_in_force,quantity,side,price=0.0):
        payload = {
            'account': self.get_account()['url'],
            'instrument': instrument,
            'quantity': quantity,
            'side': side,
            'symbol': symbol,
            'time_in_force': time_in_force,
            'trigger': 'immediate',
            'type': 'market'
        }
        if side == 'buy':
            payload['price']=price
        res = self.session.post(
            self.endpoints['orders'],
            data=payload
        )

        return res.json()
