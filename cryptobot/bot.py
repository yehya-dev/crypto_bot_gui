import requests, math
from cryptobot.TSL import TrailingStopLoss
from binance.client import Client
from unicorn_binance_websocket_api.unicorn_binance_websocket_api_manager import BinanceWebSocketApiManager
import dotenv
import os

class CryptoAsset:
    dotenv.load_dotenv()
    API_KEY = os.environ.get('API_KEY')
    SECRET_KEY = os.environ.get('SECRET_KEY')

    CLIENT = Client(API_KEY, SECRET_KEY)

    LOT_SIZE_DATA = {}
    info = CLIENT.get_exchange_info()
    for coin in info['symbols']:
        for item in coin['filters']:
            if item['filterType'] == 'LOT_SIZE':
                LOT_SIZE_DATA[coin['symbol']] = float(item['stepSize'])
                break
            
    class SOCKET_MANAGER:

        callback_fns = dict()
        def run(data, stream_buffer_name):
            data = data.get('data', {})
            symbol = data.get('s')
            if symbol and (callback := CryptoAsset.SOCKET_MANAGER.callback_fns.get(symbol)):
                callback(data)

        ws_api_man = BinanceWebSocketApiManager(exchange="binance.com", process_stream_data=run)
        
        ws_stream_sid = None
        
        @classmethod
        def start_trade_socket(self, symbol, callback):
            self.callback_fns[symbol] = callback
            if not self.ws_stream_sid:
                self.ws_stream_sid =  self.ws_api_man.create_stream(['trade'], [symbol.lower()], output="dict")
            else:
                self.ws_api_man.subscribe_to_stream(self.ws_stream_sid, channels=[], markets=[symbol.lower()])
            
        
        @classmethod
        def stop_socket(self, symbol):
            self.ws_api_man.unsubscribe_from_stream(self.ws_stream_sid, markets=[symbol.lower()])
            self.callback_fns.pop(symbol.upper())
            if not self.callback_fns:
                self.ws_api_man.stop_stream(self.ws_stream_sid)
                self.ws_stream_sid = None

        @classmethod
        def restart_socket(self):
            self.ws_api_man.set_restart_request(self.ws_stream_sid)

    def __init__(self, base_currency :str, quote_currency :str = "USDT", is_pump=False):
        self.quote_currency = quote_currency.upper()
        self.base_currency = base_currency.upper()
        self.symbol = self.base_currency + self.quote_currency

        if not self.symbol in self.LOT_SIZE_DATA:
            raise ValueError("This coin pair is not listed on binance or is invalid.")

        self.quote_currency_balance = float(self.CLIENT.get_asset_balance(asset=quote_currency).get('free'))
        self.is_pump = is_pump
        self.initial_price = self.get_ticker_price()
        self.set_quantity_precision()
        self.tsl = None

        if not is_pump:
            self.get_current_asset_info()
            self.set_price_precision()
            
    @property
    def base_currency_quantity_inhand(self):
        return float(self.CLIENT.get_asset_balance(asset=self.base_currency).get('free'))

    def get_ticker_price(self):
        """get the current price of a symbol.

        params
        symbol : str
        """
        return float(requests.get(f'https://api.binance.com/api/v1/ticker/price?symbol={self.symbol}').json().get('price'))

    def get_current_asset_info(self):
        self.current_symbol_info = self.CLIENT.get_symbol_info(self.symbol)

    def set_price_precision(self):
        tickSize = float(self.current_symbol_info['filters'][0]['tickSize'])
        self.price_precision = int(round(-math.log(tickSize, 10), 0))

    def set_quantity_precision(self):
        stepSize = self.LOT_SIZE_DATA[self.symbol]
        self.quantity_precision = int(round(-math.log(stepSize, 10), 0))

    def get_price_at_percentage(self, percentage):
        newPrice = self.initial_price + (self.initial_price * float(percentage) / 100)
        newPrice = float(round(newPrice, self.price_precision))
        return newPrice
    
    def market_buy(self, percentage_of_quote: float) -> dict:
        """buy an base for a percent of the quote"""
        trade_amount = percentage_of_quote / 100
        quantity = self.quote_currency_balance / self.initial_price * trade_amount
        quantity = float(round(quantity, self.quantity_precision))
        print(quantity)
        buy_order = self.CLIENT.order_market_buy(
        symbol=self.symbol,
        quantity=str(quantity))
        if self.is_pump:
            self.get_current_asset_info()
            self.set_price_precision()
        return buy_order

            
    def market_sell(self, sell_percent=None):
        """sell a particular percent of base, sell 100% base by default"""
        sell_quantity = self.base_currency_quantity_inhand
        if sell_percent:
            sell_quantity = self.base_currency_quantity_inhand * sell_percent / 100

        sell_quantity = float(round(sell_quantity, self.quantity_precision))
        
        market_sell_order = self.CLIENT.order_market_sell(
        symbol=self.symbol,
        quantity=sell_quantity)

        return market_sell_order


    def multi_limit_sell(self, sell_data :dict):
        """set limit sell orders of set quantities at set prices.
        
        Keyword arguments:
            sell_data : dict
                price increase percent (key) : sell amount percent (value) 

        Note: For every next limit order the percent of the remaining available base currency is calculated, so
        to sell of everything in the end it's best to have a final order with {percent: None}.

        Ex : 50 + 50 won't sell off everything, it will only sell 75% of the total base asset, to actually sell 100%
        pass sell data as: 
            {
                1 : 50,
                1.5 : None
            }

        """
        for price_percent, sell_quantity_percent in sell_data.items():
            self.limit_sell_order(price_percent, sell_quantity_percent)

    def cancel_all_orders(self):
        open_orders = self.CLIENT.get_open_orders(symbol=self.symbol)
        for item in open_orders:
            order_id = item['orderId']
            self.CLIENT.cancel_order(symbol=self.symbol, order_id = str(order_id))
    
    def limit_sell_order(self, price_percent=None, quantity_percent=None, exact_price=None):
        if not (price_percent or exact_price):
            raise ValueError("Either price percent or exact price is required to set a limit sell order")

        try:
            if price_percent:
                sell_price = self.get_price_at_percentage(price_percent)
            else:
                sell_price = exact_price
                
            sell_quantity = self.base_currency_quantity_inhand
            if quantity_percent:
                sell_quantity = self.base_currency_quantity_inhand * quantity_percent / 100
                
            sell_quantity = float(round(sell_quantity, self.quantity_precision))

            limit_sell_order = self.CLIENT.order_limit_sell(
                symbol=self.symbol,
                quantity=sell_quantity,
                price=sell_price)

            return limit_sell_order

        except Exception as e:
            print(f"couldn't place limit sell order with price: {sell_price} and quantity: {sell_quantity} | {e}")

    def start_TSL(self, follow_percent, sell_quantity_percent=None, limit_sell_safety_percent=0, sell_order_type='limit'):
        if self.tsl:
            self.stop_TSL()

        self.tsl = TrailingStopLoss(self, follow_percent, sell_quantity_percent, limit_sell_safety_percent, sell_order_type)
        self.tsl.start()

    def stop_TSL(self):
        if self.is_TSL_alive():
            self.tsl.stop()

    def is_TSL_alive(self):
        return self.symbol in self.SOCKET_MANAGER.callback_fns

    def get_balance(self):
        return self.base_currency_quantity_inhand

    def limit_buy_order(self,  price_percent=None, quantity_percent=None, exact_price=None):
        if not (price_percent or exact_price):
            raise ValueError("Either price percent or exact price is required to set a limit sell order")

        try:
            if price_percent:
                if not price_percent < 0:
                    price_percent *= -1
                sell_price = self.get_price_at_percentage(price_percent)
            else:
                sell_price = exact_price
                
            sell_quantity = self.base_currency_quantity_inhand
            if quantity_percent:
                sell_quantity = self.base_currency_quantity_inhand * quantity_percent / 100
                
            sell_quantity = float(round(sell_quantity, self.quantity_precision))

            limit_sell_order = self.CLIENT.order_limit_sell(
                symbol=self.symbol,
                quantity=sell_quantity,
                price=sell_price)

            self.base_currency_quantity_inhand -= float(limit_sell_order['executedQty'])

            return limit_sell_order

        except Exception as e:
            print(f"couldn't place limit sell order with price: {sell_price} and quantity: {sell_quantity} | {e}")

    def __repr__(self) -> str:
        return self.symbol

