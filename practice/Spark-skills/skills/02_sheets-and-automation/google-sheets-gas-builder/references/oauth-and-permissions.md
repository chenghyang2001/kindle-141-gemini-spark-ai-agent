# OAuth 權限管理與 appsscript.json 規範

本文件說明 Google Apps Script 專案的 `appsscript.json` 設定檔寫作規範、常用 `oauthScopes` 權限清單，以及使用者授權流程。

---

## 一、appsscript.json 基礎設定

`appsscript.json` 是 Apps Script 的專案清單檔 (Manifest File)，用於定義運行時版本、時區與 OAuth 權限。

### 標準 appsscript.json 範例
```json
{
  "timeZone": "Asia/Taipei",
  "dependencies": {},
  "exceptionLogging": "STACKDRIVER",
  "runtimeVersion": "V8",
  "oauthScopes": [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/script.container.ui"
  ]
}
```

---

## 二、常用 Google 服務與 oauthScopes 對照表

請遵循**最小權限原則**，僅宣告程式碼中實際呼叫的服務權限。

| Google 服務 | 呼叫類別 (Classes) | 建議的 OAuth Scope 網址 |
| :--- | :--- | :--- |
| **Google 試算表 (當前)** | `SpreadsheetApp.getActiveSpreadsheet()` | `https://www.googleapis.com/auth/spreadsheets.currentonly` |
| **Google 試算表 (全部)** | `SpreadsheetApp` | `https://www.googleapis.com/auth/spreadsheets` |
| **Gmail 寄信** | `GmailApp.sendEmail()`, `MailApp` | `https://www.googleapis.com/auth/gmail.send` |
| **Google Drive 檔案歸檔** | `DriveApp.createFolder()`, `File` | `https://www.googleapis.com/auth/drive.file` (僅存取由本程式建立的檔案) |
| **Google Drive (完全)** | `DriveApp` | `https://www.googleapis.com/auth/drive` |
| **Google 日曆** | `CalendarApp` | `https://www.googleapis.com/auth/calendar` |
| **外部 API 呼叫** | `UrlFetchApp.fetch()` | `https://www.googleapis.com/auth/script.external_request` |
| **自訂選單與對話框** | `SpreadsheetApp.getUi()` | `https://www.googleapis.com/auth/script.container.ui` |
| **觸發器管理** | `ScriptApp.newTrigger()` | `https://www.googleapis.com/auth/script.scriptapp` |

---

## 三、使用者授權與初次執行引導 SOP

當 Apps Script 首次執行或新增了 Scope 時，Google 會要求使用者完成 OAuth 授權。請在交付時提供以下提示文字：

### 👨‍💻 使用者授權操作步驟
1. 開啟目標 Google 試算表，點擊上方選單列出現的自訂選單（或至「擴充功能 → Apps Script」執行任一函式）。
2. 畫面會彈出 **「需要授權」** 的對話視窗，請點擊 **「繼續」**。
3. 選擇您的 Google 帳號。
4. 若出現 **「Google 尚未核實這個應用程式」** 的警告畫面：
   - 點擊左下方的 **「進階 (Advanced)」** 連結。
   - 點擊 **「前往『[專案名稱]』（不安全） (Go to [Project Name] (unsafe))」**。
5. 檢視程式碼要求的存取權限，確認無誤後點擊 **「允許 (Allow)」**。
6. 授權完成！程式將可正常自動化運作。
