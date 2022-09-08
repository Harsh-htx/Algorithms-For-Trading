from alice_blue import *
import csv
import datetime
import statistics
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


# access_token = "-cSOX_024Fo7-GbXYc8a2y5z0U3kfkXBO9x8mQdXahk.7raJdBGSjuya1xg0-3L0UIUkr6XOeJJc26q_vQtsZto"
alice=AliceBlue(username= username ,password= password, access_token=access_token)

socket_opened = False
def event_handler_quote_update(message):
 	#print(f" Exchange:{message['exchange']}, Token:{message['token']}, Symbol:{message['instrument'].symbol}, Lot_Size:{message['instrument'].lot_size}, LTP:{message['ltp']}, High:{message['high']}, Low:{message['low']}, Volume:{message['volume']}, Time:{datetime.datetime.fromtimestamp(message['exchange_time_stamp'])} ")
	Stock = message['instrument'].symbol
	ltp = message['ltp']
	quantity = int(1)
	minute_close = []
	current_signal = ''
	while True:
		if(datetime.datetime.now().second == 0):
			minute_close.append(ltp)
			print(f"Passed time: {len(minute_close)} minute ")
			if(len(minute_close) > 24):
				sma_9 = statistics.mean(minute_close[-9:])
				sma_24 = statistics.mean(minute_close[-24:])
				if(current_signal != 'Buy'):
					if(sma_9 > sma_24):
						buy_order = alice.place_order(transaction_type = TransactionType.Buy,
												   instrument = alice.get_instrument_by_symbol('NSE', Stock),
												   quantity = quantity,
												   order_type = OrderType.Market,
												   product_type = ProductType.Intraday,
												   price = 0.0,
												   trigger_price = None,
												   stop_loss = None,
												   square_off = None,
												   trailing_sl = None,
												   is_amo = False)
						print(f"Buy Order Placed for: {Stock}, at Price: {ltp} for Quantity: {quantity}, with order_id: {buy_order['data']['oms_order_id']} at time: {datetime.datetime.now()}")
						current_signal = 'Buy'
				if(current_signal != 'Sell'):
					if(sma_9 < sma_24):
						sell_order = alice.place_order(transaction_type = TransactionType.Sell,
												   instrument = alice.get_instrument_by_symbol('NSE', Stock),
												   quantity = quantity,
												   order_type = OrderType.Market,
												   product_type = ProductType.Intraday,
												   price = 0.0,
												   trigger_price = None,
												   stop_loss = None,
												   square_off = None,
												   trailing_sl = None,
												   is_amo = False)
						print(f"Sell Order Placed for: {Stock}, at Price: {ltp} for Quantity: {quantity}, with order_id: {sell_order['data']['oms_order_id']} at time: {datetime.datetime.now()}")
						current_signal = 'Sell'
			time.sleep(1)
		time.sleep(0.1)

def open_callback():
	global socket_opened
	socket_opened = True

alice.start_websocket(subscribe_callback=event_handler_quote_update,
					  socket_open_callback=open_callback,
					  run_in_background=True)
while(socket_opened==False):
	pass
while True:
	alice.subscribe(alice.get_instrument_by_symbol('NSE', 'TATASTEEL'), LiveFeedType.MARKET_DATA)
	time.sleep(1)