import requests
from scipy.stats import linregress
import pandas as pd
import config
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
import asyncio

GLASSNODE_KEY = config.GLASSNODE_KEY
API_KEY = config.API_KEY
SECRET_KEY = config.SECRET_KEY

HEADERS = {'APCA-API-KEY-ID': API_KEY,'APCA-API-SECRET-KEY': SECRET_KEY}

trading_client = TradingClient(API_KEY, SECRET_KEY)

MARGIN, COUNT, asset = 1.05, 0, 'ETH'

values = {
  'add' : 0,
  'fee' : 0, 
  'tx' : 0
}

assets = {'ETH': 'ETH/USD'}

waitTime = 200

async def main():
        while True:
            task = loop.create_task(get_dfs(asset))
            task2 = loop.create_task(calculate())
            task3 = loop.create_task(trade(asset))
            await asyncio.wait([task, task2, task3])
            # Wait for the tasks to finish
            # # Wait for the value of waitTime between each quote request
            await asyncio.sleep(waitTime)

rows = 100

async def get_dfs(symbol: str):
  # Make requets for each group of data and put them into dataframes
  address_df = pd.read_json(submit_req('addresses/active_count', symbol).text)
  address_df = address_df.tail(rows)
  fee_df = pd.read_json(submit_req('fees/gas_price_median', symbol).text)
  fee_df = fee_df.tail(rows)
  tx_df = pd.read_json(submit_req('transactions/count', symbol).text)
  tx_df = tx_df.tail(rows)
  
  # Extracting the values we need to run Linear Regressions
  add_tuple = (address_df.t, address_df.v)
  fee_tuple = (fee_df.t, fee_df.v)
  tx_tuple = (tx_df.t, tx_df.v)

  # Getting slope values and updating dictionary 
  add_stat = linregress(add_tuple)
  values['add'] = add_stat.slope
  fee_stat = linregress(fee_tuple)
  values['fee'] = fee_stat.slope
  tx_stat = linregress(tx_tuple)
  values['tx']= tx_stat.slope
  print(values)

# Submitting request for glassnode API data
def submit_req(URL: str, asset : str):
    request = requests.get('https://api.glassnode.com/v1/metrics/' + URL, 
    params={'a': asset, 'api_key': GLASSNODE_KEY})
    return request

# Updating COUNT value
async def calculate():
  tmp = 0
  for element in values:
    if values[element] > MARGIN:
      tmp += 1
  COUNT = tmp
  
# Using COUNT value to trade
async def trade(symbol: str):
  if owns_asset(symbol):
    print("None"); return False
  if COUNT == 2 or COUNT == 3:
    post_order()
    print("Done"); return True
  return False

def owns_asset(asset: str):
  if TradingClient.get_open_position(assets[asset]):
    return False
  return True

def post_order(symbol: str):
  # prepare order
  try:
    market_order_data = MarketOrderRequest(
      symbol = assets[symbol], 
      qty=0.01,
      side=OrderSide.BUY,
      time_in_force=TimeInForce.DAY)

    market_order = trading_client.submit_order(
      order_data=market_order_data)
    
    print("Bought {}".format(assets[symbol]))
    return market_order
  
  except Exception as e:
    print("Issue posting order to Alpaca: {}".format(e))
    return False

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
loop.close()