from flask import Flask
from threading import Thread
import os, time, requests, yfinance as yf, pandas as pd
from datetime import datetime, timedelta, timezone

UTC = timezone(timedelta(hours=5, minutes=30))
app = Flask('')
@app.route('/')
def home(): return "Live"
def run(): app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
Thread(target=run, daemon=True).start()

BOT=os.environ.get("BOT_TOKEN")
CHAT=os.environ.get("CHAT_ID")
SYMS={"EURUSD=X":"EURUSD","GBPUSD=X":"GBPUSD","USDJPY=X":"USDJPY","AUDUSD=X":"AUDUSD"}

def send(t):
    try: requests.post(f"https://api.telegram.org/bot{BOT}/sendMessage",data={"chat_id":CHAT,"text":t},timeout=15)
    except: pass

def get_trend(sym, per, inv):
    try:
        df=yf.download(sym,period=per,interval=inv,progress=False,auto_adjust=True)
        if len(df)<40: return None
        try:
            if isinstance(df.columns, pd.MultiIndex): df.columns=df.columns.get_level_values(0)
        except: pass
        c=df['Close']
        try: c=c.iloc[:,0]
        except: pass
        e20=float(c.ewm(span=20).mean().iloc[-1]); e50=float(c.ewm(span=50).mean().iloc[-1])
        d=c.diff(); g=d.where(d>0,0).rolling(14).mean().iloc[-1]; l=-d.where(d<0,0).rolling(14).mean().iloc[-1]
        try: g=float(g.iloc[-1])
        except: g=float(g)
        try: l=float(l.iloc[-1])
        except: l=float(l)
        r=100-(100/(1+g/l)) if l!=0 else 50; p=float(c.iloc[-1])
        if e20>e50 and r>50: return "BUY",p,r
        if e20<e50 and r<50: return "SELL",p,r
        return "SIDEWAYS",p,r
    except: return None

def get_price(sym):
    try:
        df=yf.download(sym,period="1d",interval="1m",progress=False,auto_adjust=True)
        try:
            if isinstance(df.columns, pd.MultiIndex): df.columns=df.columns.get_level_values(0)
        except: pass
        return float(df['Close'].iloc[-1])
    except: return None

def get_prob(side, bc, sc, rsi):
    if side=="BUY":
        base=70 if bc==4 else 85
        up=int(min(95, base + max(0, rsi-50)*0.8))
        return up, 100-up
    else:
        base=70 if sc==4 else 85
        down=int(min(95, base + max(0, 50-rsi)*0.8))
        return 100-down, down

def check_result(sym, name, side, entry, etime):
    time.sleep(1200)
    ex=get_price(sym)
    if not ex: return
    ch=((ex-entry)/entry)*100
    if side=="BUY":
        if ch>0: send(f"✅ PROFIT {name} {side}\nEntry {round(entry,5)} ({etime})\nExit {round(ex,5)}\nChange {round(ch,3)}%")
        else: send(f"❌ LOSS {name} {side}\nEntry {round(entry,5)} ({etime})\nExit {round(ex,5)}\nChange {round(ch,3)}%")
    else:
        if ch<0: send(f"✅ PROFIT {name} {side}\nEntry {round(entry,5)} ({etime})\nExit {round(ex,5)}\nChange {round(ch,3)}%")
        else: send(f"❌ LOSS {name} {side}\nEntry {round(entry,5)} ({etime})\nExit {round(ex,5)}\nChange {round(ch,3)}%")

send("✅ Bot Started - With %")

while True:
    try:
        for s,n in SYMS.items():
            a=get_trend(s,"5d","5m"); b=get_trend(s,"5d","15m"); c=get_trend(s,"5d","30m"); d=get_trend(s,"5d","60m"); e=get_trend(s,"6mo","1d")
            if not all([a,b,c,d,e]): continue
            tr=[a[0],b[0],c[0],d[0],e[0]]; bc=tr.count("BUY"); sc=tr.count("SELL")
            if bc>=4: side="BUY"
            elif sc>=4: side="SELL"
            else: continue
            pr=b[1]; rs=b[2]; up_p, down_p=get_prob(side, bc, sc, rs)
            now=datetime.now(UTC); ex=now+timedelta(minutes=20)
            es=now.strftime("%I:%M %p"); exs=ex.strftime("%I:%M %p"); ds=now.strftime("%d %b")
            msg=f"Strict {side} {n}\nTrade: {es} se {exs} tak (20 min)\nPrice: {round(pr,5)}\nRsi: {round(rs,1)}\nUp: {up_p}% Down: {down_p}%\nTime: {ds} {es} UTC+5:30"
            send(msg)
            Thread(target=check_result,args=(s,n,side,pr,es),daemon=True).start()
        time.sleep(300)
    except: time.sleep(60)
