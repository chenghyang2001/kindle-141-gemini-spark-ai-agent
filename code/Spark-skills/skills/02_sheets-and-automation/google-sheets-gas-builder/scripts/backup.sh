#!/usr/bin/env bash
# ----------------------------------------------------------------------------
# Google Apps Script 自動備份腳本 (Bash)
# ----------------------------------------------------------------------------
SCRIPT_ID="${1:-}"
PROJECT_PATH="${2:-.}"

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_DIR="${PROJECT_PATH}/backup/${TIMESTAMP}"

mkdir -p "$BACKUP_DIR"
echo "備份目標目錄: $BACKUP_DIR"

cd "$BACKUP_DIR" || exit 1

if [ -n "$SCRIPT_ID" ]; then
    echo "正在拉取 Script ID: $SCRIPT_ID..."
    clasp clone "$SCRIPT_ID"
elif [ -f "${PROJECT_PATH}/.clasp.json" ]; then
    cp "${PROJECT_PATH}/.clasp.json" .
    echo "正在拉取遠端最新代碼..."
    clasp pull
else
    echo "[提示] 未發現既有 .clasp.json，跳過備份。"
fi

echo -e "\033[0;32m[成功] 備份完成！\033[0m"
