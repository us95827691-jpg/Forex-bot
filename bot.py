from flask import Flask
from threading import Thread
import os, time, requests
import yfinance as yf
import pandas as pd

app = Flask('')
@app.route('/')
def home(): return "Bot Alive - 4 Pairs Live"
def run(): app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
Thread(target=run).start()

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

# SIRF 4 MOST LIVE PAIRS
SYMBOLS = {
    "EURUSD=X": "EURUSD",
    "GBPUSD=X": "GBPUSD",
    "USDJPY=X": "USDJPY",
    "AUDUSD=X": "AUDUSD"
}

TIMEFRAMES = ["5m", "15m"]

def send_msg(text):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}, timeout=10)
    except Exception as e:
        print(e, flush=True)

def get_signals(symbol, interval):
    period = "1d" if interval == "5m" else "2d"
    df = yf.download(symbol, period=period, interval=interval, progress=False, auto_adjust=True)
    if len(df) < 60: return None
    close = df['Close']
    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]
    ema20 = close.ewm(span=20).mean()
    ema50 = close.ewm(span=50).mean()
    delta = close.diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = -delta.where(delta < 0, 0).rolling(14).mean()
    rsi = 100 - (100 / (1 + gain/loss))
    ema12 = close.ewm(span=12).mean()
    ema26 = close.ewm(span=26).mean()
    macd = ema12 - ema26
    signal_line = macd.ewm(span=9).mean()
    last_close = float(close.iloc[-1])
    last_rsi = float(rsi.iloc[-1])
    last_ema20 = float(ema20.iloc[-1])
    last_ema50 = float(ema50.iloc[-1])
    last_macd = float(macd.iloc[-1])
    last_sig = float(signal_line.iloc[-1])
    if last_ema20 > last_ema50 and last_rsi < 45 and last_macd > last_sig:
        return "BUY", last_close, last_rsi
    if last_ema20 < last_ema50 and last_rsi > 55 and last_macd < last_sig:
        return "SELL", last_close, last_rsi
    return None

send_msg("✅ *Forex Bot Started - 4 Pairs LIVE*\nPairs: EURUSD, GBPUSD, USDJPY, AUDUSD\nTF: 5M & 15M")

while True:
    print("--- SCANNING 4 LIVE PAIRS ---", flush=True)
    for tf in TIMEFRAMES:
        for sym, name in SYMBOLS.items():
            try:
                print(f"Checking {name} {tf}...", flush=True)
                res = get_signals(sym, tf)
                if res:
                    side, price, rsi = res
                    emoji = "🟢" if side == "BUY" else "🔴"
                    send_msg(f"{emoji} *{side} {name} - {tf.upper()}*\nPrice: `{price}`\nRSI: `{round(rsi,2)}`")
                else:
                    print(f"{name} {tf} -> No Signal", flush=True)
            except Exception as e:
                print(f"{sym} {tf} error {e}", flush=True)
    print("Sleeping 5 min...", flush=True)
    time.sleep(300)
