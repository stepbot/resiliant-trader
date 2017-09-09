from flask import Flask
from flask import jsonify
from robinhood import Robinhood
import numpy as np
import math



app = Flask(__name__)
@app.route('/')
def index():

	rh = Robinhood()
	spyHist = rh.get_historical_quote('SPY','5minute','week')
	tltHist = rh.get_historical_quote('TLT','5minute','week')

	spyPrices = spyHist[:,4]
	spyVolumes = spyHist[:,5]

	tltPrices = tltHist[:,4]
	tltVolumes = tltHist[:,5]

	spyVWAP = np.average(spyPrices, axis=0, weights=spyVolumes)
	tltVWAP = np.average(tltPrices, axis=0, weights=tltVolumes)

	spyPricesNorm = spyPrices/spyVWAP
	tltPricesNorm = tltPrices/tltVWAP

	spyVolatility = np.std(spyPricesNorm)
	tltVolatility = np.std(tltPricesNorm)

	totalVolatility = spyVolatility+tltVolatility

	spyRawAllocation = 1-(spyVolatility/totalVolatility)
	spyAllocation = 1/(1+math.exp(-20*(spyRawAllocation-.5)))
	if spyAllocation > 1:
		spyAllocation = 1
	if spyAllocation < 0:
		spyAllocation = 0

	#return jsonify(spyVolumes.shape())
	return jsonify(spyAllocation)
	#return jsonify(sharesTraded)

if __name__ == "__main__":
	app.run()
