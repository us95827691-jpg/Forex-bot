from flask import Flask
from threading import Thread
import os, time, requests, yfinance as yf
from datetime import datetime, timedelta, timezone

UTC = timezone(timedelta(hours=5, minutes=30))
app = Flask('')
@app.route('/')
def home(): return "Bot Live - Checking"
def run(): app.run(host='0.0.0.0', port=8080)
Thread(target=run, daemon=True).start()

PAIRS = ["EURUSD=X", "GBPUSD=X", "USDJPY=X"]
EXPIRY = 5
TOKEN = os.getenv("BOT_TOKEN")
CHAT = os.getenv("CHAT_ID")

def send(msg):
    try:
        r = requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT, "text": msg}, timeout=15)
        print(f"Telegram sent: {r.status_code} {r.text}")
    except Exception as e:
        print(f"Telegram error: {e}")

# STARTUP TEST - ye aana hi chahiye Telegram pe
time.sleep(5)
send(f"✅ Bot Started at {datetime.now(UTC).strftime('%I:%M %p')} - Testing... Pair count: {len(PAIRS)}")

while True:
    try:
        for PAIR in PAIRS:
            df = yf.download(PAIR, period="1d", interval="1m", progress=False, auto_adjust=True)
            print(f"Checked {PAIR} len={len(df)}")
            if len(df) < 25: continue
            close = df['Close'].iloc[:,0] if 'DataFrame' in str(type(df['Close'])) else df['Close']
            open_p = df['Open'].iloc[:,0] if 'DataFrame' in str(type(df['Open'])) else df['Open']
            high = df['High'].iloc[:,0] if 'DataFrame' in str(type(df['High'])) else df['High']
            low = df['Low'].iloc[:,0] if 'DataFrame' in str(type(df['Low'])) else df['Low']

            ema9 = float(close.ewm(span=9).mean().iloc[-1])
            ema21 = float(close.ewm(span=21).mean().iloc[-1])
            delta = close.diff(); gain = delta.where(delta>0,0).rolling(14).mean(); loss = -delta.where(delta<0,0).rolling(14).mean()
            rsi = float((100-(100/(1+gain/loss))).iloc[-1])
            last_o = float(open_p.iloc[-1]); last_c = float(close.iloc[-1]); last_h = float(high.iloc[-1]); last_l = float(low.iloc[-1])
            power = (abs(last_c-last_o)/(last_h-last_l)*100) if (last_h-last_l)!=0 else 0

            now = datetime.now(UTC); exit_t = now + timedelta(minutes=EXPIRY)
            name = PAIR.replace("=X","")
            sig = None
            if ema9 > ema21 and 50 < rsi < 72 and power > 50 and last_c > last_o: sig="BUY"
            elif ema9 < ema21 and 28 < rsi < 50 and power > 50 and last_c < last_o: sig="SELL"

            if sig:
                msg = f"Strict {sig} {name}\nTrade: {now.strftime('%I:%M %p')} se {exit_t.strftime('%I:%M %p')} tak ({EXPIRY} min)\nRSI: {rsi:.1f} Power: {power:.0f}%\nTime: {now.strftime('%d %b %I:%M %p')}"
                send(msg)
                time.sleep(2)
        time.sleep(120)
    except Exception as e:
        print(f"Loop error: {e}"); time.sleep(30)
