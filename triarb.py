import alpaca_trade_api as alpaca
import requests
import asyncio
# import pprint

# Alpaca Constants
API_KEY = 'PKJC1E2UEYY5JABS3ZSD'
SECRET_KEY = 'ujyyROB5Kol8aiSassJHyb8FU74OfVypt9g5oWRH'


LIVE_KEY = 'AKI9JGTTD8QXKDSDQSI4'
LIVE_SECRET = 'ai3y4AAse5UIigrEbDgjA9oeyw1HQjctEEQp2ipK'

HEADERS = {'APCA-API-KEY-ID': API_KEY,
           'APCA-API-SECRET-KEY': SECRET_KEY}

ALPACA_BASE_URL = 'https://paper-api.alpaca.markets'
DATA_URL = 'https://data.alpaca.markets'
# initiate alpaca connection
rest_api = alpaca.REST(API_KEY, SECRET_KEY, ALPACA_BASE_URL)

prices = {
    'ETHUSD' : 0,
    'BTCUSD' : 0,
    'ETH/BTC' : 0
}

# time between each quote
waitTime = 3

min_arb_percent = 0.3

async def main():
        while True:
            task1 = loop.create_task(get_quote("ETHUSD"))
            task2 = loop.create_task(get_quote("BTCUSD"))
            task3 = loop.create_task(get_quote("ETH/BTC"))
            # Wait for the tasks to finish
            await asyncio.wait([task1, task2, task3])
            await check_arb()
            # # Wait for the value of waitTime between each quote request
            await asyncio.sleep(waitTime)

async def get_quote(symbol: str):
    '''
    Get quote data from Alpaca API
    '''

    try:
        # make the request
        if symbol == "ETH/BTC":
            quote = requests.get('{0}/v1beta2/crypto/latest/trades?symbols=ETH/BTC'.format(DATA_URL, headers=HEADERS))
            prices[symbol] = quote.json()['trades'][symbol]['p']
        else: 
            quote = requests.get('{0}/v1beta1/crypto/{1}/trades/latest?exchange=FTXU'.format(DATA_URL, symbol), headers=HEADERS)
            prices[symbol] = quote.json()['trade']['p']
        # Status code 200 means the request was successful
        if quote.status_code != 200:
            print("Undesirable response from Alpaca! {}".format(quote.json()))
            return False
        # Get the latest quoted asking price from the quote response in terms US Dollar
        # # Log the latest quote of MATICUSD

    except Exception as e:
        print("There was an issue getting trade quote from Alpaca: {0}".format(e))
        return False
        


async def check_arb():
    '''
    Check to see if an arbitrage condition exists
    '''
    # get_quote("ETHUSD")
    # get_quote("BTCUSD")
    ETH = prices['ETHUSD']
    BTC = prices['BTCUSD']
    ETHBTC = prices['ETH/BTC']
    DIV = prices['ETHUSD'] / prices['BTCUSD'] 
    BUY_ETH = 1000 / ETH
    BUY_BTC = 1000 / BTC 
    SELL_BTC = BUY_ETH * ETHBTC
    SELL_ETH = BUY_BTC / ETHBTC

    if DIV > ETHBTC * (1 + min_arb_percent/100):
        order1 = post_Alpaca_order("BTCUSD", BUY_BTC, "buy")
        if order1.status_code == 200:
            # print("BTC bought")
            order2 = post_Alpaca_order("ETH/BTC", BUY_BTC, "buy")
        else:
            return False
        if order2.status_code == 200:
                # print("ETHBTC bought")
            order3 = post_Alpaca_order("ETHUSD", SELL_ETH, "sell")
        else:
            post_Alpaca_order("BTCUSD", BUY_BTC, "sell")
            return False
        if order3.status_code == 200:
            print("Done (type 1) eth: {} btc: {} ethbtc {}".format(ETH, BTC, ETHBTC))
        else:
            post_Alpaca_order("BTCUSD", BUY_BTC, "sell")
            post_Alpaca_order("ETH/BTC", BUY_BTC, "sell")
            return False
                
    elif DIV < ETHBTC * (1 - min_arb_percent/100):
        order1 = post_Alpaca_order("ETHUSD", BUY_ETH, "buy")
        if order1.status_code == 200:
            # print("eth bought")
            order2 = post_Alpaca_order("ETH/BTC", BUY_ETH, "sell")
        else:
            return False    
        if order2.status_code == 200:
                # print("eth/btc bought")
            order3 = post_Alpaca_order("BTCUSD", SELL_BTC, "sell")
        else:
            post_Alpaca_order("ETHUSD", BUY_ETH, "sell")
            return False    
        if order3.status_code == 200:
            print("Done (type 2) eth: {} btc: {} ethbtc {}".format(ETH, BTC, ETHBTC))
        else:
            post_Alpaca_order("ETHUSD", BUY_ETH, "sell")
            post_Alpaca_order("ETH/BTC", BUY_ETH, "buy")
            return False
    else:
        print("No arb opportunity")
# get_quote('')

def post_Alpaca_order(symbol, qty, side):
    '''
    Post an order to Alpaca
    '''
    try:
        order = requests.post(
            '{0}/v2/orders'.format(ALPACA_BASE_URL), headers=HEADERS, json={
                'symbol': symbol,
                'qty': qty,
                'side': side,
                'type': 'market',
                'time_in_force': 'gtc',
            })
        return order
    except Exception as e:
        print("There was an issue posting order to Alpaca: {0}".format(e))
        return False


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
loop.close()