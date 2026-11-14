# 實際應用情境 Prompt 與代碼範例

本文件提供 3 個實際的自然語言需求範例、對應的解析邏輯、產出程式碼與 `appsscript.json` 設定。

---

## 範例 1：Google 表單歸檔與自動 Email 通知

### 💬 自然語言需求 Prompt
> 「當有人填寫 Google 表單後，幫我把資料自動整理到『部門表』。如果是『資訊部』就歸檔到『資訊部』工作表，並在 Drive 中建立以申請人姓名命名的資料夾；同時寄出一封 Gmail 確認信給申請人。」

### 📋 需求解析與規劃
* **服務與 Scopes**：
  * Sheets: `https://www.googleapis.com/auth/spreadsheets`
  * Drive: `https://www.googleapis.com/auth/drive.file`
  * Gmail: `https://www.googleapis.com/auth/gmail.send`
* **觸發器**：`onFormSubmit` 表單提交觸發器。

### 💻 產出程式碼 (`Code.gs`)
```javascript
/**
 * 表單提交觸發器入口函式
 * @param {Object} e - 表單提交事件物件
 */
function onFormSubmitTrigger(e) {
  const lock = LockService.getScriptLock();
  if (!lock.tryLock(10000)) return; // 防止重複寫入

  try {
    const spreadsheet = SpreadsheetApp.getActiveSpreadsheet();
    // 若 e 未傳入（例如直接從 GAS 執行），則抓取當前工作表最後一行
    const responsesSheet = spreadsheet.getSheetByName('表單回應 1') || spreadsheet.getActiveSheet();
    const lastRow = responsesSheet.getLastRow();
    const rowData = responsesSheet.getRange(lastRow, 1, 1, responsesSheet.getLastColumn()).getValues()[0];

    // 假設欄位順序：[0]時間戳記, [1]姓名, [2]Email, [3]部門, [4]主旨
    const applicantName = rowData[1];
    const applicantEmail = rowData[2];
    const department = rowData[3];
    const subject = rowData[4];

    // 1. 自動整理至指定部門工作表
    let targetSheet = spreadsheet.getSheetByName(department);
    if (!targetSheet) {
      targetSheet = spreadsheet.insertSheet(department);
      targetSheet.appendRow(['時間戳記', '姓名', 'Email', '部門', '主旨', '資料夾ID']);
    }

    // 2. 於 Google Drive 建立個人歸檔資料夾
    const parentFolder = DriveApp.getRootFolder(); // 亦可寫入特定資料夾 ID
    const newFolder = parentFolder.createFolder(`${department}_${applicantName}_歸檔`);
    const folderUrl = newFolder.getUrl();

    // 3. 寫入目標部門工作表
    targetSheet.appendRow([new Date(), applicantName, applicantEmail, department, subject, folderUrl]);

    // 4. 寄送 Gmail 確認信
    if (applicantEmail && applicantEmail.includes('@')) {
      const emailSubject = `【系統通知】表單申請已收悉 - ${department}`;
      const emailBody = `${applicantName} 您好：\n\n您的申請（主旨：${subject}）已成功登記至 ${department}。\n歸檔資料夾連結：${folderUrl}\n\n感謝您的使用！`;
      GmailApp.sendEmail(applicantEmail, emailSubject, emailBody);
    }
  } catch (error) {
    Logger.log('表單自動處理失敗: ' + error.toString());
  } finally {
    lock.releaseLock();
  }
}
```

---

## 範例 2：清理重複資料與條件高亮標示

### 💬 自然語言需求 Prompt
> 「幫我檢查『客戶名冊』工作表，根據 Email 欄位自動刪除重複的列，保留最新的一筆。另外，如果『逾期天數』大於 30 天，把該列背景標示為粉紅色。」

### 💻 產出程式碼 (`Code.gs`)
```javascript
/**
 * 清理重複客戶資料並進行條件高亮
 */
function cleanAndHighlightCustomers() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('客戶名冊');
  if (!sheet) throw new Error('找不到「客戶名冊」工作表');

  const lastRow = sheet.getLastRow();
  const lastCol = sheet.getLastColumn();
  if (lastRow <= 1) return; // 無資料

  // 1. 批次讀取整張工作表資料
  const range = sheet.getRange(1, 1, lastRow, lastCol);
  const values = range.getValues();
  const headers = values[0];

  // 尋找欄位索引
  const emailIdx = headers.indexOf('Email');
  const overdueIdx = headers.indexOf('逾期天數');

  if (emailIdx === -1 || overdueIdx === -1) {
    throw new Error('未找到「Email」或「逾期天數」標題欄位');
  }

  // 2. 使用 Map 反向過濾重複資料（保留最後/最新出現者）
  const uniqueMap = new Map();
  for (let i = 1; i < values.length; i++) {
    const email = values[i][emailIdx];
    if (email) {
      uniqueMap.set(email, values[i]); // 後發覆蓋先發
    }
  }

  // 重構乾淨資料陣列 (含 Header)
  const cleanedValues = [headers, ...Array.from(uniqueMap.values())];

  // 3. 清空舊工作表並批次寫回
  sheet.clearContents();
  sheet.getRange(1, 1, cleanedValues.length, lastCol).setValues(cleanedValues);

  // 4. 條件高亮：逾期天數 > 30 標為粉紅色 (#FFC0CB)
  const backgrounds = [];
  for (let i = 0; i < cleanedValues.length; i++) {
    const rowBg = new Array(lastCol).fill('#FFFFFF');
    if (i > 0 && cleanedValues[i][overdueIdx] > 30) {
      rowBg.fill('#FFD1D1'); // 深粉紅/淺紅背景
    }
    backgrounds.push(rowBg);
  }

  sheet.getRange(1, 1, cleanedValues.length, lastCol).setBackgrounds(backgrounds);
  SpreadsheetApp.getActiveSpreadsheet().toast('重複資料清理與條件高亮完成！', '系統通知', 5);
}
```

---

## 範例 3：自訂選單、側邊欄 UI 與外部 API 串接

### 💬 自然語言需求 Prompt
> 「在試算表建立一個『金融工具』自訂選單，點擊後打開側邊欄。側邊欄要有一個按鈕，點擊後會抓取外部美金對台幣匯率 API，並把最新匯率填入試算表 A2 儲存格。」

### 💻 產出程式碼 (`Code.gs`)
```javascript
/**
 * 試算表開啟時自動建立選單
 */
function onOpen() {
  const ui = SpreadsheetApp.getUi();
  ui.createMenu('金融工具')
    .addItem('開啟匯率更新側邊欄', 'showCurrencySidebar')
    .addToUi();
}

/**
 * 展示側邊欄 UI
 */
function showCurrencySidebar() {
  const html = HtmlService.createHtmlOutputFromFile('Sidebar')
    .setTitle('即時匯率工具')
    .setWidth(300);
  SpreadsheetApp.getUi().showSidebar(html);
}

/**
 * 給前端側邊欄呼叫的 API 處理函式
 */
function fetchAndUpdateExchangeRate() {
  try {
    // 呼叫公開匯率 API
    const response = UrlFetchApp.fetch('https://open.er-api.com/v6/latest/USD');
    const json = JSON.parse(response.getContentText());
    const twdRate = json.rates.TWD;

    if (!twdRate) throw new Error('無法取得 TWD 匯率資料');

    // 寫入試算表
    const sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
    sheet.getRange('A1').setValue('USD/TWD 匯率');
    sheet.getRange('A2').setValue(twdRate);
    sheet.getRange('B2').setValue(new Date());

    return { success: true, rate: twdRate };
  } catch (error) {
    return { success: false, error: error.toString() };
  }
}
```

### 💻 產出 UI 樣板 (`Sidebar.html`)
```html
<!DOCTYPE html>
<html>
  <head>
    <base target="_top">
    <style>
      body { font-family: sans-serif; padding: 15px; background: #f9f9f9; }
      .btn { background: #1a73e8; color: white; border: none; padding: 10px 15px; border-radius: 4px; cursor: pointer; width: 100%; }
      .btn:hover { background: #1557b0; }
      #result { margin-top: 15px; font-weight: bold; color: #333; }
    </style>
  </head>
  <body>
    <h3>美金匯率更新器</h3>
    <p>點擊下方按鈕以取得最新匯率並寫入試算表：</p>
    <button class="btn" onclick="updateRate()">立即更新匯率</button>
    <div id="result"></div>

    <script>
      function updateRate() {
        document.getElementById('result').innerText = '更新中...';
        google.script.run
          .withSuccessHandler(function(res) {
            if (res.success) {
              document.getElementById('result').innerText = '成功！最新匯率：' + res.rate;
            } else {
              document.getElementById('result').innerText = '失敗：' + res.error;
            }
          })
          .fetchAndUpdateExchangeRate();
      }
    </script>
  </body>
</html>
```
