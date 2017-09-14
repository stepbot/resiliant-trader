from robinhood import Robinhood
import numpy as np
import math
import os
import random
import time
import smtplib
import datetime
from pymongo import MongoClient
import quandl


try:
    import config
    print('using local config file')
    rhuser = config.rhuser
    rhpass = config.rhpass
    guser = config.guser
    gpass = config.gpass
    mongodb_uri = config.mongodb_uri
    quandl_key = config.quandl_key
except:
    print('using environment variable')
    rhuser = os.getenv('RHUSER')
    rhpass = os.getenv('RHPASS')
    guser = os.getenv('GUSER')
    gpass = os.getenv('GPASS')
    mongodb_uri = os.getenv('MONGODB_URI')
    quandl_key = os.getenv('QUANDL_KEY')

#from https://stackoverflow.com/questions/865618/how-can-i-perform-divison-on-a-datetime-timedelta-in-python

def divtd(td1, td2):
    us1 = td1.microseconds + 1000000 * (td1.seconds + 86400 * td1.days)
    us2 = td2.microseconds + 1000000 * (td2.seconds + 86400 * td2.days)
    return float(us1) / us2

def run_gather_data():
    #code that gets and logs performance data
    print("Gathering Data")
    success = True

    rh = Robinhood()
    now = datetime.datetime.utcnow()
    try:
        success = rh.marketOpenCheck()
        if not success:
            print('markets are closed')
            success = True
        else:
            print('markets are open')
    except Exception as e:
        print('rh market check error ', str(e))
        success = False

    if success:
        try:
            success = rh.login(username=rhuser, password=rhpass)
            if success:
                print('robinhood login succesful')
            else:
                print('robinhood login unsuccesful')
        except Exception as e:
            print('rh login error ', str(e))
            success = False



    if success:
        try:
            client = MongoClient(mongodb_uri)
            db = client.get_database()
        except Exception as e:
            print('mongo login error ', str(e))
            success = False

    if success:
        try:
            #get pricing data
            spyAskPrice = rh.ask_price('SPY')
            spyBidPrice = rh.bid_price('SPY')
            spyAvgCost = (spyAskPrice+spyBidPrice)/2
            print('spyAvgCost = ', spyAvgCost)

            tltAskPrice = rh.ask_price('TLT')
            tltBidPrice = rh.bid_price('TLT')
            tltAvgCost = (tltAskPrice+tltBidPrice)/2
            print('tltAvgCost = ', tltAvgCost)
        except Exception as e:
            print('etf price error ', str(e))
            success = False

    if success:
        try:
            #get portfolioValue
            portfolioValue = rh.equity()
            print('portfolioValue =', portfolioValue)
        except Exception as e:
            print('portfolio value error ', str(e))
            success = False

    if success:
        try:
            #get treasury risk free rate
            quandl.ApiConfig.api_key = quandl_key
            riskFree = (quandl.get("USTREASURY/BILLRATES.3", rows=1,returns='numpy')[0])[1]
            print('riskFree =', riskFree)
        except Exception as e:
            print('risk free error ', str(e))
            success = False

    if success:
        try:
            #get last data
            lastData = db.rawPrices.find_one(sort=[("timestamp", -1)])
            lastTimestamp = lastData['timestamp']
            lastSpy = lastData['spy']
            lastTlt = lastData['tlt']
            lastPortfolio = lastData['portfolio']
            lastRiskFree = lastData['annualized90day']
        except Exception as e:
            print('error getting previous data ', str(e))
            success = False

    if success:
        try:
            # calculate percentage changes
            spyChange = (spyAvgCost-lastSpy)/lastSpy
            print('spyChange = ',spyChange)
            tltChange = (tltAvgCost-lastTlt)/lastTlt
            print('tltChange = ',tltChange)
            portfolioChange = (portfolioValue-lastPortfolio)/lastPortfolio
            print('portfolioChange = ',portfolioChange)
            elapsedTime = now - lastTimestamp
            year = datetime.timedelta(days=365)
            treasuryChange = ((1+((lastRiskFree+riskFree)/2))**(divtd(elapsedTime,year)))-1
            print('treasuryChange = ',treasuryChange)
        except Exception as e:
            print('error calculating change ', str(e))
            success = False

    if success:
        try:
            # save data
            percentageData = {
                "timestamp":now,
                "spy":spyChange,
                "tlt":tltChange,
                "portfolio":tltChange,
                "90dayTreasury":treasuryChange
            }
            data_id = db.percentageMove.insert_one(percentageData).inserted_id
            print("data saved to",data_id)
        except Exception as e:
            print('data save error ', str(e))
            success = False



    if success:
        try:
            # save data
            rawData = {
                "timestamp":now,
                "spy":spyAvgCost,
                "tlt":tltAvgCost,
                "portfolio":portfolioValue,
                "annualized90day":riskFree
            }
            data_id = db.rawPrices.insert_one(rawData).inserted_id
            print("data saved to",data_id)
        except Exception as e:
            print('data save error ', str(e))
            success = False







def send_email(user, pwd, recipient, subject, body):

    gmail_user = user
    gmail_pwd = pwd
    FROM = user
    TO = recipient if type(recipient) is list else [recipient]
    SUBJECT = subject
    TEXT = body

    # Prepare actual message
    message = """From: %s\nTo: %s\nSubject: %s\n\n%s
    """ % (FROM, ", ".join(TO), SUBJECT, TEXT)
    try:
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.ehlo()
        server.login(gmail_user, gmail_pwd)
        server.sendmail(FROM, TO, message)
        server.close()
        print('successfully sent the mail')
    except:
        print("failed to send mail")

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
    try:
        print("running trader at: "+str(datetime.datetime.now()))
        message = "running trader at: "+str(datetime.datetime.now())
        success = True

        rh = Robinhood()
        success = rh.marketOpenCheck()
        if not success:
            print('markets are closed')
            message += '\nmarkets are closed'
        else:
            print('markets are open')
            message += '\nmarkets are open'

        if success:
            success = rh.login(username=rhuser, password=rhpass)

        if success:
            print('login succesful')
            message += '\nlogin succesful'
        else:
            print('login unsuccesful')
            message += '\nlogin unsuccesful'


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
                message += '\nno extra positions found to close'
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
                    message += '\nremaining unresolved orders, waiting'
                    time.sleep(60)


            for order in sellOrders:
                orderDetail = sellOrders[order]
                if orderDetail['status'] == 'failure':
                    success = False

        if not success:
            print('unable to sell extra positions correctly')
            message += '\nunable to sell extra positions correctly'

        if success:
            #get portfolio current value
            portfolioValue = rh.equity()
            print('portfolioValue =', portfolioValue)
            message += '\nportfolioValue = '
            message += str(portfolioValue)

            #allocate portfolio
            spyAllocationPercentage = calcAlloc(rh)
            tltAllocationPercentage = 1-spyAllocationPercentage
            print('spyAllocationPercentage = ', spyAllocationPercentage)
            message += '\nspyAllocationPercentage = '
            message += str(spyAllocationPercentage)
            print('tltAllocationPercentage = ', tltAllocationPercentage)
            message += '\ntltAllocationPercentage = '
            message += str(tltAllocationPercentage)

            spyTargetAllocation = spyAllocationPercentage*portfolioValue
            tltTargetAllocation = tltAllocationPercentage*portfolioValue
            print('spyTargetAllocation = ', spyTargetAllocation)
            message += '\nspyTargetAllocation = '
            message += str(spyTargetAllocation)
            print('tltTargetAllocation = ', tltTargetAllocation)
            message += '\ntltTargetAllocation = '
            message += str(tltTargetAllocation)

            #get pricing data
            spyAskPrice = rh.ask_price('SPY')
            spyBidPrice = rh.bid_price('SPY')
            spyAvgCost = (spyAskPrice+spyBidPrice)/2
            spyBuyPrice = spyAskPrice+(spyAskPrice - spyBidPrice)
            spySellPrice = spyBidPrice-(spyAskPrice - spyBidPrice)
            print('spyAskPrice = ', spyAskPrice)
            message += '\nspyAskPrice = '
            message += str(spyAskPrice)
            print('spyBidPrice = ', spyBidPrice)
            message += '\nspyBidPrice = '
            message += str(spyBidPrice)

            tltAskPrice = rh.ask_price('TLT')
            tltBidPrice = rh.bid_price('TLT')
            tltAvgCost = (tltAskPrice+tltBidPrice)/2
            tltBuyPrice = tltAskPrice+(tltAskPrice - tltBidPrice)
            tltSellPrice = tltBidPrice-(tltAskPrice - tltBidPrice)
            print('tltAskPrice = ', tltAskPrice)
            message += '\ntltAskPrice = '
            message += str(tltAskPrice)
            print('tltBidPrice = ', tltBidPrice)
            message += '\ntltBidPrice = '
            message += str(tltBidPrice)

            #recommend position sizes
            [spyTargetShares,tltTargetShares] = recommendTarget(portfolioValue,spyAllocationPercentage,tltAllocationPercentage,spyBuyPrice,tltBuyPrice)

            print('spyTargetShares = ', spyTargetShares)
            message += '\nspyTargetShares = '
            message += str(spyTargetShares)
            print('tltTargetShares = ', tltTargetShares)
            message += '\ntltTargetShares = '
            message += str(tltTargetShares)

            targetPurchaseCost = targetTotalCost(spyTargetShares,tltTargetShares,spyBuyPrice,tltBuyPrice)


            spyTargetAllocationPercentage = allocationPercentage(spyTargetShares,spyBuyPrice,targetPurchaseCost)
            tltTargetAllocationPercentage = allocationPercentage(tltTargetShares,tltBuyPrice,targetPurchaseCost)
            print('spyTargetAllocationPercentage = ',spyTargetAllocationPercentage)
            message += '\nspyTargetAllocationPercentage = '
            message += str(spyTargetAllocationPercentage)
            print('tltTargetAllocationPercentage = ',tltTargetAllocationPercentage)
            message += '\ntltTargetAllocationPercentage = '
            message += str(tltTargetAllocationPercentage)

            targetLoss = allocationLoss(spyTargetAllocationPercentage,spyAllocationPercentage,tltTargetAllocationPercentage,tltAllocationPercentage)
            print('target loss = ',targetLoss)

            targetRemainingCash = portfolioValue-targetPurchaseCost
            print('targetPurchaseCost = ', targetPurchaseCost)
            message += '\ntargetPurchaseCost = '
            message += str(targetPurchaseCost)
            print('targetRemainingCash = ', targetRemainingCash)
            message += '\ntargetRemainingCash = '
            message += str(targetRemainingCash)

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
            message += '\nspyRequired = '
            message += str(spyRequired)
            print('tltRequired = ',tltRequired)
            message += '\ntltRequired = '
            message += str(tltRequired)

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
                        print('remaining unresolved spySell, waiting')
                        message += '\nremaining unresolved spySell, waiting'
                        time.sleep(60)




                if spySellOrder['status'] == 'failure':
                    success = False

        if not success:
            print('unable to sell required spy')
            message += '\nunable to sell required spy'

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
                        print('remaining unresolved tltSell, waiting')
                        message += '\nremaining unresolved tltSell, waiting'
                        time.sleep(60)



                if tltSellOrder['status'] == 'failure':
                    success = False

        if not success:
            print('unable to sell required tlt')
            message += '\nunable to sell required tlt'


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
                        print('remaining unresolved spyBuy, waiting')
                        message += '\nremaining unresolved spyBuy, waiting'
                        time.sleep(60)



                if spyBuyOrder['status'] == 'failure':
                    success = False
        if not success:
            print('unable to buy required spy')
            message += '\nunable to buy required spy'

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
                        print('remaining unresolved tltBuy, waiting')
                        message += '\nremaining unresolved tltBuy, waiting'
                        time.sleep(60)



                if tltBuyOrder['status'] == 'failure':
                    success = False

        if not success:
            print('unable to buy required tlt')
            message += '\nunable to buy required tlt'

        if success:
            success = rh.logout()
        if not success:
            print('unable to logout')
            message += '\nunable to logout'
        else:
            print('succesfully logged out')
            message += '\nsuccesfully logged out'
        send_email(guser,gpass,'stephanbotes@gmail.com',('resiliant-trader log '+str(datetime.datetime.now())),message)
    except Exception as e:
        print("Unexpected error:", str(e))
        send_email(guser,gpass,'stephanbotes@gmail.com',('resiliant-trader log '+str(datetime.datetime.now())),("Unexpected error: "+str(e)))
        raise
