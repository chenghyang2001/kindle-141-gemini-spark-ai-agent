#!/usr/bin/env bash
# ----------------------------------------------------------------------------
# Google Apps Script 環境檢查腳本 (Bash)
# ----------------------------------------------------------------------------

echo -e "\033[0;36m========================================\033[0m"
echo -e "\033[0;36m 檢查 Google Apps Script 開發與部署環境 \033[0m"
echo -e "\033[0;36m========================================\033[0m"

# 1. Node.js 檢查
if command -v node >/dev/null 2>&1; then
    echo -e "[1/3] Node.js 狀態: \033[0;32m已安裝 ($(node -v))\033[0m"
else
    echo -e "[1/3] Node.js 狀態: \033[0;31m未安裝\033[0m"
    echo "請先安裝 Node.js (v18+)。"
    exit 1
fi

# 2. clasp 檢查
if command -v clasp >/dev/null 2>&1; then
    echo -e "[2/3] @google/clasp 狀態: \033[0;32m已安裝 (v$(clasp -v))\033[0m"
else
    echo -e "[2/3] @google/clasp 狀態: \033[0;33m未安裝，正在安裝...\033[0m"
    npm install -g @google/clasp
fi

# 3. Credentials 檢查
CLASPRC="$HOME/.clasprc.json"
if [ -f "$CLASPRC" ]; then
    echo -e "[3/3] Google 帳號授權狀態: \033[0;32m已登入 ($CLASPRC)\033[0m"
else
    echo -e "[3/3] Google 帳號授權狀態: \033[0;33m未登入\033[0m"
    echo "請執行 'clasp login' 完成登入。"
fi

echo -e "\033[0;32m環境檢查完成！\033[0m"
