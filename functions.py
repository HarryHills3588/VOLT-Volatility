import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup
from io import StringIO
from datetime import datetime
from datetime import timedelta
from dotenv import load_dotenv
import os
from scipy.stats import norm
import time

load_dotenv('.env')
fmp_key = os.getenv("FMP_KEY")
proxy_password = os.getenv("PROXY_PASS")

host = 'brd.superproxy.io:22225'

username = 'brd-customer-hl_14b6dbba-zone-test'
password = proxy_password

proxy_url = f'http://{username}:{password}@{host}'

proxies = {
    'http': proxy_url,
    'https': proxy_url
}

## Getting 30 Day Volatility
def getkdayVolatility (stock: str, k:int) -> int:
    def getUnixNearestFriday(days: int):
        # Get the date 30 days from now
        today = datetime.today()
        target_date = today + timedelta(days=days)

        # Find the nearest Friday
        days_ahead = 4 - target_date.weekday()  # Friday is weekday 4
        if days_ahead < 0:
            days_ahead += 7  # Go to the next Friday if target_date is past Friday

        nearest_friday = target_date + timedelta(days=days_ahead)

        nearest_friday_as_DT = datetime.combine(nearest_friday,datetime.min.time())

        return (int(nearest_friday_as_DT.timestamp()))
    
    def getSpecificTimestamp(soup: BeautifulSoup, k: int):
        #get all data selection items from menu
        dateTags = soup.find_all(class_='itm yf-1hdw734')

        dates = []
        for tag in dateTags:
            try:
                #append dates from date selection menu as datetimes
                dates.append(datetime.strptime(tag.text.strip(), '%b %d, %Y'))
            except Exception:
                None
        
        # Find minima for date difference
        for i in range(1,len(dates)):
            currentDiff = abs(dates[i].timestamp() - (datetime.today() + timedelta(k)).timestamp())
            previousDiff = abs(dates[i-1].timestamp() - (datetime.today() + timedelta(k)).timestamp())

            if currentDiff < previousDiff:
                smallestIndex = i

        return int(dates[smallestIndex].timestamp())

    ## Getting Options tables
    url = 'https://finance.yahoo.com/quote/{}/options/?straddle=false&type=all&date={}'.format(stock,getUnixNearestFriday(1))
    headers = {'User-Agent': 'Mozilla/5.0'}

    response = requests.get(url, headers=headers,proxies=proxies)

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')

        # Get actual dates and option chain
        url = 'https://finance.yahoo.com/quote/{}/options/?straddle=false&type=all&date={}'.format(stock,getSpecificTimestamp(soup,k))
        response = requests.get(url, headers=headers,proxies=proxies)

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

def getOptionsChain(symbol: str) -> pd.DataFrame:
    url = 'https://api.polygon.io/v3/reference/options/contracts?underlying_ticker={}&limit=1000&sort=expiration_date&apiKey=URuQAQnmA2ObuZQ1fY8gCSPKNfBYkrey'.format(symbol)
    df = pd.DataFrame(requests.get(url).json()['results'])
    try:
        df['expiration_date'] = pd.to_datetime(df['expiration_date'])
    except:
        print('No Available Options')
        df = pd.DataFrame()

    return df

def getClosestDate(df: pd.DataFrame, daysfromnow: int) -> str:
    requested_date = (datetime.now() + timedelta(daysfromnow)).date()

    datesGiven = df['expiration_date'].unique()

    # from dates given return closest date
    return pd.Timestamp(min(datesGiven, key=lambda d: abs(d.date() - requested_date)).date())

def getPrice(ticker: str):
    url = 'https://financialmodelingprep.com/api/v3/quote-short/{}?apikey=27c9e25e9855b9f7194cb65d119b5f47'.format(ticker)
    price = requests.get(url).json()[0]['price']

    return price

def getClosestStrikePrice(df: pd.DataFrame, symbol: str) -> float:
    price = getPrice(symbol)
    return df['strike_price'][abs(df['strike_price'] - price).idxmin()]

def getDaysUntil(date: pd.Timestamp) -> int:
    """Calculate the number of days until a specified date.

    Args:
        date (pd.Timestamp): The date to calculate the days until.

    Returns:
        int: The number of days until the specified date.
             Returns a negative value if the date is in the past.
    """
    # Get the current date
    current_date = pd.Timestamp.now()

    # Calculate the difference in days
    days_until = (date - current_date).days

    return days_until

def getMarketValue(option: str) -> float:

    # URL of the page to scrape
    url = f'https://finance.yahoo.com/quote/{option}/'
    headers = {'User-Agent': 'Mozilla/5.0'}

    # Make a GET request to fetch the raw HTML content
    response = requests.get(url, headers=headers, proxies=proxies)
    live_price = np.nan

    # Check if the request was successful
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')

        # Find the element
        live_price_element = soup.find('fin-streamer', class_='livePrice yf-1tejb6')

        # Check if the element was found and get its text
        if live_price_element:
            live_price = float(live_price_element.get_text(strip=True))
        else:
            print(f"Element not found. {option}")
            live_price = np.nan
    else:
        print(f"Failed to retrieve the page. Status code: {response.status_code} {option}")

    return (live_price)

def black_scholes(S, K, T, r, sigma, option_type='call'):
    """
    Calculate the Black-Scholes option price.

    Parameters:
        S (float): Current stock price
        K (float): Option strike price
        T (float): Time to expiration (in years)
        r (float): Risk-free interest rate (annual)
        sigma (float): Volatility of the stock (annual)
        option_type (str): 'call' or 'put'

    Returns:
        float: Option price
    """
    d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)

    if option_type == 'call':
        price = S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
    elif option_type == 'put':
        price = K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
    else:
        raise ValueError("option_type must be 'call' or 'put'")

    return price

def VEGA(S,K,T,r,sigma):
    d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    return S * norm.pdf(d1) * np.sqrt(T)

def getIV(S,K,T,r,marketPrice,contract_type,sigma_guess=1, maxIterations = 100):
    error = black_scholes(S,K,T,r,sigma_guess,contract_type) - marketPrice
    i = 0

    while abs(error) > 1e-6 and i < maxIterations:
        sigma_guess = sigma_guess - error / VEGA(S,K,T,r,sigma_guess)
        error = black_scholes(S,K,T,r,sigma_guess,contract_type) - marketPrice
        i += 1

    return sigma_guess

def get30dayIV(symbol):
    try:
        df = getOptionsChain(symbol)

        date = getClosestDate(df,30)
        df = df[df['expiration_date'] == date]

        strike = getClosestStrikePrice(df,symbol=symbol)
        df = df[df['strike_price'] == strike]

        impliedVolatilities = []
        for index, option in df.iterrows():
            price = getPrice(symbol)
            strikePrice = option['strike_price']
            timeForExpiration = getDaysUntil(option['expiration_date'])/365
            r = getTresuryRates().iloc[0]['month1']/100
            marketValue = getMarketValue(option['ticker'].replace('O:',''))
            optionType = option['contract_type']

            impliedVolatilty = getIV(price,strikePrice,timeForExpiration,r,marketValue,optionType)
            impliedVolatilities.append(impliedVolatilty)
            
        returnIV = np.mean(impliedVolatilities)
    except Exception:
        returnIV = np.nan

    return returnIV

def get30dayIVList(tickerList: list):
    first = datetime.now()
    counter = 0

    etfIV = {}
    for company in tickerList:
        print(company)
        if counter < 4:
            try:
                IV = get30dayIV(company)
                print(IV)
                etfIV[company] = IV
            except:
                etfIV[company] = np.nan

            counter += 1
            second = datetime.now()
        else:
            try:
                IV = get30dayIV(company)
                print(IV)
                etfIV[company] = IV
            except:
                etfIV[company] = np.nan

            timediff = second - first
            timetosleep = 65 - timediff.total_seconds()

            if timetosleep > 0 :
                print(timetosleep)
                time.sleep(timetosleep)
            else:
                print('sleeping for minute')
                time.sleep(60)

            first = datetime.now()
            counter = 0

    return etfIV

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
def getHistoricalVolatility(stock: str, days:int,timeAgo = datetime.today()) -> float:
    # calculate a year ago
    yearAgo = timeAgo - timedelta(days = days)
    fromDate = yearAgo.strftime('%Y-%m-%d')
    toDate = timeAgo.strftime('%Y-%m-%d')

    #historical price data 
    url = 'https://financialmodelingprep.com/api/v3/historical-price-full/{}?from={}&to={}&apikey={}'.format(stock,fromDate,toDate,fmp_key)
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
    toTime = (datetime.now() + timedelta(7)).strftime('%Y-%m-%d')
    fromTime = (datetime.now()).strftime('%Y-%m-%d')
    url = 'https://financialmodelingprep.com/api/v3/earning_calendar?from={}&to={}&apikey={}'.format(fromTime,toTime,fmp_key)
    earningsCalendar = pd.DataFrame(requests.get(url).json())

    return earningsCalendar

## News
def getCompanyNews(stock_requested: str) -> pd.DataFrame:
    fromDate = (datetime.today() - timedelta(8)).strftime('%Y-%m-%d')
    toDate = datetime.today().strftime('%Y-%m-%d')
    url = 'https://financialmodelingprep.com/api/v3/stock_news?tickers={}&page=0&from={}&to={}&apikey={}'.format(stock_requested,fromDate,toDate,fmp_key)
    news = pd.DataFrame(requests.get(url).json())
    return news

## Economics Calendar
def getEconomicsCalendar() -> pd.DataFrame:
    url = 'https://financialmodelingprep.com/api/v3/economic_calendar?from=2024-00-00&apikey={}'.format(fmp_key)

    EconomicCalendar = pd.DataFrame(requests.get(url).json())
    usEconomicCalendar = EconomicCalendar[EconomicCalendar['country'] == 'US'].drop(columns=['country','currency']).iloc[::-1]

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

#Market Index
def getMarketIndex(symbol) -> pd.Series:
    fmp_key = "27c9e25e9855b9f7194cb65d119b5f47"
    url = 'https://financialmodelingprep.com/api/v3/quotes/index?apikey={}'.format(fmp_key)

    marketIndeces = pd.DataFrame(requests.get(url).json())
    return marketIndeces[marketIndeces['symbol'] == '^'+symbol].reset_index(drop=True).iloc[0]

def getPrices(symbol: str,fromDate = datetime.today() - timedelta(365)) -> pd.DataFrame:
    fromdt = fromDate.strftime('%Y-%m-%d')

    #historical price data 
    url = 'https://financialmodelingprep.com/api/v3/historical-price-full/{}?from={}&apikey={}'.format(symbol,fromdt,fmp_key)
    df = pd.DataFrame(requests.get(url).json()['historical']).reset_index(drop=True)
    return df

def getImpliedMove(symbol):
    optionsChain = getOptionsChain(symbol=symbol)

    optionDate = getClosestDate(optionsChain,5)
    optionsWithinDate = optionsChain[optionsChain['expiration_date']==optionDate]

    strikePrice = getClosestStrikePrice(optionsWithinDate,symbol=symbol)
    straddle = optionsWithinDate[optionsWithinDate['strike_price'] == strikePrice]

    prices = []
    if len(straddle) != 0:
        for index, option in straddle.iterrows():
            ticker = option['ticker'].replace('O:','')
            price = getMarketValue(ticker)
            if price != np.nan:
                prices.append(price)
        straddlePrice = np.sum(prices)
    else:
        straddlePrice = np.nan

    return straddlePrice / getPrice(symbol)