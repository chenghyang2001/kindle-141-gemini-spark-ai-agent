# 自然語言生成與部署 Google Apps Script (GAS) 技能包

本技能包為 Antigravity、Codex 與 Claude Code 提供完整的 Google 試算表 Apps Script 自動化、程式碼生成與 `clasp` 部署流程。

---

## 一、開源專案評估與選擇報告

在建構本技能包前，我們對 GitHub 上與 Google Apps Script AI 生成及自動部署相關的熱門開源專案進行了調研與評估：

### 評估之候選專案比較

1. **[google/clasp](https://github.com/google/clasp)** (Stars: ~5.8k | Forks: ~510 | 授權: Apache-2.0 | 最新版本: 2026年3月 v3.3.0)
   * **核心功能**：Google 官方 Command Line Apps Script Projects CLI 工具。支援 Apps Script 專案創建、綁定 Google 試算表/表單/文件、代碼推拉 (`push`/`pull`)、部署管理及 OAuth 登入驗證。
   * **可沿出優勢**：官方標準，100% API 相容性，安全性最高，具備豐富的 CI/CD 整合經驗。
   * **補強重點**：缺少 AI 自然語言生成介面，需透過外部工具腳本封裝。

2. **[labnol/apps-script-starter](https://github.com/labnol/apps-script-starter)** (Stars: ~1.3k | Forks: ~195 | 授權: MIT | 最新維護: 2025/2026年)
   * **核心功能**：由 Digital Inspiration 維護的現代化 Apps Script 專案構建架構，支援 TypeScript, ES Modules, Webpack, ESLint 及 HTML 介面設計。
   * **可沿出優勢**：提供業界最佳的 GAS 程式碼結構與模組化規範，適用於複雜的選單與側邊欄開發。
   * **補強重點**：主要聚焦於開發環境，缺少自動化部署 CLI 流程。

3. **[tanaikech/ToolsForMCPServer](https://github.com/tanaikech/ToolsForMCPServer)** (Stars: ~106 | Forks: ~21 | 授權: MIT | 最新維護: 2026年)
   * **核心功能**：Google Developer Expert (Tanaike) 打造的 Gemini/MCP 與 GAS 整合工具包，解決 LLM 如何呼叫 Apps Script API 並進行自動執行的問題。
   * **可沿出優勢**：提供精確的 Google 服務與 API Scope 對照邏輯，引導 LLM 正確配置 `appsscript.json`。
   * **補強重點**：屬於開發者導向工具，需轉換為標準 Skill 工作流。

### 選擇結論
本技能包**採用 `google/clasp` 作為底層部署引擎**，結合 **`labnol/apps-script-starter` 的結構規範**與 **`tanaikech` 的 Scope 判定邏輯**，建構出兼具安全性、規範性與自動化能力的最佳實踐技能包。

---

## 二、Windows 環境安裝與準備指南

為了讓技能包的「模式 B（生成並部署）」能夠正常運作，請在 Windows 電腦上依序進行以下環境設定：

### 1. 安裝 Node.js 與 clasp
開啟 PowerShell（建議使用 PowerShell 7 或 Windows PowerShell 5.1）並執行：

```powershell
# 1. 檢查是否已安裝 Node.js (需 v18 以上)
node -v

# 2. 全域安裝 Google 官方 clasp 工具
npm install -g @google/clasp

# 3. 驗證 clasp 安裝
clasp -v
```

### 2. 啟用 Google Apps Script API 權限
1. 打開瀏覽器造訪：[Google Apps Script 使用者設定](https://script.google.com/home/usersettings)
2. 將 **「Google Apps Script API」** 開關切換為 **開啟 (ON)**。（此為 clasp 存取專案必需設定）

### 3. 完成 Google 帳號授權登入
在 PowerShell 執行登入指令：

```powershell
clasp login
```
系統會自動開啟瀏覽器頁面，請選擇您欲操作 Google 試算表的帳號並點擊「允許」。完成後憑證會自動儲存於 `%USERPROFILE%\.clasprc.json`。

---

## 三、技能包檔案結構說明

```
google-sheets-gas-builder/
├── SKILL.md                          # 技能主定義檔 (模式與 SOP)
├── README.md                         # 本說明文件
├── references/
│   ├── gas-best-practices.md         # 效能優化 (批次讀寫/LockService/PropertiesService)
│   ├── clasp-deployment.md           # clasp 推拉、綁定與備份回復流程
│   ├── oauth-and-permissions.md      # OAuth Scopes 與權限設定指南
│   └── prompt-examples.md            # 3 個實際情境語意與程式範例
├── templates/
│   ├── Code.gs                       # 模組化主程式範本
│   ├── appsscript.json               # 標準設定檔
│   ├── Sidebar.html                  # 側邊欄 UI 範本
│   └── Config.gs                     # 變數配置與 Properties 模組
└── scripts/
    ├── setup.ps1 / setup.sh          # 環境檢查腳本
    ├── deploy.ps1 / deploy.sh        # clasp 推送與部署自動化腳本
    ├── backup.ps1 / backup.sh        # 部署前自動拉取備份腳本
    └── validate.ps1 / validate.sh    # 代碼與 JSON 語法檢查腳本
```

---

## 四、指令腳本使用說明

所有腳本均支援 UTF-8 編碼與 Windows PowerShell / Bash 環境：

### 1. 環境檢測 (`setup.ps1`)
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup.ps1
```

### 2. 遠端備份 (`backup.ps1`)
在部署前自動將既有 Google 試算表綁定之專案備份至 `backup/` 目錄：
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\backup.ps1 -ScriptId "YOUR_SCRIPT_ID"
```

### 3. 程式碼驗證 (`validate.ps1`)
檢查 `.gs` 語法、函數完整度與 `appsscript.json` 中的 Scopes：
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\validate.ps1 -ProjectPath "path/to/project"
```

### 4. 自動化部署 (`deploy.ps1`)
將本地生成之 `.gs` 與 `appsscript.json` 推送至試算表專案：
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\deploy.ps1 -ProjectPath "path/to/project"
```

---

## 五、安全性與開發規範聲明

1. **繁體中文台灣用語**：所有產出的 GAS 程式碼均包含詳細的繁體中文註解。
2. **無憑證洩露**：嚴禁在程式碼中寫死 API Key、密碼或 Token；統一引導使用 `PropertiesService`。
3. **資料備份保障**：模式 B 在修改任何專案前，必須執行 `backup.ps1` 下載舊有代碼備份。
4. **專案權限獨立**：僅綁定試算表獨立專案，不會發布全域 Web App，除非使用者明確要求。
