---
name: web-scraper
description: 整合 Scrapling（本地）、CloakBrowser（隱形 Chromium）與 TinyFish（雲端 AI）的統一爬蟲技能，專長「公開、免登入」網站的快速擷取與研究。觸發詞：「爬蟲」「爬取資料」「查找資料」「找資源」「找科技新聞」「找教育新聞」「找教學內容」「找教學影片」「我想學 X」「給我 X 的學習資料」「反爬蟲」「隱形瀏覽器」「指紋」「CloakBrowser」「stealth」「scrape」「crawl」「learn」「tutorial」「news」。內建：整站爬取、自然語言抽取、反爬蟲與瀏覽器指紋隱形（FingerprintJS/BrowserScan、Cloudflare 自動挑戰）、互動式 CAPTCHA 解碼（選用 --solve-captcha 接 NopeCHA/2captcha，限授權場景）、多身份 profile 隔離、新聞速報（18 來源）、主題學習包（YT 字幕+文章+GitHub+arXiv）。輸出 JSON/CSV/Markdown/PDF/截圖。不適用：已有官方 API、純 UI 測試；需登入牆／複雜多步互動／自動解 CAPTCHA → 改用 browser-act（要截圖鐵證的可重播表單流程 → webwright）。詳見 SKILL.md 決策樹。
---

# Web Scraper — 統一爬蟲技能

整合兩大爬蟲生態：

| 來源 | 定位 | 強項 |
|------|------|------|
| [Scrapling](https://github.com/D4Vinci/Scrapling) | **本地 Python 框架** | 反偵測、繞 Cloudflare、整站爬取、選擇器自動修復、效能 |
| [TinyFish Cookbook](https://github.com/tinyfish-io/tinyfish-cookbook) | **雲端 AI 爬蟲 API** | 自然語言目標、LLM 結構化抽取、搜尋、零安裝 |
| [CloakBrowser](https://github.com/CloakHQ/CloakBrowser) | **隱形 Chromium（drop-in Playwright）** | 原始碼級指紋修補（Canvas/WebGL/字體/GPU/WebRTC/WebDriver）、多身份隔離、住宅 proxy + geoip |

> 三者互補：Scrapling 是預設主力（Firefox/camoufox 系反爬）；被 Chromium 指紋偵測擋住時換 **CloakBrowser**（Chromium 系）；要自然語言/LLM 抽取走 TinyFish。

---

## 0. 快速判斷：用哪一個？

```
使用者需求
│
├── 想用「自然語言」描述要抓什麼（例：找越南河內機車租金的最低價）
│     → TinyFish Agent（雲端，需 TINYFISH_API_KEY）
│
├── 只是想搜尋／找資源／找文章
│     → TinyFish Search（雲端、免費、< 0.5s）
│       備援：Tavily（若已有 TAVILY_API_KEY）或 DuckDuckGo
│
├── 給定具體網址，要抓乾淨內容（自動去廣告/側欄）
│     → TinyFish Fetch（雲端、免費，回傳 markdown）
│       備援：Scrapling Fetcher（本地）
│
├── 普通靜態網頁、需要 CSS/XPath 精確選取
│     → Scrapling Fetcher（本地、最快）
│
├── 網頁需要跑 JavaScript 才看得到內容
│     → Scrapling DynamicFetcher
│
├── 網站有 Cloudflare / Turnstile / 反爬蟲
│     → 直接用 `stealthy`（Scrapling，Firefox 系，solve_cloudflare=True）
│       ★ 被擋會「自動切換」交棒給 CloakBrowser（Chromium 系）重抓，無需手動換命令
│       想手動指定 Chromium 系：直接用 `cloak`
│
├── 卡在互動式 CAPTCHA（Turnstile/reCAPTCHA/hCaptcha 勾選框）
│     → `cloak --solve-captcha`（接 NopeCHA/2captcha，需自備金鑰）★限授權場景，見 legal-and-ethics
│
├── 大規模爬取怕 IP 被封 / 要輪換出口
│     → `stealthy` 或 `cloak` 加 `--proxy-file <池清單>`（被擋自動換下一個）+ `--geoip`
│
├── 三段式都打不過（cloak 回傳碼 4／印 [升級建議]）或需登入牆/多步互動/真人接手
│     → 改用 `browser-act` 技能（硬目標出口：登入牆/認證 session/真人接手/自動解 CAPTCHA）
│       ※ 要「截圖鐵證 + 可重播驗收」的表單流程 → 改用 `webwright`
│
├── 要多身份隔離（各身份固定指紋 + 各自 cookie），或住宅 proxy 要對齊時區/語系
│     → CloakBrowser `cloak --fingerprint --profile`（自架版 Multilogin）／`--proxy --geoip`
│
├── 整站爬取、要排隊、續傳、上千頁
│     → Scrapling Spider（Scrapy 風格）
│
├── 教學／研究：學術論文、政府開放資料、課程素材
│     → 先 Search 找入口 → 再 Fetch / Stealthy 擷取 → 整理成 Markdown / PDF
│
└── 「我想學 X」「給我 X 的教學內容」「找 YT 教學」
      → `learn` 子命令：YT 字幕+教學文章+GitHub+arXiv 一鍵整理為長 Markdown
```

**選型口訣**：
- 「我知道要哪個元素」→ Scrapling
- 「我要 LLM 幫我懂頁面」→ TinyFish Agent
- 「我要又快又免費的搜尋」→ TinyFish Search
- 「網站擋我」→ 先 Scrapling StealthyFetcher，再不行換 CloakBrowser `cloak`
- 「要多帳號/多身份各自固定指紋」→ CloakBrowser `cloak --fingerprint --profile`

---

## 1. 觸發後的執行流程

收到爬蟲需求時：

1. **釐清三件事**（若使用者沒給就問）：
   - **目標**：要抓什麼網站／搜什麼關鍵字？
   - **輸出**：JSON / CSV / Markdown / PDF / 截圖？要存哪？
   - **規模**：1 個 URL / 多個 URL / 整站？
2. **依決策樹路由**到對應工具。
3. **環境檢查**：依 `references/setup.md` 確認 Python、Scrapling、TinyFish API Key、Playwright 瀏覽器是否就緒；缺什麼就先安裝/提示。
4. **使用 `scripts/scrape.py` 統一 CLI**，避免每次手寫程式。複雜任務再用範本（`templates/`）寫客製腳本。
5. **完成後輸出簡短摘要**：抓了幾筆、存到哪、有無被 block。

---

## 2. 統一 CLI（`scripts/scrape.py`）

優先使用此入口，避免重複寫 boilerplate。

```bash
# 搜尋（TinyFish）
python scripts/scrape.py search "AI agent 爬蟲 2026" --top 10 --out results.json

# 抓單頁乾淨內容（自動選最便宜路徑）
python scripts/scrape.py fetch "https://example.com" --format md --out page.md

# 反爬蟲（Scrapling Stealthy，Firefox 系，先試這個）
python scripts/scrape.py stealthy "https://nopecha.com/demo/cloudflare" \
  --css "#content" --out page.html

# 隱形 Chromium（CloakBrowser）— stealthy 被擋或站方專測 Chromium 指紋時換它
python scripts/scrape.py cloak "https://example.com" --css ".article" --text --out text.json
python scripts/scrape.py cloak "https://example.com" --screenshot shot.png
# 多身份隔離 + 住宅 proxy 對齊時區/語系：
python scripts/scrape.py cloak "https://example.com" \
  --fingerprint 12345 --profile ./profiles/id-a --proxy "http://user:pass@host:port" --geoip

# JS 渲染
python scripts/scrape.py dynamic "https://quotes.toscrape.com" \
  --css ".quote .text" --out quotes.json

# 自然語言 AI 爬蟲（TinyFish Agent）
python scripts/scrape.py agent "https://shop.com" \
  --goal "列出所有商品名稱與價格，輸出 JSON 陣列" --out products.json

# 整站爬取（Scrapling Spider）
python scripts/scrape.py crawl "https://quotes.toscrape.com" \
  --selector ".quote" --max-pages 50 --out quotes.jsonl

# 抓完轉 PDF（給研究 / 教學歸檔）
python scripts/scrape.py to-pdf "https://example.com/article" --out article.pdf

# ⭐ 一鍵抓科技+教育新聞（內建 18 個來源，中英文）
python scripts/scrape.py news --topic both --pdf
python scripts/scrape.py news --topic tech --lang zh-tw
python scripts/scrape.py news --topic edu  --lang en

# ⭐ 主題學習包（YT 字幕 + 教學文章 + GitHub + arXiv 一鍵整理）
python scripts/scrape.py learn "Python 裝飾器"
python scripts/scrape.py learn "光合作用" --include yt,article
python scripts/scrape.py learn "Transformer 注意力機制" --videos 5 --arxiv 5
```

所有子命令支援 `--help`。

---

## 3. 詳細參考（按需讀取，避免一次塞爆 context）

| 文件 | 何時讀 |
|------|-------|
| [`references/scrapling-quickref.md`](references/scrapling-quickref.md) | 要寫 Scrapling 程式（Fetcher/Spider/選擇器） |
| [`references/cloakbrowser-quickref.md`](references/cloakbrowser-quickref.md) | 要用隱形 Chromium（`cloak`）、多身份 profile、proxy+geoip |
| [`references/tinyfish-quickref.md`](references/tinyfish-quickref.md) | 要呼叫 TinyFish API / 設定 MCP |
| [`references/setup.md`](references/setup.md) | 第一次使用、安裝套件、設環境變數 |
| [`references/recipes/`](references/recipes/) | 常見任務範本（搜尋、表格、整站、LLM 抽取） |
| [`references/legal-and-ethics.md`](references/legal-and-ethics.md) | 跑大規模爬取或商用前必讀 |
| [`templates/spider.py.j2`](templates/spider.py.j2) | 要客製 Spider 時複製 |
| [`templates/extractor.py.j2`](templates/extractor.py.j2) | 要客製單頁抽取腳本 |

---

## 4. 預設行為與規範

- **預設用 Python 3.10+**；專案已有 venv 就在 venv 安裝，否則建議 `pip install --user`。
- **預設禮貌**：開啟 robots.txt 檢查、加 1~2 秒延遲、設合理 User-Agent；除非使用者明確要求關閉。
- **不存敏感資料**：絕不在程式碼裡硬編 API Key／Cookie／登入密碼；都走環境變數或 `.env`。
- **大量資料先試小批**：第一次跑 `--max-pages 5` 看結果再放大。
- **失敗有 retry**：HTTP 4xx/5xx 自動退避重試 3 次。
- **三段式自動升級鏈**：`stealthy`（Firefox 系）→ 被擋自動交棒 `cloak`（Chromium 系，印 `[自動切換]`）
  → cloak 用盡 proxy 仍失敗時印 `[升級建議]` 並回傳碼 4，**此時 Claude 應改用 `browser-act` 技能**
  （登入牆／多步互動／真人接手／自動解 CAPTCHA）。關掉自動切換用 `--no-fallback`；判斷依據見 `_looks_blocked`。
- **proxy 池自動輪換**：`--proxy-file <清單檔>`（一行一個），被擋或連不上自動換下一個；
  搭配 `--geoip` 讓時區/語系跟著出口 IP。退出碼：0 成功／3 CAPTCHA 金鑰錯／4 用盡仍失敗（→ browser-act）。
- **產出格式優先順序**：使用者明說 > 副檔名推斷 > 預設 JSON Lines（巨量資料友好）。
- **教學／研究情境**：抓完自動生成 `summary.md`（來源清單、抓取時間、欄位定義）。

---

## 5. 法律與道德快速提醒

> 詳見 `references/legal-and-ethics.md`。

- 尊重 `robots.txt` 與網站 ToS。
- 個資、付費內容、未公開 API 不抓。
- 商用爬取前確認授權；學術研究遵循引用規範。
- 反爬蟲繞過僅用於合法授權場景（自家網站測試、公開資料、CTF）。
