from flask import Flask
from threading import Thread
import os, time, requests, yfinance as yf, pandas as pd
from datetime import datetime, timedelta, timezone

UTC = timezone(timedelta(hours=5, minutes=30))
app = Flask('')
@app.route('/')
def home(): return "Live 5min Bot Running"
def run(): app.run(host='0.0.0.0', port=8080)
Thread(target=run, daemon=True).start()

# --- 5 MIN LOGIC ---
PAIR = "AUDUSD=X"
EXPIRY = 5
TOKEN = os.getenv("BOT_TOKEN")
CHAT = os.getenv("CHAT_ID")

def send(msg):
    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT, "text": msg})

while True:
    try:
        df = yf.download(PAIR, period="1d", interval="1m", progress=False)
        if len(df) < 20: 
            time.sleep(60); continue
        c = df['Close']
        ema9 = float(c.ewm(span=9).mean().iloc[-1])
        ema15 = float(c.ewm(span=15).mean().iloc[-1])
        delta = c.diff(); gain = delta.where(delta>0,0).rolling(14).mean(); loss = -delta.where(delta<0,0).rolling(14).mean()
        rsi = float((100-(100/(1+gain/loss))).iloc[-1])
        now = datetime.now(UTC)
        exit_t = now + timedelta(minutes=EXPIRY)
        sig = None
        if ema9 > ema15 and rsi < 70 and rsi > 45: sig="BUY"
        elif ema9 < ema15 and rsi > 30 and rsi < 55: sig="SELL"
        
        if sig and rsi < 78:
            up = 93 if sig=="BUY" else 7
            down = 100-up
            msg = f"Strict {sig} AUDUSD\nTrade: {now.strftime('%I:%M %p')} se {exit_t.strftime('%I:%M %p')} tak ({EXPIRY} min)\nPrice: {float(c.iloc[-1]):.5f}\nRsi: {rsi:.1f}\nUp: {up}% Down: {down}%\nTime: {now.strftime('%d %b %I:%M %p')} UTC+5:30"
            send(msg)
        time.sleep(300) # 5 min baad check
    except Exception as e:
        print(e); time.sleep(60)
