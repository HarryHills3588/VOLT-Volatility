import functions as volt
from dotenv import load_dotenv
import os
import datetime
import pandas as pd

fmp_key = volt.fmp_key

def generateMarketVolatilityIndexes() -> str:
    ticker = 'SPY'

    monthIV = volt.getkdayVolatility(ticker,30)
    twoMonthIV = volt.getkdayVolatility(ticker,60)
    threeMonthIV = volt.getkdayVolatility(ticker,90)

    return 'Volatility Term Structure ' + str(ticker) +' '+ str(monthIV) +' '+ str(twoMonthIV) +' '+ str(threeMonthIV)

def IVScreener(fund: str):
    companiesInFund = volt.getCompaniesETF(fund)

    IVList = []
    for company in companiesInFund['asset']:
        companyIV = volt.getkdayVolatility(company,30)
        IVList.append(companyIV)

    companiesInFund['IV'] = IVList

    return companiesInFund.sort_values('IV',ascending=False) 
        
# Earnings impact analysis ##--------------- TODO -----------------------
def earningsImpactAnalysis():
    # get high-impact companies
    QQQCompanies = volt.getCompaniesETF('QQQ')['asset'].tolist()
    spyCompanies = volt.getCompaniesETF('SPY')['asset'].tolist()
    spyQQQSymbols = set(QQQCompanies + spyCompanies)

    # get earnings calendar
    earningsCalendar = volt.getEarningsCalendar()
    potentialUSSymbols = earningsCalendar[earningsCalendar['symbol'].str.contains(r'^[A-Za-z]+$', na=False)]

    #US symbols annoncing earnings this week
    USSymbols = potentialUSSymbols[potentialUSSymbols['symbol'].isin(spyQQQSymbols)]


    USSymbols

    ## -----------NEXT STEP-------------
    ## get market value for straddle 
    ## calculate implied move
    ## calculate historical move ((MAY NOT BE MVP))
    print(USSymbols)


#Sector Risk Profiles
def getSectorBetas():
    sectorList = ['XLK','XLV','XLF','XLY','XLP','XLE','XLI','XLB','XLU','XLRE','XLC']

    sectorsBeta = {}
    for sector in sectorList:
        sectorProfile = volt.getCompanyProfile(sector)['profile']
        sectorBeta = sectorProfile['beta']
        sectorName = sectorProfile['companyName'].replace(' Select Sector SPDR\xa0Fund','').replace(' Select Sector SPDR Fund','')

        sectorsBeta[sectorName] = sectorBeta

    return str(sectorsBeta)

def getMarketSnapshot():
    vix = volt.getMarketIndex('VIX')['price']
    vixWeekAgo = volt.getPrices('^VIX').iloc[5]['close']
    vixChange = (vix - vixWeekAgo) / vixWeekAgo

    Vvix = volt.getMarketIndex('VVIX')['price']
    VvixWeekAgo = volt.getPrices('^VVIX').iloc[5]['close']
    VvixChange = (Vvix - VvixWeekAgo) / VvixWeekAgo

    spHistVolatility = volt.getHistoricalVolatility('^SPX',30)
    weekAgo = datetime.datetime.today() - datetime.timedelta(7)
    spHistoricalVolatilityWeekAgo = volt.getHistoricalVolatility('^SPX',30,weekAgo)
    spChange = (spHistVolatility - spHistoricalVolatilityWeekAgo) / spHistoricalVolatilityWeekAgo
    
    returnDict = {
        'VIX': {
            'currentVIX': vix,
            'Weekly Change': str(vixChange * 100) + '%'
        },
        'S&P500': {
            'Realized Volatility': str(spHistVolatility * 100) + '%',
            'Realized Volatility Weekly Change': str(spChange * 100) + '%'
        },
        'VVIX': {
            'currentVVIX': Vvix,
            'Weekly Change': str(VvixChange * 100) + '%'
        }
    }

    return str(returnDict)

def getMacroRisk():
    vix = volt.getMarketIndex('VIX')
    vixWeekAgo = volt.getPrices('^VIX').iloc[5]['close']
    vixChange = (vix['price'] - vixWeekAgo)

    returnDict = {
        'Current VIX': vix['price'],
        'Weekly Change': vixChange,
        'Weekly Change Percentage': str((vixChange / vixWeekAgo) * 100) + '%',
        '52-week High': vix['yearHigh'],
        '52-week Low': vix['yearLow']
    }
    return str(returnDict)

def getHighImpactBetas():
    highImpactStocksSample = pd.concat([
        volt.getCompaniesETF('XLF')['asset'][0:15],
        volt.getCompaniesETF('XLK')['asset'][0:5],
        volt.getCompaniesETF('XLV')['asset'][0:3]
    ])

    returnDict = {}
    highImpactStocks = highImpactStocksSample.sample(5)
    for stock in highImpactStocks:
        profile = volt.getCompanyProfile(stock)['profile']
        returnDict[f"{profile['companyName']} ({profile['symbol']})"] = profile['beta']

    return str(returnDict)

def getInterestRateEnviroment():
    tresuryRates = volt.getTresuryRates()
    today = tresuryRates.iloc[0].to_dict()
    week = tresuryRates.iloc[5].to_dict()

    month1 = tresuryRates.iloc[abs(pd.to_datetime(tresuryRates['date']) - pd.Timestamp(datetime.datetime.today() - datetime.timedelta(30))).idxmin()].to_dict()

    month3 = tresuryRates.iloc[-1].to_dict()

    return {
        'Treasury Rates': {
            'Today': today,
            'One Week Ago': week,
            'One Month Ago': month1,
            'Three Months Ago': month3
        }
    }

def getHighImpactEconomicEvents():
    economicCalendar = volt.getEconomicsCalendar()

    highImpactEvents = economicCalendar[economicCalendar['impact'] == 'High'].reset_index(drop=True)
    highImpactEvents['date'] = pd.to_datetime(highImpactEvents['date'])

    future_date = pd.Timestamp(datetime.datetime.today() + datetime.timedelta(days=7))
    index = abs(highImpactEvents['date'] - future_date).idxmin() + 1 

    highImpactEventsThisWeek = highImpactEvents[0:index]
    highImpactEventsThisWeek.drop(columns=['change','actual','impact','changePercentage','unit'],inplace=True)

    returnDict = {}
    for index, row in highImpactEventsThisWeek.iterrows():
        rowDict = row.to_dict()
        rowDict['date'] = str(rowDict['date'])
        event = rowDict.pop('event')
        returnDict[event] = rowDict

    return str(returnDict)
