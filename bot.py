from flask import Flask
from threading import Thread
import os, time, requests
import yfinance as yf
import pandas as pd

app = Flask('')
@app.route('/')
def home(): return "Bot Alive - 5M & 15M Forex"
def run(): app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
Thread(target=run).start()

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

SYMBOLS = {
    "EURUSD=X": "EURUSD",
    "GBPUSD=X": "GBPUSD",
    "USDJPY=X": "USDJPY",
    "USDCHF=X": "USDCHF",
    "AUDUSD=X": "AUDUSD",
    "USDCAD=X": "USDCAD",
    "NZDUSD=X": "NZDUSD"
}

TIMEFRAMES = ["5m", "15m"] # Dono TF

def send_msg(text):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}, timeout=10)
    except Exception as e:
        print(e, flush=True)

def get_signals(symbol, interval):
    # 5m ke liye kam data, 15m ke liye zyada
    period = "1d" if interval == "5m" else "2d"
    df = yf.download(symbol, period=period, interval=interval, progress=False)
    if len(df) < 60: return None
    close = df['Close']
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

send_msg("✅ *Forex Bot Started*\nTF: *5M & 15M Both*\nPairs: 7 Major\nMode: EMA+RSI+MACD")

while True:
    print("--- SCANNING 5M & 15M ---", flush=True)
    for tf in TIMEFRAMES:
        for sym, name in SYMBOLS.items():
            try:
                print(f"Checking {name} {tf}...", flush=True)
                res = get_signals(sym, tf)
                if res:
                    side, price, rsi = res
                    emoji = "🟢" if side == "BUY" else "🔴"
                    send_msg(f"{emoji} *{side} {name} - {tf.upper()}*\nPrice: `{price}`\nRSI: `{round(rsi,2)}`\nHold: {tf} to {tf} x 3")
                else:
                    print(f"{name} {tf} -> No Signal", flush=True)
            except Exception as e:
                print(f"{sym} {tf} error {e}", flush=True)
    print("Sleeping 5 min...", flush=True)
    time.sleep(300) # 5 min me ek baar check
