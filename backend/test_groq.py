import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
api_key = os.getenv("GROQ_API_KEY")
print("API Key found:", bool(api_key))

try:
    client = Groq(api_key=api_key)
    completion = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": "hi"}],
    )
    print("Success:", completion.choices[0].message.content)
except Exception as e:
    print("Error:", str(e))
