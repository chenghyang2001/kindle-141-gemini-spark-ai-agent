# -*- coding: utf-8 -*-
"""markitdown 回歸自測。

可用 pytest 執行，也可 `python tests/test_to_markdown.py` 直接跑。
重點驗：PDF 攔阻邏輯、SUPPORTED 涵蓋、真實 HTML→MD 轉換。
"""
import importlib.util
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "..", "scripts", "to_markdown.py")


def _load():
    spec = importlib.util.spec_from_file_location("to_markdown", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


M = _load()


def test_supported_covers_office():
    for ext in (".docx", ".pptx", ".xlsx", ".csv", ".html"):
        assert ext in M.SUPPORTED, "缺少支援副檔名 %s" % ext


def test_pdf_guard_blocks_without_force():
    md = M.MarkItDown()
    with tempfile.TemporaryDirectory() as td:
        # 造一個假 pdf 檔（內容不重要，應在轉換前就被擋）
        pdf = os.path.join(td, "x.pdf")
        open(pdf, "wb").write(b"%PDF-1.4\n")
        ok, msg = M.convert_one(md, pdf, os.path.join(td, "x.md"), force_pdf=False)
        assert ok is False
        assert "pdf_to_md" in msg


def test_real_html_conversion():
    md = M.MarkItDown()
    with tempfile.TemporaryDirectory() as td:
        src = os.path.join(td, "a.html")
        dst = os.path.join(td, "a.md")
        open(src, "w", encoding="utf-8").write(
            "<html><body><h1>Title</h1><p>Hello world</p></body></html>"
        )
        ok, res = M.convert_one(md, src, dst, force_pdf=False)
        assert ok is True
        text = open(dst, encoding="utf-8").read()
        assert "Title" in text and "Hello world" in text


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("PASS", name)
    print("ALL PASS")
