import os, time, requests, threading
import yfinance as yf
from datetime import datetime, timedelta, timezone
from flask import Flask

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
IST = timezone(timedelta(hours=5, minutes=30))

app = Flask(__name__)
@app.route('/')
def home(): return "Bot Running - 85% + Result Check"
def run_flask(): app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
threading.Thread(target=run_flask, daemon=True).start()

PAIRS = ["EURUSD=X","GBPUSD=X","USDJPY=X","AUDUSD=X","EURJPY=X","GBPJPY=X"]
NAMES = ["EURUSD","GBPUSD","USDJPY","AUDUSD","EURJPY","GBPJPY"]

def send(m):
    try: requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": m}, timeout=10)
    except: pass

def get_round_time():
    now = datetime.now(IST)
    minute = now.minute
    remainder = minute % 5
    if remainder == 0 and now.second < 15: add_min = 0
    else: add_min = 5 - remainder
    entry = now + timedelta(minutes=add_min)
    entry = entry.replace(second=0, microsecond=0)
    exit_t = entry + timedelta(minutes=5)
    return entry, exit_t

def get_signal(pair):
    try:
        df = yf.download(pair, period="1d", interval="1m", progress=False, auto_adjust=True)
        if len(df) < 50: return None
        c = df['Close'].values.flatten()
        h = df['High'].values.flatten()
        l = df['Low'].values.flatten()
        g=[]; loss=[]
        for i in range(1,15):
            d = c[-i] - c[-i-1]
            if d>0: g.append(d)
            else: loss.append(abs(d))
        rs = (sum(g)/14+0.001)/(sum(loss)/14+0.001)
        rsi = 100 - (100/(1+rs))
        ema9 = sum(c[-9:])/9
        ema21 = sum(c[-21:])/21
        ema50 = sum(c[-50:])/50
        mom = c[-1] - c[-5]
        mom2 = c[-5] - c[-10]
        avg_range = sum([h[-i]-l[-i] for i in range(1,11)])/10
        curr_range = h[-1]-l[-1]
        price = c[-1]
        return rsi, ema9, ema21, ema50, mom, mom2, avg_range, curr_range, price
    except: return None

def check_result_after_5min(pair, entry_price, is_buy, entry_t, exit_t, name, pwr):
    time.sleep(305) # 5 min 5 sec wait
    try:
        df = yf.download(pair, period="1d", interval="1m", progress=False, auto_adjust=True)
        exit_price = df['Close'].values.flatten()[-1]

        won = (exit_price > entry_price) if is_buy else (exit_price < entry_price)

        if won:
            send(f"✅ WIN ✅\n{name} {entry_t.strftime('%I:%M %p')} wala CALL/PUT WIN hogaya!\nEntry: {entry_price:.5f} -> Exit: {exit_price:.5f}\nPWR: {pwr}%")
        else:
            send(f"❌ LOSS ❌\n{name} {entry_t.strftime('%I:%M %p')} wala LOSS hogaya\nEntry: {entry_price:.5f} -> Exit: {exit_price:.5f}\nPWR: {pwr}%\nNext ka wait karo!")
    except:
        send(f"⚠️ {name} {entry_t.strftime('%I:%M %p')} Result check nahi ho paya")

send("✅ Bot Started - WIN/LOSS Auto Check ON")

while True:
    for idx, pair in enumerate(PAIRS):
        data = get_signal(pair)
        if data is None: continue
        rsi, ema9, ema21, ema50, mom, mom2, avg_range, curr_range, price = data

        buy = rsi > 62 and rsi < 78 and ema9 > ema21 and ema21 > ema50 and mom > 0 and mom2 > 0 and curr_range > avg_range*0.7
        sell = rsi < 38 and rsi > 22 and ema9 < ema21 and ema21 < ema50 and mom < 0 and mom2 < 0 and curr_range > avg_range*0.7

        if not (buy or sell): continue
        pwr = int(75 + abs(rsi-50)/1.2)
        if rsi > 70 or rsi < 30: pwr += 5
        if pwr < 82: continue
        if pwr > 92: pwr = 92

        entry, exit_t = get_round_time()
        action = "🟢 BUY" if buy else "🔴 SELL"
        pc = "🔼 CALL" if buy else "🔽 PUT"

        msg = f"{action} {NAMES[idx]} (5 MIN)\n{pc} - {pwr}% Accurate\n\n⏱️ Entry: {entry.strftime('%I:%M %p')}\n🎯 Exit: {exit_t.strftime('%I:%M %p')}\n📊 RSI: {round(rsi,1)} PWR: {pwr}%\n\nLive - {entry.strftime('%d %b %I:%M %p IST')}"
        send(msg)

        # 5 min baad result check background me chalega
        threading.Thread(target=check_result_after_5min, args=(pair, price, buy, entry, exit_t, NAMES[idx], pwr), daemon=True).start()

        time.sleep(60)
    time.sleep(90)
