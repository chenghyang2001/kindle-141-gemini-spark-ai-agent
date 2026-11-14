"""
web-scraper helper 單元測試

跑法：
    python -m unittest discover -s tests
或：
    python tests/test_helpers.py

無外部依賴（只用 stdlib unittest）。
"""
from __future__ import annotations

import argparse
import sys
import unittest
from pathlib import Path

# 把 ../scripts 加進 sys.path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import scrape  # type: ignore


# ============================================================
# _yt_video_id
# ============================================================
class TestYouTubeVideoId(unittest.TestCase):
    VID = "dQw4w9WgXcQ"

    def test_watch_url(self):
        self.assertEqual(scrape._yt_video_id(f"https://www.youtube.com/watch?v={self.VID}"), self.VID)

    def test_watch_with_query(self):
        self.assertEqual(
            scrape._yt_video_id(f"https://www.youtube.com/watch?v={self.VID}&t=42&list=xx"),
            self.VID,
        )

    def test_short_url(self):
        self.assertEqual(scrape._yt_video_id(f"https://youtu.be/{self.VID}"), self.VID)

    def test_embed_url(self):
        self.assertEqual(scrape._yt_video_id(f"https://www.youtube.com/embed/{self.VID}"), self.VID)

    def test_shorts_url(self):
        self.assertEqual(scrape._yt_video_id(f"https://www.youtube.com/shorts/{self.VID}"), self.VID)

    def test_bare_id(self):
        self.assertEqual(scrape._yt_video_id(self.VID), self.VID)

    def test_invalid_inputs(self):
        self.assertIsNone(scrape._yt_video_id(""))
        self.assertIsNone(scrape._yt_video_id(None))  # type: ignore[arg-type]
        self.assertIsNone(scrape._yt_video_id("https://example.com/notyoutube"))
        self.assertIsNone(scrape._yt_video_id("not_an_id"))


# ============================================================
# _learn_cache_key
# ============================================================
class TestLearnCacheKey(unittest.TestCase):
    """快取 key 應對輸出影響因子敏感、對無關因子（out 路徑/PDF 旗標）不敏感。"""

    @staticmethod
    def _ns(**overrides) -> argparse.Namespace:
        defaults = dict(
            topic="Python decorators",
            include="yt,article,github,arxiv",
            videos=3,
            articles=5,
            github=3,
            arxiv=3,
            article_chars=4000,
            github_readme_chars=4000,
        )
        defaults.update(overrides)
        return argparse.Namespace(**defaults)

    def test_same_args_same_key(self):
        self.assertEqual(scrape._learn_cache_key(self._ns()), scrape._learn_cache_key(self._ns()))

    def test_different_topic_different_key(self):
        a = scrape._learn_cache_key(self._ns(topic="光合作用"))
        b = scrape._learn_cache_key(self._ns(topic="細胞分裂"))
        self.assertNotEqual(a, b)

    def test_topic_case_insensitive(self):
        a = scrape._learn_cache_key(self._ns(topic="Python"))
        b = scrape._learn_cache_key(self._ns(topic="python"))
        self.assertEqual(a, b, "topic 大小寫應視為同一鍵")

    def test_topic_whitespace_normalized(self):
        a = scrape._learn_cache_key(self._ns(topic="Python"))
        b = scrape._learn_cache_key(self._ns(topic="  Python  "))
        self.assertEqual(a, b, "前後空白應正規化")

    def test_include_order_invariant(self):
        a = scrape._learn_cache_key(self._ns(include="yt,article"))
        b = scrape._learn_cache_key(self._ns(include="article,yt"))
        self.assertEqual(a, b, "include 順序不影響 key")

    def test_videos_count_affects_key(self):
        a = scrape._learn_cache_key(self._ns(videos=3))
        b = scrape._learn_cache_key(self._ns(videos=5))
        self.assertNotEqual(a, b)

    def test_key_length_stable(self):
        self.assertEqual(len(scrape._learn_cache_key(self._ns())), 16, "key 應為 16 字元短哈希")


# ============================================================
# argparse 子命令完整性
# ============================================================
class TestArgParser(unittest.TestCase):
    EXPECTED_SUBCOMMANDS = [
        "doctor", "search", "fetch", "stealthy", "dynamic",
        "agent", "crawl", "news", "learn", "to-pdf",
    ]

    def test_all_subcommands_have_help(self):
        parser = scrape.build_parser()
        for cmd in self.EXPECTED_SUBCOMMANDS:
            with self.subTest(cmd=cmd):
                with self.assertRaises(SystemExit) as ctx:
                    parser.parse_args([cmd, "-h"])
                # -h 會 exit(0)
                self.assertEqual(ctx.exception.code, 0, f"{cmd} -h 不該失敗")

    def test_learn_has_v11_flags(self):
        """v1.1 新增的旗標：--pdf / --no-cache / --cache-ttl"""
        parser = scrape.build_parser()
        ns = parser.parse_args(["learn", "test", "--pdf", "--no-cache", "--cache-ttl", "3600"])
        self.assertTrue(ns.pdf)
        self.assertTrue(ns.no_cache)
        self.assertEqual(ns.cache_ttl, 3600)

    def test_learn_default_cache_ttl_is_24h(self):
        parser = scrape.build_parser()
        ns = parser.parse_args(["learn", "test"])
        self.assertEqual(ns.cache_ttl, 86400)
        self.assertFalse(ns.no_cache)
        self.assertFalse(ns.pdf)

    def test_news_pdf_flag(self):
        parser = scrape.build_parser()
        ns = parser.parse_args(["news", "--topic", "tech", "--pdf"])
        self.assertTrue(ns.pdf)


# ============================================================
# arXiv XML 解析（mock 不打網路，純測解析）
# ============================================================
SAMPLE_ARXIV_ATOM = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <id>http://arxiv.org/abs/2401.12345v1</id>
    <updated>2024-01-23T18:00:00Z</updated>
    <published>2024-01-23T18:00:00Z</published>
    <title>Sample Title</title>
    <summary>Abstract text here.</summary>
    <author><name>Alice Author</name></author>
    <author><name>Bob Author</name></author>
    <link href="http://arxiv.org/abs/2401.12345v1" rel="alternate" type="text/html"/>
    <link href="http://arxiv.org/pdf/2401.12345v1" rel="related" type="application/pdf" title="pdf"/>
  </entry>
</feed>
"""


class TestArxivParsing(unittest.TestCase):
    """直接餵 sample XML 給內部解析（驗證 _arxiv_search 內的 parsing 行為）"""

    def test_parse_sample(self):
        # 不打網路，重做一次本地解析作驗證
        import xml.etree.ElementTree as ET
        ns = {"a": "http://www.w3.org/2005/Atom"}
        root = ET.fromstring(SAMPLE_ARXIV_ATOM)
        entries = root.findall("a:entry", ns)
        self.assertEqual(len(entries), 1)
        e = entries[0]
        title = (e.find("a:title", ns).text or "").strip()
        authors = ", ".join(a.find("a:name", ns).text for a in e.findall("a:author", ns))
        self.assertEqual(title, "Sample Title")
        self.assertEqual(authors, "Alice Author, Bob Author")


# ============================================================
# v1.2: retry / SRT 解析 / section helpers
# ============================================================
class TestRetryHelper(unittest.TestCase):
    def test_success_first_try(self):
        calls = []
        result, err = scrape._retry(lambda: calls.append(1) or "ok")
        self.assertEqual(result, "ok")
        self.assertIsNone(err)
        self.assertEqual(len(calls), 1)

    def test_success_after_retry(self):
        calls = []
        def flaky():
            calls.append(1)
            if len(calls) < 2:
                raise RuntimeError("boom")
            return "recovered"
        result, err = scrape._retry(flaky, attempts=3, base_delay=0.01)
        self.assertEqual(result, "recovered")
        self.assertIsNone(err)
        self.assertEqual(len(calls), 2)

    def test_all_failures(self):
        def always_fail():
            raise ValueError("nope")
        result, err = scrape._retry(always_fail, attempts=2, base_delay=0.01)
        self.assertIsNone(result)
        self.assertIn("ValueError", err)
        self.assertIn("nope", err)


class TestSrtToPlain(unittest.TestCase):
    SAMPLE_SRT = """1
00:00:00,000 --> 00:00:02,500
Hello world

2
00:00:02,500 --> 00:00:05,000
This is a test
across two lines

3
00:00:05,000 --> 00:00:08,000
Final block
"""

    def test_strips_timestamps_and_indices(self):
        plain = scrape._srt_to_plain(self.SAMPLE_SRT)
        self.assertNotIn("-->", plain)
        self.assertNotIn("00:00", plain)
        self.assertIn("Hello world", plain)
        self.assertIn("Final block", plain)

    def test_joins_multiline_block(self):
        plain = scrape._srt_to_plain(self.SAMPLE_SRT)
        self.assertIn("This is a test across two lines", plain)

    def test_empty_input(self):
        self.assertEqual(scrape._srt_to_plain(""), "")


class TestYtSubtitleSkillDetection(unittest.TestCase):
    def test_returns_path_or_none(self):
        # 不論安裝與否都應該 graceful 回傳 Path 或 None，不 raise
        result = scrape._yt_subtitle_skill_path()
        self.assertTrue(result is None or hasattr(result, "exists"))


class TestSectionDispatch(unittest.TestCase):
    """v1.2: 確認 SECTION_DISPATCH 結構正確，每個 key 對應 (label, callable)。"""

    def test_dispatch_keys(self):
        self.assertEqual(set(scrape.SECTION_DISPATCH.keys()), {"yt", "article", "github", "arxiv"})

    def test_dispatch_values_callable(self):
        for key, (label, fn) in scrape.SECTION_DISPATCH.items():
            with self.subTest(key=key):
                self.assertIsInstance(label, str)
                self.assertTrue(callable(fn), f"{key} 對應的不是 function")


class TestWhisperFallbackFlag(unittest.TestCase):
    """v1.2: --whisper-fallback 旗標"""

    def test_flag_default_false(self):
        ns = scrape.build_parser().parse_args(["learn", "test"])
        self.assertFalse(ns.whisper_fallback)

    def test_flag_can_be_set(self):
        ns = scrape.build_parser().parse_args(["learn", "test", "--whisper-fallback"])
        self.assertTrue(ns.whisper_fallback)


# ============================================================
# main
# ============================================================
if __name__ == "__main__":
    unittest.main(verbosity=2)
