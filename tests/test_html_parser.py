"""
HTML解析ユーティリティのテストモジュール
"""

import unittest
from unittest.mock import patch
from bs4 import BeautifulSoup

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.utils.html_parser import HTMLParser, parse_html, to_absolute_url, extract_links_from_html, clean_text


class TestHTMLParser(unittest.TestCase):
    """HTMLParserクラスのテスト"""
    
    def setUp(self):
        """テストセットアップ"""
        self.base_url = "https://rpgbakin.com/csreference/doc/ja/"
        self.parser = HTMLParser(self.base_url)
        
        # テスト用のHTMLサンプル
        self.sample_html = """
        <html>
            <head><title>Test Page</title></head>
            <body>
                <div class="content">
                    <h1>Test Header</h1>
                    <p>This is a test paragraph with <a href="relative-link.html">relative link</a>.</p>
                    <p>This is another paragraph with <a href="https://example.com/absolute">absolute link</a>.</p>
                    <ul>
                        <li><a href="../parent-dir.html">Parent directory link</a></li>
                        <li><a href="/root-relative.html">Root relative link</a></li>
                    </ul>
                    <table>
                        <thead>
                            <tr><th>Name</th><th>Type</th><th>Description</th></tr>
                        </thead>
                        <tbody>
                            <tr><td>Method1</td><td>void</td><td>Test method</td></tr>
                            <tr><td>Method2</td><td>int</td><td>Another method</td></tr>
                        </tbody>
                    </table>
                </div>
            </body>
        </html>
        """
    
    def test_parse_html(self):
        """HTML解析のテスト"""
        soup = self.parser.parse_html(self.sample_html)
        self.assertIsInstance(soup, BeautifulSoup)
        self.assertEqual(soup.title.string, "Test Page")
        self.assertEqual(soup.h1.string, "Test Header")
    
    def test_to_absolute_url_relative(self):
        """相対URL変換のテスト"""
        relative_url = "relative-link.html"
        expected = "https://rpgbakin.com/csreference/doc/ja/relative-link.html"
        result = self.parser.to_absolute_url(relative_url)
        self.assertEqual(result, expected)
    
    def test_to_absolute_url_parent_directory(self):
        """親ディレクトリへの相対URL変換のテスト"""
        relative_url = "../parent-dir.html"
        expected = "https://rpgbakin.com/csreference/doc/parent-dir.html"
        result = self.parser.to_absolute_url(relative_url)
        self.assertEqual(result, expected)
    
    def test_to_absolute_url_root_relative(self):
        """ルート相対URL変換のテスト"""
        relative_url = "/root-relative.html"
        expected = "https://rpgbakin.com/root-relative.html"
        result = self.parser.to_absolute_url(relative_url)
        self.assertEqual(result, expected)
    
    def test_to_absolute_url_already_absolute(self):
        """既に絶対URLの場合のテスト"""
        absolute_url = "https://example.com/absolute"
        result = self.parser.to_absolute_url(absolute_url)
        self.assertEqual(result, absolute_url)
    
    def test_to_absolute_url_empty(self):
        """空のURL変換のテスト"""
        result = self.parser.to_absolute_url("")
        self.assertEqual(result, "")
    
    def test_to_absolute_url_with_custom_base(self):
        """カスタムベースURLでの変換のテスト"""
        relative_url = "test.html"
        custom_base = "https://custom.com/path/"
        expected = "https://custom.com/path/test.html"
        result = self.parser.to_absolute_url(relative_url, custom_base)
        self.assertEqual(result, expected)
    
    def test_is_absolute_url(self):
        """絶対URL判定のテスト"""
        self.assertTrue(self.parser._is_absolute_url("https://example.com"))
        self.assertTrue(self.parser._is_absolute_url("http://example.com"))
        self.assertTrue(self.parser._is_absolute_url("ftp://example.com"))
        self.assertFalse(self.parser._is_absolute_url("relative.html"))
        self.assertFalse(self.parser._is_absolute_url("/root-relative.html"))
        self.assertFalse(self.parser._is_absolute_url("../parent.html"))
    
    def test_extract_links(self):
        """リンク抽出のテスト"""
        soup = self.parser.parse_html(self.sample_html)
        links = self.parser.extract_links(soup, make_absolute=True)
        
        expected_links = [
            "https://rpgbakin.com/csreference/doc/ja/relative-link.html",
            "https://example.com/absolute",
            "https://rpgbakin.com/csreference/doc/parent-dir.html",
            "https://rpgbakin.com/root-relative.html"
        ]
        
        self.assertEqual(len(links), 4)
        for expected in expected_links:
            self.assertIn(expected, links)
    
    def test_extract_links_relative(self):
        """相対リンク抽出のテスト"""
        soup = self.parser.parse_html(self.sample_html)
        links = self.parser.extract_links(soup, make_absolute=False)
        
        expected_links = [
            "relative-link.html",
            "https://example.com/absolute",
            "../parent-dir.html",
            "/root-relative.html"
        ]
        
        self.assertEqual(len(links), 4)
        for expected in expected_links:
            self.assertIn(expected, links)
    
    def test_extract_text_content(self):
        """テキストコンテンツ抽出のテスト"""
        soup = self.parser.parse_html(self.sample_html)
        h1_element = soup.select_one("h1")
        text = self.parser.extract_text_content(h1_element)
        self.assertEqual(text, "Test Header")
        
        # 空の要素のテスト
        empty_text = self.parser.extract_text_content(None)
        self.assertEqual(empty_text, "")
    
    def test_extract_table_data(self):
        """テーブルデータ抽出のテスト"""
        soup = self.parser.parse_html(self.sample_html)
        table_data = self.parser.extract_table_data(soup, "table")
        
        expected_data = [
            {"Name": "Method1", "Type": "void", "Description": "Test method"},
            {"Name": "Method2", "Type": "int", "Description": "Another method"}
        ]
        
        self.assertEqual(len(table_data), 2)
        self.assertEqual(table_data, expected_data)
    
    def test_extract_table_data_no_table(self):
        """存在しないテーブルの抽出テスト"""
        soup = self.parser.parse_html("<html><body><p>No table here</p></body></html>")
        table_data = self.parser.extract_table_data(soup, "table")
        self.assertEqual(table_data, [])
    
    def test_find_element_by_text(self):
        """テキストによる要素検索のテスト"""
        soup = self.parser.parse_html(self.sample_html)
        
        # 完全一致
        element = self.parser.find_element_by_text(soup, "Test Header")
        self.assertIsNotNone(element)
        self.assertEqual(element.name, "h1")
        
        # 見つからない場合
        element = self.parser.find_element_by_text(soup, "Nonexistent Text")
        self.assertIsNone(element)
    
    def test_clean_html_text(self):
        """HTMLテキストクリーンアップのテスト"""
        dirty_text = "  This   has    multiple   spaces  \n\t  "
        clean = self.parser.clean_html_text(dirty_text)
        self.assertEqual(clean, "This has multiple spaces")
        
        # 空文字列のテスト
        empty_clean = self.parser.clean_html_text("")
        self.assertEqual(empty_clean, "")
        
        # Noneのテスト
        none_clean = self.parser.clean_html_text(None)
        self.assertEqual(none_clean, "")
    
    def test_extract_nested_text(self):
        """ネストされたテキスト抽出のテスト"""
        nested_html = """
        <div>
            Outer text
            <span>Inner text</span>
            More outer text
            <p>Paragraph <strong>bold</strong> text</p>
        </div>
        """
        soup = BeautifulSoup(nested_html, 'html.parser')
        div_element = soup.select_one("div")
        
        result = self.parser.extract_nested_text(div_element)
        expected = "Outer text Inner text More outer text Paragraph bold text"
        self.assertEqual(result, expected)
        
        # カスタム区切り文字のテスト
        result_with_separator = self.parser.extract_nested_text(div_element, " | ")
        self.assertIn(" | ", result_with_separator)


class TestHelperFunctions(unittest.TestCase):
    """ヘルパー関数のテスト"""
    
    def test_parse_html_function(self):
        """parse_html関数のテスト"""
        html = "<html><body><h1>Test</h1></body></html>"
        soup = parse_html(html)
        self.assertIsInstance(soup, BeautifulSoup)
        self.assertEqual(soup.h1.string, "Test")
    
    def test_to_absolute_url_function(self):
        """to_absolute_url関数のテスト"""
        relative = "test.html"
        base = "https://example.com/"
        expected = "https://example.com/test.html"
        result = to_absolute_url(relative, base)
        self.assertEqual(result, expected)
    
    def test_extract_links_from_html_function(self):
        """extract_links_from_html関数のテスト"""
        html = '<html><body><a href="test.html">Link</a></body></html>'
        base = "https://example.com/"
        links = extract_links_from_html(html, base)
        self.assertEqual(len(links), 1)
        self.assertEqual(links[0], "https://example.com/test.html")
    
    def test_clean_text_function(self):
        """clean_text関数のテスト"""
        dirty = "  Multiple   spaces  "
        clean = clean_text(dirty)
        self.assertEqual(clean, "Multiple spaces")


if __name__ == '__main__':
    unittest.main()