# Triangular Arbitrage and Network-Size Momentum Investing

## Triangular Arbitrage on BTC and ETH with Alpaca

### Background

With the exciting announcement of Alpaca’s coin pair trading, we introduce a triangular arbitrage strategy using BTC/USD, ETH/USD, and the new BTC/ETH coin pair to attempt to profit from potential differences between price conversions. 

### What is Triangular Arbitrage?

Triangular Arbitrage is an arbitrage opportunity that appears between three currencies that don’t have equivalent conversion rates. Traders can buy the cheaper currency, convert it to a more expensive currency, and then sell the expensive currency - this typically happens across different exchanges. For example: 

Let’s say you have 1 million euros. The conversion rates are as follows. 

EURO  / USD = 1.02
USD / YUAN = 6.71
EURO / YUAN = 6.83

Sell Euros to buy Dollars -> 1,000,000 * 1.02 -> 1,020,000 Dollars
Sell Dollars to buy Yuan -> 1,020,000 * 6.71 -> 6,844,200 Yuan
Sell Yuan to buy Euros ->  6,844,200 / 6.83 -> 1,002,079 Euros

1,002,079 - 1,000,000 = 2,079 euros of profit (excluding exchange fees)

We will do this but with ETH/USD, the new ETH/BTC coin pair, and BTC/USD. Our specific strategy will be implemented just using Alpaca’s services - we won’t have to interact cross exchanges. 

### Why Triangular Arbitrage?

Cryptocurrency pricing is volatile. This is largely because one cannot generally take traditional investing concepts and apply them successfully. There are a large number of unclear factors that can influence a cryptocurrency’s price. Arbitrage methods, including Triangular Arbitrage, are relatively risk-free and attempt to ensure a profit regardless of many market conditions, and generally don’t need to be monitored as often as other riskier strategies.

Given the need for quick quotes and trade orders, a strategy like this can really only be implemented with API trading services - where Alpaca excels. 

Historical Spread:


Plotted here is the hourly price comparison between BTC/USD and the conversion price using BTC/ETH and ETH/USD. We can see that there is almost always a price discrepancy and that they can sometimes be very large. 



This plot shows the absolute value of the dollar amount difference between the two prices.
Implementation:

To use Triangular Arbitrage, we must get the latest prices for each of these currency pairs. We then find the conversion rates, buy the cheaper currency, convert it into the expensive currency, and then finally sell the expensive currency. 

### Getting Started:

Create a new python file and import the following modules:

import alpaca_trade_api as alpaca
import requests
import asyncio

We will access market data and execute on trades using Alpaca API. The requests module will help us make calls to Alpaca API. Asyncio will help us run our code asynchronously. 


Create variables for the API_KEY and SECRET_KEY associated with your Alpaca account. These can also be put in a config.py file and then fetched using config.API_KEY and config.SECRET_KEY. 

HEADERS = {'APCA-API-KEY-ID': API_KEY,
           'APCA-API-SECRET-KEY': SECRET_KEY}

Then create the above object that captures both variables - we will need this for sending HTTP requests. 

We then want our relevant Alpaca URLs and create our connection with Alpaca in rest_api:

ALPACA_BASE_URL = 'https://paper-api.alpaca.markets'
DATA_URL = 'https://data.alpaca.markets'
rest_api = alpaca.REST(API_KEY, SECRET_KEY, ALPACA_BASE_URL)
Initialize these variables as well - we can tweak these later as you test your algos!

waitTime = 3
min_arb_percent = 0.3
Getting Data:

Before we request data from Alpaca, let’s initialize a dictionary to store price values. 

prices = {
    'ETH/USD' : 0,
    'BTC/USD' : 0,
    'ETH/BTC' : 0
}

We define the get_quote function to get the latest price of an asset, whose symbol is inputted on the function call.

We check whether a quote is valid or not by finding its status code (200 means it is successful). This function updates the dictionary with the most recent values of each asset.

async def get_quote(symbol: str):
    '''
    Get quote data from Alpaca API
    '''
 
    try:
        # make the request
            quote = requests.get('{0}/v1beta2/crypto/latest/trades?symbols={1}'.format(DATA_URL, symbol), headers=HEADERS)
            prices[symbol] = quote.json()['trades'][symbol]['p']
        # Status code 200 means the request was successful
        if quote.status_code != 200:
            print("Undesirable response from Alpaca! {}".format(quote.json()))
            return False
 
    except Exception as e:
        print("There was an issue getting trade quote from Alpaca: {0}".format(e))
        return False

### Post Trade Function:

Now we define a function that places a trade on our account given a symbol, quantity, and side. We have kept type and time_in_force constant for the purposes of this tutorial, but you are more than free to add complexity to your code. This function will be called in our arbitrage condition checker function and will place trades when the condition appears. 


def post_alpaca_order(symbol, qty, side):
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

### Arbitrage Condition Checker:

This is the core of our strategy. Now that we have set up our connection to Alpaca, can fetch and store market data, and can post trades, let’s set up our arbitrage checker: it will calculate the discrepancies between conversion rates and then place the correct trade given that the discrepancies are large enough. This value was initialized as min_arb_percent.

Let’s define our async function. The first step is to fetch the values we need. Our main function will update our prices dictionary before calling this function, so we fetch those values here and store them in the variables below. ETH, BTC, and ETHBTC just refer to the most recent values of ETH/USD, BTC/USD, and ETHBTC. This example is implemented by buying either $1000 of ETH/USD or BTC/USD but feel free to change this number to suit your needs, in the variables BUY_ETH and BUY_BTC. 

async def check_arb():
    '''
    Check to see if an arbitrage condition exists
    '''
    ETH = prices['ETH/USD']
    BTC = prices['BTC/USD']
    ETHBTC = prices['ETH/BTC']
    DIV = ETH / BTC
    spread = abs(DIV - ETHBTC)
    BUY_ETH = 1000 / ETH
    BUY_BTC = 1000 / BTC
    BUY_ETHBTC = BUY_BTC / ETHBTC
    SELL_ETHBTC = BUY_ETH / ETHBTC

DIV is our key calculation of conversion discrepancies: manually calculating ETH / BTC as opposed to taking the given coin pair value of ETH/BTC. If this discrepancy is large enough, we traverse one of two flows:

If the manual division is larger than the coin pair value (DIV > ETH/BTC), this implies that the price of BTC/USD is cheaper. 

Flow: BUY BTC/USD => SELL ETH/BTC => SELL ETH/USD

We purchase an amount of BTC/USD (BUY_BTC in our code). We convert that BTC/USD to ETH/USD by selling ETH/BTC of the appropriate amount (SELL_ETHBTC in code). Lastly, we sell our ETH/USD since it is the more expensive currency. 


If the manual division is smaller than the coin pair value (DIV < ETH/BTC), this implies that the price of ETH/USD is cheaper. 

	Flow: BUY ETH/USD => BUY ETH/BTC => SELL BTC/USD

We purchase an amount of ETH/USD (BUY_ETH in our code). Then we convert our ETH into BTC by purchasing ETHBTC (BUY_ETHBTC in code). We sell BTC/USD to net our profit. 


This logic forms the second half of our arbitrage condition checker in which we place the correct trades given the condition. Feel free to play around with the min_arb_percent value, as trades will only occur given that the discrepancy is larger. 


    if DIV > ETHBTC * (1 + min_arb_percent/100):
        order1 = post_Alpaca_order("BTCUSD", BUY_BTC, "buy")
        if order1.status_code == 200:
            order2 = post_Alpaca_order("ETH/BTC", BUY_ETHBTC, "buy")
            if order2.status_code == 200:
                order3 = post_Alpaca_order("ETHUSD", BUY_ETHBTC, "sell")
                if order3.status_code == 200:
                    print("Done (type 1) eth: {} btc: {} ethbtc {}".format(ETH, BTC, ETHBTC))
                    print("Spread: +{}".format(spread * 100))
                else:
                    post_Alpaca_order("ETH/BTC", BUY_ETHBTC, "sell")
                    print("Bad Order 3")
                    exit()
            else:
                post_Alpaca_order("BTCUSD", BUY_BTC, "sell")
                print("Bad Order 2")
                exit()
        else:
            print("Bad Order 1")
            exit()
 
    # when ETH/USD is cheaper
    elif DIV < ETHBTC * (1 - min_arb_percent/100):
        order1 = post_Alpaca_order("ETHUSD", BUY_ETH, "buy")
        if order1.status_code == 200:
            order2 = post_Alpaca_order("ETH/BTC", BUY_ETH, "sell")
            if order2.status_code == 200:
                order3 = post_Alpaca_order("BTCUSD", SELL_ETHBTC, "sell")
                if order3.status_code == 200:
                    print("Done (type 2) eth: {} btc: {} ethbtc {}".format(ETH, BTC, ETHBTC))
                    print("Spread: -{}".format(spread * 100))
                else:
                    post_Alpaca_order("ETH/BTC", SELL_ETHBTC, "buy")  
                    print("Bad Order 3")                
                    exit()
            else:
                post_Alpaca_order("ETHUSD", BUY_ETH, "sell")
                print("Bad Order 2")
                exit()    
        else:
            print("Bad order 1")
            exit()
    else:
        print("No arb opportunity, spread: {}".format(spread * 100))
        spreads.append(spread)


We check the order status of each trade because each trade in a Triangular Arbitrage depends on the successful completion of the one before it. Depending on which trade might fail, we sell or buy the correct amount to return to the positions in place before executing the sequence. Adding these guards to our code ensures that we don’t get caught in never-ending loops. 

Main Function:
Congratulations! We have the necessary functions in place to run our code. Before moving to the Main function, add these 3 lines to the bottom of your file:

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
loop.close()

We initialize these since our code utilizes concurrency and asynchronous functions.

Our Main function should be defined above the other functions as follows: 
async def main():
        while True:
            task1 = loop.create_task(get_quote("ETH/USD"))
            task2 = loop.create_task(get_quote("BTC/USD"))
            task3 = loop.create_task(get_quote("ETH/BTC"))
            # Wait for the tasks to finish
            await asyncio.wait([task1, task2, task3])
            await check_arb()
            # # Wait for the value of waitTime between each quote request
            await asyncio.sleep(waitTime)

We wait to get the latest quotes, then run check_arb(). Play around with waitTime as the code will execute as often as its value. 

You should eventually see 3-trade sequences like this in your account!



Here is $3 of risk-free profit (not including fees). 
Considerations:
Fees & Trading Volume:
Arbitrage opportunities are ultimately a game of trading volume and fees. Because profit margins tend to be <1% of the trade amount, traders can best capitalize on Triangular Arbitrage with high trading volume. 

At the same time, exercise your best judgment as a trader with respect to fees. Know at what minimum arbitrage percent and trading volume your trades will be profitable. Check out Alpaca's Updated Crypto Fees, and as always, make sure to backtest your strategies fully. 


Sources:
https://www.investopedia.com/terms/t/triangulararbitrage.asp#:~:text=Triangular%20arbitrage%20is%20the%20result,programs%20to%20automate%20the%20process.



Please note that this article is for general informational purposes only. All screenshots are for illustrative purposes only. Actual currency exchange and crypto prices may vary depending on the market price at that particular time. Alpaca does not recommend any specific cryptocurrencies.

Cryptocurrency services are made available by Alpaca Crypto LLC ("Alpaca Crypto"), a FinCEN registered money services business (NMLS # 2160858), and a wholly-owned subsidiary of AlpacaDB, Inc. Alpaca Crypto is not a member of SIPC or FINRA. Cryptocurrencies are not stocks and your cryptocurrency investments are not protected by either FDIC or SIPC. Depending on your location, cryptocurrency services may be provided by West Realm Shires Services, Inc., d/b/a FTX US (NMLS #1957771). 
 
This is not an offer, solicitation of an offer, or advice to buy or sell cryptocurrencies, or open a cryptocurrency account in any jurisdiction where Alpaca Crypto, or FTX US respectively, are not registered or licensed, as applicable.
 
Cryptocurrency is highly speculative in nature, involves a high degree of risks, such as volatile market price swings, market manipulation, flash crashes, and cybersecurity risks. Cryptocurrency is not regulated or is lightly regulated in most countries. Cryptocurrency trading can lead to large, immediate and permanent loss of financial value. You should have appropriate knowledge and experience before engaging in cryptocurrency trading. For additional information, please click here.
 
Please see alpaca.markets and Alpaca’s Disclosure Library for more information.


