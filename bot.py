from flask import Flask
from threading import Thread
import os, time, requests
import yfinance as yf

app = Flask('')
@app.route('/')
def home(): return "Easy Signal Bot Live"
def run(): app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
Thread(target=run).start()

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
SYMBOLS = ["EURUSD=X","GBPUSD=X","USDJPY=X","AUDUSD=X","GC=F"]

def send_msg(t):
    try:
        print(f"SEND: {t}", flush=True)
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": t}, timeout=10)
    except Exception as e:
        print(f"TG Error {e}", flush=True)

def check(sym, tf):
    try:
        df = yf.Ticker(sym).history(period="1d", interval=tf, auto_adjust=True)
        if len(df) < 30: return None
        c = df['Close']
        e20 = c.ewm(span=20).mean().iloc[-1]
        e50 = c.ewm(span=50).mean().iloc[-1]
        price = c.iloc[-1]
        print(f"{sym} {tf} P:{price:.5f} E20:{e20:.5f} E50:{e50:.5f}", flush=True)
        if e20 > e50:
            return f"🟢 BUY {sym} {tf} Price {price:.5f}"
        else:
            return f"🔴 SELL {sym} {tf} Price {price:.5f}"
    except Exception as e:
        print(f"{sym} {tf} Error {e}", flush=True)
    return None

send_msg("✅ Easy Bot Started - Ab har
