# 食譜 06：教學與研究素材搜集

**情境**：教師備課、研究論文文獻搜集、學生報告找資料。

**核心策略**：合規優先 → 官方 API > 開放資料 > 公開網頁；輸出可引用、可重現。

---

## 6.1 學術論文（強烈建議用 API）

| 來源 | 推薦工具 | 何時用 |
|------|---------|-------|
| arXiv | 官方 API（無需 key）| 預印本，AI/物理/數學 |
| HuggingFace Daily Papers | Web Scraping OK | 追每日新論文 |
| Crossref | 官方 API（無需 key）| DOI 解析、引文 |
| Google Scholar | **不可大量爬**，違反 ToS | 只能逐筆人工 |
| 台灣 NDLTD | OAI-PMH 協定 | 博碩士論文 |

直接用既有的 `auto-research-claw` SKILL 取代本食譜更省事。

---

## 6.2 一般教學素材搜集流程

```bash
# 1. 先搜尋（過濾教育向站點）
python scripts/scrape.py search "光合作用 國中教材" --top 15 \
  --prefer-domains ".edu.tw,.gov.tw,wikipedia.org,khan-academy" \
  --out hits.json

# 2. 從 hits.json 挑選 5 筆，下載全文
python scripts/scrape.py fetch-batch hits.json --top 5 --out lesson-pack/

# 3. 整合成一份 PDF 給學生
python scripts/scrape.py to-pdf lesson-pack/ --title "光合作用 課前讀本" \
  --out lesson.pdf
```

CLI 內建 `--education-mode` 開啟時會：
- 自動排除社群論壇、農場站
- 自動加上「來源、作者、出版年」資訊框
- 文末附 APA 引用列表

---

## 6.3 政府開放資料

**先檢查**：[data.gov.tw](https://data.gov.tw)、[opendata.epa.gov.tw](https://opendata.epa.gov.tw) 有沒有現成 CSV/JSON。
- 有 → 直接 `requests.get()` 下載即可，不用爬蟲。
- 沒有 → 用 Scrapling Fetcher（一定是公開、可索引）。

---

## 6.4 研究情境：可重現性要點

每次爬取務必輸出 `provenance.json`：

```json
{
  "task_id": "thesis-photosyn-2026-05-09",
  "queries": ["光合作用 教學設計"],
  "sources": [
    {"url": "https://...", "title": "...", "fetched_at": "2026-05-09T10:23+08:00", "sha256": "abc..."}
  ],
  "tool_version": "scrapling 0.4, tinyfish-search 1.0",
  "respect_robots": true
}
```

CLI 自動產出此檔（同名 `.provenance.json`）方便引用與審稿時佐證。

---

## 6.5 教學情境範例：時事閱讀題自動更新

```bash
# 每週一早上自動跑（搭配 ai-agent-orchestrator 排程）
python scripts/scrape.py search "本週國際新聞 教學" --top 5 --fetch \
  --filter "language:zh-tw" \
  --out /tmp/news.md

# 用 Claude 改寫成 5 題閱讀測驗
# （這部份接 claude-api SKILL 的 prompt）
```

---

## 6.6 學生報告幫手（教學示範用）

教學情境下，**示範流程**比結果重要。可以這樣展示：

1. 先讓學生搜尋自己想抓的網站。
2. 用 `python scripts/scrape.py fetch <url>` 抓單頁，看 markdown 怎麼長。
3. 再用 `python scripts/scrape.py agent <url> --goal "..."` 體驗 LLM 抽取。
4. 最後討論：哪些情況該用哪個？哪些網站不能爬？合規邊界在哪？

這個食譜搭配 `references/legal-and-ethics.md` 可以直接當資訊倫理課教材。
