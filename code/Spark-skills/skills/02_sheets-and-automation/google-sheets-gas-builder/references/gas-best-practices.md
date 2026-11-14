# Google Apps Script 最佳實踐與開發規範

本文件定義生成 Google Apps Script (GAS) 程式碼時必須遵循的架構、效能與安全性規範。

---

## 一、代碼風格與註解規範

1. **語系規範**：
   - 程式碼註解、Log 訊息與使用者提示畫面，統一採用**繁體中文台灣用語**。
   - 避免中國大陸用語（如「數組」改稱「陣列」、「腳本」改稱「程式/腳本」、「接口」改稱「API/介面」）。

2. **模組化設計**：
   - 避免將所有邏輯塞在單一巨型 Function 中。
   - 業務邏輯、資料存取與 UI 互動應適度拆分。

---

## 二、效能優化原則（批次處理）

Google Apps Script 對於試算表的 API 呼叫（如 `getValue()`, `setValue()`）極度耗時。每次 API 呼叫均需花費約 50ms~100ms 的網路 RTT。

### ❌ 錯誤寫法：迴圈逐格讀寫
```javascript
// 嚴重過慢！1000 行將花費超過 50 秒
function processRowsBadly() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  const lastRow = sheet.getLastRow();
  for (let i = 1; i <= lastRow; i++) {
    const val = sheet.getRange(i, 1).getValue();
    if (val === '已完成') {
      sheet.getRange(i, 2).setValue(new Date());
    }
  }
}
```

### ✅ 正確寫法：批次讀取與批次寫入
```javascript
/**
 * 批次處理試算表資料範例
 */
function processRowsEfficiently() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  const lastRow = sheet.getLastRow();
  if (lastRow < 1) return;

  // 1. 一次性批次讀取整區塊 (二維陣列)
  const range = sheet.getRange(1, 1, lastRow, 2);
  const values = range.getValues();

  // 2. 於記憶體中快速處理
  for (let i = 0; i < values.length; i++) {
    if (values[i][0] === '已完成') {
      values[i][1] = new Date(); // 修改二維陣列內容
    }
  }

  // 3. 一次性批次寫回
  range.setValues(values);
}
```

---

## 三、資安與保密規範 (PropertiesService)

1. **嚴禁硬編碼 (No Hardcoding)**：
   - 程式碼中**絕對不可以**硬編碼 API Key、密碼、Token 或個人 Email。
2. **採用 PropertiesService 儲存敏感情資**：

```javascript
/**
 * 設定 API 金鑰 (僅管理者執行一次)
 */
function setSecretApiKey() {
  const scriptProperties = PropertiesService.getScriptProperties();
  scriptProperties.setProperty('API_KEY', 'your_actual_api_key_here');
}

/**
 * 取得 API 金鑰範例
 */
function getSecretApiKey() {
  const scriptProperties = PropertiesService.getScriptProperties();
  const apiKey = scriptProperties.getProperty('API_KEY');
  if (!apiKey) {
    throw new Error('未設定 API_KEY，請先於 PropertiesService 中設定！');
  }
  return apiKey;
}
```

---

## 四、併發與衝突控制 (LockService)

當多位使用者同時操作，或表單 (Google Form) 在短時間內連續提交時，可能導致資料覆蓋或重複寫入。

### 範例：使用 LockService 保護關鍵區段
```javascript
/**
 * 安全地寫入資料庫/試算表，防止多重觸發衝突
 */
function safeAppendRow(dataRow) {
  const lock = LockService.getScriptLock();
  
  // 嘗試取得鎖定，最多等待 10 秒
  const success = lock.tryLock(10000);
  if (!success) {
    Logger.log('系統忙碌中，無法取得寫入鎖定！');
    throw new Error('目前操作人數較多，請稍後再試。');
  }

  try {
    const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('資料紀錄');
    sheet.appendRow(dataRow);
    SpreadsheetApp.flush(); // 強制立即寫入
  } catch (error) {
    Logger.log('寫入失敗: ' + error.toString());
    throw error;
  } finally {
    lock.releaseLock(); // 務必釋放鎖定
  }
}
```

---

## 五、時區、日期與字元處理

1. **時區處置**：
   - 避免使用 `new Date().toLocaleString()` 直接格式化，可能受伺服器地端設定影響。
   - 統一使用 `Utilities.formatDate(date, timeZone, format)`。

```javascript
/**
 * 取得格式化之台灣時間字串
 * @param {Date} date - 日期物件
 * @return {string} 格式化時間 (YYYY-MM-DD HH:mm:ss)
 */
function getFormattedTaiwanTime(date = new Date()) {
  const timeZone = Session.getScriptTimeZone(); // 讀取專案設定之時區
  return Utilities.formatDate(date, timeZone, 'yyyy-MM-dd HH:mm:ss');
}
```

---

## 六、例外處理與日誌紀錄

1. 核心邏輯必須包裹於 `try...catch`。
2. Log 記錄應清晰包含錯誤訊息與 stack trace。

```javascript
function executeSafeTask() {
  try {
    // 執行核心作業
    Logger.log('開始執行任務...');
    // ...
  } catch (error) {
    Logger.log('執行過程中發生錯誤: ' + error.message);
    Logger.log('Stack Trace: ' + error.stack);
    // 亦可視情況寄送警示郵件給管理者
  }
}
```
