import os
import requests

TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

LOW, HIGH = 0.5, 0.6  # 알림 구간(%)


def get(url, **kw):
    r = requests.get(url, timeout=15, **kw)
    r.raise_for_status()
    return r.json()


# 빗썸 원화 시세 (전체 코인)
bithumb = get("https://api.bithumb.com/public/ticker/ALL_KRW")["data"]
krw = {
    sym: float(v["closing_price"])
    for sym, v in bithumb.items()
    if isinstance(v, dict) and float(v.get("closing_price", 0)) > 0
}

# 해외 시세 (KuCoin USDT 마켓 전체)
tickers = get("https://api.kucoin.com/api/v1/market/allTickers")["data"]["ticker"]
usd = {
    t["symbol"][:-5]: float(t["last"])
    for t in tickers
    if t["symbol"].endswith("-USDT") and t["last"]
}

fx = get("https://open.er-api.com/v6/latest/USD")["rates"]["KRW"]

hits, checked = [], 0
for sym, p_krw in krw.items():
    if sym not in usd:
        continue
    checked += 1
    premium = (p_krw / (usd[sym] * fx) - 1) * 100
    if LOW <= premium <= HIGH:
        hits.append((sym, premium))

print(f"비교 코인 {checked}개 / 구간 해당 {len(hits)}개 / 환율 {fx:,.1f}")
for sym, p in sorted(hits, key=lambda x: x[1]):
    print(f"{sym} {p:.2f}%")

if hits:
    lines = [f"{s}  {p:.2f}%" for s, p in sorted(hits, key=lambda x: x[1])]
    text = f"김프 {LOW}~{HIGH}% 구간 (빗썸)\n" + "\n".join(lines[:40])
    requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        data={"chat_id": CHAT_ID, "text": text},
        timeout=10,
    )
