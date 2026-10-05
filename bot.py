from flask import Flask
from threading import Thread
import os, time, requests
import yfinance as yf

app = Flask('')
@app.route('/')
def home(): return "STRICT + POSSIBILITY BOT LIVE"
def run(): app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
Thread(target=run).start()

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
SYMBOLS = ["EURUSD=X","GBPUSD=X","USDJPY=X","AUDUSD=X","GC=F"]

def send(t):
    try:
        print(f"SEND: {t}", flush=True)
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": t}, timeout=10)
    except Exception as e:
        print(f"Err {e}", flush=True)

def chk(s, tf):
    try:
        df = yf.Ticker(s).history(period="5d", interval=tf, auto_adjust=True)
        if len(df) < 50: return None
        c = df['Close']
        h = df['High']
        l = df['Low']
        
        e20 = c.ewm(span=20).mean().iloc[-1]
        e50 = c.ewm(span=50).mean().iloc[-1]
        
        d = c.diff()
        g = d.where(d>0,0).rolling(14).mean()
        ll = -d.where(d<0,0).rolling(14).mean()
        rsi = (100 - (100/(1+g/ll))).iloc[-1]
        
        m = c.ewm(span=12).mean() - c.ewm(span=26).mean()
        mv = m.iloc[-1]
        sv = m.ewm(span=9).mean().iloc[-1]
        price = c.iloc[-1]

        # Target % ATR se
        tr = (h - l).rolling(14).mean().iloc[-1]
        atr_perc = (tr / price) * 100 * 1.5
        if atr_perc > 0.9: atr_perc = 0.8
        if atr_perc < 0.15: atr_perc = 0.20

        # Possibility % calculation (RSI + EMA + MACD strength se)
        # BUY ke liye
        if e20 > e50 and 40 < rsi < 70 and mv > sv:
            base = 60
            if rsi > 55: base += 5
            if rsi > 60: base += 5
            if (mv - sv) > 0.0005: base += 5
            if base > 82: base = 82
            up_p = base
            down_p = 100 - base
            return f"🟢 STRICT BUY {s} {tf}\nPrice: {price:.5f}\nRSI: {rsi:.1f}\nTarget: +{atr_perc:.2f}%\nUp jane ki possibility: {up_p}%\nDown jane ki possibility: {down_p}%"

        # SELL ke liye
        if e20 < e50 and 30 < rsi < 60 and mv < sv:
            base = 60
            if rsi < 45: base += 5
            if rsi < 40: base += 5
            if (sv - mv) > 0.0005: base += 5
            if base > 82: base = 82
            down_p = base
            up_p = 100 - base
            return f"🔴 STRICT SELL {s} {tf}\nPrice: {price:.5f}\nRSI: {rsi:.1f}\nTarget: -{atr_perc:.2f}%\nUp jane ki possibility: {up_p}%\nDown jane ki possibility: {down_p}%"

    except Exception as e:
        print(f"Err {s} {e}", flush=True)
    return None  
