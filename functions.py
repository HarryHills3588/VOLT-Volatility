import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup
from io import StringIO
import datetime
from dotenv import load_dotenv
import os

load_dotenv('.env')
fmp_key = os.getenv("FMP_KEY")

## Getting 30 Day Volatility
def getkdayVolatility (stock: str, k:int) -> int:
    def getUnixNearestFriday(days: int):
        # Get the date 30 days from now
        today = datetime.date.today()
        target_date = today + datetime.timedelta(days=days)

        # Find the nearest Friday
        days_ahead = 4 - target_date.weekday()  # Friday is weekday 4
        if days_ahead < 0:
            days_ahead += 7  # Go to the next Friday if target_date is past Friday

        nearest_friday = target_date + datetime.timedelta(days=days_ahead)

        nearest_friday_as_DT = datetime.datetime.combine(nearest_friday,datetime.datetime.min.time())

        return (int(nearest_friday_as_DT.timestamp()))
    
    def getSpecificTimestamp(soup: BeautifulSoup, k: int):
        #get all data selection items from menu
        dateTags = soup.find_all(class_='itm yf-1hdw734')

        dates = []
        for tag in dateTags:
            try:
                #append dates from date selection menu as datetimes
                dates.append(datetime.datetime.strptime(tag.text.strip(), '%b %d, %Y'))
            except Exception:
                None
        
        # Find minima for date difference
        for i in range(1,len(dates)):
            currentDiff = abs(dates[i].timestamp() - (datetime.datetime.today() + datetime.timedelta(k)).timestamp())
            previousDiff = abs(dates[i-1].timestamp() - (datetime.datetime.today() + datetime.timedelta(k)).timestamp())

            if currentDiff < previousDiff:
                smallestIndex = i

        return int(dates[smallestIndex].timestamp())

    ## Getting Options tables
    url = 'https://finance.yahoo.com/quote/{}/options/?straddle=false&type=all&date={}'.format(stock,getUnixNearestFriday(1))
    headers = {'User-Agent': 'Mozilla/5.0'}

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')

        # Get actual dates and option chain
        url = 'https://finance.yahoo.com/quote/{}/options/?straddle=false&type=all&date={}'.format(stock,getSpecificTimestamp(soup,k))
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')

            tables = pd.read_html(StringIO(soup.prettify()))
        else:
            print(f"Failed to retrieve page, status code: {response.status_code}")
    else:
        print(f"Failed to retrieve page, status code: {response.status_code}")

    calls = tables[0]
    puts = tables[1]

    ## get Price
    url = 'https://financialmodelingprep.com/api/v3/quote/{}?apikey={}'.format(stock,fmp_key)

    stockPrice = requests.get(url).json()[0]['price']

    callIV = calls[abs(calls['Strike'] - stockPrice) == abs(stockPrice - calls['Strike']).min()]['Implied Volatility'].str.rstrip('%').astype(float)
    putIV = puts[abs(puts['Strike'] - stockPrice) == abs(stockPrice - puts['Strike']).min()]['Implied Volatility'].str.rstrip('%').astype(float)

    monthlyVolatility = (callIV[callIV.index[0]] + putIV[putIV.index[0]]) / 2 

    return monthlyVolatility

## IV for companies in the SPY
def getCompaniesETF(ETF: str) -> pd.DataFrame:
    url = 'https://financialmodelingprep.com/api/v3/etf-holder/{}?apikey={}'.format(ETF,fmp_key)

    companiesInETF = pd.DataFrame(requests.get(url).json())[['asset']]
    companiesInETF.drop(index=companiesInETF[(companiesInETF['asset'] == '') | (companiesInETF['asset'] == ' ')].index, inplace=True)

    return companiesInETF

## Beta
def getCompaniesProfiles(ETF_requested: str) -> dict:
    companyList = getCompaniesETF(ETF_requested)['asset']

    companyProfiles = {}
    for asset in companyList:
        url = 'https://financialmodelingprep.com/api/v4/company-outlook?symbol={}&apikey={}'.format(asset,fmp_key)
        companyProfiles[asset] = requests.get(url).json()

    return companyProfiles

def getCompanyProfile(stock_requested: str) -> dict:
    companyProfile = {}
    url = 'https://financialmodelingprep.com/api/v4/company-outlook?symbol={}&apikey={}'.format(stock_requested,fmp_key)
    companyProfile = requests.get(url).json()

    return companyProfile

def getBeta(companyProfiles: dict, stock: str) -> float:
    if companyProfiles == None or (not (stock in companyProfiles.keys())):
        url = 'https://financialmodelingprep.com/api/v4/company-outlook?symbol={}&apikey={}'.format(stock,fmp_key)
        return requests.get(url=url).json()['profile']['beta']
    else:
        return companyProfiles[stock]['profile']['beta']
    
## Historical Volatility
def getHistoricalVolatility(stock: str) -> float:
    # calculate a year ago
    yearAgo = datetime.datetime.today() - datetime.timedelta(days = 365)
    fromDate = yearAgo.strftime('%Y-%m-%d')

    #historical price data 
    url = 'https://financialmodelingprep.com/api/v3/historical-price-full/{}?from={}&apikey={}'.format(stock,fromDate,fmp_key)
    df = pd.DataFrame(requests.get(url).json()['historical']).iloc[::-1].reset_index(drop=True)

    #calculate log returns
    logReturns = np.log(df['adjClose']/df['adjClose'].shift(1)) 
    df['logReturns'] = logReturns

    #standard deviation of log returns
    historicalVolatility = df['logReturns'].std()

    #annualize
    historicalVolatilityAnnualized = historicalVolatility * np.sqrt(252)
    return historicalVolatilityAnnualized


## Earnings Calendar
def getEarningsCalendar() -> pd.DataFrame:
    url = 'https://financialmodelingprep.com/api/v3/earning_calendar?from=2024-00-00&apikey={}'.format(fmp_key)
    earningsCalendar = pd.DataFrame(requests.get(url).json())

    return earningsCalendar

## News
def getCompanyNews(stock_requested: str) -> pd.DataFrame:
    url = 'https://financialmodelingprep.com/api/v3/stock_news?tickers={}&page=1&from=2024-10-01&apikey={}'.format(stock_requested,fmp_key)
    news = pd.DataFrame(requests.get(url).json())
    return news

## Economics Calendar
def getEconomicsCalendar() -> pd.DataFrame:
    url = 'https://financialmodelingprep.com/api/v3/economic_calendar?from=2024-00-00&apikey={}'.format(fmp_key)

    EconomicCalendar = pd.DataFrame(requests.get(url).json())
    usEconomicCalendar = EconomicCalendar[EconomicCalendar['country'] == 'US']

    return usEconomicCalendar.reset_index(drop=True)

## Tresury Rates
def getTresuryRates() -> pd.DataFrame:
    url = 'https://financialmodelingprep.com/api/v4/treasury?from=2024-00-00&apikey={}'.format(fmp_key)

    return pd.DataFrame(requests.get(url).json())

## Market risk premium
def getMarketRiskPremium() -> pd.DataFrame:
    url = 'https://financialmodelingprep.com/api/v4/market_risk_premium?apikey={}'.format(fmp_key)

    usRiskPremium = pd.DataFrame(requests.get(url).json())
    usRiskPremium = usRiskPremium[usRiskPremium['country'] == 'United States']
    return usRiskPremium