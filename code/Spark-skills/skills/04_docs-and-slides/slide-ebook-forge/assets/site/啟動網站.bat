@echo off
chcp 65001 >nul
cd /d "%~dp0"
title 阿亮老師 AI Coding 課程網站

echo.
echo   ================================================
echo     阿亮老師 · AI Coding 三小時實作課程
echo   ================================================
echo.
echo   正在啟動課程網站...
echo.

where python >nul 2>nul
if errorlevel 1 (
  echo   [找不到 Python]
  echo.
  echo   請先安裝 Python，在終端機執行：
  echo       winget install Python.Python.3.12
  echo   裝完後把視窗關掉重開，再執行這個檔案。
  echo.
  pause
  exit /b
)

start "" http://localhost:8877/index.html

echo   網站已開啟：http://localhost:8877/index.html
echo.
echo   ------------------------------------------------
echo    上課期間請不要關閉這個視窗。
echo    結束後直接關掉，或按 Ctrl+C 停止。
echo   ------------------------------------------------
echo.

python -m http.server 8877
