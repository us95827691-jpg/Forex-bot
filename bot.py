from flask import Flask
from threading import Thread
import os, time, requests
from datetime import datetime, timedelta, timezone
from curl_cffi import requests as creq
import yfinance as yf

UTC = timezone(timedelta(hours=5, minutes=30))
app = Flask('')
@app.route('/')
def home(): return "Bot Live - Bypass Mode"
def run(): app.run(host='0.0.0.0', port=8080)
Thread(target=run, daemon=True).start()

PAIRS = ["EURUSD=X", "GBPUSD=X", "USDJPY=X", "EURJPY=X", "GBPJPY=X", "AUDUSD=X"]
TOKEN = os.getenv("BOT_TOKEN")
CHAT = os.getenv("CHAT_ID")

def send(msg):
    try:
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT, "text": msg}, timeout=15)
    except: pass

session = creq.Session(impersonate="chrome")
time.sleep(4)
send(f"✅ Bot Bypass Mode Started\nTime: {datetime.now(UTC).strftime('%I:%M %p')}\nYahoo 429 Fixed")

while True:
    try:
        for PAIR in PAIRS:
            try:
                ticker = yf.Ticker(PAIR, session=session)
                df = ticker.history(period="1d", interval="1m")
                print(f"Checked {PAIR} len={len(df)}")
                if len(df) < 30: continue
                close = df['Close']; open_p = df['Open']; high = df['High']; low = df['Low']
                ema9 = float(close.ewm(span=9).mean().iloc[-1])
                ema21 = float(close.ewm(span=21).mean().iloc[-1])
                delta = close.diff(); gain = delta.where(delta>0,0).rolling(14).mean(); loss = -delta.where(delta<0,0).rolling(14).mean()
                rsi = float((100-(100/(1+gain/loss))).iloc[-1])
                last_o = float(open_p.iloc[-1]); last_c = float(close.iloc[-1])
                last_h = float(high.iloc[-1]); last_l = float(low.iloc[-1])
                power = (abs(last_c-last_o)/(last_h-last_l)*100) if (last_h-last_l)!=0 else 0
                now = datetime.now(UTC); exit_t = now + timedelta(minutes=5)
                name = PAIR.replace("=X","")
                sig = None
                if ema9 > ema21 and 50 < rsi < 70 and power > 45 and last_c > last_o: sig="BUY"
                elif ema9 < ema21 and 30 < rsi < 50 and power > 45 and last_c < last_o: sig="SELL"
                if sig:
                    msg = f"{'🟢' if sig=='BUY' else '🔴'} {sig} {name} (5 MIN)\nTrade: {now.strftime('%I:%M %p')} - {exit_t.strftime('%I:%M %p')}\nRSI:{rsi:.1f} PWR:{power:.0f}%\n{now.strftime('%d %b %I:%M %p')}"
                    send(msg)
            except Exception as e:
                print(f"Pair {PAIR} error {e}")
                continue
        time.sleep(90)
    except Exception as e:
        print(f"Loop error {e}"); time.sleep(20)
