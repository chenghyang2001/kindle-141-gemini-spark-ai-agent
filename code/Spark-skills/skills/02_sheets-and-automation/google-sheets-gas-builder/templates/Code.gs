/**
 * ============================================================================
 * Google Apps Script 模組化主程式範本
 * 說明：提供試算表自動化、自訂選單、批次讀寫與錯誤處置標準結構。
 * 語言：繁體中文 (台灣用語)
 * ============================================================================
 */

/**
 * 當試算表開啟時自動觸發，建立自訂工具選單
 */
function onOpen() {
  try {
    const ui = SpreadsheetApp.getUi();
    ui.createMenu('⚡ 自動化工具箱')
      .addItem('開啟工具側邊欄', 'openMainSidebar')
      .addSeparator()
      .addItem('執行批次資料整理', 'runBatchDataProcessing')
      .addToUi();
  } catch (error) {
    Logger.log('建立選單失敗: ' + error.toString());
  }
}

/**
 * 打開自訂側邊欄
 */
function openMainSidebar() {
  try {
    const htmlOutput = HtmlService.createHtmlOutputFromFile('Sidebar')
      .setTitle('自動化工具箱控制台')
      .setWidth(320);
    SpreadsheetApp.getUi().showSidebar(htmlOutput);
  } catch (error) {
    SpreadsheetApp.getUi().alert('無法開啟側邊欄：' + error.message);
  }
}

/**
 * 高效能批次資料處理範本
 */
function runBatchDataProcessing() {
  const lock = LockService.getScriptLock();
  if (!lock.tryLock(10000)) {
    SpreadsheetApp.getUi().alert('系統忙碌中，請稍後再試。');
    return;
  }

  try {
    const sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
    const lastRow = sheet.getLastRow();
    const lastCol = sheet.getLastColumn();

    if (lastRow <= 1) {
      SpreadsheetApp.getUi().alert('工作表中無足夠的資料列！');
      return;
    }

    // 1. 批次讀取 (二維陣列)
    const range = sheet.getRange(1, 1, lastRow, lastCol);
    const data = range.getValues();

    // 2. 記憶體中高速處理
    let processedCount = 0;
    for (let i = 1; i < data.length; i++) {
      // 範例邏輯：若第一欄不為空，則於最後一欄加上更新時間
      if (data[i][0]) {
        data[i][lastCol - 1] = getFormattedCurrentTime();
        processedCount++;
      }
    }

    // 3. 批次寫回
    range.setValues(data);

    SpreadsheetApp.getActiveSpreadsheet().toast(`處理完成！共更新 ${processedCount} 筆資料。`, '成功', 5);
  } catch (error) {
    Logger.log('批次處理失敗: ' + error.stack);
    SpreadsheetApp.getUi().alert('執行失敗：' + error.message);
  } finally {
    lock.releaseLock();
  }
}

/**
 * 格式化目前台灣時間 helper 函式
 * @return {string} 格式化日期時間
 */
function getFormattedCurrentTime() {
  const timeZone = Session.getScriptTimeZone() || 'Asia/Taipei';
  return Utilities.formatDate(new Date(), timeZone, 'yyyy-MM-dd HH:mm:ss');
}
