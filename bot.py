from flask import Flask
from threading import Thread
import os, time, requests
import yfinance as yf

app = Flask('')
@app.route('/')
def home(): return "STRICT BOT LIVE + % Target"
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
        print(f"TG Error {e}", flush=True)

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

        # ATR se % Target nikalna
        tr = (h - l).rolling(14).mean().iloc[-1]
        atr_perc = (tr / price) * 100
        # Prediction %
        target_perc = atr_perc * 1.5
        if target_perc > 1.0: target_perc = 0.8
        if target_perc < 0.15: target_perc = 0.20

        print(f"{s} {tf} P:{price:.5f} RSI:{rsi:.1f} ATR%:{atr_perc:.3f}", flush=True)

        if e20 > e50 and 40 < rsi < 70 and mv > sv:
            return f"🟢 STRICT BUY {s} {tf}\nPrice: {price:.5f}\nRSI: {rsi:.1f}\n🎯 Target: +{target_perc:.2f}% Up\n📉 SL: -{target_perc/2:.2f}%"

        if e20 < e50 and 30 < rsi < 60 and mv < sv:
            return f"🔴 STRICT SELL {s} {tf}\nPrice: {price:.5f}\nRSI: {rsi:.1f}\n🎯 Target: -{target_perc:.2f}% Down\n📈 SL: +{target_perc/2:.2f}%"

    except Exception as e:
        print(f"Err {s} {e}", flush=True)
    print(f"{s} {tf} -> No Signal", flush=True)
    return None

send("✅ STRICT + TARGET BOT STARTED\nTarget % prediction ON")

while True:
    for tf in ["5m","15m"]:
        for s in SYMBOLS:
            x = chk(s, tf)
            if x: send(x)
            time.sleep(3)
    print("Sleeping 5 min...", flush=True)
    time.sleep(300)
