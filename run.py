from robinhood import Robinhood
import numpy as np
import math
import os
import random
import time

try:
    import config
    rhuser = config.rhuser
    rhpass = config.rhpass
    print('using local config file')
except:
    print('using environment variable')
    rhuser = os.getenv('RHUSER')
    rhpass = os.getenv('RHPASS')

def run_gather_data():
  #code that gets and logs performance data
  print("Gathering Data")

def recommendInitialTarget(portfolioValue,spyAllocationPercentage,tltAllocationPercentage,spyBuyPrice,tltBuyPrice):
    spyTargetAllocation = spyAllocationPercentage*portfolioValue
    tltTargetAllocation = tltAllocationPercentage*portfolioValue
    spyTargetShares = math.floor(spyTargetAllocation/spyBuyPrice)
    tltTargetShares = math.floor(tltTargetAllocation/tltBuyPrice)
    return spyTargetShares,tltTargetShares

def recommendTarget(portfolioValue,spyAllocationPercentage,tltAllocationPercentage,spyBuyPrice,tltBuyPrice):
    allocationRatio = math.floor(spyAllocationPercentage/tltAllocationPercentage)
    tltTargetShares = math.floor(portfolioValue/(tltBuyPrice+(spyBuyPrice*allocationRatio)))
    spyTargetShares =math.floor(tltTargetShares*allocationRatio)
    return spyTargetShares,tltTargetShares

def targetTotalCost(spyTargetShares,tltTargetShares,spyBuyPrice,tltBuyPrice):
    targetPurchaseCost = (spyTargetShares*spyBuyPrice)+(tltTargetShares*tltBuyPrice)
    return targetPurchaseCost

def allocationPercentage(shares,cost,totalCost):
    percentage = (shares*cost)/totalCost
    return percentage

def allocationLoss(spyTarget,spyAchieved,tltTarget,tltAchieved):
    loss = math.sqrt((spyTarget-spyAchieved)**2+(tltTarget-tltAchieved)**2)
    return loss




def calcAlloc(rh):
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

	return spyAllocation

def run_trader():
    print("running trader")
    success = True

    rh = Robinhood()
    success = rh.marketOpenCheck()
    if not success:
        print('markets are closed')
    else:
        print('markets are open')

    if success:
        success = rh.login(username=rhuser, password=rhpass)

    if success:
        print('login succesful')
    else:
        print('login unsuccesful')


    if success:
        #exit extra postions
        openPositions = rh.securities_owned()['results']

        sellOrders = {}
        for position in openPositions:
            instrumentURL = position['instrument']
            positionTicker = rh.get_url(instrumentURL)['symbol']
            positionQuantity = position['quantity']
            if (positionTicker != 'SPY') and (positionTicker != 'TLT'):
                print('position in ', positionTicker, ' is not needed, selling')
                stock_instrument = rh.instruments(positionTicker)[0]
                sellOrders[positionTicker] = rh.place_immediate_market_order(instrumentURL,positionTicker,'gfd',positionQuantity,'sell')
        if sellOrders == {}:
            print('no extra positions found to close')
        else:
            print(sellOrders)

        orderOutcome = 'unresolved'

        while orderOutcome != 'resolved':
            remainingUnresolved = False
            for order in sellOrders:
                orderDetail = sellOrders[order]
                orderDetail['status'] = rh.check_order_status(orderDetail['url'])
                if orderDetail['status'] == 'unresolved':
                    remainingUnresolved = True
            if not remainingUnresolved:
                orderOutcome = 'resolved'
            else:
                print('remaining unresolved orders, waiting')
                time.sleep(60)


        for order in sellOrders:
            orderDetail = sellOrders[order]
            if orderDetail['status'] == 'failure':
                success = False

    if not success:
        print('unable to sell extra positions correctly')

    if success:
        #get portfolio current value
        portfolioValue = rh.equity()
        print('portfolioValue =', portfolioValue)

        #allocate portfolio
        spyAllocationPercentage = calcAlloc(rh)
        tltAllocationPercentage = 1-spyAllocationPercentage
        print('spyAllocationPercentage = ', spyAllocationPercentage)
        print('tltAllocationPercentage = ', tltAllocationPercentage)

        spyTargetAllocation = spyAllocationPercentage*portfolioValue
        tltTargetAllocation = tltAllocationPercentage*portfolioValue
        print('spyTargetAllocation = ', spyTargetAllocation)
        print('tltTargetAllocation = ', tltTargetAllocation)

        #get pricing data
        spyAskPrice = rh.ask_price('SPY')
        spyBidPrice = rh.bid_price('SPY')
        spyAvgCost = (spyAskPrice+spyBidPrice)/2
        spyBuyPrice = spyAskPrice+(spyAskPrice - spyBidPrice)
        spySellPrice = spyBidPrice-(spyAskPrice - spyBidPrice)
        print('spyAskPrice = ', spyAskPrice)
        print('spyBidPrice = ', spyBidPrice)

        tltAskPrice = rh.ask_price('TLT')
        tltBidPrice = rh.bid_price('TLT')
        tltAvgCost = (tltAskPrice+tltBidPrice)/2
        tltBuyPrice = tltAskPrice+(tltAskPrice - tltBidPrice)
        tltSellPrice = tltBidPrice-(tltAskPrice - tltBidPrice)
        print('tltAskPrice = ', tltAskPrice)
        print('tltBidPrice = ', tltBidPrice)

        #recommend position sizes
        [spyTargetShares,tltTargetShares] = recommendTarget(portfolioValue,spyAllocationPercentage,tltAllocationPercentage,spyBuyPrice,tltBuyPrice)

        print('spyTargetShares = ', spyTargetShares)
        print('tltTargetShares = ', tltTargetShares)

        targetPurchaseCost = targetTotalCost(spyTargetShares,tltTargetShares,spyBuyPrice,tltBuyPrice)


        spyTargetAllocationPercentage = allocationPercentage(spyTargetShares,spyBuyPrice,targetPurchaseCost)
        tltTargetAllocationPercentage = allocationPercentage(tltTargetShares,tltBuyPrice,targetPurchaseCost)
        print('spyTargetAllocationPercentage = ',spyTargetAllocationPercentage)
        print('tltTargetAllocationPercentage = ',tltTargetAllocationPercentage)

        targetLoss = allocationLoss(spyTargetAllocationPercentage,spyAllocationPercentage,tltTargetAllocationPercentage,tltAllocationPercentage)
        print('target loss = ',targetLoss)

        targetRemainingCash = portfolioValue-targetPurchaseCost
        print('targetPurchaseCost = ', targetPurchaseCost)
        print('targetRemainingCash = ', targetRemainingCash)

        #detemine required rebalancing
        spyRequired = spyTargetShares
        tltRequired = tltTargetShares
        for position in openPositions:
            instrumentURL = position['instrument']
            positionTicker = rh.get_url(instrumentURL)['symbol']
            positionQuantity = float(position['quantity'])
            if (positionTicker == 'SPY'):
                spyRequired = spyTargetShares-positionQuantity
            if (positionTicker == 'TLT'):
                tltRequired = tltTargetShares-positionQuantity

        print('spyRequired = ',spyRequired)
        print('tltRequired = ',tltRequired)

        spyInstrumentUrl = (rh.instruments('SPY')[0])['url']
        tltInstrumentUrl = (rh.instruments('TLT')[0])['url']

    if success:
        #sell positions
        if spyRequired < 0.0:
            print('selling ',-spyRequired,' of SPY')
            spySellOrder = rh.place_immediate_market_order(spyInstrumentUrl,'SPY','gfd',-spyRequired,'sell')
            print(spySellOrder)

            orderOutcome = 'unresolved'

            while orderOutcome != 'resolved':
                remainingUnresolved = False
                spySellOrder['status'] = rh.check_order_status(spySellOrder['url'])
                if orderResponse['status'] == 'unresolved':
                    remainingUnresolved = True
                if not remainingUnresolved:
                    orderOutcome = 'resolved'
                else:
                    print('remaining unresolved orders, waiting')
                    time.sleep(60)




            if spySellOrder['status'] == 'failure':
                success = False

    if not success:
        print('unable to sell required spy')

    if success:
        if tltRequired < 0.0:
            print('selling ',-tltRequired,' of TLT')
            tltSellOrder = rh.place_immediate_market_order(tltInstrumentUrl,'TLT','gfd',-tltRequired,'sell')
            print(tltSellOrder)

            orderOutcome = 'unresolved'

            while orderOutcome != 'resolved':
                remainingUnresolved = False
                tltSellOrder['status'] = rh.check_order_status(tltSellOrder['url'])
                if orderResponse['status'] == 'unresolved':
                    remainingUnresolved = True
                if not remainingUnresolved:
                    orderOutcome = 'resolved'
                else:
                    print('remaining unresolved orders, waiting')
                    time.sleep(60)



            if tltSellOrder['status'] == 'failure':
                success = False

    if not success:
        print('unable to sell required tlt')


    #buy positions
    if success:
        if spyRequired > 0.0:
            print('buying ',spyRequired,' of SPY')
            spyBuyOrder = rh.place_immediate_market_order(spyInstrumentUrl,'SPY','gfd',spyRequired,'sell',spyBuyPrice)
            print(spyBuyOrder)

            orderOutcome = 'unresolved'

            while orderOutcome != 'resolved':
                remainingUnresolved = False
                spyBuyOrder['status'] = rh.check_order_status(spyBuyOrder['url'])
                if orderResponse['status'] == 'unresolved':
                    remainingUnresolved = True
                if not remainingUnresolved:
                    orderOutcome = 'resolved'
                else:
                    print('remaining unresolved orders, waiting')
                    time.sleep(60)



            if spyBuyOrder['status'] == 'failure':
                success = False
    if not success:
        print('unable to buy required spy')

    if success:
        if tltRequired > 0.0:
            print('buying ',tltRequired,' of TLT')
            tltBuyOrder = rh.place_immediate_market_order(tltInstrumentUrl,'TLT','gfd',tltRequired,'sell',tltBuyPrice)
            print(tltBuyOrder)

            orderOutcome = 'unresolved'

            while orderOutcome != 'resolved':
                remainingUnresolved = False
                tltBuyOrder['status'] = rh.check_order_status(tltBuyOrder['url'])
                if orderResponse['status'] == 'unresolved':
                    remainingUnresolved = True
                if not remainingUnresolved:
                    orderOutcome = 'resolved'
                else:
                    print('remaining unresolved orders, waiting')
                    time.sleep(60)



            if tltBuyOrder['status'] == 'failure':
                success = False

    if not success:
        print('unable to buy required tlt')

    if success:
        success = rh.logout()
    if not success:
        print('unable to logout')
    else:
        print('succesfully logged out')
