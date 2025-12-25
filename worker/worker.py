from ib_insync import IB, Stock, Option, Order
import asyncio, threading

class IBWorker:
    def __init__(self):
        self.ib = IB()
        self.connected = False
        self.loop = None

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
        threading.Thread(
            target=self._connect_thread, args=(host, port, clientId), daemon=True
        ).start()

    def build_contract(self, symbol, is_option=False, expiry=None, strike=None, right="C"):
        if is_option:
            contract = Option(symbol, expiry, strike, right, 'SMART')
        else:
            contract = Stock(symbol, 'SMART', 'USD')
        return contract

    def place_order(self, symbol, qty, limit_price=None, trail_amount=None, order_type="Limit",
                    is_option=False, expiry=None, strike=None, right="C", action="BUY"):
        if not self.connected or not self.loop:
            print("Not connected to IBKR yet")
            return None

        contract = self.build_contract(symbol, is_option, expiry, strike, right)
        asyncio.run_coroutine_threadsafe(self.ib.qualifyContractsAsync(contract), self.loop).result()

        req_id = self.ib.client.getReqId()

        # TRAILING ORDER
        if order_type.lower() == "trail":
            parent_order = Order(
                orderId=req_id,
                action=action,
                orderType="LMT",
                totalQuantity=qty,
                lmtPrice=limit_price,
                tif="DAY",
                transmit=False
            )

            trail_order = Order(
                action="SELL" if action=="BUY" else "BUY",  # всегда противоположное для трейла
                orderType="TRAIL",
                auxPrice=trail_amount,
                totalQuantity=qty,
                parentId=req_id,
                transmit=True
            )

            async def place_orders():
                trade_parent = self.ib.placeOrder(contract, parent_order)
                await asyncio.sleep(0.2)
                trade_trail = self.ib.placeOrder(contract, trail_order)
                return trade_parent, trade_trail

            future = asyncio.run_coroutine_threadsafe(place_orders(), self.loop)
            return future.result()

        # OTHER ORDERS: Limit / Market / Stop
        else:
            ot = order_type.upper()
            if ot == "LIMIT":
                ot = "LMT"
            elif ot == "MARKET":
                ot = "MKT"
            elif ot == "STOP":
                ot = "STP"

            order = Order(
                orderId=req_id,
                action=action,
                orderType=ot,
                totalQuantity=qty,
                lmtPrice=limit_price if ot=="LMT" else None,
                transmit=True
            )

            async def place():
                return self.ib.placeOrder(contract, order)

            future = asyncio.run_coroutine_threadsafe(place(), self.loop)
            return future.result()
