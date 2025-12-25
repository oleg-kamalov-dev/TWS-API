from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
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

def connect_worker():
    worker.start('127.0.0.1', 7496, clientId=1)

threading.Thread(target=connect_worker, daemon=True).start()


# 👇 ВАЖНО
class TrailingOrderRequest(BaseModel):
    symbol: str
    qty: int
    limit_price: float
    trail_amount: float


@app.post("/buy_trailing")
def buy_trailing(data: TrailingOrderRequest):
    trade = worker.place_trailing_order(
        symbol=data.symbol,
        qty=data.qty,
        limit_price=data.limit_price,
        trail_amount=data.trail_amount,
    )

    if trade is None:
        return {"status": "error", "message": "IBKR not connected yet"}

    return {
        "status": "success",
        "orderId": trade.order.orderId
    }
