from flask import Flask
from threading import Thread
import os, time, requests
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta, timezone

UTC_530 = timezone(timedelta(hours=5, minutes=30))

app = Flask('')
@app.route('/')
def home(): return "MTF Bot Live - UTC+5:30 + Dynamic %"

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
Thread(target=run_flask, daemon=True).start()

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
SYMBOLS = {"EURUSD=X":"EURUSD","GBPUSD=X":"GBPUSD","USDJPY=X":"USDJPY","AUDUSD=X":"AUDUSD"}

def send_msg(text):
    try:
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={"chat_id":CHAT_ID,"text":text}, timeout=15)
    except: pass

def get_trend(symbol, period, interval):
    try:
        df = yf.download(symbol, period=period, interval=interval, progress=False, auto_adjust=True)
        if len(df) == 0: return None
        if len(df) < 50 and interval!= "1d": return None
        if len(df) < 40 and interval == "1d": return None
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        close = df['Close']
        if isinstance(close, pd.DataFrame): close = close.iloc[:, 0]
        ema20 = float(close.ewm(span=20).mean().iloc[-1])
        ema50 = float(close.ewm(span=50).mean().iloc[-1])
        delta = close.diff()
        gain = delta.where(delta>0,0).rolling(14).mean().iloc[-1]
        loss = -delta.where(delta<0,0).rolling(14).mean().iloc[-1]
        if isinstance(gain, pd.Series): gain = float(gain.iloc[-1])
        if isinstance(loss, pd.Series): loss = float(loss.iloc[-1])
        rsi = 100 - (100/(1+gain/loss)) if loss!=0 else 50
        price = float(close.iloc[-1])
        if ema20 > ema50 and rsi > 50: return "BUY", price, float(rsi)
        if ema20 < ema50 and rsi < 50: return "SELL", price, float(rsi)
        return "SIDEWAYS", price, float(rsi)
    except: return None

def get_probability(side, buy_count, sell_count, rsi):
    if side == "BUY":
        base = 70 if buy_count == 4 else 85
        up_prob = int(min(95, base + max(0, rsi-50)*0.8))
        return up_prob, 100-up_prob
    else:
        base = 70 if sell_count == 4 else 85
        down_prob = int(min(95, base + max(0, 50-rsi)*0.8))
        return 100-down_prob, down_prob

send_msg("✅ Bot Started - UTC+5:30")

while True:
    for sym, name in SYMBOLS.items():
        t5m = get_trend(sym, "5d", "5m")
        t15m = get_trend(sym, "5d", "15m")
        t45m = get_trend(sym, "5d", "30m")
        t1h = get_trend(sym, "5d", "60m")
        t1d = get_trend(sym, "6mo", "1d")
        if not all([t5m,t15m,t45m,t1h,t1d]): continue
        trends = [t5m[0], t15m[0], t45m[0], t1h[0], t1d[0]]
        buy_count = trends.count("BUY")
        sell_count = trends.count("SELL")
        if buy_count >= 4: final_side = "BUY"
        elif sell_count >= 4: final_side = "SELL"
        else: continue
        price = t15m[1]; rsi = t15m[2]
        up_p, down_p = get_probability(final_side, buy_count, sell_count, rsi)
        time_now = datetime.now(UTC_530).strftime("%d %b %I:%M %p UTC+5:30")
        if final_side == "BUY":
            msg = f"Strict {final_side} {name}=15m se 20 min\nPrice: {round(price,5)}\nRsi: {round(rsi,1)}\nTarget: +0.35%\nUp: {up_p}% Down: {down_p}%\nTime: {time_now}"
        else:
            msg = f"Strict {final_side} {name}=15m se 20 min\nPrice: {round(price,5)}\nRsi: {round(rsi,1)}\nTarget: -0.20%\nUp: {up_p}% Down: {down_p}%\nTime: {time_now}"
        send_msg(msg)
    time.sleep(300)
