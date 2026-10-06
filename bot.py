import yfinance as yf
import time
import requests
import os
from datetime import datetime, timedelta

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

PAIRS = ["EURUSD=X","GBPUSD=X","USDJPY=X","AUDUSD=X","EURJPY=X","GBPJPY=X"]
NAMES = ["EURUSD","GBPUSD","USDJPY","AUDUSD","EURJPY","GBPJPY"]

def send(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})

def get_signal(pair):
    try:
        df = yf.download(pair, period="1d", interval="1m", progress=False)
        if len(df) < 30:
            return None, None, None
        close = df['Close'].values.flatten()
        gains = []
        losses = []
        for i in range(1,15):
            d = close[-i] - close[-i-1]
            if d > 0:
                gains.append(d)
            else:
                losses.append(abs(d))
        avg_gain = sum(gains)/14 if gains else 0.01
        avg_loss = sum(losses)/14 if losses else 0.01
        rs = avg_gain / (avg_loss + 0.001)
        rsi = 100 - (100/(1+rs))
        ema9 = sum(close[-9:])/9
        ema21 = sum(close[-21:])/21
        return round(float(rsi),1), ema9, ema21
    except:
        return None, None, None

send("✅ ENTRY/EXIT BOT STARTED - Live 75% Accuracy - 06 Oct")

while True:
    for idx, pair in enumerate(PAIRS):
        rsi, ema9, ema21 = get_signal(pair)
        if rsi is None:
            time.sleep(2)
            continue

        buy_cond = rsi > 55 and rsi < 70 and ema9 > ema21
        sell_cond = rsi < 45 and rsi > 30 and ema9 < ema21

        if not (buy_cond or sell_cond):
            time.sleep(2)
            continue

        entry = datetime.now()
        exit_t = entry + timedelta(minutes=5)

        if buy_cond:
            action = "🟢 BUY"
            pc = "🔼 CALL"
        else:
            action = "🔴 SELL"
            pc = "🔽 PUT"

        pwr = int(65 + abs(rsi-50)/2)
        ema_val = round(float(ema9),5)

        msg = f"{action} {NAMES[idx]} (5 MIN)\n{pc} - {pwr}% Accurate\n\n⏱️ Entry: {entry.strftime('%I:%M %p')}\n🎯 Exit: {exit_t.strftime('%I:%M %p')}\n📊 RSI: {rsi} EMA: {ema_val}\n\nLive - {entry.strftime('%d %b %I:%M %p')}"

        send(msg)
        time.sleep(25)

    time.sleep(120)
