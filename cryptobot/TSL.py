import threading
class TrailingStopLoss:

    def __init__(self, asset_obj, follow_percent, sell_quantity_percent=None, limit_sell_safety_percent=0, sell_order_type='limit') -> None:
        self.socket_man = asset_obj.SOCKET_MANAGER
        self.asset_obj = asset_obj
        self.sell_quantity_percent = sell_quantity_percent
        self.follow_at_percent = follow_percent
        self.highest_price = 0.0
        self.follow_at_price = 0.0
        self.sell_order_type = sell_order_type
        self.limit_sell_safety_perc = limit_sell_safety_percent
        self.target_reached = False

    def start(self):
        self.socket_man.start_trade_socket(self.asset_obj.symbol,self.process_data)

    def process_data(self, msg):
        latest_price = float(msg['p'])
        print(self.asset_obj, f'Current Price: {latest_price} , SL Price : {self.follow_at_price}')
        if latest_price > self.highest_price:
            print(self.asset_obj, f'new high price : {latest_price} > {self.highest_price}')
            self.highest_price = latest_price
            self.follow_at_price = self.highest_price - (self.follow_at_percent * self.highest_price / 100)
        
        elif latest_price <= self.follow_at_price:
            with threading.Lock():
                if not self.target_reached:
                    self.target_reached = True
                    self.stop()
                    print(self.asset_obj, f'target price reached : {latest_price}')
                    correction = latest_price * self.limit_sell_safety_perc / 100
                    sell_price = latest_price - correction
                    sell_price = float(round(sell_price, self.asset_obj.price_precision))
                    print(self.asset_obj, "sell price :", sell_price)
                    if self.sell_order_type == 'limit':
                        order = self.asset_obj.limit_sell_order(quantity_percent=self.sell_quantity_percent, exact_price=sell_price)
                    elif self.sell_order_type == 'market':
                        order = self.asset_obj.market_sell(self.sell_quantity_percent)
                    print(self.asset_obj, f"{self.sell_order_type} sell order placed : ", order)

    def stop(self):
        try:
            self.socket_man.stop_socket(self.asset_obj.symbol)  
        except Exception as e:
            print("Could not stop TSL, reason :", e)