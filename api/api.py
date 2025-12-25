from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from worker.worker import IBWorker
import threading

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

worker = IBWorker()
threading.Thread(target=lambda: worker.start(), daemon=True).start()


class OrderRequest(BaseModel):
    symbol: str
    qty: int
    limit_price: Optional[float] = None
    trail_amount: Optional[float] = None
    order_type: str = "Limit"
    is_option: bool = False
    expiry: Optional[str] = None
    strike: Optional[float] = None
    right: Optional[str] = None


@app.post("/buy_order")
def buy_order(data: OrderRequest):
    trade = worker.place_order(
        symbol=data.symbol,
        qty=data.qty,
        limit_price=data.limit_price,
        trail_amount=data.trail_amount,
        order_type=data.order_type,
        is_option=data.is_option,
        expiry=data.expiry,
        strike=data.strike,
        right=data.right,
        action="BUY"
    )
    if trade is None:
        return {"status": "error", "message": "IBKR not connected yet"}

    # если это обычный ордер
    order_id = getattr(trade, "orderId", None)  # для Order
    return {"status": "success", "orderId": order_id}


@app.post("/sell_order")
def sell_order(data: OrderRequest):
    trade = worker.place_order(
        symbol=data.symbol,
        qty=data.qty,
        limit_price=data.limit_price,
        trail_amount=data.trail_amount,
        order_type=data.order_type,
        is_option=data.is_option,
        expiry=data.expiry,
        strike=data.strike,
        right=data.right,
        action="SELL"
    )
    if trade is None:
        return {"status": "error", "message": "IBKR not connected yet"}

    order_id = getattr(trade, "orderId", None)
    return {"status": "success", "orderId": order_id}


@app.post("/buy_trailing")
def buy_trailing(data: OrderRequest):
    result = worker.place_order(
        symbol=data.symbol,
        qty=data.qty,
        limit_price=data.limit_price,
        trail_amount=data.trail_amount,
        order_type="Trail",
        is_option=data.is_option,
        expiry=data.expiry,
        strike=data.strike,
        right=data.right,
        action="BUY"
    )
    if result is None:
        return {"status": "error", "message": "IBKR not connected yet"}

    parent_trade, trail_trade = result
    return {
        "status": "success",
        "parentOrderId": parent_trade.order.orderId,
        "trailOrderId": trail_trade.order.orderId
    }
