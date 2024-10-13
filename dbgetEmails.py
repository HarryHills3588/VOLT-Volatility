import psycopg2
import pandas as pd
from dotenv import load_dotenv
import os

load_dotenv('.env')
db_url = os.getenv('DATABASE_URL')

conn = psycopg2.connect(db_url)

with conn.cursor() as cursor:
    cursor.execute("SELECT * FROM emails")

    results = cursor.fetchall()
conn.close()

df = pd.DataFrame(results, columns=['ID','emails'])

print(df.iloc[0]['emails'])