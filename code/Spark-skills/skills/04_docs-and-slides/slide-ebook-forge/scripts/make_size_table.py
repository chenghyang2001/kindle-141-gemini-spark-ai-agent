# -*- coding: utf-8 -*-
r"""
掃描 annotated/ 產生「圖片尺寸對照表」，寫書稿時直接抄 width。
用法：python make_size_table.py <annotated資料夾>
來源：F:\GAS 專案工法（先做表再寫書稿，省下大量調圖時間）
"""
import os, sys
from PIL import Image

PAGE_W_MM = 174.0     # 版面可用寬
PAGE_H_MM = 254.5     # 一頁可用高


def pick_width(px_w, px_h):
    """依圖片比例挑一個不會溢頁的 width%（90/93/96 三檔，沿用 GAS 慣例）"""
    for w in (96, 93, 90):
        mm_w = PAGE_W_MM * w / 100.0
        mm_h = mm_w * px_h / px_w
        if mm_h <= PAGE_H_MM * 0.62:      # 單圖不超過頁高六成，留位置給解說
            return w, mm_w, mm_h
    w = 90
    mm_w = PAGE_W_MM * w / 100.0
    return w, mm_w, mm_w * px_h / px_w


def main(d):
    rows = []
    for name in sorted(os.listdir(d)):
        if not name.lower().endswith('.png'):
            continue
        with Image.open(os.path.join(d, name)) as im:
            w, h = im.size
        pw, mw, mh = pick_width(w, h)
        rows.append((name, w, h, pw, mw, mh))

    out = os.path.join(os.path.dirname(d.rstrip('\\/')), '_圖片尺寸對照.md')
    with open(out, 'w', encoding='utf-8') as f:
        f.write('# 圖片尺寸對照（寫書稿時直接抄 width）\n\n')
        f.write('版面可用寬 %.0fmm、一頁可用高 %.1fmm。\n' % (PAGE_W_MM, PAGE_H_MM))
        f.write('`<img class="shot" style="width:NN%;margin:0 auto" '
                'src="real/annotated/mNN.png" alt="">`\n\n')
        f.write('> ★ 標記重點圖（請自行補上內容說明）\n\n')
        f.write('| 圖 | 內容 | 像素 | width | 印出 (mm) |\n|---|---|---|---|---|\n')
        for name, w, h, pw, mw, mh in rows:
            f.write('| %s | （待填） | %dx%d | **%d%%** | %.1f x %.1f |\n'
                    % (os.path.splitext(name)[0], w, h, pw, mw, mh))
    print('產出 -> %s（共 %d 張）' % (out, len(rows)))


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else '.')
