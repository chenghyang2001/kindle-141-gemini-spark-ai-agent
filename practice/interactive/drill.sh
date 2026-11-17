#!/bin/bash
# K141 互動導覽（外觀與行為照 K135／K136 的 chNN.sh）：
# 直接讀 prompts/chNN.md，每段清畫面＋標題框、綠色提示詞、黃色 💡 說明，段末「👉 按 Enter 繼續…」。
# 練習段會用 claude -p 讓 Claude 扮演 Gemini Spark 實際產出結果（Spark 本身無法在終端機操作）。
#
# 用法：bash drill.sh <章號，例如 2 或 ch02> [起始段落，預設 1]
#   段 1＝這章重點＋作者例子；段 2 起每個練習一段；最後是教練解說要點（完成畫面）
# 不用 set -e：某個練習失敗只顯示 exit code，不該讓整個導覽中斷。

C='\033[1;36m'; Y='\033[1;33m'; G='\033[1;32m'; R='\033[1;31m'; D='\033[0;37m'; N='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PRACTICE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
REPO_DIR="$(cd "$PRACTICE_DIR/.." && pwd)"
RUN_DIR="$PRACTICE_DIR/run2"
SEG_FILE="$RUN_DIR/seg"   # 主控 Claude 讀這個檔就知道練習格在哪一段
mkdir -p "$RUN_DIR"

usage() { echo "用法：bash $(basename "$0") <章號 0~27 或 chNN> [起始段落]" >&2; exit 1; }

raw_ch="${1:-}"; [ -z "$raw_ch" ] && usage
raw_ch="${raw_ch#ch}"
if ! [[ "$raw_ch" =~ ^[0-9]+$ ]]; then echo -e "${R}錯誤：章號要是數字，收到「$1」${N}" >&2; usage; fi
CH=$((10#$raw_ch)); CH_TAG="$(printf 'ch%02d' "$CH")"
MD="$REPO_DIR/${K141_PROMPTS:-prompts-cc}/$CH_TAG.md"   # 2026-11-17 起預設 Claude Code 版教材
[ -f "$MD" ] || { echo -e "${R}錯誤：找不到教材 $MD${N}" >&2; exit 1; }

START="${2:-1}"
if ! [[ "$START" =~ ^[0-9]+$ ]] || [ "$START" -lt 1 ]; then
  echo -e "${R}錯誤：起始段落必須是正整數，收到「$START」${N}" >&2; usage
fi

command -v claude >/dev/null 2>&1 || { echo -e "${R}錯誤：找不到 claude 指令（PATH 要含 ~/.local/bin）${N}" >&2; exit 1; }

# ---------- 讀教材 ----------
# 取某個 ## 標題底下的條列（到下一個 ## 為止）
section_bullets() {
  awk -v h="## $1" '
    index($0, h) == 1 { on = 1; next }
    /^## / { on = 0 }
    on && /^- / { sub(/^- /, ""); print }
  ' "$MD"
}
CH_TITLE="$(head -1 "$MD" | sed -E 's/^# *ch[0-9]+｜//')"
EX_COUNT="$(grep -c '^### 練習' "$MD")"
TOTAL=$((EX_COUNT + 1))

# 取第 m 個練習的欄位：title／goal／prompt／watch
exercise_field() {
  awk -v m="$1" -v f="$2" '
    /^### 練習/ { n++; if (n == m && f == "title") { t = $0; sub(/^### 練習 *[0-9]+(：|:) */, "", t); print t } ; inex = (n == m); mode = ""; next }
    /^## / { inex = 0 }
    !inex { next }
    /^\*\*目的\*\*/ { if (f == "goal") { g = $0; sub(/^\*\*目的\*\*(：|:) */, "", g); print g }; next }
    /^\*\*控制台接手\*\*/ { if (f == "handoff") { h = $0; sub(/^\*\*控制台接手\*\*(：|:) */, "", h); print h }; next }
    /^```/ { if (mode == "code") { mode = "" } else if (!seen) { mode = "code"; seen = 1 }; next }
    mode == "code" { if (f == "prompt") print; next }
    /^\*\*觀察重點\*\*/ { mode = "watch"; next }
    mode == "watch" && /^- / { if (f == "watch") { w = $0; sub(/^- /, "", w); print w } }
  ' "$MD"
}

# ---------- 畫面 ----------
title() {
  clear
  echo -e "${C}════════════════════════════════════════════${N}"
  echo -e "${C} K141 第 ${CH} 章演練 $1${N}"
  echo -e "${C}════════════════════════════════════════════${N}\n"
}
note() { echo -e "${Y}💡 $*${N}"; }
next() { echo; read -rp "👉 按 Enter 繼續…" _; }
seg() {
  local n="$1" label="$2"
  [ "$n" -lt "$START" ] && return 1
  echo "$CH_TAG 段 $n/$TOTAL" > "$SEG_FILE"
  title "($n/$TOTAL) $label"
  return 0
}

# 讓 Claude 扮演 Spark 跑一個練習；結果另存 run2/chNN/練習M.md
run_exercise() {
  local m="$1" prompt="$2"
  local out_dir="$RUN_DIR/$CH_TAG"; mkdir -p "$out_dir" "$PRACTICE_DIR/$CH_TAG"
  local out_file="$out_dir/練習$m.md"
  # 教材裡的 practice/ 路徑在練習目錄下要去掉
  prompt="$(printf '%s' "$prompt" | sed 's#practice/##g')"
  local full="全自動執行：不要問我任何問題、不要用選擇題，所有選擇一律採用你的推薦，直接做完。
安全規則：信件只存草稿絕不寄出；測試物件標題以「課程練習」開頭；不刪改非本次建立的東西；建立的真實物件記到 $CH_TAG/cleanup.md。
回答會顯示在終端機上，請精簡（不超過 40 行），用條列與短表格。不要執行任何 git 指令（不 commit、不 push）。最後的回答要直接列出成果本身（精簡版），不要只說存了哪些檔。

$prompt"
  echo -e "${G}\$ claude -p  <<提示詞（Claude Code 實作，可用 Gmail／日曆／雲端硬碟）${N}"
  printf '%s\n' "$prompt" | sed "s/^/  /" | while IFS= read -r line; do echo -e "${G}${line}${N}"; done
  echo
  echo -e "${D}⏳ Claude 產出中（約 1～2 分鐘）…${N}"
  local t0=$SECONDS rc
  ( cd "$PRACTICE_DIR" && env -u CLAUDECODE -u CLAUDE_CODE_ENTRYPOINT \
      claude -p "$full" --settings '{"disableAllHooks":true}' --permission-mode acceptEdits --allowedTools mcp__claude_ai_Gmail mcp__claude_ai_Google_Calendar mcp__claude_ai_Google_Drive WebSearch WebFetch Skill "Bash(python:*)" "Bash(ls:*)" \
      --disallowedTools mcp__claude_ai_Gmail__send_message mcp__claude_ai_Gmail__reply mcp__claude_ai_Gmail__trash_message mcp__claude_ai_Gmail__trash_thread "Bash(git:*)" ) | tee "$out_file"
  rc=${PIPESTATUS[0]}
  echo
  if [ "$rc" -ne 0 ]; then echo -e "${R}（claude 結束碼 $rc）${N}"; else echo -e "${D}✔ 完成，用時 $((SECONDS - t0)) 秒，全文存在 run2/$CH_TAG/練習$m.md${N}"; fi
  echo
}

# ---------- 段落 ----------
if seg 1 "$CH_TITLE"; then
  note "這章在講什麼："
  section_bullets "這章在講什麼" | while IFS= read -r b; do echo "  • $b"; done
  echo
  ex="$(section_bullets "作者做過的實驗")"
  if [ -n "$ex" ]; then
    note "作者的例子："
    printf '%s\n' "$ex" | while IFS= read -r b; do echo "  • $b"; done
  fi
  echo; note "本章共 $EX_COUNT 個練習，接下來每段由 Claude Code 實際做一次。"
  next
fi

for ((m = 1; m <= EX_COUNT; m++)); do
  if seg $((m + 1)) "練習 $m：$(exercise_field "$m" title)"; then
    goal="$(exercise_field "$m" goal)"
    [ -n "$goal" ] && note "目的：$goal" && echo
    handoff="$(exercise_field "$m" handoff)"
    [ -n "$handoff" ] && note "控制台接手：$handoff（練習格做完後由第 ① 格執行）" && echo
    run_exercise "$m" "$(exercise_field "$m" prompt)"
    note "觀察重點："
    exercise_field "$m" watch | while IFS= read -r w; do echo "  • $w"; done
    next
  fi
done

title "完成 ✅ $CH_TITLE"
note "教練解說要點："
section_bullets "教練解說要點" | while IFS= read -r b; do echo "  • $b"; done
echo "$CH_TAG 完成" > "$SEG_FILE"
echo
# 互動終端機才留一個 shell（K135 的 exec bash 行為）；測試時 stdin 不是終端機就直接結束
if [ -t 0 ]; then exec bash; fi
