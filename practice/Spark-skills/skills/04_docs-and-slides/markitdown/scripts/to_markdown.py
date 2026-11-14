#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""通用檔案轉 Markdown（微軟 markitdown）。

支援 Word / PowerPoint / Excel / CSV / HTML / EPUB / ZIP / 圖片 / 音檔等。
PDF 預設擋下並提示改用 pdf_to_md；加 --force-pdf 才放行。來源檔只讀不改。
"""
import argparse
import os
import sys


def ensure(pkg, import_name=None):
    import importlib
    name = import_name or pkg
    try:
        return importlib.import_module(name)
    except ImportError:
        import subprocess
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "--break-system-packages", "-q", pkg],
            check=True,
        )
        return importlib.import_module(name)


markitdown = ensure("markitdown")
from markitdown import MarkItDown  # noqa: E402

# markitdown 大致支援的來源副檔名
SUPPORTED = {
    ".docx", ".pptx", ".xlsx", ".xls", ".csv", ".tsv", ".json", ".xml",
    ".html", ".htm", ".epub", ".zip", ".txt",
    ".jpg", ".jpeg", ".png", ".gif", ".bmp",
    ".mp3", ".wav", ".m4a",
}


def convert_one(md, src, dst, force_pdf):
    ext = os.path.splitext(src)[1].lower()
    if ext == ".pdf" and not force_pdf:
        return False, "PDF 請改用 pdf_to_md（或加 --force-pdf 強制）"
    try:
        result = md.convert(src)
        os.makedirs(os.path.dirname(os.path.abspath(dst)), exist_ok=True)
        with open(dst, "w", encoding="utf-8") as f:
            f.write(result.text_content)
        return True, dst
    except Exception as e:
        return False, str(e)


def main():
    ap = argparse.ArgumentParser(description="通用檔案轉 Markdown（markitdown）")
    ap.add_argument("input", help="檔案或資料夾路徑")
    ap.add_argument("-o", "--output", help="輸出檔或資料夾")
    ap.add_argument("--batch", action="store_true", help="批次轉整個資料夾")
    ap.add_argument("--force-pdf", action="store_true", help="允許用 markitdown 轉 PDF")
    args = ap.parse_args()

    md = MarkItDown()

    if args.batch or os.path.isdir(args.input):
        src_dir = args.input
        if not os.path.isdir(src_dir):
            sys.exit("批次模式需要資料夾路徑：%s" % src_dir)
        out_dir = args.output or src_dir
        os.makedirs(out_dir, exist_ok=True)
        ok, fail = [], []
        for name in sorted(os.listdir(src_dir)):
            src = os.path.join(src_dir, name)
            if not os.path.isfile(src):
                continue
            if os.path.splitext(name)[1].lower() not in SUPPORTED and not (
                args.force_pdf and name.lower().endswith(".pdf")
            ):
                continue
            dst = os.path.join(out_dir, os.path.splitext(name)[0] + ".md")
            good, msg = convert_one(md, src, dst, args.force_pdf)
            (ok if good else fail).append((name, msg))
        print("批次完成：成功 %d，失敗 %d" % (len(ok), len(fail)))
        for n, m in ok:
            print("  ✓", n, "->", os.path.basename(m))
        for n, m in fail:
            print("  ✗", n, ":", m)
    else:
        if not os.path.isfile(args.input):
            sys.exit("找不到檔案：%s" % args.input)
        dst = args.output or (os.path.splitext(args.input)[0] + ".md")
        good, msg = convert_one(md, args.input, dst, args.force_pdf)
        if good:
            print("完成：", dst)
        else:
            sys.exit("轉換失敗：" + msg)


if __name__ == "__main__":
    main()
