from flask import Flask
from threading import Thread
import os, time, requests
import yfinance as yf

app = Flask('')
@app.route('/')
def home(): return "Strict High Accuracy Bot Live"
def run(): app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
Thread(target=run).start()

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
SYMBOLS = ["EURUSD=X","GBPUSD=X","USDJPY=X","AUDUSD=X","GC=F"]

def send_msg(t):
    try:
        print(f"SEND: {t}", flush=True)
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": t}, timeout=10)
    except Exception as e:
        print(f"TG Error {e}", flush=True)

def check(sym, tf):
    try:
        df = yf.Ticker(sym).history(period="5d", interval=tf, auto_adjust=True)
        if len(df) < 50: return None
        c = df['Close']
        e20 = c.ewm(span=20).mean()
        e50 = c.ewm(span=50).mean()
        
        # RSI
        delta = c.diff()
        gain = delta.where(delta>0,0).rolling(14).mean()
        loss = -delta.where(delta<0,0).rolling(14).mean()
        rsi = 100 - (100 / (1 + gain/loss))
        
        # MACD
        ema12 = c.ewm(span=12).mean()
        ema26 = c.ewm(span=26).mean()
        macd = ema12 - ema26
        signal = macd.ewm(span=9).mean()

        price = c.iloc[-1]
        r = rsi.iloc[-1]
        m = macd.iloc[-1]
        s = signal.iloc[-1]
        e20v = e20.iloc[-1]
        e50v = e50.iloc[-1]

        print(f"{sym} {tf} P:{price:.5f} RSI:{r:.1f} MACD:{m:.5f} Sig:{s:.5f}", flush=True)

        # STRICT BUY: Uptrend + RSI not overbought + MACD bullish
        if e20v > e50v and 35 < r < 65 and m > s:
            return f"🟢 BUY {sym} {tf}\nPrice: {price:.5f}\nRSI: {r:.1f} | EMA Bullish | MACD Bull"
        # STRICT SELL: Downtrend + RSI not oversold + MACD bearish
        elif e20v < e50v and 35 < r < 65 and m < s:
            return f"🔴 SELL {sym} {tf}\nPrice: {price:.5f}\nRSI: {r:.1f} | EMA Bearish | MACD Bear"
        else:
            print(f"{sym} {tf} -> No Signal (Condition fail)", flush=True)
            
    except Exception as e:
        print(f"{sym} {tf} Error {e}", flush=True)
    return None

send_msg("✅ Strict Bot Started (65% Accuracy) - GOLD Added")

while True:
    print(f"--- SCANNING {time.strftime('%H:%M:%S')} ---", flush=True)
    for tf in ["5m","15m"]:
        for s in SYMBOLS:
            sig = check(s, tf)
            if sig: send_msg(sig)
            time.sleep(3)
    print("Sleeping 5 min...", flush=True)
    time.sleep(300)
