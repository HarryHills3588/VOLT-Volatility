# import psycopg2
# import pandas as pd
# from dotenv import load_dotenv
# import os

# # load_dotenv('.env')
# # db_url = os.getenv('DATABASE_URL')

# # conn = psycopg2.connect(db_url)

# # with conn.cursor() as cursor:
# #     cursor.execute("SELECT * FROM emails")

# #     results = cursor.fetchall()
    
# # conn.close()

# # df = pd.DataFrame(results, columns=['ID','emails'])

# # print(df)
# from supabase import create_client, Client

# load_dotenv('.env')
# supaUrl = os.getenv('SUPA_URL')
# supaKey = os.getenv('SUPA_KEY')

# supabase = create_client(supaUrl,supaKey)
# # supabase.table('emails').insert({"email": 'a@case.edu'}).execute()
# data = supabase.table('emails').select("*").execute()

# print(data)

import markdown

text = '''
# VOLT Volatility Weekly Newsletter - October 15, 2024

## Introduction
As we enter yet another suspenseful week in the financial markets, we dive deep into various dimensions of volatility, spanning from the SPY’s implied volatility across different time frames, earnings season announcements, and notable economic indicators set for release. The information herein provides insights for traders, investors, and anyone attuned to the fluctuations inherent in today's dynamic market landscape.

---

### Current Volatility Snapshot

**Volatility Term Structure for SPY**  
- **30-day Implied Volatility (IV):** 15.46  
- **60-day IV:** 15.32  
- **90-day IV:** 15.02  
The term structure suggests a slight decrease in short-term volatility expectations, reflecting more stable pricing as earnings reports loom.

**Current VIX Insight**  
- **Current VIX:** 19.82 (down 12.46% week-over-week, from 22.66)
- **52-Week Range:** High at 35.05, low at 15.53  
The VIX volatility index is indicating reduced market fears, although investors should remain cautious given the backdrop of ongoing geopolitical and economic uncertainties.

---

### Earnings Season on the Horizon

This upcoming week features a flurry of earnings announcements from companies that are poised for significant market reactions due to their weighted implied volatility:

| Ticker | Implied Volatility | Earnings Date  | Implied Move Estimate |
|--------|--------------------|----------------|------------------------|
| WBA    | 83.02%             | October 15     | 14.10%                 |
| UAL    | 48.84%             | October 15     | 6.61%                  |
| ASML   | 46.79%             | October 16     | 6.21%                  |
| NFLX   | 45.88%             | October 17     | 7.68%                  |

WBA leads with remarkable IV, indicating heightened expectation around its earnings result, likely driven by the company’s growth trajectory and sector dynamics.

---

### Economic Indicators This Week

In addition to earnings reports, key economic indicators scheduled for release may inject further volatility:

- **NY Empire State Manufacturing Index (Oct)** - Oct 15
- **Retail Sales MoM (Sep)** - Est: 0.3% (Prev: 0.1%) - Oct 17
- **Consumer Confidence Indicators** - Expectations are mixed with varying prior data indicating possible consumer slowdown.

These indicators will be scrutinized closely for any signs of shifts in consumer behavior which could impact market volatility directly.

---

### Treasury Yields Analysis

In observing U.S. Treasury yields, we see notable shifts indicative of changing investor sentiment:

| Maturity | Today Yield | Last Week Yield | Last Month Yield | Three Months Ago Yield |
|----------|-------------|-----------------|------------------|-----------------------|
| 1 Month  | 4.97%       | 5.01%           | 5.11%            | 5.48%                 |
| 1 Year   | 4.18%       | 4.20%           | 3.96%            | 4.85%                 |
| 10 Year  | 4.08%       | 3.98%           | 3.63%            | 4.23%                 |

The upward creep in short-term yields compared to a more static long-term indicates changing market expectations potentially tied to inflation responses and the Federal Reserve’s policy directions.

---

### Sector Volatility Insights

Diversifying our lens, we take a look at sector betas, witnessing variance in market sensitivity:

- **Technology:** 1.22
- **Health Care:** 0.67
- **Financials:** 1.02
- **Energy:** 0.72

These reflect the heightened volatility the technology sector continues to experience, with large players heavily influencing market dynamics, particularly in earnings releases.

---

### Noteworthy Companies and Recent Developments

Recent shifts in sentiment around key players such as:

- **JPMorgan Chase (JPM)**: Better-than-expected third-quarter results have buoyed investor confidence. Despite a cautious outlook from management regarding stock valuations, the bank’s fundamentals position it for resilience.
- **Eli Lilly (LLY)**: Continuing its strong performance in the pharmaceutical sector, the stock remains a focal point this earnings season affirmed by investor enthusiasm amid innovative drug pipelines.

---

### Conclusion

This week promises to be pivotal both from an earnings perspective and in terms of economic indicators. Attention should be turned towards market reactions to these developments, especially as implied volatility trends will directly reflect shifts in investor sentiment. Stay tuned, and trade wisely as we navigate through these turbulent financial waters.
'''

html =markdown.markdown(text)

print(html)