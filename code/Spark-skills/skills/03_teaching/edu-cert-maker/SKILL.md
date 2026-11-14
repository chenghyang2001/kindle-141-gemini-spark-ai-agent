---
name: edu-cert-maker
description: 教育場域的認證證書製作技能。為線上課程、研習活動、認證計畫產生「可申請、可下載、可列印」的學生認證證書系統。支援從 CSV/Google Form 名單匯入學生資料、表單驗證、純前端產證、html2canvas 下載 PNG。提供米黃褐色學院風、深藍金色官方風、海洋藍漸層科技風三套設計模板。觸發詞：「認證」「証書」「證書」「認證證書」「認證證書製作」「線上認證」「線上証書」「線上證書」「結業證書」「研習證書」「修畢證明」「線上課程證書」「證書下載頁面」「學員證書系統」「電子證書」「學員結業」「課程修畢」「研習結業」「certificate」「e-certificate」「online certificate」。當用戶提到「為某課程做認證證書」「學員可申請證書」「下載證書頁面」「結業證書系統」「線上發證」時使用此技能。
license: 個人/教育用途
---

# 教育認證證書製作 SKILL

讓「課程結束 → 學生申請 → 自動驗證 → 產生證書 → 下載 PNG」一條龍完成。

## 適用情境

- 線上課程結業證書（如本案：太空科技與海洋永續教育暨 Google AI 認證）
- 研習活動參與證明
- 校內認證計畫（學分學程、社團認證、學習履歷加值）
- 任何「有學生名單 + 通過條件 + 要發證書」的場景

## 核心架構

```
[學生名單 CSV] --build_students.py--> [students.js (前端 JSON)]
                                           ↓
[學生開啟 cert.html] -- 輸入姓名+Email --> [比對名單]
                                           ↓
                                      [產生證書 (HTML)]
                                           ↓
                                  [html2canvas → PNG 下載]
```

**重要：純前端方案。** 不需要伺服器、不需要資料庫、不需要登入系統。把 students.js 連同網站一起部署即可。

## 使用流程（給 Claude 看的）

當使用者需要做「認證證書系統」時，依序執行：

### 1. 蒐集必要資訊

問清楚：

- **證書標題**（中文 + 英文副標）
- **認證單位**（誰發的）
- **頒發日期**
- **講師/簽署人**（可選）
- **學生名單來源**（CSV 路徑、Google Sheets URL，或要手動建立）
- **過濾條件**（例如「同意聲明」「通過考試」等欄位邏輯）
- **要顯示在證書上的學生欄位**（最少：學校 + 姓名；可選：科系/年級/班級）
- **視覺風格**（見 [references/styles.md](references/styles.md)）
- **部署目標**（Netlify / GitHub Pages / 已有的網站）

### 2. 處理學生名單

使用 [scripts/build_students.py](scripts/build_students.py) 作為起點，依 CSV 欄位名稱客製化：

- 修改 `csv.DictReader` 對應的欄位名稱
- 修改過濾邏輯（如「不同意」過濾）
- 修改流水號前綴（例如本案 `2026-AISEA-XXXX`）
- 輸出到目標網站的 `data/students.js`

**永遠要去重複**：同一 email 多筆時保留最後一筆（最新資料）。

### 3. 建立 cert.html

使用 [templates/cert-warm-academic.html](templates/cert-warm-academic.html) 作為基礎模板（米黃褐色學院風）。

需要修改的位置：
- 證書標題 (`cert-title`)
- 證書英文副標 (`cert-title-en`)
- 認證單位文字 (`cert-sig-name`)
- 講師名字
- 頒發日期 (`cert-date`)
- 申請條件文字（`cond-list`）

學生資料欄位若有差異，調整 JS 部分的 `renderCert()` 函式。

### 4. 整合到既有網站

- 把 `cert.html` 放到網站根目錄
- 把 `data/students.js` 放到資料目錄
- 在主頁加入「申請證書」按鈕連到 `cert.html`
- 若是 markdown 驅動的網站，加入一個「申請證書」單元說明條件

### 5. 測試清單

完成後請以使用者身份打開測試：

- [ ] 用名單中真實的 email + 姓名 → 應該成功
- [ ] 故意拼錯姓名 → 應顯示「姓名不一致，名單中為 XX」
- [ ] 用不在名單的 email → 應顯示「查無資料」
- [ ] 不勾選確認 → 應擋下
- [ ] 下載 PNG → 解析度應為 2x、檔名含學生姓名與證書編號
- [ ] 列印預覽 → 只顯示證書本體

## 設計原則

### 為什麼用純前端而非後端？

| 考量 | 純前端 | 有後端 |
|------|--------|--------|
| 部署複雜度 | 拖到 Netlify 即可 | 要設 API、資料庫 |
| 維護成本 | 改 CSV + rebuild | 要管伺服器 |
| 安全性 | 名單會曝光在前端（但只有姓名+email，非敏感資料）| 較安全 |
| 對學生 | 載入快、不用登入 | 要帳密 |

**教育情境通常選純前端**：學生名單不算機密、發證需求簡單、希望易維護。

若需要保護名單（例如包含成績、學號），改用 [Google Apps Script](references/backend-options.md) 方案。

### 為什麼用 html2canvas 而非後端產 PDF？

html2canvas 在瀏覽器端把 DOM 截圖為 PNG，**零伺服器成本**、**對學生瞬時完成**。若一定要 PDF，可加上 jsPDF（見 references）。

### 證書編號格式建議

格式：`{年份}-{活動代號}-{流水號}`

例如：
- `2026-AISEA-0001` （2026 AI Space Education Award）
- `2026-GEMINI-0042`
- `2026-MOE-0157`

**流水號要在生成 students.js 時就固定**（依 email 排序產生），避免每次重新生成順序跑掉。

## 證書視覺風格

提供三套模板，詳見 [references/styles.md](references/styles.md)：

1. **米黃褐色學院風** (`cert-warm-academic.html`) — 預設、最常用，傳統學院感
2. **深藍金色官方風** (`cert-navy-formal.html`) — 政府單位、正式場合
3. **海洋藍漸層科技風** (`cert-ocean-tech.html`) — 科技類活動、現代感

## 反模式（不要這樣做）

❌ **不要把名單寫死在 cert.html 裡** — 用 students.js 分離出來，未來才能單獨更新名單
❌ **不要用客戶端隨機產生證書編號** — 同一學生每次申請編號都不同，無法追溯
❌ **不要省略「條件確認」勾選框** — 法律上是學生自我聲明，要留下確認動作
❌ **不要假設 CSV 欄位順序固定** — 用 `csv.DictReader` 以欄位名稱讀取
❌ **不要省略 email 小寫正規化** — 大小寫差異會讓比對失敗

## 進階：批次寄送證書

若需要主動把證書 email 給每位學生：

1. 用 `scripts/batch_render.py`（待擴充）配合 Playwright 為每個學生產生 PNG
2. 用 `imap-smtp-email` SKILL 寄送

## 參考實作

- 本案：`D:\AI教學與專案實作\專案_Google學生認證\website\cert.html`
- 早期實作：`D:\AI教學與專案實作\專案_AI 認知認證\exam.html`（米黃褐色 CSS 來源）
