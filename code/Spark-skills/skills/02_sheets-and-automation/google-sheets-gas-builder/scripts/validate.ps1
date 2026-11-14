# ----------------------------------------------------------------------------
# Google Apps Script 代碼與設定驗證腳本 (PowerShell)
# ----------------------------------------------------------------------------
param (
    [string]$ProjectPath = "."
)

$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "========================================" -ForegroundColor Cyan
Write-Host " 驗證 Google Apps Script 語法與設定" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

$hasErrors = $false

# 1. 檢查 appsscript.json
$manifestPath = Join-Path $ProjectPath "appsscript.json"
Write-Host "`n[1/3] 檢查 appsscript.json 清單檔..." -NoNewline

if (Test-Path $manifestPath) {
    try {
        $jsonContent = Get-Content $manifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
        if (-not $jsonContent.timeZone) {
            Write-Host " [警告] 未設定 timeZone，建議補充 'Asia/Taipei'" -ForegroundColor Yellow
        } else {
            Write-Host " [OK]" -ForegroundColor Green
        }
    } catch {
        Write-Host " [錯誤] appsscript.json 不是合法 JSON 格式！" -ForegroundColor Red
        $hasErrors = $true
    }
} else {
    Write-Host " [錯誤] 找不到 appsscript.json 檔案！" -ForegroundColor Red
    $hasErrors = $true
}

# 2. 檢查 .gs 與 .html 檔案
Write-Host "[2/3] 掃描專案檔案..." -NoNewline
$gsFiles = Get-ChildItem -Path $ProjectPath -Filter "*.gs" -Recurse
$htmlFiles = Get-ChildItem -Path $ProjectPath -Filter "*.html" -Recurse

if ($gsFiles.Count -eq 0) {
    Write-Host " [錯誤] 專案中找不到任何 .gs 程式檔！" -ForegroundColor Red
    $hasErrors = $true
} else {
    Write-Host " [OK] (包含 $($gsFiles.Count) 個 .gs 檔, $($htmlFiles.Count) 個 .html 檔)" -ForegroundColor Green
}

# 3. 檢查資安隱患 (硬編碼 Key / Secret)
Write-Host "[3/3] 資安與代碼規範檢查..." -NoNewline
$suspiciousPatterns = @('AIzaSy', 'sk_live_', 'AKIA[0-9A-Z]{16}')
$foundSecurityIssue = $false

foreach ($file in $gsFiles) {
    $content = Get-Content $file.FullName -Raw -Encoding UTF8
    foreach ($pattern in $suspiciousPatterns) {
        if ($content -match $pattern) {
            Write-Host "`n [警告] 於 $($file.Name) 發現疑似硬編碼 API 金鑰/憑證 ($pattern)！" -ForegroundColor Red
            $foundSecurityIssue = $true
            $hasErrors = $true
        }
    }
}

if (-not $foundSecurityIssue) {
    Write-Host " [OK] 未發現已知敏感情資硬編碼。" -ForegroundColor Green
}

Write-Host "`n========================================" -ForegroundColor Cyan
if ($hasErrors) {
    Write-Host " 驗證完成：發現部分問題，請依提示修正。" -ForegroundColor Yellow
    exit 1
} else {
    Write-Host " 驗證完成：所有檢查項目皆已通過！" -ForegroundColor Green
    exit 0
}
