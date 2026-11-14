# 食譜 01：搜尋 → 抓乾淨內容 → LLM 摘要

**情境**：使用者問「找最新關於 X 的資料整理給我」。

**路徑**：TinyFish Search → TinyFish Fetch → 自行用 LLM 摘要 → 輸出 Markdown / PDF。

---

## CLI 速攻

```bash
# 一行搞定（搜尋 + 抓前 5 篇 + 整成 markdown）
python scripts/scrape.py search "AI agent 工作流程 2026" --top 5 \
  --fetch --out research.md
```

`--fetch` 會對每個搜尋結果再呼叫 TinyFish Fetch，把全文塞進輸出。

---

## Python 範本

```python
import os, requests, json
from pathlib import Path

API_KEY = os.environ["TINYFISH_API_KEY"]
QUERY   = "AI agent 工作流程 2026"
TOP     = 5

# 1) Search
hits = requests.get(
    "https://api.search.tinyfish.ai",
    params={"query": QUERY, "limit": TOP},
    headers={"X-API-Key": API_KEY},
    timeout=15,
).json()["results"]

# 2) Fetch（批次）
urls = [h["url"] for h in hits]
docs = requests.post(
    "https://api.fetch.tinyfish.ai",
    json={"urls": urls},
    headers={"X-API-Key": API_KEY},
    timeout=60,
).json()

# 3) 拼成 markdown
out = [f"# {QUERY}\n\n_搜尋日期：{__import__('datetime').date.today()}_\n"]
for h, d in zip(hits, docs):
    out.append(f"## [{h['title']}]({h['url']})\n")
    out.append(f"> {h['snippet']}\n")
    out.append(d.get("markdown", "") + "\n\n---\n")

Path("research.md").write_text("\n".join(out), encoding="utf-8")
print("OK → research.md")
```

---

## 進階：交給 Claude 自己摘要

收完 `research.md` 後，可以：

1. 直接讓 Claude 讀檔做摘要（最省 token）。
2. 或外加 `claude-api` SKILL，在腳本中呼叫 Claude API 並開啟 prompt caching。

---

## 教學情境變形

把 query 改成課程主題，加 `--education-mode` 旗標（CLI 內建），會自動：
- 過濾掉論壇、低品質農場站
- 偏好 .edu / 政府站 / 學術期刊
- 在輸出加上「適合 X 年級」「重點觀念」「可延伸活動」三段
