# TinyFish 速查表

> 官方：<https://github.com/tinyfish-io/tinyfish-cookbook> ｜ 主頁：<https://agent.tinyfish.ai>

TinyFish 把「沒有 API 的網站」變成可程式化的資料來源，採**雲端服務**形式。三大端點分層使用：

| 端點 | 速度 | 計費 | 用途 |
|------|------|------|------|
| **Search** | < 0.5s | **免費** | 全網搜尋，回 LLM 友好 JSON |
| **Fetch** | 1–3s | **免費** | 抓單頁，自動清乾淨回 markdown |
| **Agent** | 5–60s | 付費 | 自然語言目標 → 多步驟瀏覽 → 結構化資料 |

---

## 註冊與 API Key

1. 到 <https://agent.tinyfish.ai/> 註冊（**免信用卡**，Search/Fetch 永久免費）。
2. 拿到 API Key 後寫入環境變數：

```powershell
# Windows PowerShell（永久）
[Environment]::SetEnvironmentVariable("TINYFISH_API_KEY","tf_xxx","User")

# 當前 session
$env:TINYFISH_API_KEY = "tf_xxx"
```

```bash
# macOS / Linux
export TINYFISH_API_KEY="tf_xxx"
echo 'export TINYFISH_API_KEY="tf_xxx"' >> ~/.zshrc
```

---

## SDK 安裝

```bash
# Python
pip install tinyfish

# Node / TypeScript
npm install @tiny-fish/sdk

# CLI（互動）
npm install -g @tiny-fish/cli
tinyfish auth login
```

---

## 1) Search — 全網搜尋

純 HTTP，最簡單：

```python
import os, requests

r = requests.get(
    "https://api.search.tinyfish.ai",
    params={"query": "AI agent 爬蟲框架 2026", "limit": 10},
    headers={"X-API-Key": os.environ["TINYFISH_API_KEY"]},
    timeout=10,
)
hits = r.json()["results"]
for h in hits:
    print(h["title"], "→", h["url"])
```

特色：
- 回傳結構：`{title, url, snippet, score, published_at}`
- 速度比直接打 Google/Bing 快得多
- 排名穩定（適合 LLM workflow）

**何時用 Search 而不是 Tavily**：
- 想要「免費 + 不限額度」 → Search 勝。
- 想要「事實 grounding + 學術排名」 → Tavily 更強。

---

## 2) Fetch — 抓乾淨單頁

```python
import os, requests

r = requests.post(
    "https://api.fetch.tinyfish.ai",
    json={"urls": ["https://example.com/article"]},
    headers={"X-API-Key": os.environ["TINYFISH_API_KEY"]},
    timeout=30,
)
data = r.json()
print(data[0]["markdown"])      # 清乾淨的 markdown
print(data[0]["title"])
print(data[0]["html"])          # 也可拿 HTML
```

支援批次：`urls` 傳多個，平行抓。

**何時用 TinyFish Fetch 而不是 Scrapling Fetcher**：
- 你要「LLM 用得順的 markdown」（自動去除 nav/廣告/script）。
- 你不想本地裝 Python 套件、Playwright、Chromium。
- 不在意延遲、量不大。

---

## 3) Agent — 自然語言爬蟲

最強，但較貴／較慢。把整個瀏覽過程交給 AI agent：

```python
import os, requests, json

resp = requests.post(
    "https://agent.tinyfish.ai/v1/automation/run",   # 同步版
    json={
        "url": "https://www.kayak.com",
        "goal": "搜尋 2026/06/15 台北飛東京最便宜的單程機票，列出航空公司、起飛時間、價格 (JSON 陣列，價格用 USD)",
    },
    headers={"X-API-Key": os.environ["TINYFISH_API_KEY"]},
    timeout=120,
)
result = resp.json()
print(json.dumps(result["data"], ensure_ascii=False, indent=2))
```

### 串流（SSE）— 即時看 agent 在做什麼

```python
import os, requests

with requests.post(
    "https://agent.tinyfish.ai/v1/automation/run-sse",
    json={"url": "https://amazon.com", "goal": "..."},
    headers={"X-API-Key": os.environ["TINYFISH_API_KEY"]},
    stream=True, timeout=300,
) as r:
    for line in r.iter_lines(decode_unicode=True):
        if line.startswith("data: "):
            print(line[6:])
```

### Vault — 認證後的網站

```python
# 一次存好憑證
client.vault.store(service="amazon", credentials={"username": "...", "password": "..."})

# 後續自動登入
client.agent.run(
    url="https://amazon.com/myorders",
    goal="列出我所有未出貨訂單與追蹤編號",
    vault={"service": "amazon"},
)
```

---

## MCP 整合（Claude Code / Cursor）

加進 `~/.claude/mcp.json` 或 Cursor MCP 設定：

```json
{
  "mcpServers": {
    "tinyfish": {
      "url": "https://mcp.tinyfish.ai",
      "env": { "TINYFISH_API_KEY": "tf_xxx" }
    }
  }
}
```

之後可在對話中直接呼叫 `tinyfish_search`、`tinyfish_fetch`、`tinyfish_agent` 等工具。

---

## Cookbook 食譜對照表（直接借鑑）

| 範例 | 學到什麼 |
|------|---------|
| `viet-bike-scout` | **平行價格比價**：對多個 URL 同時跑 agent，再 aggregate |
| `tutor-finder` | **多平台聚合搜尋**：用 search + fetch 串起多源 |
| `openbox-deals` | **跨零售商即時聚合**：8 家網站平行抓 + dedupe |
| `tinyskills` | **抓 docs + GitHub** 自動產知識庫 |
| `summer-school-finder` | **學術 / 教育站搜集**（最貼近教師研究情境） |
| `scholarship-finder` | **獎學金聚合**：search → 過濾 → fetch 詳情 |
| `loan-decision-copilot` | **多步表單填寫 + 抓結果** |
| `code-reference-finder` | **抓 GitHub / 官方 docs 給 LLM 引用** |

完整 repo：`git clone https://github.com/tinyfish-io/tinyfish-cookbook`，每個資料夾都有可跑的 README。

---

## 常見坑

| 症狀 | 處理 |
|------|------|
| `401 Unauthorized` | 檢查 `TINYFISH_API_KEY` 是否設對 |
| Agent 跑超久才回 | 改用 `run-sse` 串流；給更明確的 `goal` |
| 結果不是 JSON | `goal` 結尾明寫「**輸出純 JSON 陣列，不要任何前後文字**」 |
| 拿不到付費內容 | 用 Vault 存登入；或改其他合法資料源 |
| 中文目標 agent 聽不懂 | 把 goal 改用英文，或中英並陳 |

---

## 何時 *不* 該用 TinyFish

- 量大（上萬頁）：費用高，改用 **Scrapling Spider 本地跑**。
- 需要極低延遲（即時）：本地 `Fetcher.get()` 永遠更快。
- 隱私敏感（公司內網／本地檔）：絕不要送雲端，改走 Scrapling。
- 純 HTML 結構固定的網站：選擇器一次寫好用十年，不必燒 LLM token。
