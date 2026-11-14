#!/usr/bin/env bash
# ----------------------------------------------------------------------------
# Google Apps Script 自動化部署腳本 (Bash)
# ----------------------------------------------------------------------------
PROJECT_PATH="${1:-.}"
SPREADSHEET_ID="${2:-}"

echo -e "\033[0;36m========================================\033[0m"
echo -e "\033[0;36m 開始執行 Google Apps Script 部署流程 \033[0m"
echo -e "\033[0;36m========================================\033[0m"

cd "$PROJECT_PATH" || exit 1

# 1. 代碼與 Manifest 驗證
if [ -f "appsscript.json" ]; then
    echo "驗證 appsscript.json 存在..."
else
    echo -e "\033[0;31m[錯誤] 缺少 appsscript.json，終止部署。\033[0m"
    exit 1
fi

# 2. .clasp.json 綁定檢查
if [ ! -f ".clasp.json" ]; then
    if [ -n "$SPREADSHEET_ID" ]; then
        echo "建立新綁定專案..."
        clasp create --title "GAS Automation" --parentId "$SPREADSHEET_ID" --type sheets
    else
        echo -e "\033[0;31m[錯誤] 缺少 .clasp.json 且未傳入 Spreadsheet ID。\033[0m"
        exit 1
    fi
fi

# 3. 執行 Push
echo "正在推送代碼至遠端專案 (clasp push)..."
clasp push --force

if [ $? -eq 0 ]; then
    echo -e "\033[0;32m[成功] 部署完成！\033[0m"
else
    echo -e "\033[0;31m[失敗] clasp push 失敗。\033[0m"
    exit 1
fi
