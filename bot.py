# stock-bot（リポジトリ名）
# ├─ bot.py
# ===== ライブラリ =====

import yfinance as yf
import ta
import requests
import json

# ===== 設定 =====
CODES = {
"7203.T": "トヨタ",
"6758.T": "ソニー",
"9984.T": "ソフトバンク"
“9432.T”: “NTT”
“8267.T”:”イオン”
“8766.T”:”東京海上ホールディングス”
}

CHANNEL_ACCESS_TOKEN = os.environ["WmeRh9HpZbrsCYjMLD/hPdh5CLhx5a9fymTsDIKikD+zkYT4hFs5d54hMxWpDbllOY7ErDzNnZjE3+XcgajXB9p/ABJxVwK34r9mH4lVgVspqmQE3iQ7U0y7++h7IALBwsbyGiTcMagk+sWwCkNwKgdB04t89/1O/w1cDnyilFU="]

USER_ID = os.environ["U2d78a497e58c747d311fee5b48ff3da8"]

results = []

# ===== 銘柄ごとに分析 =====
for code, name in CODES.items():
df = yf.download(code, period="3mo", progress=False)
df["RSI"] = ta.momentum.rsi(df["Close"], window=14)

latest = df.iloc[-1]

if latest["RSI"] < 30:
judge = "売られすぎ"
elif latest["RSI"] > 70:
judge = "買われすぎ"
else:
judge = "様子見"

results.append(
f"{name}（{code}）\n"
f"終値：{round(latest['Close'],1)}円\n"
f"RSI：{round(latest['RSI'],1)}\n"
f"判定：{judge}\n"
)

# ===== メッセージ作成 =====
message = "【株分析BOT（複数銘柄）】\n\n" + "\n".join(results)

# ===== LINE送信 =====
url = "https://api.line.me/v2/bot/message/push"
headers = {
"Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}",
"Content-Type": "application/json"
}

data = {
"to": USER_ID,
"messages": [{"type": "text", "text": message}]
}

requests.post(url, headers=headers, data=json.dumps(data))

print("✅ 複数銘柄をLINEに送信しました")
├─ requirements.txt
└─ .github/
   └─ workflows/
      └─ run.yml
