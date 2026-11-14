# 食譜 03：用自然語言抽取結構化資料

**情境**：使用者說「幫我從這個網站抓 X、Y、Z 三個欄位」，但網站結構雜亂、選擇器不穩。

**最佳解**：TinyFish Agent — 你只描述「目標」，agent 自己決定怎麼點、怎麼抓。

---

## CLI 速攻

```bash
python scripts/scrape.py agent "https://www.amazon.com/s?k=usb-c+hub" \
  --goal "列出前 10 個搜尋結果，每筆包含 title, price_usd, rating, url。輸出純 JSON 陣列。" \
  --out hubs.json
```

---

## Python 範本

```python
import os, requests, json

resp = requests.post(
    "https://agent.tinyfish.ai/v1/automation/run",
    headers={"X-API-Key": os.environ["TINYFISH_API_KEY"]},
    json={
        "url": "https://www.amazon.com/s?k=usb-c+hub",
        "goal": (
            "List the top 10 search results. "
            "For each, return a JSON object with: "
            "title (string), price_usd (number), rating (float, 0-5), url (string). "
            "Output ONLY a JSON array, no preamble or explanation."
        ),
    },
    timeout=180,
)
items = resp.json()["data"]
print(json.dumps(items, indent=2, ensure_ascii=False))
```

---

## Goal 撰寫秘訣

| 寫得好 | 寫得糟 |
|--------|--------|
| 明列欄位名稱與型別 | 「抓商品資訊」 |
| 規定輸出純 JSON、無前後文 | 沒講格式 → 拿到 prose |
| 限定數量（top 10） | 不限 → agent 跑超久或斷掉 |
| 一個任務只做一件事 | 一次又搜尋又比價又翻譯 |

範本：

```text
Navigate to {url} and extract {what}.
For each item, return: {field1 (type)}, {field2 (type)}, ...
Output ONLY a JSON array. No markdown, no commentary.
If a field is missing, use null.
Stop after the first {N} items.
```

---

## 平行抽取（價格比較類）

```python
import asyncio, os, aiohttp, json

URLS = [
  "https://shop1.com/iphone-15",
  "https://shop2.com/iphone-15",
  "https://shop3.com/iphone-15",
]
GOAL = "Extract product price (number, USD) and stock_status (string). Return ONLY JSON object."
KEY  = os.environ["TINYFISH_API_KEY"]

async def one(session, url):
    async with session.post(
        "https://agent.tinyfish.ai/v1/automation/run",
        headers={"X-API-Key": KEY},
        json={"url": url, "goal": GOAL},
        timeout=180,
    ) as r:
        data = (await r.json()).get("data", {})
        return {"url": url, **data}

async def main():
    async with aiohttp.ClientSession() as s:
        results = await asyncio.gather(*(one(s, u) for u in URLS))
    print(json.dumps(results, indent=2))

asyncio.run(main())
```

---

## 何時改用 Scrapling

- Agent 跑太貴（一單 NT$x，你要跑十萬筆）→ Agent 跑 5 筆當「老師」，你看它怎麼做，自己用 Scrapling 寫死選擇器。
- 結構非常固定 → 寫死選擇器一次寫好用很久。
- 隱私／本地需求 → 不能送 LLM。
