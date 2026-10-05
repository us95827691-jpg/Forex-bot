from flask import Flask
from threading import Thread
import os, time, requests
import yfinance as yf

app = Flask('')
@app.route('/')
def home(): 
    return "Forex Bot is Alive"

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

# Flask ko background me chalao
Thread(target=run_flask, daemon=True).start()

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

SYMBOLS = {
    "EURUSD=X": "EURUSD",
    "GBPUSD=X": "GBPUSD",
    "USDJPY=X": "USDJPY",
    "AUDUSD=X": "AUDUSD",
    "USDCAD=X": "USDCAD"
}

def send_msg(text):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": text}, timeout=10)
        print(f"SENT: {text}", flush=True)
    except Exception as e:
        print(f"Send error {e}", flush=True)

def get_signals(symbol):
    try:
        df = yf.download(symbol, period="2d", interval="15m", progress=False)
        if len(df) < 60: 
            print(f"{symbol} not enough data", flush=True)
            return None
        close = df['Close']
        ema20 = close.ewm(span=20).mean()
        ema50 = close.ewm(span=50).mean()
        delta = close.diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = -delta.where(delta < 0, 0).rolling(14).mean()
        rs = gain/loss
        rsi = 100 - (100 / (1 + rs))
        
        last_close = float(close.iloc[-1])
        last_rsi = float(rsi.iloc[-1])
        last_ema20 = float(ema20.iloc[-1])
        last_ema50 = float(ema50.iloc[-1])

        print(f"{symbol} -> Close:{last_close:.5f} RSI:{last_rsi:.1f} EMA20:{last_ema20:.5f} EMA50:{last_ema50:.5f}", flush=True)

        if last_ema20 > last_ema50 and last_rsi < 65:
            return "BUY", last_close, last_rsi
        if last_ema20 < last_ema50 and last_rsi > 35:
            return "SELL", last_close, last_rsi
        return None
    except Exception as e:
        print(f"{symbol} error {e}", flush=True)
        return None

print("=== BOT STARTING ===", flush=True)
send_msg("✅ Forex Bot Started - Easy Mode\nMarket open ka wait kar raha hu...")

while True:
    print("--- SCANNING ALL PAIRS ---", flush=True)
    for sym, name in SYMBOLS.items():
        res = get_signals(sym)
        if res:
            side, price, rsi_val = res
            if side == "BUY":
                target = "+0.35%"
                up = 70
                down = 30
            else:
                target = "-0.20%"
                up = 30
                down = 70
            
            msg = f"{side} {name}=15m\nPrice: {round(price,5)}\nRSI: {round(rsi_val,1)}\nTarget: {target}\nUp jane ki possibly: {up}%\nDown jane ki possibly: {down}%"
            send_msg(msg)
    print("Sleeping 5 min...", flush=True)
    time.sleep(300)
