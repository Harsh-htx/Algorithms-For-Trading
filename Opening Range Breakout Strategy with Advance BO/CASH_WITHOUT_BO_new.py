# pip install schedule
# pip install alice_blue
from alice_blue import *
import schedule
import csv
import datetime
import time
import document_details
from threading import Timer
import requests

username = document_details.username
password = document_details.password
twoFA = document_details.twoFA
api_secret = document_details.api_secret
app_id = document_details.app_id
bot_Token = document_details.token
bot_Chatid = document_details.chat_id


access_token = AliceBlue.login_and_get_access_token(username= username, password= password, twoFA= twoFA,  api_secret= api_secret, app_id = app_id)
# print(access_token)

with open('access_token.txt','w') as wr1:
	wr=csv.writer(wr1)
	wr.writerow([access_token])
access_token=open('access_token.txt','r').read().strip()


# access_token = "GwDIae7g0jPqAjMwsq-N44cx5BSL5UVhK9rQuck1fw0._VbSepaXrZc2DtbOrZWfmpAOzq9Y6W6ScriGAMiFNqM"
alice=AliceBlue(username= username ,password= password, access_token=access_token)

# def telegram_send_message(bot_message):
# 	global bot_Token, bot_Chatid
# 	bot_Token = bot_Token
# 	bot_Chatid = bot_Chatid   
# 	to_url = "https://api.telegram.org/bot{}/sendMessage?chat_id={}&text={}&parse_mode=HTML".format(bot_Token,bot_Chatid,bot_message)    
# 	response = requests.post(to_url)

orderplacetime = int(9) * 60 + int(30)
closingtime = int(15)*60 + int(9)
timenow = (datetime.datetime.now().hour * 60 + datetime.datetime.now().minute)
print("Waiting for 9.30 AM , CURRENT TIME : {}".format(datetime.datetime.now()))
# telegram_send_message("Waiting for 9.30 AM , CURRENT TIME : {}".format(datetime.datetime.now()))

while timenow < orderplacetime:
	time.sleep(0.2)
	timenow = (datetime.datetime.now().hour * 60 + datetime.datetime.now().minute)
print("Ready for trading, CURRENT TIME : {}".format(datetime.datetime.now()))
# telegram_send_message("Ready for trading, CURRENT TIME : {}".format(datetime.datetime.now()))

def order_management():
	order = alice.get_order_history()
	
	if bool(order["data"]) == True:
		if bool(order["data"]["pending_orders"]) == True:
			order_pending = order["data"]["pending_orders"]
			day_wise = alice.get_daywise_positions()
			position = day_wise["data"]["positions"]

			closed_trade = []
			for i in position:
				quantity = i["net_quantity"]
				script = i["trading_symbol"]
				if quantity == 0:
					closed_trade.append(script)

			for i in order_pending:
				script = i["trading_symbol"]
				order_id = i['oms_order_id']
				if script in closed_trade:
					alice.cancel_order(order_id)
					print(f"Cancelling pending order for {script} : {order_id} at time: {datetime.datetime.now()}")
					# telegram_send_message(f"Cancelling pending order for {script} : {order_id} at time: {datetime.datetime.now()}")
	Timer(1, order_management).start()

completed_id = []
pending_id = []

def closing_position():

	order = alice.get_order_history()
	day_wise = alice.get_daywise_positions()

	position = day_wise["data"]["positions"]
	order_pending = order["data"]["pending_orders"]
	order_completed = order["data"]["completed_orders"]

	for i in order_completed:
		order_id = i["oms_order_id"]
		completed_id.append(order_id)

	for i in order_pending:
		order_id = i["oms_order_id"]
		pending_id.append(order_id)

	for i in position:
		token = i['instrument_token']
		symbol = i['trading_symbol']
		quant = i['net_quantity']

		quantity = abs(quant)
		if quant > 0:
			message = alice.place_order(transaction_type = TransactionType.Sell, instrument = alice.get_instrument_by_token('NSE', token), quantity = quantity , order_type = OrderType.Market, product_type = ProductType.Intraday, price = 0.0, trigger_price = None, stop_loss = None, square_off = None, trailing_sl = None, is_amo = False)
			print(f"Sell Order Placed for {symbol}, for Quantity: {quantity}, with order_id: {message['data']['oms_order_id']} at time: {datetime.datetime.now()}")
		
		elif quant < 0:
			message = alice.place_order(transaction_type = TransactionType.Buy, instrument = alice.get_instrument_by_token('NSE', token), quantity = quantity , order_type = OrderType.Market, product_type = ProductType.Intraday, price = 0.0, trigger_price = None, stop_loss = None, square_off = None, trailing_sl = None, is_amo = False)
			print(f"Buy Order Placed for {symbol}, for Quantity: {quantity}, with order_id: {message['data']['oms_order_id']} at time: {datetime.datetime.now()}")

		elif quant == 0:
			print("No Position to Exit")
			pass

	for i in pending_id:
		alice.cancel_order(i)
		print(f"Order Cancelled for {i}")
		# telegram_send_message(f"Order Cancelled for {i}")

traded_stocks = []
socket_opened = False

def event_handler_quote_update(message):
	# print(f" Exchange:{message['exchange']}, Token:{message['token']}, Symbol:{message['instrument'].symbol}, Lot_Size:{message['instrument'].lot_size}, LTP:{message['ltp']}, High:{message['high']}, Low:{message['low']}, Volume:{message['volume']}, Time:{datetime.datetime.fromtimestamp(message['exchange_time_stamp'])} ")
	# telegram_send_message(f" Exchange:{message['exchange']}, Token:{message['token']}, Symbol:{message['instrument'].symbol}, Lot_Size:{message['instrument'].lot_size}, LTP:{message['ltp']}, High:{message['high']}, Low:{message['low']}, Volume:{message['volume']}, Time:{datetime.datetime.fromtimestamp(message['exchange_time_stamp'])} ")
	
	script = message['instrument'].symbol
	high = message['high']
	low = message['low']
	ltp = message['ltp']
	quantity = int(1)

	# Target is 1.5% of ltp of script and Stoploss is 2% of ltp of script
	buy_target = round(ltp*1.015,1) 
	buy_stoploss = round(ltp*0.98,1)
	sell_target = round(ltp*0.985,1)
	sell_stoploss = round(ltp*1.02,1)

	if (ltp == high) and (script not in traded_stocks):
		traded_stocks.append(script)		
		order1 = {"transaction_type" : TransactionType.Buy, "instrument" : alice.get_instrument_by_symbol('NSE', script), "quantity" : quantity , "order_type" : OrderType.Limit, "product_type" : ProductType.Intraday, "price" : ltp, "trigger_price" : None, "stop_loss" : None, "square_off" : None, "trailing_sl" : None, "is_amo" : False}
		order2 = {"transaction_type" : TransactionType.Sell, "instrument" : alice.get_instrument_by_symbol('NSE', script), "quantity" : quantity , "order_type" : OrderType.Limit, "product_type" : ProductType.Intraday, "price" : buy_target, "trigger_price" : None, "stop_loss" : None, "square_off" : None, "trailing_sl" : None, "is_amo" : False}
		order3 = {"transaction_type" : TransactionType.Sell, "instrument" : alice.get_instrument_by_symbol('NSE', script), "quantity" : quantity , "order_type" : OrderType.StopLossLimit, "product_type" : ProductType.Intraday, "price" : buy_stoploss, "trigger_price" : buy_stoploss, "stop_loss" : None, "square_off" : None, "trailing_sl" : None, "is_amo" : False}
		orders_buy = alice.place_basket_order([order1,order2,order3])
		print(f"Buy Order Placed for: {script}, at Price: {ltp} for Quantity: {quantity}, at time: {datetime.datetime.now()}")
		# telegram_send_message(f"Buy Order Placed for: {script}, at Price: {ltp} for Quantity: {quantity}, at time: {datetime.datetime.now()}")

	if (ltp == low) and (script not in traded_stocks):
		traded_stocks.append(script)
		order1 = {"transaction_type" : TransactionType.Sell, "instrument" : alice.get_instrument_by_symbol('NSE', script), "quantity" :  quantity , "order_type" : OrderType.Limit, "product_type" : ProductType.Intraday, "price" : ltp, "trigger_price" : None, "stop_loss" : None, "square_off" : None, "trailing_sl" : None, "is_amo" : False}
		order2 = {"transaction_type" : TransactionType.Buy, "instrument" : alice.get_instrument_by_symbol('NSE', script), "quantity" : quantity , "order_type" : OrderType.Limit, "product_type" : ProductType.Intraday, "price" : sell_target, "trigger_price" : None, "stop_loss" : None, "square_off" : None, "trailing_sl" : None, "is_amo" : False}
		order3 = {"transaction_type" : TransactionType.Buy, "instrument" : alice.get_instrument_by_symbol('NSE', script), "quantity" : quantity , "order_type" : OrderType.StopLossLimit, "product_type" : ProductType.Intraday, "price" : sell_stoploss, "trigger_price" : sell_stoploss, "stop_loss" : None, "square_off" : None, "trailing_sl" : None, "is_amo" : False}
		orders_sell = alice.place_basket_order([order1,order2,order3])
		print(f"Sell Order Placed for: {script}, at Price: {ltp} for Quantity: {quantity}, at time: {datetime.datetime.now()}")
	  	# telegram_send_message(f"Sell Order Placed for: {script}, at Price: {ltp} for Quantity: {quantity}, at time: {datetime.datetime.now()}")

def open_callback():
	global socket_opened
	socket_opened = True

alice.start_websocket(subscribe_callback=event_handler_quote_update, socket_open_callback=open_callback, run_in_background=True)
while(socket_opened==False):
	pass

tickerlist = ["ZEEL", "ITC", "IBULHSGFIN", "SBIN", "DLF", "RBLBANK", "POWERGRID", "EXIDEIND", "PETRONET", "APOLLOTYRE", "INDUSTOWER", "AMBUJACEM", "HINDALCO", "JINDALSTEL", "TORNTPOWER", "BANDHANBNK"]
for i in tickerlist:
	instrument = alice.get_instrument_by_symbol('NSE', i)
	alice.subscribe(instrument, LiveFeedType.MARKET_DATA)

order_management()
schedule.every().day.at("15:10").do(closing_position)

while True:
	schedule.run_pending()
	time.sleep(1)