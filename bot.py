from flask import Flask
from threading import Thread
import os, time, requests
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta, timezone

UTC_530 = timezone(timedelta(hours=5, minutes=30))

app = Flask('')
@app.route('/')
def home(): return "MTF Bot Live - Auto Result"

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
        if isinstance(close, pd
