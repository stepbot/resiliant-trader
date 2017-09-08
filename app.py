from flask import Flask
from flask import jsonify

import pip
import Robinhood

app = Flask(__name__)
@app.route('/')
def index():

	#Setup
	my_trader = Robinhood.Robinhood()

	#Get a stock's quote
	return jsonify(my_trader.quote_data("AAPL"))

if __name__ == "__main__":
	app.run()
