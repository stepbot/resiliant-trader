from flask import Flask
from flask import jsonify

import pip
import requests

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
	stock = 'AAPL'
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

	#Get a stock's quote
	return res.json()

if __name__ == "__main__":
	app.run()
