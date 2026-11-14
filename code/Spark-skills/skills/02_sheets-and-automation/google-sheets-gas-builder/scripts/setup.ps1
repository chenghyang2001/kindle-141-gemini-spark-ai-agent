# ----------------------------------------------------------------------------
# Google Apps Script 環境檢查與設定腳本 (PowerShell)
# ----------------------------------------------------------------------------
$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "========================================" -ForegroundColor Cyan
Write-Host " 檢查 Google Apps Script 開發與部署環境" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# 1. 檢查 Node.js
Write-Host "`n[1/3] 檢查 Node.js 安裝狀態..." -NoNewline
try {
    $nodeVersion = node -v 2>$null
    if ($nodeVersion) {
        Write-Host " [成功] ($nodeVersion)" -ForegroundColor Green
    } else {
        Write-Host " [失敗]" -ForegroundColor Red
        Write-Host "未偵測到 Node.js，請先前往 https://nodejs.org/ 下載安裝 Node.js (v18+)。" -ForegroundColor Yellow
        exit 1
    }
} catch {
    Write-Host " [錯誤] 找不到 Node.js 執行檔。" -ForegroundColor Red
    exit 1
}

# 2. 檢查 @google/clasp
Write-Host "[2/3] 檢查 @google/clasp 安裝狀態..." -NoNewline
try {
    $claspVersion = clasp -v 2>$null
    if ($claspVersion) {
        Write-Host " [成功] (v$claspVersion)" -ForegroundColor Green
    } else {
        Write-Host " [未安裝]" -ForegroundColor Yellow
        Write-Host "正在為您執行 npm install -g @google/clasp 全域安裝..." -ForegroundColor Cyan
        npm install -g @google/clasp
    }
} catch {
    Write-Host " 正在全域安裝 clasp..." -ForegroundColor Cyan
    npm install -g @google/clasp
}

# 3. 檢查 clasp 登入憑證
Write-Host "[3/3] 檢查 Google 帳號 OAuth 登入狀態..." -NoNewline
$clasprcPath = Join-Path $env:USERPROFILE ".clasprc.json"
if (Test-Path $clasprcPath) {
    Write-Host " [已登入]" -ForegroundColor Green
    Write-Host "憑證檔案存在：$clasprcPath" -ForegroundColor Gray
} else {
    Write-Host " [未登入]" -ForegroundColor Yellow
    Write-Host "`n請於終端機執行下列指令完成 Google 授權登入：" -ForegroundColor Cyan
    Write-Host "  clasp login" -ForegroundColor White
}

Write-Host "`n環境檢查完成！" -ForegroundColor Green
