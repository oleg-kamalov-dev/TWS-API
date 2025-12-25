import React, { useState } from "react";
import "./App.css";

function App() {
  const [symbol, setSymbol] = useState("NVDA");
  const [qty, setQty] = useState(1);
  const [limitPrice, setLimitPrice] = useState(100);
  const [trailAmount, setTrailAmount] = useState(3);
  const [orderType, setOrderType] = useState("Limit");

  const [isOption, setIsOption] = useState(false);
  const [expiry, setExpiry] = useState("20251226");
  const [strike, setStrike] = useState("180");
  const [right, setRight] = useState("C");

  const [response, setResponse] = useState(null);

  const tickers = ["NVDA", "NVDL", "TSLA", "TSLL", "SPX"];
  const orderTypes = ["Limit", "Market", "Stop", "Trail"];

  const buyTrailing = () => {
    fetch("http://localhost:8000/buy_trailing", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        symbol,
        qty: Number(qty),
        limit_price: Number(limitPrice),
        trail_amount: Number(trailAmount),
        is_option: isOption,
        expiry: isOption ? expiry : null,
        strike: isOption ? Number(strike) : null,
        right: isOption ? right : null
      })
    })
      .then(res => res.json())
      .then(data => setResponse(data))
      .catch(console.error);
  };

  const buyOrder = () => {
    fetch("http://localhost:8000/buy_order", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        symbol,
        qty: Number(qty),
        limit_price: Number(limitPrice),
        order_type: orderType,
        is_option: isOption,
        expiry: isOption ? expiry : null,
        strike: isOption ? Number(strike) : null,
        right: isOption ? right : null
      })
    })
      .then(res => res.json())
      .then(data => setResponse(data))
      .catch(console.error);
  };

  const sellOrder = () => {
    fetch("http://localhost:8000/sell_order", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        symbol,
        qty: Number(qty),
        limit_price: Number(limitPrice),
        order_type: orderType,
        is_option: isOption,
        expiry: isOption ? expiry : null,
        strike: isOption ? Number(strike) : null,
        right: isOption ? right : null
      })
    })
      .then(res => res.json())
      .then(data => setResponse(data))
      .catch(console.error);
  };

  return (
    <div className="container">
      <h1>IBKR Order Panel</h1>

      {/* INSTRUMENT */}
      <div className="panel">
        <div className="panel-title">Instrument</div>
        <label className="checkbox">
          <input
            type="checkbox"
            checked={isOption}
            onChange={e => setIsOption(e.target.checked)}
          />
          Trade options
        </label>
      </div>

      {/* TICKER */}
      <div className="panel">
        <div className="panel-title">Ticker</div>
        <div className="button-row">
          {tickers.map(t => (
            <button
              key={t}
              className="ticker-button"
              onClick={() => setSymbol(t)}
            >
              {t}
            </button>
          ))}
        </div>

        <div className="form-row">
          <label>Ticker</label>
          <input
            className="input"
            value={symbol}
            onChange={e => setSymbol(e.target.value)}
          />
        </div>
      </div>

      {/* OPTION PARAMS */}
      {isOption && (
        <div className="panel">
          <div className="panel-title">Option Parameters</div>

          <div className="form-row">
            <label>Expiration</label>
            <input
              className="input"
              placeholder="YYYYMMDD"
              value={expiry}
              onChange={e => setExpiry(e.target.value)}
            />
          </div>

          <div className="form-row">
            <label>Strike</label>
            <input
              className="input"
              type="number"
              value={strike}
              onChange={e => setStrike(e.target.value)}
            />
          </div>

          <div className="form-row">
            <label>Right</label>
            <select className="input" value={right} onChange={e => setRight(e.target.value)}>
              <option value="C">Call</option>
              <option value="P">Put</option>
            </select>
          </div>
        </div>
      )}

      {/* ORDER PARAMS */}
      <div className="panel">
        <div className="panel-title">Order Parameters</div>

        <div className="form-row">
          <label>Type</label>
          <select className="input" value={orderType} onChange={e => setOrderType(e.target.value)}>
            {orderTypes.map(t => <option key={t}>{t}</option>)}
          </select>
        </div>

        <div className="form-row">
          <label>Price</label>
          <input className="input" type="number" value={limitPrice} onChange={e => setLimitPrice(e.target.value)} />
        </div>

        <div className="form-row">
          <label>Qty</label>
          <input className="input" type="number" value={qty} onChange={e => setQty(e.target.value)} />
        </div>

        <div className="form-row">
          <label>Trail</label>
          <input className="input" type="number" value={trailAmount} onChange={e => setTrailAmount(e.target.value)} />
        </div>
      </div>

      {/* ACTIONS */}
      <div className="panel">
        <div className="panel-title">Actions</div>
        <div className="button-row">
          <button className="btn green" onClick={buyTrailing}>Buy + Trailing</button>
          <button className="btn green" onClick={buyOrder}>Buy</button>
          <button className="btn red" onClick={sellOrder}>Sell</button>
        </div>
      </div>

      {/* LOG */}
      <div className="panel">
        <div className="panel-title">Log</div>
        <pre className="log">
          {response ? JSON.stringify(response, null, 2) : "No data"}
        </pre>
      </div>
    </div>
  );
}

export default App;
