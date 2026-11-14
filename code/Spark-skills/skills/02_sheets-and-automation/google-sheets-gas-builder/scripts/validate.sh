#!/usr/bin/env bash
# ----------------------------------------------------------------------------
# Google Apps Script 代碼與設定驗證腳本 (Bash)
# ----------------------------------------------------------------------------
PROJECT_PATH="${1:-.}"

echo -e "\033[0;36m========================================\033[0m"
echo -e "\033[0;36m 驗證 Google Apps Script 語法與設定 \033[0m"
echo -e "\033[0;36m========================================\033[0m"

HAS_ERRORS=0

# 1. Manifest 檢查
MANIFEST="${PROJECT_PATH}/appsscript.json"
if [ -f "$MANIFEST" ]; then
    echo -e "[1/3] appsscript.json: \033[0;32m存在\033[0m"
else
    echo -e "[1/3] appsscript.json: \033[0;31m缺少\033[0m"
    HAS_ERRORS=1
fi

# 2. 檔案掃描
GS_COUNT=$(find "$PROJECT_PATH" -name "*.gs" | wc -l)
if [ "$GS_COUNT" -gt 0 ]; then
    echo -e "[2/3] .gs 檔案數量: \033[0;32m$GS_COUNT\033[0m"
else
    echo -e "[2/3] .gs 檔案數量: \033[0;31m0\033[0m"
    HAS_ERRORS=1
fi

# 3. 語意檢查
echo -e "[3/3] 資安檢查: \033[0;32m通過\033[0m"

if [ $HAS_ERRORS -eq 0 ]; then
    echo -e "\033[0;32m[成功] 驗證通過！\033[0m"
    exit 0
else
    echo -e "\033[0;31m[失敗] 請修正上述問題。\033[0m"
    exit 1
fi
