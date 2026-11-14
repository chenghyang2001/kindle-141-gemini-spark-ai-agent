# 真 Chrome ＋ CDP 截圖工法

> **為什麼不用無頭瀏覽器**：同一個 profile 免每次重新登入（OAuth 授權流程很長）、
> 截出來就是學員實際看到的畫面。已驗證：GAS 專案 U01～U09 共數百張圖。

## 一、啟動帶遠端偵錯埠的 Chrome

**先完全關掉 Chrome**（工作管理員確認沒有 chrome.exe 殘留），否則埠開不起來。

```powershell
& "C:\Program Files\Google\Chrome\Application\chrome.exe" `
  --remote-debugging-port=9222 `
  --user-data-dir="C:\chrome-cdp-profile"
```

- `--user-data-dir` 指向**專用 profile 目錄**：第一次要手動登入一次，之後就記住了
- 用專用 profile 才不會動到你平常的 Chrome 設定

驗證埠開了：瀏覽器打開 `http://localhost:9222/json/version`，看得到 JSON 就成功。

## 二、playwright 連上這個 Chrome

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://localhost:9222")
    ctx = browser.contexts[0]          # 用既有 context（已登入狀態）
    page = ctx.pages[0] if ctx.pages else ctx.new_page()

    page.goto("https://docs.google.com/spreadsheets/d/xxxx/edit")
    page.wait_for_timeout(2000)

    page.screenshot(path="real/raw_sheet_new.png")

    page.get_by_role("menuitem", name="擴充功能").click()
    page.wait_for_timeout(600)
    page.screenshot(path="real/raw_menu_ext.png")
```

⚠️ **不要 `browser.close()`** — 那會關掉使用者的 Chrome。用完直接結束腳本即可。

## 三、截圖檔名規則

`raw_<語意步驟名>.png`

✅ `raw_menu.png`、`raw_key_prompt.png`、`raw_job1_result.png`
❌ `raw_01.png`、`raw_02.png`（插圖時對不上，之後補截一張就全亂）

## 四、實務建議

| 建議 | 為什麼 |
|---|---|
| 每個步驟截完**立刻存檔**，不要最後一次存 | 中途出錯不用全部重來 |
| 對話框、選單截圖前 `wait_for_timeout(500~800)` | 動畫沒跑完會截到半透明 |
| 需要局部圖時**先截全圖**，裁切交給標註階段 | 原圖留著，之後改版不用重截 |
| 腳本放 `real/_自動化腳本/` | 之後要重截或補截，直接改參數重跑 |
| 截圖前先把**視窗寬度固定** | 不同寬度截出來的圖排版會不一致 |

## 五、⚠️ 截圖前的檢查

- [ ] 畫面上**沒有真實 API 金鑰／token**（有的話截完要遮，或先換測試金鑰）
- [ ] **沒有他人個資**
- [ ] 瀏覽器分頁列沒有洩漏無關資訊
- [ ] 若畫面有日期時間，**標註階段要遮蓋**（教材不能有時效感）
