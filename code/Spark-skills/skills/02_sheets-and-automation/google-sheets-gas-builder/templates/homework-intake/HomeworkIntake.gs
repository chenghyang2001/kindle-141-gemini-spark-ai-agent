/**
 * ============================================================================
 * 學生作業繳交自動化系統
 * ----------------------------------------------------------------------------
 * 流程：Google 表單繳交 → 檔案改名歸檔到雲端硬碟 → 寫入試算表 → 寄信通知學生
 *
 * 特色：
 *   1. 單檔即可運作，不依賴其他 .gs 檔案。
 *   2. 只需修改最上方 CONFIG 區塊，其餘不用動。
 *   3. 寄信使用 GmailApp / MailApp，不需要 Google Cloud 專案、
 *      不需要 OAuth 用戶端 ID、不需要應用程式密碼、不需要 SMTP 設定。
 *
 * 語言：繁體中文（台灣用語）
 * ============================================================================
 */

// ═══ 設定區：只要改這裡 ═══════════════════════════════════════════════
const CONFIG = {
  // 雲端硬碟「作業歸檔區」資料夾 ID
  // 取得方式：開啟資料夾，網址列 /folders/ 後面那一長串
  ARCHIVE_FOLDER_ID: '請貼上你的雲端硬碟資料夾 ID',

  // 學年度／學期，會成為檔名與資料夾的第一層
  SCHOOL_YEAR: '2026',

  // 收件紀錄要寫到哪個分頁（不存在會自動建立）
  LOG_SHEET_NAME: '繳交紀錄',

  // 寄信時顯示的寄件者名稱
  SENDER_NAME: 'OO 高中教務處',

  // 表單題目名稱 → 程式欄位的對應
  // 左邊是程式用的代號，右邊是「表單上題目的文字」，必須一模一樣
  FIELDS: {
    name:    ['姓名', '學生姓名'],          // 會依序尋找，找到就用
    klass:   ['班級', '班別'],
    seat:    ['座號', '學號'],
    title:   ['作業名稱', '作品名稱', '主題'],
    email:   ['電子郵件', 'Email', '電子郵件地址']
  },

  // 是否寄送通知信（上課示範可先設 false，避免打擾學生）
  SEND_MAIL: true
};
// ══════════════════════════════════════════════════════════════════════


/**
 * 表單送出時自動執行的主流程。
 *
 * ⚠️ 觸發器必須從「試算表」建立（onFormSubmit），不可從「表單」建立。
 *    兩者名稱相同但事件物件不同，從表單建的抓不到 e.namedValues。
 *    直接執行 RUN_安裝觸發器() 就不會裝錯。
 *
 * @param {Object} e 表單送出事件
 */
function onFormSubmit(e) {
  // 同一時間可能有多位學生同時繳交，加鎖避免寫入互相覆蓋
  const lock = LockService.getScriptLock();
  if (!lock.tryLock(30000)) {
    Logger.log('取得鎖定逾時，本筆稍後由補跑機制處理。');
    return;
  }

  try {
    const data = parseFormResponse(e);

    // 沒有附件也要留紀錄，才知道誰交過但沒傳檔
    if (!data.fileId) {
      writeLogRow(data, '', '', '無附件');
      Logger.log('無附件：' + data.name);
      return;
    }

    const result = archiveFile(data);
    writeLogRow(data, result.newName, result.url, '已歸檔');

    if (CONFIG.SEND_MAIL) {
      notifyStudent(data, result);
    }

    Logger.log('完成：' + data.name + ' → ' + result.newName);

  } catch (err) {
    // 觸發器的錯誤沒人看得到，一定要記錄並通知自己
    Logger.log('處理失敗：' + err.message + '\n' + err.stack);
    notifyTeacherOnError(e, err);
  } finally {
    lock.releaseLock();
  }
}


/**
 * 把表單回覆整理成好用的物件。
 * @param {Object} e 表單送出事件
 * @return {Object} 繳交資料
 */
function parseFormResponse(e) {
  const answers = (e && e.namedValues) || {};

  /**
   * 依 CONFIG.FIELDS 設定的候選題目名稱依序尋找。
   * @param {Array<string>} candidates 候選題目名稱
   * @return {string} 找到的答案
   */
  function pick(candidates) {
    for (let i = 0; i < candidates.length; i++) {
      const v = answers[candidates[i]];
      if (v && v[0] && String(v[0]).trim() !== '') {
        return String(v[0]).trim();
      }
    }
    return '';
  }

  const data = {
    time:    new Date(),
    name:    pick(CONFIG.FIELDS.name),
    klass:   pick(CONFIG.FIELDS.klass),
    seat:    pick(CONFIG.FIELDS.seat),
    title:   pick(CONFIG.FIELDS.title),
    email:   pick(CONFIG.FIELDS.email),
    fileId:  '',
    origName: ''
  };

  // 表單沒有電子郵件題時，改用系統自動蒐集的填答者信箱
  if (!data.email && e && e.response) {
    try {
      data.email = e.response.getRespondentEmail() || '';
    } catch (ignore) {}
  }

  // 檔案上傳題要走 itemResponses 才拿得到檔案 ID
  // （namedValues 拿到的是網址字串，不好用）
  if (e && e.response) {
    const items = e.response.getItemResponses();
    for (let i = 0; i < items.length; i++) {
      if (items[i].getItem().getType() === FormApp.ItemType.FILE_UPLOAD) {
        const ids = items[i].getResponse();
        if (ids && ids.length) {
          data.fileId = ids[0];
          data.origName = DriveApp.getFileById(ids[0]).getName();
        }
        break;
      }
    }
  }

  return data;
}


/**
 * 檔名正規化並歸檔到「學年度 / 班級」資料夾。
 *
 * 檔名格式：2026_301_15_王小明_第三次作業.pdf
 *          學年度_班級_座號_姓名_作業名稱.副檔名
 *
 * @param {Object} data 繳交資料
 * @return {Object} 新檔名、網址與資料夾
 */
function archiveFile(data) {
  const file = DriveApp.getFileById(data.fileId);

  // 取副檔名（用 lastIndexOf，檔名中間有點也不會出錯）
  let ext = '';
  const dot = data.origName.lastIndexOf('.');
  if (dot > 0) ext = data.origName.substring(dot);

  // 座號補零成兩位數，排序時 2 才不會排在 10 後面
  const seat = data.seat ? padSeat(data.seat) : '';

  const parts = [
    CONFIG.SCHOOL_YEAR,
    sanitize(data.klass || '未填班級'),
    seat,
    sanitize(data.name || '未填姓名'),
    sanitize(data.title || '未命名作業')
  ].filter(function (s) { return s !== ''; });   // 沒填的欄位不留空底線

  const newName = parts.join('_') + ext;

  // 資料夾結構：歸檔區 / 2026 / 301 /
  const yearFolder = getOrCreateFolder(
    DriveApp.getFolderById(CONFIG.ARCHIVE_FOLDER_ID), CONFIG.SCHOOL_YEAR);
  const classFolder = getOrCreateFolder(yearFolder, data.klass || '未填班級');

  file.setName(newName);
  file.moveTo(classFolder);   // moveTo 是搬移；addFile 會在原處留下一份

  return {
    newName: newName,
    url: file.getUrl(),
    folder: CONFIG.SCHOOL_YEAR + '/' + (data.klass || '未填班級')
  };
}


/**
 * 座號補零成兩位數。
 * @param {string} seat 座號
 * @return {string} 補零後的座號
 */
function padSeat(seat) {
  const n = String(seat).replace(/[^0-9]/g, '');
  if (!n) return sanitize(String(seat));
  return n.length === 1 ? '0' + n : n;
}


/**
 * 移除檔名不允許的字元（Windows 會拒收這些）。
 * @param {string} s 原始文字
 * @return {string} 可當檔名的文字
 */
function sanitize(s) {
  return String(s === undefined || s === null ? '' : s)
    .replace(/[\\\/:*?"<>|]/g, '_')
    .replace(/\s+/g, ' ')
    .replace(/_{2,}/g, '_')      // 連續底線收成一個，避免 _b_駭客__b_ 這種醜檔名
    .replace(/^[_\s]+|[_\s]+$/g, '')   // 去掉頭尾的底線與空白
    .trim();
}


/**
 * 找子資料夾，沒有就建立。
 * @param {Folder} parent 上層資料夾
 * @param {string} name 子資料夾名稱
 * @return {Folder}
 */
function getOrCreateFolder(parent, name) {
  const found = parent.getFoldersByName(name);
  return found.hasNext() ? found.next() : parent.createFolder(name);
}


/**
 * 把這一筆寫進繳交紀錄分頁。
 * @param {Object} data 繳交資料
 * @param {string} newName 歸檔後檔名
 * @param {string} url 檔案網址
 * @param {string} status 狀態
 */
function writeLogRow(data, newName, url, status) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let sheet = ss.getSheetByName(CONFIG.LOG_SHEET_NAME);

  if (!sheet) {
    sheet = ss.insertSheet(CONFIG.LOG_SHEET_NAME);
    sheet.appendRow(['繳交時間', '班級', '座號', '姓名', '電子郵件',
                     '作業名稱', '原始檔名', '正規化檔名', '檔案連結', '狀態']);
    sheet.setFrozenRows(1);
    sheet.getRange(1, 1, 1, 10).setFontWeight('bold').setBackground('#F4F1E8');
    sheet.setColumnWidth(1, 150);
    sheet.setColumnWidth(8, 260);
  }

  sheet.appendRow([
    data.time, data.klass, data.seat, data.name, data.email,
    data.title, data.origName, newName, url, status
  ]);
}


/**
 * 寄送繳交成功通知信給學生。
 *
 * 使用 GmailApp 寄信、MailApp 查配額——
 * getRemainingDailyQuota() 只有 MailApp 有，兩者底層相同，混用正常。
 *
 * @param {Object} data 繳交資料
 * @param {Object} result 歸檔結果
 * @return {boolean} 是否成功寄出
 */
function notifyStudent(data, result) {
  if (!data.email) {
    Logger.log('無信箱，略過通知：' + data.name);
    return false;
  }

  // 配額用盡時 sendEmail 會丟例外中斷整個流程，一定要先檢查
  const remaining = MailApp.getRemainingDailyQuota();
  if (remaining <= 0) {
    Logger.log('今日寄信配額已用盡，未通知：' + data.email);
    return false;
  }

  const timeStr = Utilities.formatDate(
    data.time, Session.getScriptTimeZone() || 'Asia/Taipei', 'yyyy/MM/dd (E) HH:mm');

  const subject = '【繳交成功】' + (data.title || '作業') + ' — ' +
                  CONFIG.SCHOOL_YEAR + ' 學年度';

  const html = [
    '<div style="font-family:sans-serif;font-size:15px;line-height:1.85;color:#222;max-width:560px">',
    '  <p>' + esc(data.name) + ' 同學您好：</p>',
    '  <p>系統已收到您繳交的作業，以下是這次的繳交紀錄，請確認內容是否正確。</p>',
    '  <table style="border-collapse:collapse;margin:18px 0;width:100%">',
    row('作業名稱', data.title),
    row('繳交時間', timeStr),
    row('班級座號', (data.klass || '') + ' ' + (data.seat || '')),
    row('您上傳的檔名', data.origName),
    row('系統歸檔檔名', result.newName),
    '  </table>',
    '  <p style="background:#FDF6DF;border-left:3px solid #D9A404;padding:10px 14px;font-size:13.5px">',
    '    系統會依規則自動重新命名，所以檔名與您上傳時不同，這是正常的。<br>',
    '    如需修改，請重新繳交一次，老師會以<b>最後一次</b>的繳交為準。',
    '  </p>',
    '  <p style="color:#999;font-size:12px;border-top:1px solid #ddd;padding-top:12px;margin-top:20px">',
    '    本信由系統自動發送，請勿直接回覆。若有問題請聯繫任課老師。',
    '  </p>',
    '</div>'
  ].join('\n');

  GmailApp.sendEmail(data.email, subject, htmlToText(html), {
    htmlBody: html,
    name: CONFIG.SENDER_NAME,
    replyTo: Session.getEffectiveUser().getEmail()
  });

  Logger.log('已通知 ' + data.email + '（今日剩餘 ' + (remaining - 1) + ' 封）');
  return true;
}


/**
 * 產生信件表格的一列。
 * @param {string} label 欄位名稱
 * @param {string} value 欄位值
 * @return {string} HTML
 */
function row(label, value) {
  return '<tr>' +
    '<td style="padding:7px 16px 7px 0;color:#666;white-space:nowrap;' +
    'border-bottom:1px solid #eee;vertical-align:top">' + esc(label) + '</td>' +
    '<td style="padding:7px 0;font-weight:600;border-bottom:1px solid #eee">' +
    esc(value || '—') + '</td></tr>';
}


/**
 * HTML 跳脫，避免學生在姓名欄填標籤把版面弄壞。
 * @param {string} s 原始文字
 * @return {string} 跳脫後文字
 */
function esc(s) {
  return String(s === undefined || s === null ? '' : s)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}


/**
 * 產生純文字版內文，給不顯示 HTML 的信箱看。
 * sendEmail 第三個參數不要留空字串，否則那些人會收到空白信。
 * @param {string} html HTML 內文
 * @return {string} 純文字
 */
function htmlToText(html) {
  return html.replace(/<br\s*\/?>/gi, '\n')
             .replace(/<\/(p|tr|div|table)>/gi, '\n')
             .replace(/<[^>]+>/g, '')
             .replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>')
             .replace(/&quot;/g, '"').replace(/&#39;/g, "'")
             .replace(/[ \t]+/g, ' ')
             .replace(/\n{3,}/g, '\n\n').trim();
}


/**
 * 處理失敗時寄信通知老師自己。
 * @param {Object} e 原始事件
 * @param {Error} err 錯誤物件
 */
function notifyTeacherOnError(e, err) {
  try {
    const me = Session.getEffectiveUser().getEmail();
    GmailApp.sendEmail(me, '【作業繳交系統】處理失敗，需人工確認',
      '有一筆繳交處理失敗，請到試算表確認。\n\n' +
      '錯誤訊息：' + err.message + '\n\n' +
      '表單答案：\n' + JSON.stringify(e && e.namedValues, null, 2),
      { name: CONFIG.SENDER_NAME });
  } catch (ignore) {
    Logger.log('連錯誤通知都寄不出去：' + ignore.message);
  }
}


// ═══ 以下四支給老師手動執行 ═══════════════════════════════════════════

/**
 * 【第一支】檢查設定是否正確，同時觸發 OAuth 授權視窗。
 * 貼完程式後第一個執行這支。
 */
function RUN_檢查設定() {
  const lines = [];
  let ok = 0, ng = 0;

  function check(item, fn) {
    try {
      lines.push('  [通過] ' + item + '　→ ' + fn());
      ok++;
    } catch (err) {
      lines.push('  [失敗] ' + item + '　→ ' + err.message);
      ng++;
    }
  }

  lines.push('【檢查一】設定值');
  check('雲端硬碟歸檔資料夾', function () {
    if (CONFIG.ARCHIVE_FOLDER_ID.indexOf('請貼上') === 0) {
      throw new Error('還沒填！請把 CONFIG.ARCHIVE_FOLDER_ID 改成你的資料夾 ID');
    }
    return DriveApp.getFolderById(CONFIG.ARCHIVE_FOLDER_ID).getName();
  });
  check('目前的試算表', function () {
    return SpreadsheetApp.getActiveSpreadsheet().getName();
  });

  lines.push('');
  lines.push('【檢查二】寄信權限與配額');
  check('自己的信箱', function () {
    return Session.getEffectiveUser().getEmail();
  });
  check('今日剩餘寄信配額', function () {
    const n = MailApp.getRemainingDailyQuota();
    if (n <= 0) throw new Error('配額已用盡，24 小時後才會恢復');
    return n + ' 封（一般 Gmail 上限 100、學校 Workspace 1500）';
  });

  lines.push('');
  lines.push('【檢查三】表單是否已連結到這張試算表');
  check('表單連結狀態', function () {
    const url = SpreadsheetApp.getActiveSpreadsheet().getFormUrl();
    if (!url) {
      throw new Error('這張試算表還沒接表單。請到表單「回覆」分頁 → 連結至試算表');
    }
    return '已連結';
  });

  lines.push('');
  lines.push('──────────────────────────────────────');
  lines.push('  結果：' + ok + ' 項通過，' + ng + ' 項失敗');
  lines.push(ng === 0 ? '  設定正確，接著執行 RUN_寄測試信()。'
                      : '  請先修正失敗項目再往下做。');

  Logger.log(lines.join('\n'));
}


/**
 * 【第二支】寄一封測試信給自己，確認信件長相與 GmailApp 可用。
 */
function RUN_寄測試信() {
  const me = Session.getEffectiveUser().getEmail();

  const fake = {
    time: new Date(), name: '王小明', klass: '301', seat: '15',
    email: me, title: '第三次程式作業',
    origName: '我的作業 最終版(2).pdf'
  };
  const fakeResult = { newName: '2026_301_15_王小明_第三次程式作業.pdf' };

  const sent = notifyStudent(fake, fakeResult);
  Logger.log(sent ? '測試信已寄給 ' + me + '，去信箱看看長什麼樣子。'
                  : '沒有寄出，請看上面的訊息。');
}


/**
 * 【第三支】安裝表單觸發器。重複執行不會裝出兩個。
 */
function RUN_安裝觸發器() {
  const all = ScriptApp.getProjectTriggers();
  let removed = 0;
  for (let i = 0; i < all.length; i++) {
    if (all[i].getHandlerFunction() === 'onFormSubmit') {
      ScriptApp.deleteTrigger(all[i]);
      removed++;
    }
  }

  ScriptApp.newTrigger('onFormSubmit')
    .forSpreadsheet(SpreadsheetApp.getActiveSpreadsheet())
    .onFormSubmit()
    .create();

  Logger.log('觸發器已安裝' + (removed ? '（清掉舊的 ' + removed + ' 個）' : '') +
             '。\n現在去表單送一筆測試繳交，然後檢查：\n' +
             '  1. 雲端硬碟有沒有長出 ' + CONFIG.SCHOOL_YEAR + '/班級/ 資料夾\n' +
             '  2. 試算表「' + CONFIG.LOG_SHEET_NAME + '」有沒有多一列\n' +
             '  3. 學生信箱有沒有收到通知信');
}


/**
 * 【備用】補跑最後一筆表單回覆。
 * 用途：觸發器裝好之前已經有人交了，或某一筆處理失敗要重跑。
 */
function RUN_補跑最後一筆() {
  const url = SpreadsheetApp.getActiveSpreadsheet().getFormUrl();
  if (!url) {
    Logger.log('這張試算表沒有連結表單。');
    return;
  }

  const form = FormApp.openByUrl(url);
  const responses = form.getResponses();
  if (!responses.length) {
    Logger.log('表單目前沒有任何回覆。');
    return;
  }

  const last = responses[responses.length - 1];

  // 組出跟觸發器相同格式的事件物件
  const namedValues = {};
  const items = last.getItemResponses();
  for (let i = 0; i < items.length; i++) {
    namedValues[items[i].getItem().getTitle()] = [items[i].getResponse()];
  }

  onFormSubmit({ namedValues: namedValues, response: last });
  Logger.log('已補跑最後一筆，請看上方紀錄確認結果。');
}
