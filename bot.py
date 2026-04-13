# =========================================
# 株自動分析BOT（時間帯解説・🚨買い時強調・詳細版）
# =========================================

import os
import yfinance as yf
import ta
import requests
import json
from datetime import datetime, time
import pytz
import math

# ===== 環境変数 =====
LINE_TOKEN = os.getenv("LINE_TOKEN")
USER_ID = os.getenv("USER_ID")

if not LINE_TOKEN:
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

# ===== 時間帯判定 =====
jst = pytz.timezone("Asia/Tokyo")
now = datetime.now(jst)
now_time = now.time()

if time(9, 0) <= now_time <= time(11, 30):
    market_state = "取引時間中（前場）"
    time_label = f"{now.strftime('%H:%M')} 時点"
    commentary = "前場：寄り付き後の流れを確認する時間帯です。"
elif time(12, 30) <= now_time <= time(15, 0):
    market_state = "取引時間中（後場）"
    time_label = f"{now.strftime('%H:%M')} 時点"
    commentary = "後場：本日の方向感が固まりやすい時間帯です。"
elif now_time > time(15, 0):
    market_state = "取引終了後"
    time_label = "本日引け時点"
    commentary = "引け後：本日の総括です。"
else:
    market_state = "取引開始前"
    time_label = "前営業日引け時点"
    commentary = "取引前：前営業日の状況を確認します。"

results = []
any_moved = False

# =========================================
# メイン分析
# =========================================
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

        rsi = float(latest["RSI"])
        sma25 = float(latest["SMA25"])
        sma75 = float(latest["SMA75"])

        if math.isnan(rsi) or math.isnan(sma25) or math.isnan(sma75):
            results.append(f"■ {name}\n指標計算中\n")
            continue

        price = float(latest["Close"])
        prev_price = float(prev["Close"])

        diff_price = price - prev_price
        diff_percent = (diff_price / prev_price) * 100
        if diff_price != 0:
            any_moved = True

        arrow = "▲" if diff_price > 0 else "▼"

        # ===== Market Score =====
        market_score = round(rsi)
        score_bar = "█" * (market_score // 10) + "░" * (10 - market_score // 10)

        # ===== RSI状態 =====
        if rsi < 30:
            rsi_state = "売られすぎ"
        elif rsi > 70:
            rsi_state = "過熱"
        else:
            rsi_state = "中立"

        # ===== トレンド =====
        trend = "↗ 上昇" if sma25 > sma75 else "↘ 下落"

        # ===== 判定（🚨付き）=====
        if rsi < 30 and sma25 > sma75:
            judge = "🚨🟢 買い時"
        elif rsi > 70:
            judge = "🔴 売り時"
        else:
            judge = "👀 様子見"

        results.append(
            f"■ {name}\n"
            f"終値：{round(price,1)}円\n"
            f"前日比：{arrow} {round(diff_price,1)}円（{round(diff_percent,2)}%）\n"
            f"Market Score：{market_score} / 100\n"
            f"{score_bar}\n"
            f"RSI：{round(rsi,1)}（{rsi_state}）\n"
            f"トレンド：{trend}\n"
            f"判定：{judge}\n"
        )

    except Exception as e:
        results.append(f"■ {name}\nエラー：{str(e)}\n")

# ===== 動きがなければ通知しない =====
if not any_moved:
    print("全銘柄が動いていないため通知なし")
    exit(0)

# =========================================
# LINE送信
# =========================================
message = (
    f"【株分析BOT｜{now.strftime('%Y/%m/%d %H:%M')}】\n"
    f"市場状態：{market_state}\n"
    f"分析基準：{time_label}\n"
    f"{commentary}\n\n"
    + "\n".join(results)
)

url = "https://api.line.me/v2/bot/message/push"
headers = {
    "Authorization": "Bearer " + LINE_TOKEN,
    "Content-Type": "application/json",
}
payload = {
    "to": USER_ID,
    "messages": [{"type": "text", "text": message}]
}

requests.post(url, headers=headers, data=json.dumps(payload))
