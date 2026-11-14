/**
 * ============================================================================
 * PropertiesService 安全變數配置模組
 * 說明：用於安全存取金鑰與設定，防止將資安憑證硬編碼於程式碼中。
 * 語言：繁體中文 (台灣用語)
 * ============================================================================
 */

const ConfigModule = (function () {
  /**
   * 取得專案全域屬性設定
   * @param {string} key - 設定鍵名
   * @param {string} defaultValue - 預設值 (選填)
   * @return {string} 設定值
   */
  function getProperty(key, defaultValue = '') {
    const scriptProperties = PropertiesService.getScriptProperties();
    const value = scriptProperties.getProperty(key);
    return value !== null ? value : defaultValue;
  }

  /**
   * 寫入專案全域屬性設定
   * @param {string} key - 設定鍵名
   * @param {string} value - 設定值
   */
  function setProperty(key, value) {
    const scriptProperties = PropertiesService.getScriptProperties();
    scriptProperties.setProperty(key, value);
  }

  /**
   * 取得安全的 API 金鑰範例
   * @return {string} API 金鑰
   */
  function getApiKey() {
    const key = getProperty('API_KEY');
    if (!key) {
      throw new Error('未於 ScriptProperties 中找到 API_KEY，請先執行 ConfigModule.setApiKey() 進行設定。');
    }
    return key;
  }

  return {
    getProperty: getProperty,
    setProperty: setProperty,
    getApiKey: getApiKey
  };
})();
