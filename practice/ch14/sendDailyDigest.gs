/**
 * 值週紀錄每日摘要（練習用，資料為虛構範例）
 *
 * ===== 貼進 Apps Script 的步驟 =====
 * 1. 開啟 Google 試算表，匯入 daily-log.csv（檔案 → 匯入 → 上傳）。
 *    ⚠️ 匯入前先把 A 欄（日期）格式設為「純文字」，否則 11-16 會被轉成日期。
 *    （程式也有處理被轉成日期的情況，但純文字最保險。）
 * 2. 在試算表選「擴充功能 → Apps Script」，會開啟綁定這份試算表的專案。
 * 3. 刪掉預設的 myFunction，把本檔全部內容貼上，按「儲存」（磁碟圖示）。
 * 4. 上方函式下拉選單選 sendDailyDigest，按「執行」。
 *
 * ===== 第一次執行會遇到的授權提示 =====
 * 1. 跳出「需要授權」視窗 → 按「審查權限」。
 * 2. 選擇你的 Google 帳號。
 * 3. 可能出現「Google 尚未驗證這個應用程式」→ 按「進階」→「前往（專案名稱）（不安全）」。
 *    這是因為這支程式是你自己寫的、沒有送 Google 審核，不是病毒警告。
 * 4. 權限清單會列出兩項，確認後按「允許」：
 *    - 查看、編輯、建立及刪除你的 Google 試算表（讀取值週紀錄用）
 *    - 以你的身分傳送電子郵件（MailApp 寄摘要用）
 * 5. 授權完成後程式才會真正執行；之後再執行就不會再問。
 *
 * ⚠️ 執行後會真的寄一封信到你自己的信箱。只想測試內容的話，
 *    把下方 DRY_RUN 改成 true，就只會把內文印在「執行紀錄」，不寄信。
 */

// 測試模式：true 時只寫 Logger、不寄信，避免測試時一直收到信
const DRY_RUN = false;

// 用標題名稱找欄位，而不是寫死第幾欄：之後有人調整欄位順序，程式也不會讀錯
const REQUIRED_HEADERS = ['日期', '時段', '項目', '負責人', '狀態'];
const STATUS_DONE = '已完成';
const STATUS_TODO = '未完成';

function sendDailyDigest() {
  try {
    const sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
    const values = sheet.getDataRange().getValues();

    // 只有標題列或完全空白：沒有資料可統計，記錄後結束，不寄空白摘要
    if (values.length < 2) {
      Logger.log('值週紀錄表沒有資料列（只有標題或是空表），本次不寄送摘要。');
      return;
    }

    const headers = values[0].map(function (h) { return String(h).trim(); });
    const columnIndex = findColumnIndex_(headers);
    if (columnIndex === null) {
      return; // 缺欄位的細節已在 findColumnIndex_ 記錄
    }

    // 跳過標題列；同時略過整列空白，避免表格底部的空列被算進總數
    const rows = values.slice(1).filter(function (row) {
      return row.join('').trim() !== '';
    });
    if (rows.length === 0) {
      Logger.log('標題列以下都是空白列，本次不寄送摘要。');
      return;
    }

    const stats = summarizeRows_(rows, columnIndex);
    const body = buildMailBody_(stats);
    const subject = '值週紀錄每日摘要：未完成 ' + stats.todo.length + ' 項';

    if (DRY_RUN) {
      Logger.log('【測試模式，未寄信】\n主旨：' + subject + '\n\n' + body);
      return;
    }

    // 寄給「目前執行的使用者」，不寫死信箱，換人使用也不會寄錯
    const recipient = Session.getActiveUser().getEmail();
    if (!recipient) {
      Logger.log('取不到目前使用者的信箱，可能是權限不足，本次未寄信。');
      return;
    }
    MailApp.sendEmail(recipient, subject, body);
    Logger.log('已寄出摘要給 ' + recipient + '（共 ' + stats.total + ' 列）。');
  } catch (err) {
    // 任何意外錯誤都記錄下來，方便在「執行紀錄」查原因，而不是讓使用者只看到紅字
    Logger.log('產生每日摘要時發生錯誤：' + err.message);
  }
}

/**
 * 依標題名稱找出每個必要欄位的位置。
 * 缺少任何一欄就記錄並回傳 null：寧可不寄，也不要用錯的欄位算出錯的數字。
 */
function findColumnIndex_(headers) {
  const index = {};
  const missing = [];
  REQUIRED_HEADERS.forEach(function (name) {
    const position = headers.indexOf(name);
    if (position === -1) {
      missing.push(name);
    } else {
      index[name] = position;
    }
  });
  if (missing.length > 0) {
    Logger.log('缺少必要欄位：' + missing.join('、') + '；目前標題列為：' + headers.join('、'));
    return null;
  }
  return index;
}

/**
 * 統計總列數、已完成、未完成，並依負責人分組。
 * 狀態不是「已完成／未完成」的列另外記為異常，不偷偷歸到任何一邊。
 */
function summarizeRows_(rows, columnIndex) {
  const stats = { total: rows.length, done: 0, todo: [], abnormal: [], byOwner: {} };

  rows.forEach(function (row, i) {
    const status = String(row[columnIndex['狀態']]).trim();
    const owner = String(row[columnIndex['負責人']]).trim() || '（未填負責人）';
    const item = {
      sheetRow: i + 2, // +2：陣列從 0 開始，再加上標題列，才會對到試算表上看到的列號
      date: formatDateCell_(row[columnIndex['日期']]),
      slot: String(row[columnIndex['時段']]).trim(),
      task: String(row[columnIndex['項目']]).trim(),
      owner: owner
    };

    if (!stats.byOwner[owner]) {
      stats.byOwner[owner] = { done: 0, todo: 0 };
    }

    if (status === STATUS_DONE) {
      stats.done += 1;
      stats.byOwner[owner].done += 1;
    } else if (status === STATUS_TODO) {
      stats.todo.push(item);
      stats.byOwner[owner].todo += 1;
    } else {
      item.status = status;
      stats.abnormal.push(item);
      Logger.log('第 ' + item.sheetRow + ' 列狀態為「' + status + '」，不是已完成或未完成，已列為異常。');
    }
  });

  return stats;
}

/**
 * 日期欄若被試算表自動轉成日期物件，就轉回「月-日」文字；
 * 否則直接用原本的文字，避免信裡出現一長串時間格式。
 */
function formatDateCell_(cell) {
  if (cell instanceof Date) {
    return Utilities.formatDate(cell, Session.getScriptTimeZone(), 'MM-dd');
  }
  return String(cell).trim();
}

/**
 * 組成信件內文：先給總數，再列未完成清單，最後是負責人分組，
 * 讓收信的人第一眼就看到最需要處理的事。
 */
function buildMailBody_(stats) {
  const lines = [];
  lines.push('值週紀錄每日摘要');
  lines.push('');
  lines.push('總列數：' + stats.total);
  lines.push('已完成：' + stats.done);
  lines.push('未完成：' + stats.todo.length);
  if (stats.abnormal.length > 0) {
    lines.push('狀態異常：' + stats.abnormal.length + '（請檢查試算表）');
  }

  lines.push('');
  lines.push('【未完成清單】');
  if (stats.todo.length === 0) {
    lines.push('（無，全部完成）');
  } else {
    stats.todo.forEach(function (t) {
      lines.push('- ' + t.date + ' ' + t.slot + '｜' + t.task + '｜' + t.owner);
    });
  }

  lines.push('');
  lines.push('【依負責人統計】');
  Object.keys(stats.byOwner).forEach(function (owner) {
    const s = stats.byOwner[owner];
    lines.push('- ' + owner + '：已完成 ' + s.done + '、未完成 ' + s.todo);
  });

  lines.push('');
  lines.push('產生時間：' + Utilities.formatDate(new Date(), Session.getScriptTimeZone(), 'yyyy-MM-dd HH:mm'));
  return lines.join('\n');
}
