from flask import Flask
from flask import jsonify
from robinhood import Robinhood


import numpy as np

app = Flask(__name__)
@app.route('/')
def index():

	#Setup
	ses = requests.session()
	ses.headers = {
		"Accept": "*/*",
		"Accept-Encoding": "gzip, deflate",
		"Accept-Language": "en;q=1, fr;q=0.9, de;q=0.8, ja;q=0.7, nl;q=0.6, it;q=0.5",
		"Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
		"X-Robinhood-API-Version": "1.0.0",
		"Connection": "keep-alive",
		"User-Agent": "Robinhood/823 (iPhone; iOS 7.1.2; Scale/2.00)"
	}

	url = "https://api.robinhood.com/quotes/historicals/"
	stock = 'SPY'
	interval = '5minute'
	span = 'week'
	bounds = 'regular'

	params = {
		'symbols': stock,
		'interval': interval,
		'span': span,
		'bounds': bounds
	}

	res = ses.get(url,params=params)

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


	#Get a stock's quote
	return jsonify(numpyHistoricals.tolist())

if __name__ == "__main__":
	app.run()
