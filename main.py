from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import requests, pandas as pd, numpy as np

BOT_TOKEN = "8521424768:AAFFeuwCnWbmvdyHoN2oCcWHnf-xFS7uV3Y"

# ---------- DATA ----------
def get_candles(symbol):
    url = "https://api.binance.com/api/v3/klines"
    params = {"symbol": symbol, "interval": "1m", "limit": 60}
    data = requests.get(url, params=params).json()
    df = pd.DataFrame(data, columns=[
        "t","o","h","l","c","v","ct","q","n","tb","tq","i"
    ])
    df[["o","h","l","c"]] = df[["o","h","l","c"]].astype(float)
    return df

# ---------- EMA ----------
def ema(series, period):
    return series.ewm(span=period).mean()

# ---------- TREND ----------
def get_trend(df):
    ema20 = ema(df.c, 20)
    ema50 = ema(df.c, 50)

    if ema20.iloc[-1] > ema50.iloc[-1]:
        return "UP"
    if ema20.iloc[-1] < ema50.iloc[-1]:
        return "DOWN"
    return "FLAT"

# ---------- PATTERNS ----------
def candle_patterns(df):
    c = df.iloc[-1]
    p = df.iloc[-2]

    body = abs(c.c - c.o)
    lw = min(c.o, c.c) - c.l
    uw = c.h - max(c.o, c.c)

    if lw > body * 2 and uw < body:
        return "BULL"
    if c.c > c.o and p.c < p.o and c.c > p.o and c.o < p.c:
        return "BULL"

    if uw > body * 2 and lw < body:
        return "BEAR"
    if c.c < c.o and p.c > p.o and c.o > p.c and c.c < p.o:
        return "BEAR"

    return "NONE"

# ---------- STRENGTH ----------
def strength_ok(df):
    recent = df.tail(5)
    bodies = abs(recent.c - recent.o)
    return bodies.mean() > bodies.std()

# ---------- SIGNAL ----------
def generate_signal(df):
    trend = get_trend(df)
    pattern = candle_patterns(df)

    if not strength_ok(df):
        return "SKIP ⚠️⚠️⚠️"

    if trend == "UP" and pattern == "BULL":
        return "BUY 💹💹💹"

    if trend == "DOWN" and pattern == "BEAR":
        return "SELL 📉📉📉"

    return "SKIP ⚠️⚠️⚠️"

# ---------- TELEGRAM ----------
async def nexttrade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        symbol = context.args[0].upper()
        df = get_candles(symbol)
        result = generate_signal(df)
        await update.message.reply_text(result)
    except:
        await update.message.reply_text("SKIP ⚠️⚠️⚠️")

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("nexttrade", nexttrade))
app.run_polling()
