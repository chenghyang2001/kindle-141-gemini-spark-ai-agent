---
name: browser-automation
description: 瀏覽器/網頁自動化的「統一入口與路由」。當使用者要「爬資料、抓網頁、找資源／找新聞、逐步操作網站、填表送出、登入後多步流程、要截圖證據的可重播自動化、除錯本地 web/Electron app、反爬蟲隱形、解 CAPTCHA」等任何碰瀏覽器的任務，但一時難以判斷該用哪支既有技能時，先讀本技能的路由表決定唯一入口，再啟用對應技能。觸發詞：瀏覽器自動化、網頁自動化、browser automation、web automation、用瀏覽器做…、我要抓/爬/操作某網站、幫我自動化某個網頁流程、該用哪個爬蟲/自動化技能。若使用者已明確指名某支技能（playwright／web-scraper／webwright／playwright-interactive）則不必經過本入口，直接啟用該支。
---

# Browser Automation — 統一入口與路由

本技能**不自己做事**，只負責把「碰瀏覽器的需求」導到正確的既有技能。四支底層技能保持獨立（各自可更新、依賴隔離），本入口只做語意分流。

> 設計理由：這四支看似都碰瀏覽器，實則是四種工種、兩種底層引擎（Node 系 vs Python 系）。合併成一包會讓觸發描述變模糊、更容易叫錯，且無法再拉上游更新。因此採「獨立技能 + 路由入口」——只記一個入口，叫對機率最高。此模式與全域 CLAUDE.md 的 `references/routing-*.md` 叢集路由一致。

---

## 0. 快速分流表（先讀這張）

| 你的需求 | 用哪支技能 | 一句話理由 |
|---------|-----------|-----------|
| **爬公開網站抓資料**、找資源／找新聞／找教學、反爬蟲隱形、繞 Cloudflare、整站爬取、自然語言/LLM 抽取 | **`web-scraper`** | 專長「公開、免登入」的快速擷取與研究；內建 Scrapling／CloakBrowser／TinyFish 三生態 |
| **逐步操作一個網站**（open→snapshot→click→fill），臨時性的 CLI 瀏覽器操作、抓一兩張截圖 | **`playwright`** | CLI-first、輕量、逐步互動，不需要證據制度時最快 |
| **要「可重播＋當次截圖鐵證＋結構驗證」的多步 UI 流程**、登入後表單流程、把任務參數化成可重用 CLI、要能交付驗收的自動化 | **`webwright`** | 唯一具備 Critical Points 證據鏈、run 快照不可變、金流/送出前暫停、防注入安全邊界 |
| **除錯本地 web / Electron app**、要持久 session 反覆迭代、邊改程式邊做功能＋視覺 QA | **`playwright-interactive`** | js_repl 持久 handle，改完 reload 不重啟整條工具鏈 |
| **登入牆／認證 session／自動解 CAPTCHA／真人接手（remote assist）／多帳號隔離**、爬蟲三段都打不過的硬目標 | **`browser-act`** | LLM-agent 導向 CLI，資料全本地不上傳（僅 solve-captcha 送挑戰圖）；建立瀏覽器/登入/送出需你確認 |

---

## 1. 決策樹（分流條件較細時看這裡）

```
碰瀏覽器的需求
│
├── 目標是「取得網頁上的資料/內容」（不是驗證流程）
│   │
│   ├── 公開、免登入 → web-scraper
│   │     ├─ 靜態頁精確選取 → Scrapling Fetcher
│   │     ├─ 要跑 JS → Scrapling DynamicFetcher
│   │     ├─ 自然語言描述要抓什麼 / LLM 抽取 → TinyFish Agent
│   │     ├─ 只是搜尋/找資源/找新聞 → TinyFish Search
│   │     ├─ 被 Cloudflare/反爬蟲擋 → Scrapling stealthy → 自動交棒 CloakBrowser cloak
│   │     └─ 「我想學 X / 找教學」 → web-scraper 的 learn 子命令
│   │
│   └── 需登入牆 / 認證 session / 爬蟲三段都打不過 → browser-act（硬目標出口）
│
├── 目標是「操作網站完成一件事」（點擊、填表、送出、下單流程）
│   │
│   ├── 只是臨時逐步操作、不需要證據與可重播 → playwright
│   │
│   ├── 需要可重播 + 截圖證據 + 可驗收（尤其表單、金流前流程）
│   │     → webwright（Run 模式=一次性驗證腳本；Craft 模式=參數化 CLI）
│   │
│   └── 登入後多步互動、跨平台真人接手、多帳號各自隔離 → browser-act
│
├── 目標是「除錯我本地正在開發的 web/Electron app」
│     → playwright-interactive（持久 session、功能+視覺 QA）
│
└── 卡在「互動式 CAPTCHA」需自動解
      ├─ 首選 → browser-act 的 solve-captcha（僅送挑戰圖、資料本地；限授權場景）
      └─ 次選 → web-scraper 的 cloak --solve-captcha（接 NopeCHA/2captcha 需自備金鑰）
        ⚠️ webwright 明確不繞 CAPTCHA（安全設計），故 CAPTCHA 不走 webwright
```

---

## 2. browser-act 硬目標出口（已就位）

web-scraper 的決策樹把「需登入牆／複雜多步互動／爬蟲三段都打不過」導向 **`browser-act`**——這支已於 GitHub（browser-act/skills，MIT）安裝到三套環境，空洞已補。要點：

- **前置**：CLI 需 `uv tool install browser-act-cli --python 3.12`（本機已有 uv + Python 3.12，可直接裝）。SKILL.md 是 discovery stub，裝好後跑 `browser-act get-skills core` 取得完整用法。
- **登入牆／認證 session／多帳號隔離／真人接手** → browser-act 首選。
- **自動解 CAPTCHA** → browser-act 的 solve-captcha 首選（僅送挑戰圖、其餘全本地）；web-scraper 的 cloak --solve-captcha 為次選。
- **安全**：browser-act 建立瀏覽器、登入、送出表單、上傳前都會要求你確認（Confirmation Gate），與金流/資安謹慎原則一致。
- webwright 仍是「要截圖鐵證 + 可重播驗收」的首選；browser-act 偏「突破 + 認證 + 真人協作」，兩者互補不衝突。

---

## 3. 選型口訣（記不住表就記這個）

- 「我要**資料**」→ web-scraper
- 「我要**逐步點一點**、快就好」→ playwright
- 「我要**可交付、有截圖鐵證的自動化流程**」→ webwright
- 「我在**除錯自己的 app**」→ playwright-interactive
- 「網站**擋我不給資料**」→ web-scraper（stealthy→cloak）
- 「要**登入後做多步操作**」→ webwright

---

## 4. 使用方式

1. 依上表/決策樹判定唯一入口技能。
2. **只讀該支技能的 SKILL.md**（最小必要範圍，勿一次載入全部）。
3. 若一個需求同時橫跨兩支（例：先爬資料 web-scraper、再驗證流程 webwright），先說明串接順序再依序啟用。
4. 各底層技能的依賴不同：web-scraper／webwright 走 **Python**；playwright／playwright-interactive 走 **Node.js**。啟用前留意對應 runtime。
