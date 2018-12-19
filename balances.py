import requests

response = requests.get('http://localhost:5010/balances', timeout=6)

for key in response.json():
    print(str(key) + ': ' + str(response.json()[key]))

