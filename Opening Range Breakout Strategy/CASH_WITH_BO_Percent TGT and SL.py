from alice_blue import *
import pdb
import csv
import datetime
import time
import document_details


username = document_details.username
password = document_details.password
twoFA = document_details.twoFA
api_secret = document_details.api_secret
app_id = document_details.app_id


access_token = AliceBlue.login_and_get_access_token(username= username, password= password, twoFA= twoFA,  api_secret= api_secret, app_id = app_id)
# print(access_token)

with open('access_token.txt','w') as wr1:
	wr=csv.writer(wr1)
	wr.writerow([access_token])
access_token=open('access_token.txt','r').read().strip()


# access_token = "2PHwuCr-62DOdfraS2bjASmhsqb6TWF_8i05EdYgwTo.O5wz3DJWr_blhNh121NO-Kgu2LAnU8GyXZGd8peEciA"
alice=AliceBlue(username= username ,password= password, access_token=access_token)


orderplacetime = int(9) * 60 + int(30)
timenow = (datetime.datetime.now().hour * 60 + datetime.datetime.now().minute)
print("Waiting for 9.30 AM , CURRENT TIME:{}".format(datetime.datetime.now()))

while timenow < orderplacetime:
	time.sleep(0.2)
	timenow = (datetime.datetime.now().hour * 60 + datetime.datetime.now().minute)
print("Ready for trading, CURRENT TIME:{}".format(datetime.datetime.now()))

# pdb.set_trace() # This is kill switch button. Enable it if you want to stop the programme from execution.

traded_stocks = []
socket_opened = False

def event_handler_quote_update(message):
	# print(f"{message}")
	# print(f" Exchange:{message['exchange']}, Token:{message['token']}, Symbol:{message['instrument'].symbol}, Lot_Size:{message['instrument'].lot_size}, LTP:{message['ltp']}, High:{message['high']}, Low:{message['low']}, Volume:{message['volume']}, Time:{datetime.datetime.fromtimestamp(message['exchange_time_stamp'])} ")

	Stock = message['instrument'].symbol
	high = message['high']
	low = message['low']
	ltp = message['ltp']
	quantity = int(100)
	target = round(ltp*0.015, 1) # for 1.5 % tgt of each stock 
	stoploss = round(ltp*0.01, 1) # for 1 % sl of each stock

	if (ltp == high) and (Stock not in traded_stocks):
		message = alice.place_order(transaction_type = TransactionType.Buy, instrument = alice.get_instrument_by_symbol('NSE', Stock), quantity = quantity , order_type = OrderType.Limit, product_type = ProductType.BracketOrder, price = ltp, trigger_price = None, stop_loss = stoploss, square_off = target, trailing_sl = None, is_amo = False)
		print(f"Buy Order  Placed for {Stock}, at Price: {ltp} for Quantity: {quantity}, with order_id: {message['data']['oms_order_id']} at time: {datetime.datetime.now()}")
		traded_stocks.append(Stock)


	if (ltp == low) and (Stock not in traded_stocks):
		message = alice.place_order(transaction_type = TransactionType.Sell, instrument = alice.get_instrument_by_symbol('NSE', Stock), quantity =  quantity , order_type = OrderType.Limit, product_type = ProductType.BracketOrder, price = ltp, trigger_price = None, stop_loss = stoploss, square_off = target, trailing_sl = None, is_amo = False)
		print(f"Sell Order  Placed for {Stock}, at Price: {ltp} for Quantity: {quantity}, with order_id: {message['data']['oms_order_id']} at time: {datetime.datetime.now()}")
		traded_stocks.append(Stock)

def open_callback():
	global socket_opened
	socket_opened = True

alice.start_websocket(subscribe_callback=event_handler_quote_update,
					socket_open_callback=open_callback,
					run_in_background=True)
while(socket_opened==False):
	pass

# tickerlist = ["ZEEL", "ITC", "IBULHSGFIN", "SBIN", "DLF", "RBLBANK", "POWERGRID", "EXIDEIND", "PETRONET", "APOLLOTYRE", "INDUSTOWER", "AMBUJACEM", "HINDALCO", "JINDALSTEL", "TORNTPOWER", "BANDHANBNK"]
while True:
	tickerlist = ["ZEEL", "ITC", "IBULHSGFIN", "SBIN", "DLF", "RBLBANK", "POWERGRID", "EXIDEIND", "PETRONET", "APOLLOTYRE", "INDUSTOWER", "AMBUJACEM", "HINDALCO", "JINDALSTEL", "TORNTPOWER", "BANDHANBNK"]
	for i in tickerlist:
		instrument = alice.get_instrument_by_symbol('NSE', i)
		try:
			alice.subscribe(instrument, LiveFeedType.MARKET_DATA)
		except TypeError:
			pass