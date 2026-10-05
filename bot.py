from flask import Flask
from threading import Thread
import os, time, requests
import yfinance as yf

app = Flask('')
@app.route('/')
def home(): return "MTF Bot Live - Fixed"

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
Thread(target=run_flask, daemon=True).start()

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

SYMBOLS = {"EURUSD=X":"EURUSD","GBPUSD=X":"GBPUSD","USDJPY=X":"USDJPY","AUDUSD=X":"AUDUSD"}

def send_msg(text):
    try:
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={"chat_id":CHAT_ID,"text":text}, timeout=15)
        print(f"SENT: {text}", flush=True)
    except Exception as e:
        print(f"Error {e}", flush=True)

def get_trend(symbol, period, interval):
    try:
        df = yf.download(symbol, period=period, interval=interval, progress=False, auto_adjust=True)
        if len(df) < 50: return None
        close = df['Close']
        ema20 = close.ewm(span=20).mean().iloc[-1]
        ema50 = close.ewm(span=50).mean().iloc[-1]
        delta = close.diff()
        gain = delta.where(delta>0,0).rolling(14).mean().iloc[-1]
        loss = -delta.where(delta<0,0).rolling(14).mean().iloc[-1]
        rsi = 100 - (100/(1+gain/loss)) if loss!=0 else 50
        if ema20 > ema50 and rsi > 50: return "BUY", float(close.iloc[-1]), float(rsi)
        if ema20 < ema50 and rsi < 50: return "SELL", float(close.iloc[-1]), float(rsi)
        return "SIDEWAYS", float(close.iloc[-1]), float(rsi)
    except:
        return None

print("=== MTF BOT STARTING ===", flush=True)
send_msg("✅ MTF Bot Started - Fixed\n5m,15m,30m,1h,1D Analyse\nHar 5 min me signal...")

while True:
    print("--- MTF SCANNING ---", flush=True)
    for sym, name in SYMBOLS.items():
        t5m = get_trend(sym, "1d", "5m")
        t15m = get_trend(sym, "2d", "15m")
        t45m = get_trend(sym, "5d", "30m")
        t1h = get_trend(sym, "5d", "60m")
        t1d = get_trend(sym, "1mo", "1d")
        if not all([t5m,t15m,t45m,t1h,t1d]):
            print(f"{name} data missing", flush=True)
            continue
        trends = [t5m[0], t15m[0], t45m[0], t1h[0], t1d[0]]
        buy_count = trends.count("BUY")
        sell_count = trends.count("SELL")
        print(f"{name} -> {trends} B:{buy_count} S:{sell_count}", flush=True)
        final_side = None
        if buy_count >= 4: final_side = "BUY"
        elif sell_count >= 4: final_side = "SELL"
        else: continue
        price = t15m[1]
        rsi = t15m[2]
        if final_side == "BUY":
            msg = f"Strict {final_side} {name}=15m se 20 minutes\nPrice: {round(price,5)}\nRsi: {round(rsi,1)}\nTarget: +0.35%\nUp jane ki possibly: 80%\nDown jane ki possibly: 20%"
        else:
            msg = f"Strict {final_side} {name}=15m se 20 minutes\nPrice: {round(price,5)}\nRsi: {round(rsi,1)}\nTarget: -0.20%\nUp jane ki possibly: 20%\nDown jane ki possibly: 80%"
        send_msg(msg)
    time.sleep(300)
