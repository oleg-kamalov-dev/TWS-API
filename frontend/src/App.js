import React, { useState } from "react";

function App() {
  const [response, setResponse] = useState(null);

  const buyTrailing = () => {
    fetch("http://localhost:8000/buy_trailing", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        symbol: "NVDA",
        qty: 1,
        limit_price: 100,   // совпадает с параметром FastAPI
        trail_amount: 3     // совпадает с параметром FastAPI
      })
    })
      .then(res => res.json())
      .then(data => {
        console.log(data);
        setResponse(data);
      })
      .catch(err => console.error(err));
  };

  return (
    <div style={{ padding: "20px" }}>
      <h1>IBKR Trailing Order Test</h1>
      <button 
        onClick={buyTrailing} 
        style={{ fontSize: "16px", padding: "10px 20px" }}
      >
        Buy Trailing
      </button>

      {response && (
        <div style={{ marginTop: "20px" }}>
          <strong>Response:</strong> {JSON.stringify(response)}
        </div>
      )}
    </div>
  );
}

export default App;



