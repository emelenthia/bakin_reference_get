"""
クラス詳細情報スクレイピングモジュール

単一のクラスページから詳細情報（基本情報、継承情報、説明等）を抽出します。
HTMLの構造に基づいた柔軟なセレクター戦略を実装しています。
"""

import logging
import re
from typing import Optional, Dict, Any
from bs4 import BeautifulSoup, Tag

from ..models.main_models import ClassInfo
from ..utils.html_parser import HTMLParser
from .http_client import HTTPClient


class ClassDetailScraper:
    """
    クラス詳細情報のスクレイピングを行うクラス
    
    単一のクラスページから以下の情報を抽出します：
    - クラス基本情報（名前、完全名、説明）
    - 継承情報
    - その他のメタデータ
    """
    
    def __init__(self, http_client: HTTPClient):
        """
        ClassDetailScraperを初期化
        
        Args:
            http_client: HTTPクライアントインスタンス
        """
        self.http_client = http_client
        self.html_parser = HTMLParser(base_url="https://rpgbakin.com")
        self.logger = logging.getLogger(__name__)
    
    async def scrape_class_details(self, class_url: str, class_name: str, full_name: str) -> Optional[ClassInfo]:
        """
        指定されたクラスURLから詳細情報を取得
        
        Args:
            class_url: クラスページのURL
            class_name: クラス名
            full_name: 完全なクラス名
            
        Returns:
            Optional[ClassInfo]: 抽出されたクラス情報（失敗時はNone）
        """
        try:
            self.logger.info(f"Scraping class details for: {class_name}")
            
            # URLを修正（/csreference/doc/ja/ パスを追加）
            corrected_url = self._fix_class_url(class_url)
            self.logger.debug(f"Corrected URL: {corrected_url}")
            
            # HTMLを取得
            html_content = await self.http_client.get(corrected_url)
            soup = self.html_parser.parse_html(html_content)
            
            # クラス基本情報を抽出
            class_info = self._extract_basic_class_info(soup, class_name, full_name)
            
            self.logger.info(f"Successfully scraped details for class: {class_name}")
            return class_info
            
        except Exception as e:
            self.logger.error(f"Failed to scrape class details for {class_name}: {e}")
            return None
    
    def _extract_basic_class_info(self, soup: BeautifulSoup, class_name: str, 
                                 full_name: str) -> ClassInfo:
        """
        基本的なクラス情報を抽出
        
        Args:
            soup: BeautifulSoupオブジェクト
            class_name: クラス名
            full_name: 完全なクラス名
            class_url: クラスURL
            
        Returns:
            ClassInfo: 基本情報が設定されたClassInfoオブジェクト
        """
        # クラス説明を抽出
        description = self._extract_class_description(soup)
        
        # 継承情報を抽出
        inheritance = self._extract_inheritance_info(soup)
        
        # ClassInfoオブジェクトを作成
        class_info = ClassInfo(
            name=class_name,
            full_name=full_name,
            description=description,
            inheritance=inheritance
        )
        
        return class_info
    
    def _extract_class_description(self, soup: BeautifulSoup) -> Optional[str]:
        """
        クラスの説明を抽出
        
        Args:
            soup: BeautifulSoupオブジェクト
            
        Returns:
            Optional[str]: クラスの説明（見つからない場合はNone）
        """
        # Doxygenスタイルのドキュメントから説明を抽出
        
        # 1. .textblock内の説明を探す（Doxygenの一般的なパターン）
        textblock = soup.select_one(".textblock")
        if textblock:
            # textblock内の最初の段落を取得
            first_p = textblock.select_one("p")
            if first_p:
                description = self.html_parser.extract_text_content(first_p)
                if description and len(description.strip()) > 5:
                    return self.html_parser.clean_html_text(description)
        
        # 2. .memdoc内の説明を探す
        memdoc = soup.select_one(".memdoc")
        if memdoc:
            first_p = memdoc.select_one("p")
            if first_p:
                description = self.html_parser.extract_text_content(first_p)
                if description and len(description.strip()) > 5:
                    return self.html_parser.clean_html_text(description)
        
        # 3. div.contents内の最初の意味のある段落を探す
        contents_div = soup.select_one("div.contents")
        if contents_div:
            paragraphs = contents_div.select("p")
            for p in paragraphs:
                text = self.html_parser.extract_text_content(p)
                # ナビゲーション的なテキストを除外
                if (text and len(text.strip()) > 10 and 
                    not any(nav_text in text for nav_text in [
                        "公開メンバ関数", "公開変数類", "全メンバ一覧", 
                        "#include", "Public Member Functions", "Public Attributes"
                    ])):
                    return self.html_parser.clean_html_text(text)
        
        # 4. テーブルから説明を抽出
        description = self._extract_description_from_table(soup)
        if description:
            return self.html_parser.clean_html_text(description)
        
        # 5. フォールバック: ページタイトルから基本情報を抽出
        title = soup.select_one("title")
        if title:
            title_text = self.html_parser.extract_text_content(title)
            # "BAKIN: SharpKmyGfx::Color クラス" のような形式から情報を抽出
            if "クラス" in title_text:
                return f"Bakinの{title_text.split(':')[-1].strip()}です。"
        
        return None
    
    def _extract_description_from_table(self, soup: BeautifulSoup) -> Optional[str]:
        """
        テーブルから説明を抽出
        
        Args:
            soup: BeautifulSoupオブジェクト
            
        Returns:
            Optional[str]: 抽出された説明
        """
        # テーブル行を検索
        tables = soup.select("table")
        for table in tables:
            rows = table.select("tr")
            for row in rows:
                cells = row.select("td, th")
                if len(cells) >= 2:
                    first_cell_text = self.html_parser.extract_text_content(cells[0]).lower()
                    if "説明" in first_cell_text or "description" in first_cell_text:
                        return self.html_parser.extract_text_content(cells[1])
        
        return None
    
    def _extract_inheritance_info(self, soup: BeautifulSoup) -> Optional[str]:
        """
        継承情報を抽出
        
        Args:
            soup: BeautifulSoupオブジェクト
            
        Returns:
            Optional[str]: 継承情報（見つからない場合はNone）
        """
        # 継承情報のセレクター戦略
        inheritance_selectors = [
            # 一般的な継承情報のセレクター
            ".inheritance",
            ".base-class",
            ".inherits",
            # テーブル内の継承情報
            "table tr:contains('継承') td:last-child",
            "table tr:contains('Inheritance') td:last-child",
            "table tr:contains('Base') td:last-child",
            # その他の可能性
            ".class-hierarchy",
            "div[class*='inherit']",
        ]
        
        for selector in inheritance_selectors:
            try:
                if ":contains(" in selector:
                    # テーブルから継承情報を抽出
                    inheritance = self._extract_inheritance_from_table(soup)
                    if inheritance:
                        return self.html_parser.clean_html_text(inheritance)
                else:
                    element = soup.select_one(selector)
                    if element:
                        inheritance = self.html_parser.extract_text_content(element)
                        if inheritance and len(inheritance.strip()) > 0:
                            return self.html_parser.clean_html_text(inheritance)
            except Exception as e:
                self.logger.debug(f"Failed to extract inheritance with selector '{selector}': {e}")
                continue
        
        # フォールバック: クラス定義から継承情報を抽出
        inheritance = self._extract_inheritance_from_class_definition(soup)
        if inheritance:
            return inheritance
        
        return None
    
    def _extract_inheritance_from_table(self, soup: BeautifulSoup) -> Optional[str]:
        """
        テーブルから継承情報を抽出
        
        Args:
            soup: BeautifulSoupオブジェクト
            
        Returns:
            Optional[str]: 抽出された継承情報
        """
        tables = soup.select("table")
        for table in tables:
            rows = table.select("tr")
            for row in rows:
                cells = row.select("td, th")
                if len(cells) >= 2:
                    first_cell_text = self.html_parser.extract_text_content(cells[0]).lower()
                    if any(keyword in first_cell_text for keyword in ["継承", "inheritance", "base", "extends"]):
                        return self.html_parser.extract_text_content(cells[1])
        
        return None
    
    def _extract_inheritance_from_class_definition(self, soup: BeautifulSoup) -> Optional[str]:
        """
        クラス定義から継承情報を抽出
        
        Args:
            soup: BeautifulSoupオブジェクト
            
        Returns:
            Optional[str]: 抽出された継承情報
        """
        # Doxygenスタイルの継承情報を探す
        
        # 1. 継承図やクラス階層を探す
        inheritance_sections = soup.select(".inherit, .inheritance, .hierarchy")
        for section in inheritance_sections:
            text = self.html_parser.extract_text_content(section)
            if text and len(text.strip()) > 0:
                return text
        
        # 2. テーブル内の継承情報を探す
        tables = soup.select("table")
        for table in tables:
            rows = table.select("tr")
            for row in rows:
                cells = row.select("td, th")
                if len(cells) >= 2:
                    first_cell = self.html_parser.extract_text_content(cells[0]).lower()
                    if any(keyword in first_cell for keyword in ["継承", "inheritance", "base", "parent"]):
                        inheritance_text = self.html_parser.extract_text_content(cells[1])
                        if inheritance_text and inheritance_text.strip():
                            return inheritance_text
        
        # 3. クラス定義のパターンを検索
        code_elements = soup.select("code, pre, .code, .definition, .memproto")
        
        for element in code_elements:
            text = self.html_parser.extract_text_content(element)
            
            # C#のクラス定義パターンをマッチ
            # 例: "public class ClassName : BaseClass"
            class_pattern = r'class\s+\w+\s*:\s*([^{,\s]+)'
            match = re.search(class_pattern, text, re.IGNORECASE)
            
            if match:
                base_class = match.group(1).strip()
                # 一般的でない基底クラス名の場合のみ返す
                if base_class.lower() not in ['object', 'system.object']:
                    return base_class
        
        # 4. Doxygenの継承リンクを探す
        inheritance_links = soup.select("a[href*='class_']")
        for link in inheritance_links:
            # リンクのコンテキストを確認
            parent = link.parent
            if parent:
                parent_text = self.html_parser.extract_text_content(parent).lower()
                if any(keyword in parent_text for keyword in ["継承", "inherit", "base", "extends"]):
                    link_text = self.html_parser.extract_text_content(link)
                    if link_text and link_text.strip():
                        return link_text
        
        return None
    
    def _fix_class_url(self, class_url: str) -> str:
        """
        クラスURLを修正して正しいパスを追加
        
        Args:
            class_url: 元のクラスURL
            
        Returns:
            str: 修正されたURL
        """
        # 既に正しいパスが含まれている場合はそのまま返す
        if "/csreference/doc/ja/" in class_url:
            return class_url
        
        # https://rpgbakin.com/class_ を https://rpgbakin.com/csreference/doc/ja/class_ に変換
        if "https://rpgbakin.com/class_" in class_url:
            return class_url.replace(
                "https://rpgbakin.com/class_",
                "https://rpgbakin.com/csreference/doc/ja/class_"
            )
        
        return class_url
    
    def get_flexible_selectors(self) -> Dict[str, list]:
        """
        柔軟なセレクター戦略の設定を取得
        
        Returns:
            Dict[str, list]: セレクター戦略の辞書
        """
        return {
            'description': [
                ".description",
                ".class-description", 
                ".summary",
                ".brief",
                ".textblock p:first-of-type",
                "div.contents p:first-of-type",
                "div[class*='desc'] p",
                "p"  # フォールバック
            ],
            'inheritance': [
                ".inheritance",
                ".base-class",
                ".inherits",
                ".class-hierarchy",
                "div[class*='inherit']",
                "code",  # フォールバック
                "pre"    # フォールバック
            ]
        }