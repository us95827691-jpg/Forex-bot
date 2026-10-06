from flask import Flask
from threading import Thread
import os, time, requests, yfinance as yf
from datetime import datetime, timedelta, timezone

UTC = timezone(timedelta(hours=5, minutes=30))
app = Flask('')
@app.route('/')
def home(): return "High Accuracy Bot Live"
def run(): app.run(host='0.0.0.0', port=8080)
Thread(target=run, daemon=True).start()

PAIRS = ["EURUSD=X", "GBPUSD=X", "USDJPY=X", "EURJPY=X", "GBPJPY=X", "AUDUSD=X"]
EXPIRY = 5
TOKEN = os.getenv("BOT_TOKEN")
CHAT = os.getenv("CHAT_ID")

def send(msg):
    try:
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT, "text": msg}, timeout=15)
    except: pass

time.sleep(5)
send(f"✅ High Accuracy Bot Started - 5 Min Expiry Active\nTime: {datetime.now(UTC).strftime('%I:%M %p')}")

while True:
    try:
        for PAIR in PAIRS:
            df = yf.download(PAIR, period="2d", interval="1m", progress=False, auto_adjust=True)
            if len(df) < 50: continue
            
            close = df['Close'].iloc[:,0] if 'DataFrame' in str(type(df['Close'])) else df['Close']
            open_p = df['Open'].iloc[:,0] if 'DataFrame' in str(type(df['Open'])) else df['Open']
            high = df['High'].iloc[:,0] if 'DataFrame' in str(type(df['High'])) else df['High']
            low = df['Low'].iloc[:,0] if 'DataFrame' in str(type(df['Low'])) else df['Low']

            ema9 = float(close.ewm(span=9).mean().iloc[-1])
            ema21 = float(close.ewm(span=21).mean().iloc[-1])
            ema50 = float(close.ewm(span=50).mean().iloc[-1])
            
            delta = close.diff(); gain = delta.where(delta>0,0).rolling(14).mean(); loss = -delta.where(delta<0,0).rolling(14).mean()
            rsi = float((100-(100/(1+gain/loss))).iloc[-1])

            last_o = float(open_p.iloc[-1]); last_c = float(close.iloc[-1])
            prev_o = float(open_p.iloc[-2]); prev_c = float(close.iloc[-2])
            last_h = float(high.iloc[-1]); last_l = float(low.iloc[-1])
            
            power = (abs(last_c-last_o)/(last_h-last_l)*100) if (last_h-last_l)!=0 else 0

            # Trend filter
            up_trend = ema9 > ema21 and ema21 > ema50
            down_trend = ema9 < ema21 and ema21 < ema50

            now = datetime.now(UTC); exit_t = now + timedelta(minutes=EXPIRY)
            name = PAIR.replace("=X","")
            sig = None

            # HIGH ACCURACY LOGIC - 2 candle confirmation + Power 58+
            if up_trend and 55 < rsi < 68 and power > 58 and last_c > last_o and prev_c > prev_o:
                sig = "BUY"
            elif down_trend and 32 < rsi < 45 and power > 58 and last_c < last_o and prev_c < prev_o:
                sig = "SELL"

            if sig:
                msg = f"🔥 HIGH ACCURACY {sig} {name}\n\n⏰ Trade: {now.strftime('%I:%M %p')} se {exit_t.strftime('%I:%M %p')} tak ({EXPIRY} MIN)\n📊 RSI: {rsi:.1f} | Power: {power:.0f}% | Trend: OK\n✅ 2 Candle Confirm\n\nTime: {now.strftime('%d %b %I:%M %p')}"
                send(msg)
                time.sleep(3)
        time.sleep(180) # har 3 min me check
    except Exception as e:
        print(f"Error: {e}"); time.sleep(30)
