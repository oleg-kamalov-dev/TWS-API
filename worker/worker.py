from ib_insync import IB, Stock, Option, Order, Index
import asyncio, threading
import math

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

    # ------------------ НОВЫЕ ФУНКЦИИ ------------------

    def get_underlying_price(self, symbol):
        """
        Возвращает текущую цену underlying (акция или индекс)
        """
        symbol = symbol.upper()
        if not self.connected or not self.loop:
            return None

        if symbol in ['SPX', 'NDX', 'RUT']:
            contract = Index(symbol, 'CBOE', 'USD')
        else:
            contract = Stock(symbol, 'SMART', 'USD')

        fut = asyncio.run_coroutine_threadsafe(
            self.ib.qualifyContractsAsync(contract), self.loop
        )
        fut.result()

        ticker = self.ib.reqTickers(contract)[0]
        return ticker.marketPrice()

    # Внутри IBWorker
    async def _get_atm_option_async(self, symbol: str, right: str = "C", expiry: str = None):
        # --- UNDERLYING ---
        if symbol in ['SPX', 'NDX', 'RUT']:
            stk = Index(symbol, 'CBOE', 'USD')
        else:
            stk = Stock(symbol, 'SMART', 'USD')

        await self.ib.qualifyContractsAsync(stk)

        ul_ticker = (await self.ib.reqTickersAsync(stk))[0]
        ul_price = ul_ticker.marketPrice()
        if ul_price is None or math.isnan(ul_price):
            return {"error": "Не удалось получить цену underlying"}

        # --- OPTION CHAINS ---
        chains = await self.ib.reqSecDefOptParamsAsync(stk.symbol, '', stk.secType, stk.conId)
        if not chains:
            return {"error": "Option chain not found"}

        # --- FIND CHAIN BY EXPIRY ---
        chain = None
        expiry_input = expiry
        for c in chains:
            valid_expirations = [d if isinstance(d, str) else d.strftime('%Y%m%d') for d in c.expirations]
            if expiry_input and expiry_input in valid_expirations:
                chain = c
                break

        if not chain:
            chain = chains[0]
            if not expiry_input or expiry_input not in chain.expirations:
                expiry_input = sorted(chain.expirations)[0]

        # --- AVAILABLE STRIKES ---
        available_strikes = sorted(chain.strikes)

        # --- CHOOSE ATM STRIKE BASED ON CALL/PUT ---
        if right.upper() == "C":  # Call — страйк ≥ цена underlying
            atm_strike = min((s for s in available_strikes if s >= ul_price), default=max(available_strikes))
        else:  # Put — страйк ≤ цена underlying
            atm_strike = max((s for s in available_strikes if s <= ul_price), default=min(available_strikes))

        # --- OPTION CONTRACT ---
        opt = Option(
            symbol=symbol,
            lastTradeDateOrContractMonth=expiry_input,
            strike=atm_strike,
            right=right,
            exchange='SMART',
            currency='USD',
            multiplier='100',
            tradingClass=chain.tradingClass
        )
        await self.ib.qualifyContractsAsync(opt)

        opt_ticker = (await self.ib.reqTickersAsync(opt))[0]

        # --- BID / ASK / MID ---
        bid = opt_ticker.bid
        ask = opt_ticker.ask

        bid = bid if bid is not None and not math.isnan(bid) else None
        ask = ask if ask is not None and not math.isnan(ask) else None
        mid = (bid + ask) / 2 if bid is not None and ask is not None else None

        return {
            "symbol": symbol,
            "expiry": expiry_input,
            "right": right,
            "atm_strike": atm_strike,
            "underlying": ul_price,
            "bid": bid,
            "ask": ask,
            "mid": mid,
            "tradingClass": chain.tradingClass
        }

    def get_atm_option(self, symbol: str, right: str = "C", expiry: str = None):
        """
        Синхронный вызов асинхронной функции через loop IBWorker.
        """
        if not self.connected or not self.loop:
            return {"error": "IBKR not connected yet"}

        future = asyncio.run_coroutine_threadsafe(
            self._get_atm_option_async(symbol, right, expiry), self.loop
        )
        return future.result()

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

    async def _get_net_liquidation_async(self):
        # managedAccounts() — синхронный метод, не await
        account = self.ib.managedAccounts()[0]

        summary = await self.ib.accountSummaryAsync(account)

        for item in summary:
            if item.tag == "NetLiquidation":
                try:
                    return float(item.value)
                except ValueError:
                    return None
        return None

    def get_net_liquidation(self):
        """
        Возвращает Net Liquidation Value (ликвидную стоимость портфеля)
        """
        if not self.connected or not self.loop:
            return None

        future = asyncio.run_coroutine_threadsafe(
            self._get_net_liquidation_async(), self.loop
        )
        return future.result()
