# ----------------------------------------------------------------------------
# Google Apps Script 自動備份腳本 (PowerShell)
# ----------------------------------------------------------------------------
param (
    [string]$ScriptId = "",
    [string]$ProjectPath = "."
)

$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "========================================" -ForegroundColor Cyan
Write-Host " 執行 Google Apps Script 遠端備份流程" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupDir = Join-Path $ProjectPath "backup\$timestamp"

if (-not (Test-Path $backupDir)) {
    New-Item -ItemType Directory -Force -Path $backupDir | Out-Null
}

Write-Host "備份目標目錄：$backupDir" -ForegroundColor Gray

Push-Location $backupDir

try {
    if ($ScriptId -ne "") {
        Write-Host "正在拉取 Script ID: $ScriptId 之遠端程式碼..." -ForegroundColor Yellow
        clasp clone $ScriptId
    } else {
        # 檢查當前目錄是否有 .clasp.json
        $claspJsonPath = Join-Path $ProjectPath ".clasp.json"
        if (Test-Path $claspJsonPath) {
            Copy-Item $claspJsonPath -Destination $backupDir -Force
            Write-Host "正在拉取遠端最新代碼..." -ForegroundColor Yellow
            clasp pull
        } else {
            Write-Host "[提示] 未發現既有 .clasp.json，視為全新專案建立，跳過拉取舊 code。" -ForegroundColor Yellow
        }
    }
    Write-Host "[成功] 備份流程完成！" -ForegroundColor Green
} catch {
    Write-Host "[警告] 備份過程中發生異常: $_" -ForegroundColor Red
} finally {
    Pop-Location
}
