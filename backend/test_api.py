import requests

# Test standard text query
print("Testing standard query...")
res = requests.post("http://localhost:8000/api/query", data={"query": "hi"})
print("Status Code:", res.status_code)
print("Response:", res.text)
