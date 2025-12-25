# IBKR Trader

A modular IBKR trading application with multiple interfaces.

## Structure

ibkr-trader/
│
├── core/ # Shared logic
│ ├── init.py
│ ├── ib_client.py # Wrapper over ib_insync
│ ├── orders.py # Limit, trailing, market orders
│ └── models.py # OrderRequest, TradeResult
│
├── worker/ # IBKR runtime
│ ├── init.py
│ └── worker.py
│
├── api/ # FastAPI
│ ├── init.py
│ └── main.py
│
├── gui_tk/ # Tkinter UI
│ ├── init.py
│ └── app.py
│
├── frontend/ # React
│ ├── package.json
│ └── src/
│
├── tests/ # Tests (IBKR mocked)
│ ├── init.py
│ ├── test_orders.py
│ └── test_worker.py
│
├── README.md
├── pyproject.toml
├── requirements.txt
└── .gitignore


## Installation

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

Running

    API: python run.py

    Tkinter GUI: python gui_tk/app.py

    React frontend: cd frontend && npm install && npm start

Notes

    IBKR API calls should be mocked for testing.

    Use requirements.txt to install all Python dependencies.