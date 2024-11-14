import requests
import json

API_BASE_URL="https://data-api.binance.vision/api/v3"
EXCHANGE_BASE_ENDPOINT="exchangeInfo"
PING_ENDPOINT="ping"

def main ():
  response = requests.get('/'.join([API_BASE_URL, EXCHANGE_BASE_ENDPOINT]))
  symbols = json.loads(response.content)["symbols"]
  assets = sorted(set(filter(lambda x: str(x).endswith("USDT"), list(map(lambda x : x["symbol"], symbols)))))
  with open("assets.json", "w") as f:
    json.dump(assets, f)
  
  with open("assets.txt", "w") as f:
    f.write('\n'.join(assets))
   
  
  
  
  
  
  
  
  

if __name__ == "__main__":
  main()