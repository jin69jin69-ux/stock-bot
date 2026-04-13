# =========================================
# 株自動分析BOT（可視化フル版・安全修正）
# =========================================

import os
import yfinance as yf
import ta
import requests
import json
from datetime import datetime
import pytz
import math

# ===== 環境変数 =====
CHANNEL_ACCESS_TOKEN = os.getenv("LINE_TOKEN")
USER_ID = os.getenv("USER_ID")

if not CHANNEL_ACCESS_TOKEN:
    raise RuntimeError("LINE_TOKEN が設定されていません")
if not USER_ID:
    raise RuntimeError("USER_ID が設定されていません")

# ===== 銘柄 =====
CODES = {
    "7203.T": "トヨタ",
    "6758.T": "ソニー",
    "9984.T": "ソフトバンク",
    "9432.T": "NTT",
    "8766.T": "東京海上HD",
    "8267.T": "イオン",
}

results = []

for code, name in CODES.items():
    try:
        df = yf.download(code, period="3mo", progress=False)

        if len(df) < 30:
            results.append(f"■ {name}\nデータ不足（分析不可）\n")
            continue

        df["RSI"] = ta.momentum.rsi(df["Close"], window=14)
        df["SMA25"] = ta.trend.sma_indicator(df["Close"], window=25)
        df["SMA75"] = ta.trend.sma_indicator(df["Close"], window=75)

        latest = df.iloc[-1]
        prev = df.iloc[-2]

        rsi = latest["RSI"]
        sma25 = latest["SMA25"]
        sma75 = latest["SMA75"]

        if math.isnan(rsi) or math.isnan(sma25) or math.isnan(sma75):
            results.append(f"■ {name}\n指標計算中（NaN）\n")
            continue

        price = float(latest["Close"])
        prev_price = float(prev["Close"])
        diff_price = price - prev_price
        diff_percent = (diff_price / prev_price) * 100
        arrow = "▲" if diff_price > 0 else "▼"

        market_score = round(rsi)
        bar = "█" * (market_score // 10) + "░" * (10 - market_score // 10)

        if rsi < 30:
            rsi_state = "売られすぎ"
        elif rsi > 70:
            rsi_state = "過熱"
        else:
            rsi_state = "中立"

        if sma25 > sma75:
            trend = "↗ 上昇"
        else:
            trend = "↘ 下落"

        if rsi < 30 and sma25 > sma75:
            judge = "🟢 買い時"
        elif rsi > 70:
            judge = "🔴 売り時"
        else:
            judge = "👀 様子見"

        results.append(
            f"■ {name}\n"
            f"終値：{round(price,1)}円\n"
            f"前日比：{arrow} {round(diff_price,1)}円（{round(diff_percent,2)}%）\n"
            f"Market Score：{market_score} / 100\n"
            f"{bar}\n"
            f"RSI：{round(rsi,1)}（{rsi_state}）\n"
            f"トレンド：{trend}\n"
            f"判定：{judge}\n"
        )

    except Exception as e:
        results.append(f"■ {name}\nエラー発生：{str(e)}\n")

# ===== LINE送信 =====
jst = pytz.timezone("Asia/Tokyo")
now = datetime.now(jst).strftime("%Y/%m/%d %H:%M")

message = f"【株分析BOT｜{now}】\n\n" + "\n".join(results)

url = "https://api.line.me/v2/bot/message/push"
headers = {
    "Authorization": "Bearer " + CHANNEL_ACCESS_TOKEN,
    "Content-Type": "application/json"
}
payload = {
    "to": USER_ID,
    "messages": [{"type": "text", "text": message}]
}

requests.post(url, headers=headers, data=json.dumps(payload))
