# =========================================
# 株自動分析BOT（RSI＋移動平均・LINE通知）
# =========================================

import os
import yfinance as yf
import ta
import requests
import json
from datetime import datetime
import pytz

# ===== 設定 =====
CODES = {
    "7203.T": "トヨタ",
    "6758.T": "ソニー",
    "9984.T": "ソフトバンク",
    "9432.T": "NTT",
    "8766.T": "東京海上HD",
    "8267.T": "イオン",
}

CHANNEL_ACCESS_TOKEN = os.environ["LINE_TOKEN"]
USER_ID = os.environ["USER_ID"]

results = []

for code, name in CODES.items():
    try:
        df = yf.download(code, period="3mo", progress=False)

        if df.empty:
            continue

        df["RSI"] = ta.momentum.rsi(df["Close"], window=14)
        df["SMA25"] = ta.trend.sma_indicator(df["Close"], window=25)
        df["SMA75"] = ta.trend.sma_indicator(df["Close"], window=75)

        latest = df.iloc[-1]

        rsi = float(latest["RSI"])
        price = float(latest["Close"])
        sma25 = float(latest["SMA25"])
        sma75 = float(latest["SMA75"])

        if rsi < 30 and sma25 > sma75:
            judge = "🟢 買い時（反発＋上昇トレンド）"
        elif rsi > 70:
            judge = "🔴 売り時（過熱）"
        else:
            continue

        results.append(
            f"{name}\n"
            f"終値：{round(price,1)} 円\n"
            f"RSI：{round(rsi,1)}\n"
            f"25MA / 75MA：{round(sma25,1)} / {round(sma75,1)}\n"
            f"{judge}\n"
        )

    except Exception:
        continue

# ===== 日本時間 =====
jst = pytz.timezone("Asia/Tokyo")
now = datetime.now(jst).strftime("%Y/%m/%d %H:%M")

if results:
    message = "【株分析BOT｜" + now + "】\n\n" + "\n".join(results)
else:
    message = "【株分析BOT｜" + now + "】\n該当銘柄はありませんでした"

# ===== LINE送信 =====
url = "https://api.line.me/v2/bot/message/push"

headers = {
    "Authorization": "Bearer " + CHANNEL_ACCESS_TOKEN,
    "Content-Type": "application/json",
}

data = {
    "to": USER_ID,
    "messages": [
        {
            "type": "text",
            "text": message
        }
    ],
}

requests.post(url, headers=headers, data=json.dumps(data))
