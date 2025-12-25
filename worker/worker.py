# backend/worker.py
import threading
import asyncio
from ib_insync import IB, Stock, LimitOrder, Order

class IBWorker:
    def __init__(self):
        self.ib = IB()
        self.connected = False

    def _connect_thread(self, host, port, clientId):
        loop = asyncio.new_event_loop()
        self.loop = loop
        asyncio.set_event_loop(loop)
        try:
            self.ib.connect(host, port, clientId)
            self.connected = True
            print("Connected to IBKR")
            loop.run_forever()
        except Exception as e:
            print("API connection failed:", e)

    def start(self, host='127.0.0.1', port=7496, clientId=1):
        """Запуск подключения в отдельном потоке"""
        threading.Thread(
            target=self._connect_thread, args=(host, port, clientId), daemon=True
        ).start()

    # Пример отправки лимитного ордера
    def place_limit_order(self, symbol: str, qty: int, price: float, action: str = "BUY"):
        if not self.connected:
            print("Not connected to IBKR yet")
            return None

        contract = Stock(symbol, 'SMART', 'USD')
        order = LimitOrder(action, qty, price)
        trade = self.ib.placeOrder(contract, order)
        return trade

    def place_trailing_order_threadsafe(self, symbol: str, qty: int, limit_price: float, trail_amount: float,
                                        action: str = "BUY"):
        """Запуск трейлинг ордера в отдельном потоке, чтобы избежать проблем с event loop"""
        result = {}

        def target():
            result['trade'] = self.place_trailing_order(symbol, qty, limit_price, trail_amount, action)

        thread = threading.Thread(target=target)
        thread.start()
        thread.join()
        return result.get('trade')

    # Добавляем трейлинг-ордер
    from ib_insync import Stock, Order
    import asyncio

    def place_trailing_order(
            self,
            symbol: str,
            qty: int,
            limit_price: float,
            trail_amount: float,
            action: str = "BUY"
    ):
        if not self.connected or not self.loop:
            print("Not connected to IBKR yet")
            return None

        contract = Stock(symbol, 'SMART', 'USD')

        order = Order(
            action=action,
            orderType="TRAIL",
            totalQuantity=qty,
            lmtPrice=limit_price,
            auxPrice=trail_amount
        )

        async def place():
            return self.ib.placeOrder(contract, order)

        future = asyncio.run_coroutine_threadsafe(place(), self.loop)
        return future.result()

# Пример использования:
# worker = IBWorker()
# worker.start()
# worker.place_limit_order('NVDA', 10, 500)
# worker.place_trailing_order('NVDA', 10, 500, 5)
