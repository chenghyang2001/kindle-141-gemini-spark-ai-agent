# ----------------------------------------------------------------------------
# Google Apps Script 自動化部署腳本 (PowerShell)
# ----------------------------------------------------------------------------
param (
    [string]$ProjectPath = ".",
    [string]$SpreadsheetId = "",
    [string]$ProjectTitle = "Google Sheets Automation"
)

$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "========================================" -ForegroundColor Cyan
Write-Host " 開始執行 Google Apps Script 部署流程" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

Push-Location $ProjectPath

try {
    # 1. 執行代碼驗證
    $validateScript = Join-Path $PSScriptRoot "validate.ps1"
    if (Test-Path $validateScript) {
        & $validateScript -ProjectPath "."
        if ($LASTEXITCODE -ne 0) {
            Write-Host "[錯誤] 代碼驗證未通過，終止部署流程！" -ForegroundColor Red
            exit 1
        }
    }

    # 2. 檢查專案是否已綁定 .clasp.json
    if (-not (Test-Path ".clasp.json")) {
        if ($SpreadsheetId -ne "") {
            Write-Host "建立並綁定至 Google 試算表 (ID: $SpreadsheetId)..." -ForegroundColor Yellow
            clasp create --title $ProjectTitle --parentId $SpreadsheetId --type sheets
        } else {
            Write-Host "[錯誤] 找不到 .clasp.json 且未指定 -SpreadsheetId！" -ForegroundColor Red
            Write-Host "請先執行 clasp clone <scriptId> 或傳入 -SpreadsheetId 參數。" -ForegroundColor Yellow
            exit 1
        }
    }

    # 3. 執行推送到遠端專案
    Write-Host "正在將本地程式碼推送到 Apps Script 遠端專案 (clasp push)..." -ForegroundColor Yellow
    clasp push --force

    if ($LASTEXITCODE -eq 0) {
        Write-Host "`n========================================" -ForegroundColor Green
        Write-Host " 部署成功！" -ForegroundColor Green
        Write-Host "========================================" -ForegroundColor Green
        Write-Host "請開啟試算表並於選單點擊執行，依提示完成首次 Google OAuth 授權。" -ForegroundColor White
    } else {
        Write-Host "`n[失敗] clasp push 執行失敗，請檢查權限或 clasp 登入狀態。" -ForegroundColor Red
    }
} catch {
    Write-Host "[例外錯誤] 部署過程發生異常: $_" -ForegroundColor Red
} finally {
    Pop-Location
}
