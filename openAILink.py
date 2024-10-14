import os 
from dotenv import load_dotenv

load_dotenv('.env')
fmp_key = os.getenv("FMP_KEY")
proxy_password = os.getenv("PROXY_PASS")
openAIKey = os.getenv('OPEN_AI_KEY')

from openai import OpenAI
client = OpenAI()

completion = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {
            "role": "user",
            "content": "Write a haiku about recursion in programming."
        }
    ]
)

print(completion.choices[0].message.content)

