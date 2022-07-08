import alpaca_trade_api as alpaca

API_KEY = 'PKTU92QZTXEW9REEB156'
SECRET_KEY = 'M5A9DW8Yr910u69xfvVdO1Y6GVkZdVkbB1EpQyVT'

rest_api = alpaca.REST(API_KEY, SECRET_KEY, 'https://paper-api.alpaca.markets')
account = rest_api.get_account()
print(account)

rest_api.submit_order(symbol="BTCUSD", notional=0.005, side="buy")
print("done")