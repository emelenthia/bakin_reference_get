"""
HTML解析ユーティリティモジュール

BeautifulSoup4を使用したHTML解析ヘルパー関数と
相対URLを絶対URLに変換する機能を提供します。
"""

from typing import List, Optional, Dict, Any
from urllib.parse import urljoin, urlparse, urlunparse
import re
from bs4 import BeautifulSoup, Tag, NavigableString


class HTMLParser:
    """HTML解析のためのユーティリティクラス"""
    
    def __init__(self, base_url: str = ""):
        """
        HTMLParserを初期化します
        
        Args:
            base_url: 相対URL変換のためのベースURL
        """
        self.base_url = base_url
    
    def parse_html(self, html_content: str) -> BeautifulSoup:
        """
        HTML文字列をBeautifulSoupオブジェクトに変換します
        
        Args:
            html_content: 解析するHTML文字列
            
        Returns:
            BeautifulSoup: 解析されたHTMLオブジェクト
        """
        return BeautifulSoup(html_content, 'html.parser')
    
    def to_absolute_url(self, relative_url: str, base_url: Optional[str] = None) -> str:
        """
        相対URLを絶対URLに変換します
        
        Args:
            relative_url: 変換する相対URL
            base_url: ベースURL（指定されない場合はインスタンスのbase_urlを使用）
            
        Returns:
            str: 絶対URL
        """
        if not relative_url:
            return ""
        
        # 既に絶対URLの場合はそのまま返す
        if self._is_absolute_url(relative_url):
            return relative_url
        
        # ベースURLを決定
        url_base = base_url or self.base_url
        if not url_base:
            return relative_url
        
        # 相対URLを絶対URLに変換
        return urljoin(url_base, relative_url)
    
    def _is_absolute_url(self, url: str) -> bool:
        """
        URLが絶対URLかどうかを判定します
        
        Args:
            url: 判定するURL
            
        Returns:
            bool: 絶対URLの場合True
        """
        parsed = urlparse(url)
        return bool(parsed.netloc)
    
    def extract_links(self, soup: BeautifulSoup, selector: str = "a", 
                     href_attr: str = "href", make_absolute: bool = True) -> List[str]:
        """
        指定されたセレクターでリンクを抽出します
        
        Args:
            soup: BeautifulSoupオブジェクト
            selector: CSSセレクター（デフォルト: "a"）
            href_attr: href属性名（デフォルト: "href"）
            make_absolute: 絶対URLに変換するかどうか
            
        Returns:
            List[str]: 抽出されたURLのリスト
        """
        links = []
        elements = soup.select(selector)
        
        for element in elements:
            href = element.get(href_attr)
            if href:
                if make_absolute:
                    href = self.to_absolute_url(href)
                links.append(href)
        
        return links
    
    def extract_text_content(self, element: Tag, strip_whitespace: bool = True) -> str:
        """
        要素からテキストコンテンツを抽出します
        
        Args:
            element: BeautifulSoupのTag要素
            strip_whitespace: 前後の空白を削除するかどうか
            
        Returns:
            str: 抽出されたテキスト
        """
        if not element:
            return ""
        
        text = element.get_text()
        if strip_whitespace:
            text = text.strip()
        
        return text
    
    def extract_table_data(self, soup: BeautifulSoup, table_selector: str) -> List[Dict[str, str]]:
        """
        テーブルからデータを抽出します
        
        Args:
            soup: BeautifulSoupオブジェクト
            table_selector: テーブルのCSSセレクター
            
        Returns:
            List[Dict[str, str]]: テーブルデータのリスト
        """
        table_data = []
        table = soup.select_one(table_selector)
        
        if not table:
            return table_data
        
        # ヘッダー行を取得
        header_row = table.select_one("thead tr") or table.select_one("tr")
        if not header_row:
            return table_data
        
        headers = [self.extract_text_content(th) for th in header_row.select("th, td")]
        
        # データ行を取得
        data_rows = table.select("tbody tr") or table.select("tr")[1:]
        
        for row in data_rows:
            cells = row.select("td, th")
            if len(cells) >= len(headers):
                row_data = {}
                for i, header in enumerate(headers):
                    if i < len(cells):
                        row_data[header] = self.extract_text_content(cells[i])
                table_data.append(row_data)
        
        return table_data
    
    def find_element_by_text(self, soup: BeautifulSoup, text: str, 
                           tag: str = None, partial_match: bool = False) -> Optional[Tag]:
        """
        テキスト内容で要素を検索します
        
        Args:
            soup: BeautifulSoupオブジェクト
            text: 検索するテキスト
            tag: 検索対象のタグ名（指定しない場合は全てのタグ）
            partial_match: 部分一致を許可するかどうか
            
        Returns:
            Optional[Tag]: 見つかった要素（見つからない場合はNone）
        """
        if partial_match:
            pattern = re.compile(re.escape(text), re.IGNORECASE)
            # テキストを含む要素を検索
            for element in soup.find_all(tag):
                if element.string and pattern.search(element.string):
                    return element
            return None
        else:
            # 完全一致で検索
            for element in soup.find_all(tag):
                if element.string and element.string.strip() == text:
                    return element
            return None
    
    def clean_html_text(self, text: str) -> str:
        """
        HTMLテキストをクリーンアップします
        
        Args:
            text: クリーンアップするテキスト
            
        Returns:
            str: クリーンアップされたテキスト
        """
        if not text:
            return ""
        
        # 複数の空白を単一の空白に変換
        text = re.sub(r'\s+', ' ', text)
        
        # 前後の空白を削除
        text = text.strip()
        
        # HTMLエンティティをデコード（BeautifulSoupが自動的に行うが、念のため）
        return text
    
    def extract_nested_text(self, element: Tag, separator: str = " ") -> str:
        """
        ネストされた要素からテキストを抽出し、指定された区切り文字で結合します
        
        Args:
            element: BeautifulSoupのTag要素
            separator: テキストを結合する際の区切り文字
            
        Returns:
            str: 結合されたテキスト
        """
        if not element:
            return ""
        
        texts = []
        for content in element.contents:
            if isinstance(content, NavigableString):
                text = str(content).strip()
                if text:
                    texts.append(text)
            elif isinstance(content, Tag):
                nested_text = self.extract_nested_text(content, separator)
                if nested_text:
                    texts.append(nested_text)
        
        return separator.join(texts)


# 便利な関数として直接使用できるヘルパー関数
def parse_html(html_content: str) -> BeautifulSoup:
    """HTML文字列を解析します"""
    return BeautifulSoup(html_content, 'html.parser')


def to_absolute_url(relative_url: str, base_url: str) -> str:
    """相対URLを絶対URLに変換します"""
    parser = HTMLParser(base_url)
    return parser.to_absolute_url(relative_url)


def extract_links_from_html(html_content: str, base_url: str = "", 
                          selector: str = "a") -> List[str]:
    """HTMLからリンクを抽出します"""
    parser = HTMLParser(base_url)
    soup = parser.parse_html(html_content)
    return parser.extract_links(soup, selector)


def clean_text(text: str) -> str:
    """テキストをクリーンアップします"""
    parser = HTMLParser()
    return parser.clean_html_text(text)