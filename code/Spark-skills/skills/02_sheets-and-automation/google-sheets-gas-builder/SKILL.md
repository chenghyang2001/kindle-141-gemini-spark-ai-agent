---
name: google-sheets-gas-builder
description: 自然語言生成與部署 Google Apps Script (GAS) 技能包。能解析自然語言需求，自動規劃權限與資料流程，生成模組化且具繁體中文註解的 .gs 與 HTML/json 設定檔，並結合 Google 官方 clasp 工具進行備份、驗證與部署至 Google 試算表。當使用者需要寫 GAS、自動化 Google 試算表、建立擴充功能、設定觸發器、製作自動化、收取檔案自動化、學生繳交作業、表單收檔案、檔名正規化、寄信通知或部署 Apps Script 時自動啟用。
---

# Google Apps Script 自然語言生成與部署技能包

本技能包為 Codex、Claude Code 與 Antigravity 提供標準化的「自然語言生成與部署 Google Apps Script (GAS)」工作流。

## 一、技能觸發條件

當使用者出現以下需求關鍵詞或類似表達時，自動啟用本技能：
* 「幫我寫 Google Apps Script」
* 「幫我自動化 Google 試算表」
* 「幫我把 GAS 放到試算表」
* 「幫我建立試算表擴充功能」
* 「幫我設定 Google Sheets 觸發器」
* 「幫我用自然語言產生 GAS」
* 「幫我串接 Google 表單、Drive 或 Gmail」
* 「幫我部署 Apps Script」
* 「製作自動化」
* 「收取檔案自動化」
* 「學生繳交作業／收作業」
* 「表單收檔案並歸檔」
* 「檔名正規化／自動改名」
* 「寄信通知學生已繳交」

---

## 二、支援的運作模式

本技能包支援兩種模式，請根據使用者需求與授權狀況切換：

### 模式 A：僅生成程式碼（預設模式 / 未授權時）
1. 解析自然語言需求，確認需要呼叫的 Google 服務與權限範圍。
2. 在本地產生完整的 `.gs` 程式碼、`appsscript.json` 清單檔、`Config.gs` 配置模組與 UI (`Sidebar.html`)。
3. 所有程式碼均附帶詳細的繁體中文台灣用語註解。
4. 提供手動複製貼上或安裝的步驟說明，不連接或修改 Google 帳號中的任何遠端專案。

### 模式 B：生成並部署（獲明確授權時）
1. 取得或確認目標 Google 試算表網址或 `Spreadsheet ID`。
2. 確認係「建立新 Apps Script 專案」或「修改既有專案」。
3. **強制備份**：呼叫 `scripts/backup.ps1` (或 `.sh`) 拉取遠端既有程式碼進行備份。
4. 在本地產生與驗證程式碼（呼叫 `scripts/validate.ps1`）。
5. 呼叫 `scripts/deploy.ps1` 使用官方 `clasp push` 將程式碼推送至指定試算表綁定專案。
6. 提供首次執行的 OAuth 權限授權步驟與功能測試指南。

> ⚠️ **權限與安全原則**：
> - 未取得使用者明確授權前，絕不進行 Google 帳號登入、試算表修改、程式覆蓋或郵件寄送。
> - 嚴格區分「試算表綁定專案」與「網頁應用程式 (Web App)」。若僅要在試算表內執行選單或觸發器，**切勿部署為 Web App**。


---

## 二點五、現成情境範本（優先使用，不要重新發明）

遇到下列情境時，**直接取用 `templates/` 底下已經過端對端測試的範本**，
在其上修改，不要從零重寫。這些範本都通過模擬實測，且內含真實授課踩過的坑。

| 使用者需求 | 直接用這個範本 | 已驗證 |
|---|---|---|
| 學生用表單繳作業 → 檔案改名歸檔 → 寫試算表 → 寄信通知 | `templates/homework-intake/HomeworkIntake.gs` | 45 項端對端測試通過 |
| 試算表自訂選單 ＋ 側邊欄 ＋ 批次讀寫 | `templates/Code.gs` ＋ `Sidebar.html` | — |
| 金鑰／設定安全存取 | `templates/Config.gs` | — |

### homework-intake 範本說明

**適用**：學生繳交作業／學生上傳檔案／收件歸檔 ＋ 自動通知，
這一類「表單進、檔案歸、信件出」的需求。

**內容**：

- `HomeworkIntake.gs` — 單檔可運作的完整流程，只需改最上方 `CONFIG`
- `appsscript.json` — 已配好最小必要 scopes
- `上課操作步驟.md` — 可直接投影的分步教學，含常見卡關對照表

**已內建的防護**（生成任何新程式時務必比照辦理）：

1. `LockService` 防止同時繳交互相覆蓋
2. 寄信前先查 `MailApp.getRemainingDailyQuota()`，配額用盡不會炸掉整個流程
3. 學生填的內容一律用 `esc()` 跳脫，防止 HTML 破版
4. `sendEmail` 同時提供 HTML 版與純文字版（第三個參數不可留空）
5. 檔名清掉違規字元、收斂連續底線、座號補零成兩位數
6. 缺欄位有預設值，不會產生 `__` 或頭尾底線
7. `try/catch` 包住主流程，失敗自動寄信通知老師
   （**觸發器的錯誤沒有人看得到，這一條最重要**）
8. `RUN_補跑最後一筆()` 可補救觸發器裝好前漏掉的繳交

**表單題目名稱容錯**：`CONFIG.FIELDS` 支援每個欄位多個候選題目名稱
（姓名／學生姓名、班級／班別、座號／學號…），依序尋找，避免因為老師
把題目寫成不同字就抓不到答案。

---

## 二點六、寄信的正確做法（最常被問的問題）

使用者常問：「用程式寄 Gmail 要不要申請 API 金鑰／憑證／應用程式密碼？」

**在 Apps Script 裡完全不用。** 直接用內建的 `GmailApp` 或 `MailApp` 即可。

| 方式 | 要 Cloud 專案 | 要應用程式密碼 | Apps Script 可用 |
|---|---|---|---|
| **GmailApp / MailApp** | 否 | 否 | **內建，一行搞定** |
| Gmail API + OAuth 用戶端 | **是** | 否 | 可用但完全是繞遠路 |
| SMTP + 應用程式密碼 | 否 | **是** | **做不到**，沒有 SMTP 函式庫 |

- 「應用程式密碼」是給 **Google 外部**的程式用的（Python `smtplib`、n8n、
  Outlook、影印機掃描寄信），且必須先開兩步驟驗證才看得到選項。
- 只要寄信就用 `MailApp`（權限最小，授權畫面較不嚇人）；
  需要建草稿／讀信／加標籤才用 `GmailApp`。
- **`getRemainingDailyQuota()` 只有 `MailApp` 有**，所以
  「`GmailApp` 寄信 ＋ `MailApp` 查配額」混用是正常且必要的寫法。

**寄信配額**：一般 Gmail 每日 100 封、Workspace 1,500 封；
算的是收件人數而非寄送次數，且為滾動 24 小時而非午夜重置。

---

## 三、作業步驟 SOP

### 步驟 1：需求解析與權限評估
分析使用者輸入，判定：
* **資料來源與流程**：如 Form 提交、工作表篩選、Drive 歸檔、Gmail 通知等。
* **需要的 Google 服務**：
  * `SpreadsheetApp` (基礎)
  * `GmailApp` / `MailApp` (寄信)
  * `DriveApp` (檔案與資料夾操作)
  * `CalendarApp` (日曆事件)
  * `UrlFetchApp` (外部 API 呼叫)
* **必要的 Scopes 宣告**：寫入 `appsscript.json` 中的 `oauthScopes` 陣列（參照 `references/oauth-and-permissions.md`）。

### 步驟 2：程式碼生成品質規範
遵循 `references/gas-best-practices.md`：
1. **註解**：全部採用**繁體中文台灣用語**。
2. **模組化**：功能拆分為獨立 Function，入口點明確（如 `onOpen()`, `onFormSubmitTrigger()`）。
3. **效能優化（批次處理）**：
   - 禁止在迴圈內使用 `getValue()` / `setValue()`。
   - 一律使用 `getValues()` 讀取二維陣列，記憶體處理後一次以 `setValues()` 寫回。
4. **安全配置**：
   - 嚴禁硬編碼 API Key、密碼或敏感 Token。
   - 使用 `PropertiesService.getScriptProperties()` 存取環境變數。
5. **併發與重覆控制**：
   - 大批量寫入或表單觸發加入 `LockService.getScriptLock()` 防止衝突。
6. **例外處理**：
   - 所有核心流程均封裝於 `try...catch`，並以 `Logger.log()` 記錄完整錯誤資訊。

### 步驟 3：部署與驗證（模式 B 專用）
1. 執行 `scripts/setup.ps1` 確認本機已安裝 `@google/clasp` 且完成 `clasp login`。
2. 執行 `scripts/backup.ps1` 完成備份。
3. 執行 `scripts/deploy.ps1` 完成推拉與綁定。
4. 指引使用者打開試算表，點擊選單並完成「進階 → 前往專案（不安全）→ 授權」流程。

---

## 四、技能檔案參考指引

執行任務時，請參閱本技能包內的參考文件：
- **`README.md`**：專案說明、開源評估報告與 Windows/PowerShell 操作指南。
- **`references/gas-best-practices.md`**：GAS 開發最佳實踐細節與寫作規範。
- **`references/clasp-deployment.md`**：clasp 指令集、專案綁定與備份回復流程。
- **`references/oauth-and-permissions.md`**：OAuth Scopes 設定與權限授權指南。
- **`references/prompt-examples.md`**：3 個完整的實際自然語言需求與對應產出範例。
- **`templates/`**：包含可直接套用的 `Code.gs`、`appsscript.json`、`Sidebar.html` 與 `Config.gs`。
- **`templates/homework-intake/`**：**表單繳交自動化完整範本**（已通過 45 項端對端測試）。
  包含 `HomeworkIntake.gs`、專用 `appsscript.json` 與可投影的 `上課操作步驟.md`。
  遇到「學生繳交作業／表單收檔案／檔名正規化／寄信通知」需求時**優先取用**。
- **`scripts/`**：提供 PowerShell 與 Bash 的自動化工具腳本。
