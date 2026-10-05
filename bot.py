import yfinance as yf
import time
import requests
from datetime import datetime, timedelta
import pytz

# --- SETTING ---
PAIR = "AUDUSD=X"
EXPIRY_MIN = 5  # <-- 5 MIN FIX
BOT_TOKEN = "YOUR_BOT_TOKEN"
CHAT_ID = "YOUR_CHAT_ID"

def send_tg(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})

while True:
    try:
        df = yf.download(PAIR, period="1d", interval="1m")
        c = df['Close']
        
        ema9 = float(c.ewm(span=9).mean().iloc[-1])
        ema15 = float(c.ewm(span=15).mean().iloc[-1])
        
        # RSI
        delta = c.diff()
        gain = delta.where(delta>0, 0).rolling(14).mean()
        loss = -delta.where(delta<0, 0).rolling(14).mean()
        rs = gain/loss
        rsi = float((100 - (100/(1+rs))).iloc[-1])

        now_ist = datetime.now(pytz.timezone('Asia/Kolkata'))
        entry = now_ist
        exit_time = entry + timedelta(minutes=EXPIRY_MIN)
        
        # SAHI LOGIC
        signal = None
        if ema9 > ema15 and rsi < 70 and rsi > 40: # BUY only if not overbought
            signal = "BUY"
            up, down = 93, 7
        elif ema9 < ema15 and rsi > 30 and rsi < 60: # SELL only if not oversold
            signal = "SELL"
            up, down = 7, 93

        if signal and rsi < 79: # 80 RSI wale fake signal block
            msg = f"""Strict {signal} AUDUSD
Trade: {entry.strftime('%I:%M %p')} se {exit_time.strftime('%I:%M %p')} tak ({EXPIRY_MIN} min)
Price: {c.iloc[-1]:.5f}
Rsi: {rsi:.1f}
Up: {up}% Down: {down}%
Time: {now_ist.strftime('%d %b %I:%M %p')} UTC+5:30"""
            send_tg(msg)
        
        time.sleep(60*5) # Har 5 min check

    except Exception as e:
        print(e)
        time.sleep(60)
