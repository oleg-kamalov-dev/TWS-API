from ib_insync import *
# from ib_async import *
import tkinter as tk
from tkinter import ttk
from decimal import Decimal
import sv_ttk

# ================== IB CONNECTION ==================
ib = IB()
ib.connect('127.0.0.1', 7496, clientId=1)

# ================== HELPERS ==================
def build_contract():
    symbol = entry_symbol.get().upper().strip()
    if option_var.get():
        right = "C" if right_var.get() == "Call" else "P"
        return Option(
            symbol,
            expiry_entry.get(),
            float(strike_entry.get()),
            right,
            exchange='SMART',
            currency='USD'
        )
    return Stock(symbol, 'SMART', 'USD')


def get_qty():
    try:
        return Decimal(qty_entry.get())
    except:
        price_label.config(text="Invalid Qty")
        return None


def get_price(contract):
    ticker = ib.reqTickers(contract)[0]
    price = round(ticker.marketPrice(), 2)
    price_label.config(text=f"{contract.symbol}: {price} USD")
    return price


# ================== ACTIONS ==================
def buy_stock():
    contract = build_contract()
    qty = get_qty()
    price = float(limit_price_entry.get())

    ib.qualifyContracts(contract)

    order = LimitOrder('BUY', qty, price, tif='DAY')
    order.orderId = ib.client.getReqId()

    ib.placeOrder(contract, order)
    orders_text.insert(tk.END, f"BUY {contract.symbol} @ {price}, Qty={qty}\n")


def buy_bracket():
    contract = build_contract()
    qty = get_qty()
    price = float(limit_price_entry.get())

    ib.qualifyContracts(contract)

    parent = Order(
        orderId=ib.client.getReqId(),
        action="BUY",
        orderType="LMT",
        totalQuantity=qty,
        lmtPrice=price,
        tif="DAY",
        transmit=False
    )

    stop = Order(
        orderId=ib.client.getReqId(),
        action="SELL",
        orderType="STP",
        auxPrice=price - 3,
        totalQuantity=qty,
        parentId=parent.orderId,
        transmit=False
    )

    take_profit = Order(
        orderId=ib.client.getReqId(),
        action="SELL",
        orderType="LMT",
        lmtPrice=price + 5,
        totalQuantity=qty,
        parentId=parent.orderId,
        transmit=True
    )

    ib.placeOrder(contract, parent)
    ib.sleep(0.2)
    ib.placeOrder(contract, stop)
    ib.sleep(0.2)
    ib.placeOrder(contract, take_profit)


    orders_text.insert(tk.END, f"Bracket BUY {contract.symbol}\n")


def buy_trailing():
    contract = build_contract()
    qty = get_qty()
    price = float(limit_price_entry.get())
    trailing = float(trailing_entry.get())

    ib.qualifyContracts(contract)

    parent = Order(
        orderId=ib.client.getReqId(),
        action="BUY",
        orderType="LMT",
        totalQuantity=qty,
        lmtPrice=price,
        tif="DAY",
        transmit=False
    )

    trail = Order(
        orderId=ib.client.getReqId(),
        action="SELL",
        orderType="TRAIL",
        auxPrice=trailing,
        totalQuantity=qty,
        parentId=parent.orderId,
        transmit=True
    )

    ib.placeOrder(contract, parent)
    ib.sleep(0.2)
    ib.placeOrder(contract, trail)



    orders_text.insert(tk.END, f"Trailing BUY {contract.symbol}\n")

# ================== ORDER UPDATER ==================
def update_orders():
    orders_text.delete(1.0, tk.END)  # очищаем окно
    trades = ib.trades()
    if not trades:
        orders_text.insert(tk.END, "Ордеров нет\n")
    else:
        for trade in trades:
            symbol = trade.contract.symbol
            status = trade.orderStatus.status
            filled = trade.orderStatus.filled
            remaining = trade.orderStatus.remaining
            avg_price = trade.orderStatus.avgFillPrice
            orders_text.insert(
                tk.END,
                f"{symbol}: {status}, Filled: {filled}, Remaining: {remaining}, AvgPrice: {avg_price}\n"
            )

    root.after(2000, update_orders)  # повторяем каждые 2 секунды

# ================== GUI ==================
root = tk.Tk()
root.title("TWS API (Dark)")
root.geometry("950x780")
sv_ttk.set_theme("dark")

root.columnconfigure(0, weight=1)
root.rowconfigure(3, weight=1)

# ===== HEADER =====
header = ttk.Frame(root, padding=10)
header.grid(row=0, column=0, sticky="ew")

entry_symbol = tk.StringVar()

for sym in ("NVDA", "NVDL", "TSLA", "TSLL", "SPX"):
    ttk.Button(header, text=sym, command=lambda s=sym: entry_symbol.set(s)).pack(side="left", padx=5)

ttk.Label(header, text="Ticker:").pack(side="left", padx=10)
ttk.Entry(header, textvariable=entry_symbol, width=10).pack(side="left")

# ===== ORDER PARAMS =====
order_frame = ttk.LabelFrame(root, text="Order Parameters", padding=10)
order_frame.grid(row=1, column=0, sticky="ew", padx=10)

ttk.Label(order_frame, text="Qty").grid(row=0, column=0, sticky="e")
qty_entry = ttk.Entry(order_frame, width=8)
qty_entry.insert(0, "1")
qty_entry.grid(row=0, column=1)

ttk.Label(order_frame, text="Limit Price").grid(row=0, column=2, sticky="e")
limit_price_entry = ttk.Entry(order_frame, width=6)
limit_price_entry.insert(0, "100")
limit_price_entry.grid(row=0, column=3)

ttk.Label(order_frame, text="Trailing").grid(row=0, column=4, sticky="e")
trailing_entry = ttk.Entry(order_frame, width=6)
trailing_entry.insert(0, "3")
trailing_entry.grid(row=0, column=5)

option_var = tk.BooleanVar()
ttk.Checkbutton(order_frame, text="Option", variable=option_var).grid(row=1, column=0)

right_var = tk.StringVar(value="Call")
ttk.Combobox(
    order_frame,
    textvariable=right_var,
    values=("Call", "Put"),
    width=6,
    state="readonly"
).grid(row=1, column=1)

ttk.Label(order_frame, text="Strike").grid(row=1, column=2, sticky="e")
strike_entry = ttk.Entry(order_frame, width=6)
strike_entry.insert(0, "100")
strike_entry.grid(row=1, column=3)

ttk.Label(order_frame, text="Exp").grid(row=1, column=4, sticky="e")
expiry_entry = ttk.Entry(order_frame, width=8)
expiry_entry.insert(0, "20251219")
expiry_entry.grid(row=1, column=5)

# ===== ACTIONS =====
actions = ttk.Frame(root, padding=10)
actions.grid(row=2, column=0, sticky="ew")

ttk.Button(actions, text="Get Price", command=lambda: get_price(build_contract())).pack(side="left", padx=5)
ttk.Button(actions, text="Buy", command=buy_stock).pack(side="left", padx=5)
ttk.Button(actions, text="Buy + Bracket", command=buy_bracket).pack(side="left", padx=5)
ttk.Button(actions, text="Buy + Trailing", command=buy_trailing).pack(side="left", padx=5)

# ===== ORDERS =====
orders_frame = ttk.LabelFrame(root, text="Active Orders", padding=10)
orders_frame.grid(row=3, column=0, sticky="nsew", padx=10, pady=10)

orders_frame.rowconfigure(0, weight=1)
orders_frame.columnconfigure(0, weight=1)

orders_text = tk.Text(orders_frame, bg="#1e1e1e", fg="white")
orders_text.grid(row=0, column=0, sticky="nsew")

price_label = ttk.Label(root, font=("Segoe UI", 12))
price_label.grid(row=4, column=0, sticky="w", padx=10)

update_orders()
root.mainloop()
