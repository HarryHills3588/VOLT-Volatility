import psycopg2
import pandas as pd
from dotenv import load_dotenv
import os

# load_dotenv('.env')
# db_url = os.getenv('DATABASE_URL')

# conn = psycopg2.connect(db_url)

# with conn.cursor() as cursor:
#     cursor.execute("SELECT * FROM emails")

#     results = cursor.fetchall()
    
# conn.close()

# df = pd.DataFrame(results, columns=['ID','emails'])

# print(df)
from supabase import create_client, Client

load_dotenv('.env')
supaUrl = os.getenv('SUPA_URL')
supaKey = os.getenv('SUPA_KEY')

supabase = create_client(supaUrl,supaKey)
# supabase.table('emails').insert({"email": 'a@case.edu'}).execute()
data = supabase.table('emails').select("*").execute()

print(data)