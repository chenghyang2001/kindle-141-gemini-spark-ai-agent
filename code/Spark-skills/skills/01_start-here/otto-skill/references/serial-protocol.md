# OTTO 即時遙控 · 序列指令表

遙控韌體 `firmware/OttoRemote`（＝原廠 `Otto_Mblock_Scratch_Serial_V9`）在 **115200** 監聽序列埠，
與 mBlock / Scratch 完全相容。指令以空白分隔、換行結尾；OTTO 回覆包在 `&&…%%`
（`&&A%%`＝收到、`&&F%%`＝動作完成、`&&D 25%%`＝距離 25cm）。

`otto_ctl.py remote/console` 會自動把白話翻成下面的協定，也接受直接打原生協定。

## 動作 M — `M 動作編號 時間T 幅度size`

| 編號 | 動作 | 白話別名 | 範例 |
|----|------|---------|------|
| 0 | 回正/停 | home、stop | `M 0` |
| 1 | 前進 | forward、walk | `M 1 1000 15` |
| 2 | 後退 | back、backward | `M 2 1000 15` |
| 3 | 左轉 | left、turnleft | `M 3 1000 15` |
| 4 | 右轉 | right、turnright | `M 4 1000 15` |
| 5 | 上下 | updown | `M 5 1000 30` |
| 6/7 | 月球漫步 左/右 | moonwalk / moonwalkr | `M 6 1000 30` |
| 8 | 搖擺 | swing | `M 8 1000 30` |
| 9/10 | crusaito 左/右 | crusaito | `M 9 1000 30` |
| 11 | 跳 | jump | `M 11 1000` |
| 12/13 | 拍動 左/右 | flapping | `M 12 1000 30` |
| 14 | 踮腳搖擺 | tiptoe | `M 14 1000 30` |
| 15/16 | 彎腰 左/右 | bend | `M 15 500` |
| 17/18 | 抖腿 左/右 | shakeleg | `M 17 500` |
| 19 | 顫動 | jitter | `M 19 500 30` |
| 20 | 上升轉 | ascturn | `M 20 500 15` |

> 時間 T 越大動作越慢（單位 ms）；幅度 size 越大擺越開。動作會**持續重複**到收到 `S`（stop）。

## 手勢 H — `H 手勢編號`（會配臉部音效）

1 開心・2 超開心・3 難過・4 睡覺・5 放屁・6 困惑・7 愛心・8 生氣・9 焦躁・10 魔法・11 揮手・12 勝利・13 失敗
白話：`gesture 11`

## 唱歌 K — `K 音效編號`

1 連線・2 斷線・3 驚訝・4 OhOoh・5 OhOoh2・6 撒嬌・7 睡・8 開心・9 超開心・10 短開心・11 難過・12 困惑・13-15 放屁・16-18 模式音・19 按鈕
白話：`sing 8`

## 查詢類（會回值）

| 指令 | 白話 | 回覆 |
|------|------|------|
| `D` | dist、distance | `&&D 距離cm%%` |
| `N` | noise | `&&N 噪音值%%` |
| `B` | battery | `&&B 電量%%` |
| `S` | stop、home | 立即回正 |

## 常用範例（otto_ctl.py console 內）

```
forward          # 一直往前走，直到 stop
right 800        # 右轉，速度快一點
jump             # 跳
gesture 11       # 揮手打招呼
sing 8           # 開心音效
dist             # 讀前方距離
stop             # 停下回正
```
