# 食譜 08：主題式學習包（YT + 文章 + GitHub + arXiv）

**情境**：「我想學 Python 裝飾器」「我要找光合作用的教學」「給我 RAG 系統的學習資料」。

**最快路徑**：`python scripts/scrape.py learn "<主題>"` 一行解決，自動同時找 YouTube 影片字幕、教學文章、GitHub 範例、arXiv 論文，整理成單份長 Markdown。

---

## 一鍵速攻

```bash
# 全套（4 種來源都要）
python scripts/scrape.py learn "Python 裝飾器"

# 只要 YouTube + 文章（沒寫程式不需要 github/arxiv）
python scripts/scrape.py learn "光合作用" --include yt,article

# 抓多一點影片，文章不要
python scripts/scrape.py learn "Transformer 注意力機制" \
  --include yt,arxiv --videos 5 --arxiv 5

# 指定輸出檔名
python scripts/scrape.py learn "RAG 檢索增強生成" --out rag-learning.md

# v1.2: 沒 CC 字幕的影片也救（委派 youtube-subtitle SKILL 跑 Whisper）
python scripts/scrape.py learn "光合作用" --whisper-fallback

# v1.2: 強制重抓（24h 內想更新時）
python scripts/scrape.py learn "Python 裝飾器" --no-cache --pdf

# v1.2: 改快取期限為一週
python scripts/scrape.py learn "教學設計" --cache-ttl 604800
```

## v1.2 增強

- **`--whisper-fallback`**：CC 字幕失敗的影片，自動委派給 `youtube-subtitle` SKILL 用 Whisper 辨識（首次需下載 ~75MB tiny 模型）
- **retry/backoff**：arXiv / GitHub API 暫時失敗會自動退避重試 3 次，不會整批失敗
- **失敗摘要**：每次跑完，產出檔案末尾 + console 都會列出哪些項目失敗、為什麼失敗
- **架構重構**：`cmd_learn` 拆成 4 個 `_learn_*_section` helper，每段獨立可測

---

## 自動做了什麼？

```
主題 → 4 個搜尋管道平行：
├── YouTube 教學影片
│     ├── TinyFish Search 找 site:youtube.com 的「{主題} 教學」
│     ├── 對每部影片用 youtube-transcript-api 抓字幕
│     ├── 中文字幕優先（zh-TW > zh-Hant > zh > en）
│     └── 沒中文字幕？自動翻譯成 zh-TW
│
├── 網路教學文章
│     ├── TinyFish Search「{主題} 教學 OR tutorial」
│     ├── 排除已在 YouTube 區的連結
│     ├── 偏好 .tw、ithome、CSDN、Wikipedia 等中文站
│     └── TinyFish Fetch 批次抓乾淨 markdown（每篇截 4000 字）
│
├── GitHub 相關專案
│     ├── GitHub API 搜 repo（按 stars 排序）
│     ├── 抓每個 repo 的 README（截 4000 字）
│     └── 適合：Python/JS/Rust 等程式類主題
│
└── arXiv 論文
      ├── 官方 API（無需 key，公開資料）
      ├── 取相關性最高的 3 篇
      └── 適合：學術、AI、科學類主題
```

最後拼成一份 **長 Markdown**：

```
# 📚 {主題} ── 學習包
🎬 YouTube 教學影片
   ### 1. [標題](url)
   <details><summary>📜 完整字幕</summary>
   ```（字幕內容）```
   </details>
📰 網路教學文章
   ### 1. [標題](url)
   （文章 markdown）
🐙 GitHub 相關專案
   ### 1. [owner/repo](url) ⭐12,345
   <details><summary>📄 README</summary>
   （README 內容）
   </details>
📑 arXiv 相關論文
   ### 1. [標題](url)
   _作者 ｜ 發表日_
   > Abstract
```

---

## 中文優先策略

| 階段 | 中文優先做法 |
|------|------------|
| YouTube 搜尋 | query 用中文「教學」，再 fallback 英文「tutorial」 |
| YouTube 字幕 | langs 順序：zh-TW → zh-Hant → zh-CN → zh → zh-Hans → en |
| 字幕無中文版 | 自動呼叫 `transcript.translate("zh-TW")` 翻譯 |
| 文章 | query 用中文，並把 `.tw` / `ithome` / 簡中站排在前面 |
| GitHub | repo 描述很多是英文，這邊不強制中文 |
| arXiv | 學術論文幾乎全英文，原文保留 |

---

## 教學情境組合技

### 1) 學完直接生成 PDF 給學生

```bash
python scripts/scrape.py learn "光合作用" --include yt,article --out 光合作用.md
python scripts/scrape.py to-pdf 光合作用.md --out 光合作用.pdf
```

### 2) 學完丟給 Claude 整理重點

抓完後直接跟我說：「讀 `learn-Python_裝飾器.md`，整理 5 條重點 + 3 道練習題」。
（我會用 Read 把整份讀進來、生成精煉摘要。）

### 3) 排程每週追新主題

`ai-agent-orchestrator` 排程，每週一抓「最新 AI agent 框架」更新一次知識包：

```yaml
schedule: "0 8 * * 1"
steps:
  - run: python scripts/scrape.py learn "AI agent 框架 最新" --videos 5
  - notify:
      channel: line
      message: "本週 AI agent 學習包已更新"
```

---

## 速度與成本

| 來源 | 速度 | 成本 |
|------|------|------|
| YouTube 字幕 | 每部 1–3 秒 | **免費**（youtube-transcript-api 無需 key） |
| 教學文章（TinyFish Fetch）| 5 篇約 5 秒 | **免費**（TinyFish Search/Fetch 永久免費） |
| GitHub | 即時 | 免費（未登入有限額；設 `GITHUB_TOKEN` 更穩） |
| arXiv | 約 1 秒 | **免費**（官方 API） |

整套跑下來通常 < 30 秒，產出 5–20 KB Markdown。

---

## 常見坑

| 症狀 | 原因 | 處理 |
|------|------|------|
| `未安裝 youtube-transcript-api` | 套件沒裝 | `pip install youtube-transcript-api` |
| 「字幕無法取得」 | 該影片作者停用字幕、私人影片 | 看下一部；或用 OpenAI Whisper 自己轉 |
| YouTube 全是英文影片 | 中文 query 太精確、影片少 | 加 `--videos 5` 多抓幾部，看不懂可請我翻譯 |
| GitHub 403 rate limit | 未登入 IP 被限 | 設環境變數 `GITHUB_TOKEN`（personal access token） |
| arXiv 拿不到資料 | 網路問題 / 主題太冷 | 換主題或 `--include yt,article` 跳過 |
| 整份檔案太大 | 文章字數開太大 | 加 `--article-chars 2000 --github-readme-chars 2000` |

---

## 何時該用此食譜

✅ 想學新主題、要快速橫掃多種媒材  
✅ 老師備課，要同時參考影片和文章  
✅ 學生報告，要找教學資料 + 開源範例 + 學術論文  
✅ 想產出可以印出來看的學習包

❌ 已經知道是哪個 YouTube 頻道 → 直接 `youtube-subtitle` 技能更專注  
❌ 純學術文獻搜尋 → `auto-research-claw` 技能更完整（OAI-PMH、Crossref、APA）  
❌ 想要互動測驗、自動出題 → 用 `tw-anti-ai-exam-combo` 技能
