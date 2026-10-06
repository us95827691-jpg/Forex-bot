from flask import Flask
from threading import Thread
import os, time, requests, yfinance as yf
from datetime import datetime, timedelta, timezone

UTC = timezone(timedelta(hours=5, minutes=30))
app = Flask('')
@app.route('/')
def home(): return "My Best 5min Strategy Live"
def run(): app.run(host='0.0.0.0', port=8080)
Thread(target=run, daemon=True).start()

PAIRS = ["AUDUSD=X", "EURUSD=X", "GBPUSD=X", "USDJPY=X", "EURJPY=X", "GBPJPY=X"]
EXPIRY = 5
TOKEN = os.getenv("BOT_TOKEN")
CHAT = os.getenv("CHAT_ID")

def send(msg):
    try:
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT, "text": msg}, timeout=10)
    except: pass

while True:
    try:
        for PAIR in PAIRS:
            df = yf.download(PAIR, period="1d", interval="1m", progress=False, auto_adjust=True)
            if len(df) < 25: continue
            
            # Fix for yfinance columns
            close = df['Close'].iloc[:,0] if hasattr(df['Close'], 'iloc') and str(type(df['Close'])).find('DataFrame')!=-1 else df['Close']
            open_p = df['Open'].iloc[:,0] if hasattr(df['Open'], 'iloc') and str(type(df['Open'])).find('DataFrame')!=-1 else df['Open']
            high = df['High'].iloc[:,0] if hasattr(df['High'], 'iloc') and str(type(df['High'])).find('DataFrame')!=-1 else df['High']
            low = df['Low'].iloc[:,0] if hasattr(df['Low'], 'iloc') and str(type(df['Low'])).find('DataFrame')!=-1 else df['Low']

            ema9 = float(close.ewm(span=9).mean().iloc[-1])
            ema21 = float(close.ewm(span=21).mean().iloc[-1])
            
            delta = close.diff()
            gain = delta.where(delta>0,0).rolling(14).mean()
            loss = -delta.where(delta<0,0).rolling(14).mean()
            rsi = float((100-(100/(1+gain/loss))).iloc[-1])

            # Candle Power Filter
            last_o = float(open_p.iloc[-1]); last_c = float(close.iloc[-1])
            last_h = float(high.iloc[-1]); last_l = float(low.iloc[-1])
            body = abs(last_c - last_o)
            full_range = last_h - last_l
            power = (body / full_range * 100) if full_range !=0 else 0

            now = datetime.now(UTC)
            exit_t = now + timedelta(minutes=EXPIRY)
            name = PAIR.replace("=X","")
            sig = None

            # MY STRATEGY LOGIC
            if ema9 > ema21 and 52 < rsi < 72 and power > 60 and last_c > last_o:
                sig = "BUY"
            elif ema9 < ema21 and 28 < rsi < 48 and power > 60 and last_c < last_o:
                sig = "SELL"

            if sig:
                conf = int(75 + power/5) # 75-95% confidence
                if conf > 93: conf = 93
                msg = f"✅ {sig} {name} - {conf}% Confident\nLogic: EMA9>21 + RSI {rsi:.1f} + Power {power:.0f}%\nTrade: {now.strftime('%I:%M %p')} se {exit_t.strftime('%I:%M %p')} tak ({EXPIRY} min)\nTime: {now.strftime('%d %b %I:%M %p')}"
                send(msg)
                time.sleep(3)
        time.sleep(240) # Har 4 min me check
    except Exception as e:
        print(e); time.sleep(60)
