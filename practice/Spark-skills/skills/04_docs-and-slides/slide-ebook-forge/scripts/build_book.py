# -*- coding: utf-8 -*-
r"""
把原始程式碼依行號切段、語法上色，注入電子書 template 的 <!--G1--> 標記，
並自動重編頁碼。

用法：改下面 CONFIG 後執行 `python build_book.py`

⚠️ 產出的 _ebook.html 是自動生成的，改內容請改 _ebook_template.html
來源：F:\GAS 專案已驗證工法
"""
import io, re, html, sys

# ============ CONFIG ============
SRC   = r'F:\專案\學員下載區\U01_單元\U01_單元.py'   # 原始程式（單一事實來源）
TPL   = r'F:\專案\講義製作\U01\U01_ebook_template.html'
OUT   = r'F:\專案\講義製作\U01\U01_ebook.html'

# 每段行號範圍（1 起算，含頭含尾）。⚠️ 每段 ≤28 行，每行都要涵蓋、不重疊
SEGMENTS = {
    'G1': (1, 28),
    'G2': (29, 56),
}

# 語言關鍵字（依專案語言調整）
KEYWORDS = ['function', 'return', 'continue', 'break', 'var', 'let', 'const', 'new',
            'if', 'else', 'elif', 'for', 'while', 'try', 'catch', 'except', 'finally',
            'def', 'class', 'import', 'from', 'true', 'false', 'True', 'False', 'None']
COMMENT_MARKS = ('//', '#')
MAX_LINES_PER_SEG = 28
# ================================


def highlight(line):
    """一行上色：切註解 → 抽字串 → 關鍵字/數字(佔位符) → 還原

    ⚠️ 兩個實測踩過的雷，改動前先看懂：
      1. 字串佔位符不能只用數字，否則會被「數字上色」吃掉，字串內容全變 0/1
      2. 關鍵字上色也必須用佔位符：'class' 本身是關鍵字，會回頭把剛產生的
         <span class="k"> 標籤裡的 class 再上一次色，標籤就爛了
    """
    code, comment = line, ''
    in_str, quote = False, ''
    i = 0
    while i < len(line):
        ch = line[i]
        if in_str:
            if ch == quote:
                in_str = False
        elif ch in "'\"":
            in_str, quote = True, ch
        else:
            hit = False
            for m in COMMENT_MARKS:
                if line.startswith(m, i):
                    code, comment = line[:i], line[i:]
                    hit = True
                    break
            if hit:
                break
        i += 1

    strings = []

    def stash(m):
        strings.append(m.group(0))
        return '\x00STR%d\x00' % (len(strings) - 1)

    code = re.sub(r"'(?:[^'\\]|\\.)*'", stash, code)
    code = re.sub(r'"(?:[^"\\]|\\.)*"', stash, code)
    code = html.escape(code)

    tags = []

    def tag(kind, text):
        tags.append('<span class="%s">%s</span>' % (kind, text))
        return '\x00TAG%d\x00' % (len(tags) - 1)

    for kw in KEYWORDS:
        code = re.sub(r'\b%s\b' % re.escape(kw),
                      lambda m: tag('k', m.group(0)), code)
    code = re.sub(r'(?<![\w.])(\d+)(?![\w])',
                  lambda m: tag('n', m.group(0)), code)

    # 函式名：緊接在 function/def 佔位符後的識別字
    def fname(m):
        idx = int(m.group(1))
        if re.search(r'>(?:function|def)<', tags[idx]):
            return m.group(0).replace(m.group(2), tag('f', m.group(2)))
        return m.group(0)

    code = re.sub(r'\x00TAG(\d+)\x00 (\w+)', fname, code)

    code = re.sub(r'\x00TAG(\d+)\x00', lambda m: tags[int(m.group(1))], code)
    code = re.sub(r'\x00STR(\d+)\x00',
                  lambda m: '<span class="s">%s</span>' % html.escape(strings[int(m.group(1))]),
                  code)
    if comment:
        code += '<span class="c">%s</span>' % html.escape(comment)
    return code


def check_segments(total_lines):
    """檢查：每行都涵蓋、不重疊、不超過 28 行"""
    seen, errs = {}, []
    for key, (a, b) in SEGMENTS.items():
        if b - a + 1 > MAX_LINES_PER_SEG:
            errs.append('%s 有 %d 行，超過 %d 行會溢頁' % (key, b-a+1, MAX_LINES_PER_SEG))
        for ln in range(a, b + 1):
            if ln in seen:
                errs.append('第 %d 行重複出現在 %s 與 %s' % (ln, seen[ln], key))
            seen[ln] = key
    missing = [n for n in range(1, total_lines + 1) if n not in seen]
    if missing:
        errs.append('未涵蓋的行：%s' % missing[:20])
    return errs


def main():
    book = io.open(TPL, encoding='utf-8').read()
    src = io.open(SRC, encoding='utf-8').read().split('\n')

    errs = check_segments(len(src))
    if errs:
        print('分段檢查未通過：')
        for e in errs:
            print('  -', e)
        sys.exit(1)

    for key, (a, b) in SEGMENTS.items():
        block = '\n'.join(highlight(l) for l in src[a-1:b]).strip('\n')
        marker = '<!--%s-->' % key
        assert marker in book, '找不到標記 %s' % marker
        book = book.replace(marker, block)
        print('%s  lines %d-%d  = %d 行' % (key, a, b, b-a+1))

    # 頁碼重編：封面不編號，之後依序 02、03……
    def renumber(m, box=[1]):
        box[0] += 1
        return '<span class="pg">%02d</span>' % box[0]

    book, n = re.subn(r'<span class="pg">\d+</span>', renumber, book)
    print('頁碼重編 %d 頁，總頁數 = %d' % (n, n + 1))

    io.open(OUT, 'w', encoding='utf-8').write(book)
    print('產出 ->', OUT)


if __name__ == '__main__':
    main()
