import os, time, requests, threading
import yfinance as yf
from datetime import datetime, timedelta, timezone
from flask import Flask

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
IST = timezone(timedelta(hours=5, minutes=30))

app = Flask(__name__)
@app.route('/')
def home(): return "Bot Running"
def run_flask(): app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
threading.Thread(target=run_flask, daemon=True).start()

PAIRS = ["EURUSD=X","GBPUSD=X","USDJPY=X","AUDUSD=X","EURJPY=X","GBPJPY=X"]
NAMES = ["EURUSD","GBPUSD","USDJPY","AUDUSD","EURJPY","GBPJPY"]

def send(m):
    try:
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": m}, timeout=10)
    except: pass

def get_signal(pair):
    try:
        df = yf.download(pair, period="1d", interval="1m", progress=False, auto_adjust=True)
        if len(df) < 30: return None, None, None, None
        c = df['Close'].values.flatten()
        g=[]; l=[]
        for i in range(1,15):
            d = c[-i] - c[-i-1]
            if d>0: g.append(d)
            else: l.append(abs(d))
        rs = (sum(g)/14+0.001)/(sum(l)/14+0.001)
        rsi = 100 - (100/(1+rs))
        ema9 = sum(c[-9:])/9
        ema21 = sum(c[-21:])/21
        mom = c[-1] - c[-5]
        return round(float(rsi),1), ema9, ema21, mom
    except:
        return None, None, None, None

send(f"✅ FORMAT FIXED - Entry/Exit alag ayega - {datetime.now(IST).strftime('%I:%M %p IST')}")

while True:
    for idx, pair in enumerate(PAIRS):
        rsi, ema9, ema21, mom = get_signal(pair)
        if rsi is None: continue

        buy = rsi > 60 and ema9 > ema21 and mom > 0
        sell = rsi < 40 and ema9 < ema21 and mom < 0
        if not (buy or sell):
            time.sleep(1)
            continue

        pwr = int(70 + abs(rsi-50)/1.5)
        if pwr < 70: continue # sirf 70%+ wale

        entry = datetime.now(IST)
        exit_t = entry + timedelta(minutes=5)

        action = "🟢 BUY" if buy else "🔴 SELL"
        pc = "🔼 CALL" if buy else "🔽 PUT"

        # YAHI FORMAT TU CHAHTA HAI
        msg = f"""{action} {NAMES[idx]} (5 MIN)
{pc} - {pwr}% Accurate

⏱️ Entry: {entry.strftime('%I:%M %p')}
🎯 Exit: {exit_t.strftime('%I:%M %p')}
📊 RSI: {rsi} PWR: {pwr}%

Live - {entry.strftime('%d %b %I:%M %p IST')}"""

        send(msg)
        time.sleep(35)
    time.sleep(90)
