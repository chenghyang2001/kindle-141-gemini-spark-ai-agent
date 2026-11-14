---
name: tavily-search
description: |
  研究級網路搜尋（Tavily LLM-optimized API）— 補位內建 WebSearch 沒有的「相關性分數」、
  「精煉 chunk」、「網域過濾」、「時間範圍」、「深度搜尋」這幾個高精準場景。
  內建本地快取（1 小時 TTL）與自動重試（429/5xx 指數退避）。
  **觸發條件**：使用者明確要求**精準度高的研究查詢**，或內建 WebSearch 結果不夠用時。
  Tavily-specific 觸發詞：「Tavily」「相關性分數」「research-grade search」
  「精準研究」「我要 chunk」「給我 score」「網域過濾搜尋」「深度搜尋」、
  以及任何明說 `scripts/search.mjs` 或 `tavily-search` 的需求。
  **優先順序規則**：
  - 一般「搜尋一下」「上網查」→ 用內建 **WebSearch**（免 key、夠用）
  - 抓單一頁面內容 → 用內建 **WebFetch**
  - **要相關性分數、要 chunk、要 score 過濾、要深度研究、要新聞模式** → 用 Tavily
  - 使用者明說「Tavily」→ 直接用 Tavily
homepage: https://tavily.com
---

# Tavily Search

LLM 友善的網路搜尋。**補位**內建 WebSearch 沒有的精準度與過濾能力。

## 跟內建工具的分工

| 場景 | 用什麼 | 為什麼 |
|------|-------|-------|
| 隨手查、看 docs | `WebSearch` | 免 key、預設工具 |
| 抓單一頁面 | `WebFetch` | 不用 API |
| 要相關性分數過濾 | **Tavily** | WebSearch 沒有 score |
| 要 LLM 友善的 chunk | **Tavily** | WebSearch 給整段，Tavily 給精煉片段 |
| 限定特定網域 | **Tavily** | `--include-domains` |
| 限定時間範圍 | **Tavily** | `--time-range week/month/year` |
| 深度研究查詢 | **Tavily** | `--depth advanced` |
| 新聞模式 | **Tavily** | `--topic news` |

**判斷規則**：使用者沒明說工具時，先用 WebSearch；如果結果不夠精準或要過濾，再升級用 Tavily。

## 認證

到 [tavily.com](https://tavily.com) 申請 API key（免費 1000 次/月）：

```bash
# bash / zsh
export TAVILY_API_KEY="tvly-XXXXXXXXXXXXXXXXXXXXXXXXX"

# PowerShell
$env:TAVILY_API_KEY = "tvly-..."
[System.Environment]::SetEnvironmentVariable('TAVILY_API_KEY','tvly-...','User')
```

## 使用方式

```bash
node scripts/search.mjs "claude code 1.0.130 release notes"
node scripts/search.mjs "react server components" -n 10
node scripts/search.mjs "AI safety news" --topic news --time-range week
node scripts/search.mjs "TSMC 2nm" --include-domains anandtech.com,techpowerup.com
node scripts/search.mjs "python asyncio" --depth advanced --json
```

## Options

| Option | 說明 | 預設 |
|--------|------|------|
| `-n <count>` | 結果數（1–20） | 10 |
| `--depth <mode>` | `ultra-fast` / `fast` / `basic` / `advanced` | `basic` |
| `--topic <topic>` | `general` / `news` | `general` |
| `--time-range <range>` | `day` / `week` / `month` / `year` | — |
| `--include-domains <list>` | 逗號分隔白名單 | — |
| `--exclude-domains <list>` | 逗號分隔黑名單 | — |
| `--raw-content` | 回傳完整頁面 | false |
| `--no-cache` | 跳過本地快取 | — |
| `--cache-ttl <sec>` | 快取存活秒數 | 3600 |
| `--timeout <ms>` | 單次 timeout | 30000 |
| `--json` | 輸出原始 JSON | false |

## 快取與重試

- **本地快取**：`~/.claude/skill-data/tavily-search/cache/`，1h TTL，省 API 額度
- **自動重試**：429 / 5xx 指數退避 3 次（讀 Retry-After header）
- **Timeout 重試**：超時也會重試
- **Client error 不重試**：401 / 432 直接報錯

## Search Depth 取捨

| Depth | 延遲 | 相關性 | 用途 |
|-------|------|--------|------|
| `ultra-fast` | 最低 | 較低 | 即時 chat |
| `fast` | 低 | 中 | 延遲敏感 |
| `basic` | 中 | 高 | 通用、平衡 |
| `advanced` | 高 | 最高 | 研究、要求精準 |

## 常見錯誤

| HTTP | 含義 | 處理 |
|------|------|------|
| 401 | API key 錯/未設 | 檢查 `TAVILY_API_KEY` |
| 429 | rate limit | 自動重試 3 次 |
| 432 | 額度用完 | 到 dashboard 充值 |
| 500/503 | upstream error | 自動重試 |

## License

MIT-0 · 原作者 [@matthew77](https://github.com/matthew77) · Claude 整合：阿亮老師
