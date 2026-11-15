/**
 * ============================================================================
 * 班級圖書借閱表：借出登記（練習用，資料為虛構範例）
 * 依 Spark-skills「google-sheets-gas-builder」技能撰寫，採「模式 A：僅生成程式碼」。
 * 語言：繁體中文（台灣用語）
 *
 * 用法：
 *   lendBook('想飛的鋼琴少年', '黃品瑄')            // 直接指定書名與借閱人
 *   lendFromSentence('借出 想飛的鋼琴少年 給 黃品瑄') // 對應老師說的一句話
 *
 * 需要的權限（appsscript.json 的 oauthScopes）：
 *   只需要 https://www.googleapis.com/auth/spreadsheets.currentonly
 *   （只動這份綁定的試算表；本程式不寄信，所以不需要 Gmail／MailApp 權限）
 *
 * 安全原則：
 *   - 只會在最後面「新增一列」，絕不修改或刪除既有列。
 *   - 不寄信、不連外部網址、不建立觸發器。
 * ============================================================================
 */

// 設定集中在這裡，換班級或改借期只要改這一區
const LEND_CONFIG = {
  SHEET_NAME: '借閱紀錄',
  LOAN_DAYS: 14,
  STATUS_LENDING: '借閱中',
  ID_PREFIX: 'B',
  HEADERS: ['編號', '書名', '借閱人', '借出日', '應還日', '狀態', '備註']
};

/**
 * 把老師說的一句話「借出 某書 給 某人」拆成書名與借閱人，再交給 lendBook。
 * 句型不符時直接回報，不猜測哪個字是書名。
 */
function lendFromSentence(sentence) {
  const match = String(sentence || '').trim().match(/^借出\s*(.+?)\s*給\s*(.+)$/);
  if (!match) {
    const message = '句型不符，請用「借出 書名 給 借閱人」：' + sentence;
    Logger.log(message);
    return { ok: false, message: message };
  }
  return lendBook(match[1], match[2]);
}

/**
 * 新增一筆借閱紀錄：自動補下一個編號、借出日（今天）、應還日（+14 天）、狀態「借閱中」。
 * 回傳 { ok, message, row }，讓呼叫的人能把結果念給老師聽。
 */
function lendBook(bookTitle, borrower) {
  // 先檢查輸入：書名或借閱人空白就不寫入，避免表裡多出一列空資料
  const title = String(bookTitle || '').trim();
  const person = String(borrower || '').trim();
  if (!title) {
    return fail_('書名是空白的，沒有新增任何資料。');
  }
  if (!person) {
    return fail_('借閱人是空白的，沒有新增任何資料。');
  }

  // 兩位老師同時登記時，避免搶到同一個編號
  const lock = LockService.getScriptLock();
  if (!lock.tryLock(10000)) {
    return fail_('系統忙碌中（其他人正在登記），請稍後再試，沒有新增任何資料。');
  }

  try {
    const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(LEND_CONFIG.SHEET_NAME);
    if (!sheet) {
      return fail_('找不到工作表「' + LEND_CONFIG.SHEET_NAME + '」，請確認分頁名稱，沒有新增任何資料。');
    }

    // 一次讀完整張表（批次讀取，不在迴圈裡逐格 getValue）
    const values = sheet.getDataRange().getValues();
    const headers = values[0].map(function (h) { return String(h).trim(); });
    const missing = LEND_CONFIG.HEADERS.filter(function (h) { return headers.indexOf(h) === -1; });
    if (missing.length > 0) {
      return fail_('標題列缺少欄位：' + missing.join('、') + '，沒有新增任何資料。');
    }

    const today = new Date();
    const dueDate = new Date(today.getTime());
    dueDate.setDate(dueDate.getDate() + LEND_CONFIG.LOAN_DAYS); // 用 setDate 加天數，跨月、跨年都會自動進位

    const record = {
      '編號': nextId_(values, headers.indexOf('編號')),
      '書名': title,
      '借閱人': person,
      '借出日': formatMonthDay_(today),
      '應還日': formatMonthDay_(dueDate),
      '狀態': LEND_CONFIG.STATUS_LENDING,
      '備註': ''
    };

    // 依「實際標題順序」組成一列，欄位被調換順序也不會寫錯欄
    const newRow = headers.map(function (h) { return record.hasOwnProperty(h) ? record[h] : ''; });

    // 只寫在最後一列的下一列：既有列完全不會被碰到
    const targetRow = sheet.getLastRow() + 1;
    const targetRange = sheet.getRange(targetRow, 1, 1, newRow.length);

    // 先把這一列設成純文字，否則「11-15」會被試算表自動轉成日期
    targetRange.setNumberFormat('@');
    targetRange.setValues([newRow]);

    const message = '已新增 ' + record['編號'] + '：' + record['書名'] + '／' + record['借閱人'] +
      '，借出 ' + record['借出日'] + '，應還 ' + record['應還日'] + '。（未寄信）';
    Logger.log(message);
    return { ok: true, message: message, row: record };
  } catch (error) {
    // 任何意外都記下完整訊息，並明確告知沒有寫入成功
    return fail_('借出登記失敗：' + error.message);
  } finally {
    lock.releaseLock();
  }
}

/**
 * 找出目前最大的編號再加 1（B05 → B06）。
 * 用最大值而不是列數，是因為中間如果有人刪過列，用列數會產生重複編號。
 */
function nextId_(values, idColumn) {
  let maxNumber = 0;
  for (let i = 1; i < values.length; i++) {
    const match = String(values[i][idColumn]).trim().match(/^B(\d+)$/);
    if (match) {
      maxNumber = Math.max(maxNumber, parseInt(match[1], 10));
    }
  }
  const nextNumber = maxNumber + 1;
  return LEND_CONFIG.ID_PREFIX + (nextNumber < 10 ? '0' + nextNumber : String(nextNumber));
}

/**
 * 日期轉成「月-日」文字（例如 11-15），時區用試算表專案設定，避免差一天。
 */
function formatMonthDay_(date) {
  return Utilities.formatDate(date, Session.getScriptTimeZone(), 'MM-dd');
}

/**
 * 統一的失敗回報：記錄到 Logger，並回傳 ok:false，不讓程式整個中斷。
 */
function fail_(message) {
  Logger.log(message);
  return { ok: false, message: message };
}
