import functions as volt
from dotenv import load_dotenv
import os
import datetime
import pandas as pd
import time
import numpy as np
from openai import OpenAI
from supabase import create_client
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

fmp_key = volt.fmp_key
supaUrl = os.getenv('SUPA_URL')
supaKey = os.getenv('SUPA_KEY')

def generateMarketVolatilityIndexes() -> str:
    ticker = 'SPY'

    monthIV = round(volt.getkdayVolatility(ticker,30),2)
    twoMonthIV = round(volt.getkdayVolatility(ticker,60),2)
    threeMonthIV = round(volt.getkdayVolatility(ticker,90),2)
    
    termStructre = {
        'Volatility Term Structure SPY': {
            '30-day IV': monthIV,
            '60-day IV': twoMonthIV,
            '90-day IV': threeMonthIV
        }
    }

    return str(termStructre)

def highImpactStocksIV():
    spy = volt.getCompaniesETF('SPY')['asset'].tolist()

    spyImpliedVolatilities = volt.get30dayIVList(spy)
    df = pd.DataFrame(list(spyImpliedVolatilities.items()),columns=['ticker','IV'])
    df = df.dropna()
    df = df[~np.isinf(df['IV'])]
    df = df[df['IV'] != 1.0].sort_values('IV',ascending=False)

    return str(df.to_dict())
        
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

    return str({
        'Treasury Rates': {
            'Today': today,
            'One Week Ago': week,
            'One Month Ago': month1,
            'Three Months Ago': month3
        }
    })

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

def getEarningsImpact():
    QQQCompanies = volt.getCompaniesETF('QQQ')['asset'].tolist()
    spyCompanies = volt.getCompaniesETF('SPY')['asset'].tolist()
    spyQQQSymbols = set(QQQCompanies + spyCompanies)

    earningsCalendar = volt.getEarningsCalendar()
    potentialUSSymbols = earningsCalendar[earningsCalendar['symbol'].str.contains(r'^[A-Za-z]+$', na=False)]

    USSymbols = potentialUSSymbols[potentialUSSymbols['symbol'].isin(spyQQQSymbols)]

    impliedVolatilites = volt.get30dayIVList(USSymbols['symbol'].tolist())
    time.sleep(60)

    df = pd.DataFrame(list(impliedVolatilites.items()),columns=['ticker','IV'])
    df = df[~np.isinf(df['IV'])]
    df = df[df['IV'] != 1.0].sort_values('IV',ascending=False)

    if len(df) < 5:
        df = df[0:len(df)]
    else:
        df = df[0:5]

    df = df.reset_index(drop=True)
    for i in df.index:
        ticker = df.iloc[i]['ticker']
        date = earningsCalendar[earningsCalendar['symbol'] == ticker]['date'].values[0]
        df.loc[i, 'date'] = date
        df.loc[i, 'impliedMove'] = volt.getImpliedMove(ticker)

    return str((df.dropna()).to_dict())

def getMarketExpectations():
    spyIV = volt.getkdayVolatility('SPY',30) / 100
    qqqIV = volt.getkdayVolatility('QQQ',30) /100

    spyHV = volt.getHistoricalVolatility('SPY',30)
    qqqHV = volt.getHistoricalVolatility('QQQ',30)

    if spyIV == 1.0 or qqqIV == 1.0 or abs(spyIV) == np.inf or abs(qqqIV) == np.inf or spyIV == np.nan or qqqIV == np.nan:
        spyIV = 'unable to retrieve'
        qqqIV = 'unable to retrieve'
        spyIVHVratio =  spyHV
        QQQIVHVratio =   qqqHV
    else:
        spyIVHVratio = spyIV / spyHV
        QQQIVHVratio = qqqIV / qqqHV

    volatilities = {
        'SPY': {
            'Current Implied Volatility': spyIV,
            'Current 30-day Historical Volatility': spyHV,
            'IV/HV Ratio': spyIVHVratio
        },
        'QQQ': {
            'Current Implied Volatility': qqqIV,
            'Current 30-day Historical Volatility': qqqHV,
            'IV/HV Ratio': QQQIVHVratio
        }
    }

    return str(volatilities)

def getImpactNews():
    returnNews = {}
    companyList = volt.getCompaniesETF('SPY')['asset'].tolist()[0:20]
    companyList.insert(0,'SPY')
    companyList.insert(0,'QQQ')

    for company in companyList:
        returnNews[company] = []
        news = pd.DataFrame(volt.getCompanyNews(company))
        news = news[news['site'] != 'youtube.com']

        for index, article in news.iterrows():
            returnNews[company].append(article['text'])

    return str(returnNews)

def chatGPTFinancialCompletion(data :str):
    client = OpenAI()
    completion = client.chat.completions.create(
    model="gpt-4o-mini",
    max_tokens=16000,
    temperature=0.75,
    messages=[
        {"role": "system", "content": "you are a financial analyst working for the VOLT volatility newsletter, your job is to get data and synthesize it into a newsletter providing tables and insight on volatility. Make sure to provide your analysis for the data "},
        {
            "role": "user",
            "content": f"take all this data and synthesize it into a financial newsletter section focused on volatility. Data: {data}"
        }
    ])

    return completion.choices[0].message.content.replace('```html','').replace('```','')

def chatGPTCondensationCompletion(data :str):
    client = OpenAI()
    completion = client.chat.completions.create(
    model="gpt-4o-mini",
    max_tokens=16000,
    temperature=0.75,
    messages=[
        {"role": "system", "content": "you are a financial analyst working for the VOLT volatility newsletter, your job is to get sections written independently and synthesize it into a single, cohesive newsletter providing tables and insight on volatility. Make sure to provide your analysis for the data "},
        {
            "role": "user",
            "content": f"take all these sections and synthesize it into a financial newsletter focused on volatility the newsletter should be about 1300 words. Data: {data}"
        }
    ])

    return completion.choices[0].message.content.replace('```html','').replace('```','')

def chatGPTHTMLCompletion(data :str):
    client = OpenAI()
    completion = client.chat.completions.create(
    model="gpt-4o-mini",
    max_tokens=16000,
    temperature=0.05,
    messages=[
        {"role": 'system','content':"markdown to html converter, please provide html only in response."},
        {
        "role": "user",
        "content": f"please convert this markdown to html, please be sure to copy everything and include inline CSS to copy the markdown style, no image tags: {data}"
        }
    ])

    return completion.choices[0].message.content.replace('```html','').replace('```','')

def chatGPTCSSCompletion(data :str):
    client = OpenAI()
    completion = client.chat.completions.create(
    model="gpt-4o-mini",
    max_tokens=16000,
    temperature=0.05,
    messages=[
        {"role": 'system','content':"you are a html internal css to html inline CSS converter, please provide html with inline CSS only in response."},
        {
        "role": "user",
        "content": f"please convert this html with internal css to html with inline CSS, please be sure to copy everything and include inline CSS: {data}"
        }
    ])

    return completion.choices[0].message.content.replace('```html','').replace('```','')

newsLetterPrompts = {
    'SP500_IV': f'This dataset represents ticker symbols of stocks from the S&P 500 and their corresponding Implied Volatility (IV) values. {highImpactStocksIV()}',
    'term_structure': f'This data represents the volatility term structure for the SPY (an ETF tracking the S&P 500), with implied volatility (IV) levels over different time horizons. {generateMarketVolatilityIndexes()}',
    'earnings_impact': f'This data reprsents a volatility watchlist for the companies announcing earnings this week with the highest implied volatility and their implied moves because of reporting their earnings{getEarningsImpact()}',
    'high_impact_economic_events': f'The following is a economic calendar which tracks teh release date of important economic indicators, as well as their estimates and preivious values {getHighImpactEconomicEvents()}',
    'Interest_rate_enviroment': f'This data represents U.S. Treasury yields across various maturities, showing how rates have changed over different timeframes: today, one week ago, one month ago, and three months ago. {getInterestRateEnviroment()}',
    'sector_betas': f'This data represents sectors across the stock market and their sector betas {getSectorBetas()}',
    'high-impact-betas': f'This data represents the beta values relative to the SP500 of influential companies in the three largest sectors of the stock market: Technology, Financial Services, Healthcare {getHighImpactBetas()}',
    'macro_risk': f'This data represents key statistics related to the VIX (CBOE Volatility Index) {getMacroRisk()}',
    'market_snapshot': f'This data provides insights into the volatility of the stock market, with metrics for the VIX, S&P 500 Realized Volatility, and the VVIX (Volatility of Volatility Index) {getMarketSnapshot()}',
    'market_expectations': f'This data presents the implied volatility and historical volatility for two popular exchange-traded funds (ETFs): SPY (S&P 500 ETF) and QQQ (NASDAQ-100 ETF). This data is used to percieve market expectation {getMarketExpectations()}',
    'impact_news': f'This data represents the recent news for two of the largest indices and largest companies in the stock market {getImpactNews()}'
}

newsLetterSections = {}
for key in newsLetterPrompts.keys():
    newsLetterSections[key] = chatGPTFinancialCompletion(newsLetterPrompts[key])

newsLetterMarkdown = chatGPTCondensationCompletion(str(newsLetterSections))

newsLetterHTML = chatGPTHTMLCompletion(newsLetterMarkdown)

newsLetterHTMLCSS = chatGPTCSSCompletion(newsLetterHTML)

print(newsLetterHTMLCSS)

supabase = create_client(supaUrl,supaKey)
data = supabase.table('emails').select('email').execute()
df = pd.DataFrame(data.data)
emailList = df['email'].tolist()

print(emailList)

message = Mail(
    from_email='Volt@voltvolatility.com',
    to_emails=emailList,
    subject='Your Weekly Volt Volatility Newsletter',
    html_content=newsLetterHTML)

try:
    sg = SendGridAPIClient(os.getenv('EMAIL_KEY'))
    response = sg.send(message)
    print(response.status_code)
    print(response.body)
    print(response.headers)
except Exception as e:
    print(e)