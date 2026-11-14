# OTTO 燒錄 / 連線 除錯筆記

## 偵測不到序列埠（detect 空的）
1. OTTO 沒插上、或線是「只充電不傳輸」的爛線 → 換一條能傳資料的 USB 線。
2. **CH340 驅動沒裝**（OTTO 主控 Nano 用 CH340 晶片）：裝 `工具下載/CH341SER`（原廠驅動）。裝完重插 USB。
3. 裝置管理員看「連接埠(COM & LPT)」有沒有出現 `USB-SERIAL CH340 (COMx)`；有黃色驚嘆號＝驅動要重裝。

## 燒錄失敗 upload failed / not in sync / avrdude timeout
排查順序（依經驗，由上而下）：
1. **序列埠被占用**：關掉 Arduino IDE 的序列埠監控、關掉 `otto_ctl.py console`、關掉 mBlock，再燒一次（同一個 COM 同時只能一個程式用）。
2. **選錯 COM**：多個埠時用 `-p COMx` 明確指定 OTTO 那個（拔插 USB 看哪個 COM 消失/出現就是它）。
3. **bootloader 波特率不合**：預設走舊版 `atmega328old`（57600）。若一直 sync 失敗，加 `--new-bootloader` 改用新版（115200）再試。兩種互換通常能中一個。
4. 還是不行：換 USB 孔（避開沒供電的前面板孔/爛 hub）、換線、重開機。

## 馬達異常（新組裝最常見）
- 通電後「答答答」＋馬達發燙 ＝ **伺服卡死/超出行程**。標準解法：**先歸零、再裝腳**。
  1. 不要先鎖腳。燒 `flash-example footalign`（腳掌對齊）或 `flash-example calib`。
  2. 讓四顆馬達回到中位（90°），再把腳掌以正確角度鎖上。
- 走路歪、站不正 ＝ trim 沒校正 → `flash-example calibserial` 用序列埠微調，或走課程 CH16 校正章。

## 即時遙控沒反應
1. 先確認已燒過遙控韌體：`flash-remote -p COMx`（只需一次）。
2. `remote/console` 的鮑率要 **115200**（腳本預設值，別改成 9600）。
3. 送出後 OTTO 沒動但有回 `&&F%%` ＝ 指令收到了，可能是動作太小或幅度 size 太小 → 加大：`M 1 1000 30`。
4. `pip install pyserial` 沒裝 → 腳本會提示，裝了再跑。

## 沒有真機時
本機沒接 OTTO 只能做 `build` / `build-example`（純編譯驗證）。`flash*` / `remote` / `console`
一定要在**接著 OTTO 的電腦**上跑；不要假裝燒錄成功，如實告知需要真機那一步。
