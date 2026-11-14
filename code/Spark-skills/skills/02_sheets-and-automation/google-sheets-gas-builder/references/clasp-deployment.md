# clasp 部署與專案管理指引

`clasp` (Command Line Apps Script Projects) 是 Google 官方提供的 CLI 工具，用於在本地開發環境管理與部署 Apps Script 專案。

---

## 一、核心指令說明

| 指令 | 說明 | 範例 |
| :--- | :--- | :--- |
| `clasp login` | 開啟瀏覽器進行 Google OAuth 2.0 登入 | `clasp login` |
| `clasp create` | 建立全新的 Apps Script 專案 | `clasp create --title "我的專案" --parentId "SPREADSHEET_ID"` |
| `clasp clone` | 下載現有的 Apps Script 專案程式碼 | `clasp clone "SCRIPT_ID"` |
| `clasp push` | 將本地的 `.gs` 及 `.html` 檔案上傳推送到 Apps Script 雲端專案 | `clasp push` |
| `clasp pull` | 將遠端 Apps Script 雲端專案最新的代碼拉取回本地 | `clasp pull` |
| `clasp version` | 建立專案版本號 (Immutable Version) | `clasp version "v1.0.0 第一次發布"` |
| `clasp deploy` | 部署專案為 Web App 或 API 服務 | `clasp deploy --versionNumber 1 --description "Web App 發布"` |

---

## 二、專案類型區分：綁定專案 vs 獨立專案

在 Google Apps Script 中，務必明確區分兩種類型：

1. **容器綁定專案 (Container-bound Script)**：
   - 專案依附於某個特定的 Google 試算表、文件或表單。
   - 在試算表中點擊「擴充功能 → Apps Script」打開的即為此類專案。
   - 使用 `clasp create --parentId "SPREADSHEET_ID"` 可建立此類綁定專案。
   - **常規試算表自動化（如自訂選單、側邊欄、表格觸發器）只需上傳至綁定專案即可，不需要進行 Web App 部署！**

2. **獨立專案 (Standalone Script)**：
   - 獨立存放在 Google Drive 中的專案，未綁定特定文件。
   - 多用於對外提供 Web App (doGet/doPost) 或微服務。

---

## 三、自動備份與回復 SOP (Backup & Restore)

在針對任何現有 Apps Script 專案進行修改或推送（`clasp push`）前，必須執行備份以保障舊有資料與程式碼安全。

### 1. 備份流程 (Backup)
1. 建立獨立備份目錄（如 `backup/yyyyMMdd_HHmmss/`）。
2. 在該目錄中初始化或執行 `clasp pull`。
3. 確保遠端的 `Code.gs` 與 `appsscript.json` 完整儲存在備份目錄中。

### 2. 回復流程 (Restore)
1. 若新推的代碼發生異常，切換至 `backup/` 最新備份目錄。
2. 執行 `clasp push` 將備份目錄的代碼強制覆蓋回遠端專案。

---

## 四、常見錯誤與排解 (Troubleshooting)

### 錯誤 1: `User has not enabled the Apps Script API`
* **原因**：使用者尚未在 Google Apps Script 設定頁中啟用 API 存取權。
* **解決方案**：
  1. 請使用者造訪 [https://script.google.com/home/usersettings](https://script.google.com/home/usersettings)
  2. 將 **「Google Apps Script API」** 切換為 **「開啟 (ON)」**。

### 錯誤 2: `OAuth2 credentials not found / Invalid credentials`
* **原因**：登入憑證失效或 `.clasprc.json` 損壞。
* **解決方案**：
  在命令列執行 `clasp login --force` 重新開啟授權頁面進行登入。

### 錯誤 3: `File push conflict / Files on remote have changed`
* **原因**：遠端 Apps Script 編輯器有人手動修改過程式碼。
* **解決方案**：
  先執行 `clasp pull` 下載最新程式碼並進行比對，確認無誤後再執行 `clasp push`。
