"""
クラス詳細情報スクレイピングモジュール

単一のクラスページから詳細情報（基本情報、継承情報、説明等）を抽出します。
HTMLの構造に基づいた柔軟なセレクター戦略を実装しています。
"""

import asyncio
import logging
import re
from typing import Optional, Dict, Any, List
from bs4 import BeautifulSoup, Tag
import aiohttp

from ..models.main_models import ClassInfo
from ..models.basic_models import ConstructorInfo, ParameterInfo, MethodInfo, ExceptionInfo
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
    
    # 定数定義
    MIN_DESCRIPTION_LENGTH = 5
    MIN_MEANINGFUL_TEXT_LENGTH = 10
    
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
            
            # コンストラクタ情報を抽出
            constructors = self._extract_constructors(soup, class_name)
            class_info.constructors = constructors
            
            # メソッド情報を抽出
            methods = self._extract_methods(soup, class_name)
            class_info.methods = methods
            
            self.logger.info(f"Successfully scraped details for class: {class_name} (found {len(constructors)} constructors, {len(methods)} methods)")
            return class_info
            
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            self.logger.error(f"Network error while scraping class details for {class_name}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error while scraping class details for {class_name}: {e}")
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
                if description and len(description.strip()) > self.MIN_DESCRIPTION_LENGTH:
                    return self.html_parser.clean_html_text(description)
        
        # 2. .memdoc内の説明を探す
        memdoc = soup.select_one(".memdoc")
        if memdoc:
            first_p = memdoc.select_one("p")
            if first_p:
                description = self.html_parser.extract_text_content(first_p)
                if description and len(description.strip()) > self.MIN_DESCRIPTION_LENGTH:
                    return self.html_parser.clean_html_text(description)
        
        # 3. div.contents内の最初の意味のある段落を探す
        contents_div = soup.select_one("div.contents")
        if contents_div:
            paragraphs = contents_div.select("p")
            for p in paragraphs:
                text = self.html_parser.extract_text_content(p)
                # ナビゲーション的なテキストを除外
                if (text and len(text.strip()) > self.MIN_MEANINGFUL_TEXT_LENGTH and 
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
    
    def _extract_from_table_by_keywords(self, soup: BeautifulSoup, keywords: list) -> Optional[str]:
        """
        テーブルからキーワードに基づいて情報を抽出
        
        Args:
            soup: BeautifulSoupオブジェクト
            keywords: 検索するキーワードのリスト
            
        Returns:
            Optional[str]: 抽出された情報
        """
        tables = soup.select("table")
        for table in tables:
            rows = table.select("tr")
            for row in rows:
                cells = row.select("td, th")
                if len(cells) >= 2:
                    first_cell_text = self.html_parser.extract_text_content(cells[0]).lower()
                    if any(keyword in first_cell_text for keyword in keywords):
                        return self.html_parser.extract_text_content(cells[1])
        
        return None
    
    def _extract_inheritance_from_table(self, soup: BeautifulSoup) -> Optional[str]:
        """
        テーブルから継承情報を抽出
        
        Args:
            soup: BeautifulSoupオブジェクト
            
        Returns:
            Optional[str]: 抽出された継承情報
        """
        return self._extract_from_table_by_keywords(
            soup, ["継承", "inheritance", "base", "extends", "parent"]
        )
    
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
        inheritance_text = self._extract_inheritance_from_table(soup)
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
    
    def _extract_constructors(self, soup: BeautifulSoup, class_name: str) -> List[ConstructorInfo]:
        """
        コンストラクタ情報を抽出
        
        Args:
            soup: BeautifulSoupオブジェクト
            class_name: クラス名
            
        Returns:
            List[ConstructorInfo]: 抽出されたコンストラクタ情報のリスト
        """
        constructors = []
        
        try:
            # Doxygenスタイルのコンストラクタセクションを探す
            constructor_sections = self._find_constructor_sections(soup)
            
            for section in constructor_sections:
                constructor = self._parse_constructor_from_section(section, class_name)
                if constructor:
                    constructors.append(constructor)
            
            # セクションが見つからない場合、テーブルから探す
            if not constructors:
                constructors = self._extract_constructors_from_table(soup, class_name)
            
            # それでも見つからない場合、コードブロックから探す
            if not constructors:
                constructors = self._extract_constructors_from_code(soup, class_name)
            
            self.logger.debug(f"Extracted {len(constructors)} constructors for class {class_name}")
            return constructors
            
        except Exception as e:
            self.logger.error(f"Error extracting constructors for {class_name}: {e}")
            return []
    
    def _find_constructor_sections(self, soup: BeautifulSoup) -> List[Tag]:
        """
        コンストラクタセクションを検索
        
        Args:
            soup: BeautifulSoupオブジェクト
            
        Returns:
            List[Tag]: コンストラクタセクションのリスト
        """
        sections = []
        
        # 1. Doxygenの一般的なコンストラクタセクション
        constructor_selectors = [
            # メンバー関数セクション内のコンストラクタ
            ".memitem",
            ".memproto",
            ".memdoc",
            # テーブル行
            "tr",
            # 定義リスト
            "dl dt",
            # その他の可能性
            "div[class*='constructor']",
            "div[class*='member']"
        ]
        
        for selector in constructor_selectors:
            elements = soup.select(selector)
            for element in elements:
                # コンストラクタらしいテキストを含むかチェック
                text = self.html_parser.extract_text_content(element).lower()
                if any(keyword in text for keyword in [
                    "constructor", "コンストラクタ", "ctor", "new ", "初期化"
                ]):
                    sections.append(element)
        
        return sections
    
    def _parse_constructor_from_section(self, section: Tag, class_name: str) -> Optional[ConstructorInfo]:
        """
        セクションからコンストラクタ情報を解析
        
        Args:
            section: HTMLセクション
            class_name: クラス名
            
        Returns:
            Optional[ConstructorInfo]: 解析されたコンストラクタ情報
        """
        try:
            # セクション内のテキストを取得
            section_text = self.html_parser.extract_text_content(section)
            
            # 静的フィールドやプロパティを除外
            if any(exclude_word in section_text.lower() for exclude_word in [
                'static', 'readonly', 'const', 'guid(', 'new guid'
            ]):
                return None
            
            # コンストラクタの定義を探す（より厳密なパターン）
            constructor_patterns = [
                # アクセス修飾子 + クラス名 + パラメータ
                rf'(public|private|protected|internal)\s+{re.escape(class_name)}\s*\([^)]*\)',
                # クラス名 + パラメータ（戻り値の型がないことを確認）
                rf'(?<![\w.]){re.escape(class_name)}\s*\([^)]*\)(?!\s*[=;])'
            ]
            
            for pattern in constructor_patterns:
                match = re.search(pattern, section_text, re.IGNORECASE)
                if match:
                    constructor_def = match.group(0)
                    
                    # 戻り値の型がある場合は除外
                    if re.search(rf'\b\w+\s+{re.escape(class_name)}\s*\(', constructor_def):
                        continue
                    
                    # パラメータを抽出
                    parameters = self._parse_parameters_from_definition(constructor_def)
                    
                    # 説明を抽出
                    description = self._extract_description_from_section(section)
                    
                    # アクセス修飾子を抽出
                    access_modifier = self._extract_access_modifier_from_section(section)
                    
                    return ConstructorInfo(
                        name=class_name,
                        parameters=parameters,
                        description=description,
                        access_modifier=access_modifier
                    )
            
            return None
            
        except Exception as e:
            self.logger.debug(f"Error parsing constructor from section: {e}")
            return None
    
    def _extract_constructors_from_table(self, soup: BeautifulSoup, class_name: str) -> List[ConstructorInfo]:
        """
        テーブルからコンストラクタ情報を抽出
        
        Args:
            soup: BeautifulSoupオブジェクト
            class_name: クラス名
            
        Returns:
            List[ConstructorInfo]: 抽出されたコンストラクタ情報のリスト
        """
        constructors = []
        
        tables = soup.select("table")
        for table in tables:
            rows = table.select("tr")
            
            for row in rows:
                cells = row.select("td, th")
                if len(cells) >= 2:
                    # 最初のセルにコンストラクタ定義があるかチェック
                    first_cell_text = self.html_parser.extract_text_content(cells[0])
                    
                    # 静的フィールドやプロパティを除外
                    if any(exclude_word in first_cell_text.lower() for exclude_word in [
                        'static', 'readonly', 'const', 'guid(', 'new guid', '='
                    ]):
                        continue
                    
                    # コンストラクタらしいパターンをチェック
                    if (class_name in first_cell_text and "(" in first_cell_text and 
                        not re.search(rf'\b\w+\s+{re.escape(class_name)}\s*\(', first_cell_text)):
                        
                        # パラメータを解析
                        parameters = self._parse_parameters_from_definition(first_cell_text)
                        
                        # 説明を取得（2番目のセル）
                        description = None
                        if len(cells) > 1:
                            description = self.html_parser.extract_text_content(cells[1])
                            if description and len(description.strip()) < self.MIN_DESCRIPTION_LENGTH:
                                description = None
                        
                        constructor = ConstructorInfo(
                            name=class_name,
                            parameters=parameters,
                            description=description,
                            access_modifier="public"  # デフォルト
                        )
                        constructors.append(constructor)
        
        return constructors
    
    def _extract_constructors_from_code(self, soup: BeautifulSoup, class_name: str) -> List[ConstructorInfo]:
        """
        コードブロックからコンストラクタ情報を抽出
        
        Args:
            soup: BeautifulSoupオブジェクト
            class_name: クラス名
            
        Returns:
            List[ConstructorInfo]: 抽出されたコンストラクタ情報のリスト
        """
        constructors = []
        seen_signatures = set()  # 重複を避けるため
        
        # コードブロックを検索
        code_elements = soup.select("code, pre, .code, .definition, .memproto")
        
        for element in code_elements:
            text = self.html_parser.extract_text_content(element)
            
            # 静的フィールドやプロパティを除外するため、より厳密なパターンを使用
            # C#のコンストラクタパターンを検索（戻り値の型がないことを確認）
            constructor_patterns = [
                # アクセス修飾子 + クラス名 + パラメータ（戻り値の型なし）
                rf'(public|private|protected|internal)\s+{re.escape(class_name)}\s*\([^)]*\)',
                # クラス名 + パラメータ（newキーワードの後ではない）
                rf'(?<!new\s){re.escape(class_name)}\s*\([^)]*\)'
            ]
            
            for pattern in constructor_patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
                
                for match in matches:
                    constructor_def = match.group(0).strip()
                    
                    # 静的フィールドやプロパティの定義を除外
                    if any(exclude_word in constructor_def.lower() for exclude_word in [
                        'static', 'readonly', 'const', '=', 'new guid', 'guid(', 'new '
                    ]):
                        continue
                    
                    # 戻り値の型がある場合は除外（メソッドの可能性）
                    if re.search(rf'\b\w+\s+{re.escape(class_name)}\s*\(', constructor_def):
                        continue
                    
                    # new キーワードが含まれている場合は除外（インスタンス化の可能性）
                    if 'new ' in constructor_def.lower():
                        continue
                    
                    # パラメータを解析
                    parameters = self._parse_parameters_from_definition(constructor_def)
                    
                    # アクセス修飾子を抽出（元のテキストからも検索）
                    access_modifier = "public"  # デフォルト
                    access_match = re.search(r'\b(public|private|protected|internal)\b', constructor_def, re.IGNORECASE)
                    if access_match:
                        access_modifier = access_match.group(1).lower()
                    else:
                        # 元のテキストからアクセス修飾子を探す
                        element_text = self.html_parser.extract_text_content(element)
                        if re.search(rf'\b(private|protected|internal)\s+{re.escape(class_name)}\s*\(', element_text, re.IGNORECASE):
                            access_match = re.search(rf'\b(private|protected|internal)\s+{re.escape(class_name)}\s*\(', element_text, re.IGNORECASE)
                            if access_match:
                                access_modifier = access_match.group(1).lower()
                    
                    # 重複チェック用のシグネチャを作成
                    param_signature = ','.join([f"{p.type} {p.name}" for p in parameters])
                    signature = f"{access_modifier} {class_name}({param_signature})"
                    
                    if signature not in seen_signatures:
                        seen_signatures.add(signature)
                        constructor = ConstructorInfo(
                            name=class_name,
                            parameters=parameters,
                            description=None,  # コードブロックからは説明を取得しない
                            access_modifier=access_modifier
                        )
                        constructors.append(constructor)
        
        return constructors
    
    def _parse_parameters_from_definition(self, definition: str) -> List[ParameterInfo]:
        """
        定義文字列からパラメータを解析
        
        Args:
            definition: コンストラクタ定義文字列
            
        Returns:
            List[ParameterInfo]: 解析されたパラメータのリスト
        """
        parameters = []
        
        try:
            # 括弧内のパラメータ部分を抽出
            param_match = re.search(r'\(([^)]*)\)', definition)
            if not param_match:
                return parameters
            
            param_text = param_match.group(1).strip()
            if not param_text:
                return parameters
            
            # ジェネリック型を考慮してパラメータを分割
            param_parts = self._split_parameters_safely(param_text)
            
            for param_part in param_parts:
                if not param_part:
                    continue
                
                # パラメータの型と名前を解析
                # 例: "int paramName", "string paramName = defaultValue"
                param_info = self._parse_single_parameter(param_part)
                if param_info:
                    parameters.append(param_info)
        
        except Exception as e:
            self.logger.debug(f"Error parsing parameters from definition '{definition}': {e}")
        
        return parameters
    
    def _split_parameters_safely(self, param_text: str) -> List[str]:
        """
        ジェネリック型を考慮してパラメータを安全に分割
        
        Args:
            param_text: パラメータテキスト
            
        Returns:
            List[str]: 分割されたパラメータのリスト
        """
        parameters = []
        current_param = ""
        bracket_depth = 0
        
        for char in param_text:
            if char == '<':
                bracket_depth += 1
                current_param += char
            elif char == '>':
                bracket_depth -= 1
                current_param += char
            elif char == ',' and bracket_depth == 0:
                # ジェネリック型の外側のカンマのみで分割
                if current_param.strip():
                    parameters.append(current_param.strip())
                current_param = ""
            else:
                current_param += char
        
        # 最後のパラメータを追加
        if current_param.strip():
            parameters.append(current_param.strip())
        
        return parameters
    
    def _parse_single_parameter(self, param_text: str) -> Optional[ParameterInfo]:
        """
        単一のパラメータテキストを解析
        
        Args:
            param_text: パラメータテキスト
            
        Returns:
            Optional[ParameterInfo]: 解析されたパラメータ情報
        """
        try:
            # デフォルト値を除去
            param_text = re.sub(r'\s*=\s*[^,]*', '', param_text).strip()
            
            # 型と名前を分離
            # 一般的なパターン: "type name" または "type[] name"
            parts = param_text.split()
            
            if len(parts) >= 2:
                # 最後の部分が名前、それ以外が型
                param_name = parts[-1]
                param_type = ' '.join(parts[:-1])
                
                # 特殊文字を除去（ref, out, params等）
                param_type = re.sub(r'\b(ref|out|params)\s+', '', param_type)
                
                return ParameterInfo(
                    name=param_name,
                    type=param_type,
                    description=None
                )
            elif len(parts) == 1:
                # 型のみの場合（名前が省略されている）
                return ParameterInfo(
                    name="param",
                    type=parts[0],
                    description=None
                )
        
        except Exception as e:
            self.logger.debug(f"Error parsing single parameter '{param_text}': {e}")
        
        return None
    
    def _extract_description_from_section(self, section: Tag) -> Optional[str]:
        """
        セクションから説明を抽出
        
        Args:
            section: HTMLセクション
            
        Returns:
            Optional[str]: 抽出された説明
        """
        # セクション内の段落を探す
        paragraphs = section.select("p")
        for p in paragraphs:
            text = self.html_parser.extract_text_content(p)
            if text and len(text.strip()) > self.MIN_DESCRIPTION_LENGTH:
                return self.html_parser.clean_html_text(text)
        
        # 段落が見つからない場合、セクション全体のテキストから抽出
        section_text = self.html_parser.extract_text_content(section)
        lines = section_text.split('\n')
        
        for line in lines:
            line = line.strip()
            if (line and len(line) > self.MIN_DESCRIPTION_LENGTH and 
                not any(skip_word in line.lower() for skip_word in [
                    "constructor", "コンストラクタ", "public", "private", "protected"
                ])):
                return line
        
        return None
    
    def _extract_access_modifier_from_section(self, section: Tag) -> str:
        """
        セクションからアクセス修飾子を抽出
        
        Args:
            section: HTMLセクション
            
        Returns:
            str: アクセス修飾子（デフォルトは"public"）
        """
        section_text = self.html_parser.extract_text_content(section).lower()
        
        if "private" in section_text:
            return "private"
        elif "protected" in section_text:
            return "protected"
        elif "internal" in section_text:
            return "internal"
        else:
            return "public"
    
    def _extract_methods(self, soup: BeautifulSoup, class_name: str) -> List[MethodInfo]:
        """
        メソッド情報を抽出
        
        Args:
            soup: BeautifulSoupオブジェクト
            class_name: クラス名
            
        Returns:
            List[MethodInfo]: 抽出されたメソッド情報のリスト
        """
        methods = []
        
        try:
            # Doxygenスタイルのメソッドセクションを探す
            method_sections = self._find_method_sections(soup, class_name)
            
            for section in method_sections:
                method = self._parse_method_from_section(section, class_name)
                if method:
                    methods.append(method)
            
            # セクションが見つからない場合、テーブルから探す
            if not methods:
                methods = self._extract_methods_from_table(soup, class_name)
            
            # それでも見つからない場合、コードブロックから探す
            if not methods:
                methods = self._extract_methods_from_code(soup, class_name)
            
            # 重複を除去
            methods = self._remove_duplicate_methods(methods)
            
            self.logger.debug(f"Extracted {len(methods)} methods for class {class_name}")
            return methods
            
        except Exception as e:
            self.logger.error(f"Error extracting methods for {class_name}: {e}")
            return []
    
    def _find_method_sections(self, soup: BeautifulSoup, class_name: str) -> List[Tag]:
        """
        メソッドセクションを検索
        
        Args:
            soup: BeautifulSoupオブジェクト
            class_name: クラス名
            
        Returns:
            List[Tag]: メソッドセクションのリスト
        """
        sections = []
        
        # Doxygenの一般的なメソッドセクション
        method_selectors = [
            ".memitem",
            ".memproto", 
            ".memdoc",
            "tr",
            "dl dt",
            "div[class*='method']",
            "div[class*='member']",
            "div[class*='function']"
        ]
        
        for selector in method_selectors:
            elements = soup.select(selector)
            for element in elements:
                text = self.html_parser.extract_text_content(element).lower()
                
                # コンストラクタを除外
                if class_name.lower() in text and "(" in text:
                    # コンストラクタでない場合のみ追加
                    if not self._is_constructor_like(text, class_name):
                        sections.append(element)
                elif any(method_keyword in text for method_keyword in [
                    "method", "メソッド", "function", "関数", "()", "returns", "戻り値"
                ]):
                    sections.append(element)
        
        return sections
    
    def _is_constructor_like(self, text: str, class_name: str) -> bool:
        """
        テキストがコンストラクタ定義らしいかどうかを判定
        
        Args:
            text: 判定するテキスト
            class_name: クラス名
            
        Returns:
            bool: コンストラクタ定義らしい場合True
        """
        text_lower = text.lower()
        class_name_lower = class_name.lower()
        
        # コンストラクタの特徴的なパターン
        constructor_indicators = [
            "constructor", "コンストラクタ", "ctor", "初期化"
        ]
        
        if any(indicator in text_lower for indicator in constructor_indicators):
            return True
        
        # クラス名が戻り値の型として使われていない場合はコンストラクタの可能性
        if class_name_lower in text_lower:
            # "返回值" や "戻り値" などがない場合
            if not any(return_keyword in text_lower for return_keyword in [
                "return", "戻り値", "返回值", "→", "returns"
            ]):
                # アクセス修飾子 + クラス名のパターン
                if re.search(rf'\b(public|private|protected)\s+{re.escape(class_name_lower)}\s*\(', text_lower):
                    return True
        
        return False
    
    def _parse_method_from_section(self, section: Tag, class_name: str) -> Optional[MethodInfo]:
        """
        セクションからメソッド情報を解析
        
        Args:
            section: HTMLセクション
            class_name: クラス名
            
        Returns:
            Optional[MethodInfo]: 解析されたメソッド情報
        """
        try:
            section_text = self.html_parser.extract_text_content(section)
            
            # コンストラクタを除外
            if self._is_constructor_like(section_text, class_name):
                return None
            
            # メソッドのパターンを探す
            # C#メソッドパターン: [アクセス修飾子] [static] 戻り値の型 メソッド名(パラメータ)
            method_patterns = [
                # 完全なメソッド定義
                r'(public|private|protected|internal)?\s*(static)?\s*(\w+(?:\[\])?(?:\<[^>]+\>)?)\s+(\w+)\s*\(([^)]*)\)',
                # 戻り値の型 + メソッド名
                r'(\w+(?:\[\])?(?:\<[^>]+\>)?)\s+(\w+)\s*\(([^)]*)\)',
                # メソッド名のみ（戻り値の型が別の場所にある場合）
                r'(\w+)\s*\(([^)]*)\)'
            ]
            
            for pattern in method_patterns:
                matches = re.finditer(pattern, section_text, re.IGNORECASE)
                
                for match in matches:
                    groups = match.groups()
                    
                    if len(groups) == 5:  # 完全なパターン
                        access_modifier, is_static, return_type, method_name, params = groups
                        access_modifier = access_modifier or "public"
                        is_static = bool(is_static)
                    elif len(groups) == 3 and not groups[0] in ['public', 'private', 'protected']:  # 戻り値の型 + メソッド名
                        return_type, method_name, params = groups
                        access_modifier = "public"
                        is_static = "static" in section_text.lower()
                    elif len(groups) == 2:  # メソッド名のみ
                        method_name, params = groups
                        return_type = self._extract_return_type_from_section(section)
                        access_modifier = "public"
                        is_static = "static" in section_text.lower()
                    else:
                        continue
                    
                    # クラス名と同じメソッド名はスキップ（コンストラクタの可能性）
                    if method_name.lower() == class_name.lower():
                        continue
                    
                    # C#の予約語や特殊なメソッド名をスキップ
                    if method_name.lower() in ['get', 'set', 'add', 'remove', 'new', 'static', 'const']:
                        continue
                    
                    # パラメータを解析
                    parameters = self._parse_parameters_from_definition(f"method({params})")
                    
                    # 説明を抽出
                    description = self._extract_description_from_section(section)
                    
                    # 例外情報を抽出
                    exceptions = self._extract_exceptions_from_section(section)
                    
                    method_info = MethodInfo(
                        name=method_name,
                        return_type=return_type or "void",
                        parameters=parameters,
                        description=description,
                        is_static=is_static,
                        access_modifier=access_modifier,
                        exceptions=exceptions if exceptions else None
                    )
                    
                    return method_info
            
            return None
            
        except Exception as e:
            self.logger.debug(f"Error parsing method from section: {e}")
            return None
    
    def _extract_return_type_from_section(self, section: Tag) -> Optional[str]:
        """
        セクションから戻り値の型を抽出
        
        Args:
            section: HTMLセクション
            
        Returns:
            Optional[str]: 戻り値の型
        """
        section_text = self.html_parser.extract_text_content(section)
        
        # 戻り値の型に関するキーワードを探す
        return_patterns = [
            r'戻り値\s*[:：]\s*(\w+(?:\[\])?)',
            r'return\s+type\s*[:：]\s*(\w+(?:\[\])?)',
            r'returns?\s*[:：]\s*(\w+(?:\[\])?)',
            r'→\s*(\w+(?:\[\])?)'
        ]
        
        for pattern in return_patterns:
            match = re.search(pattern, section_text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return "void"
    
    def _extract_exceptions_from_section(self, section: Tag) -> List[ExceptionInfo]:
        """
        セクションから例外情報を抽出
        
        Args:
            section: HTMLセクション
            
        Returns:
            List[ExceptionInfo]: 抽出された例外情報のリスト
        """
        exceptions = []
        section_text = self.html_parser.extract_text_content(section)
        
        # 例外情報のパターンを探す
        exception_patterns = [
            r'throws?\s+(\w+Exception)(?:\s*[:：]\s*([^.\n]+))?',
            r'例外\s*[:：]\s*(\w+Exception)(?:\s*[:：]\s*([^.\n]+))?',
            r'(\w+Exception)\s*[:：]\s*([^.\n]+)',
            r'スロー\s*[:：]\s*(\w+Exception)(?:\s*[:：]\s*([^.\n]+))?'
        ]
        
        for pattern in exception_patterns:
            matches = re.finditer(pattern, section_text, re.IGNORECASE)
            for match in matches:
                groups = match.groups()
                exception_type = groups[0]
                exception_desc = groups[1] if len(groups) > 1 and groups[1] else "例外が発生する可能性があります"
                
                exceptions.append(ExceptionInfo(
                    type=exception_type,
                    description=exception_desc.strip()
                ))
        
        return exceptions
    
    def _extract_methods_from_table(self, soup: BeautifulSoup, class_name: str) -> List[MethodInfo]:
        """
        テーブルからメソッド情報を抽出
        
        Args:
            soup: BeautifulSoupオブジェクト
            class_name: クラス名
            
        Returns:
            List[MethodInfo]: 抽出されたメソッド情報のリスト
        """
        methods = []
        
        tables = soup.select("table")
        for table in tables:
            rows = table.select("tr")
            
            for row in rows:
                cells = row.select("td, th")
                if len(cells) >= 2:
                    first_cell_text = self.html_parser.extract_text_content(cells[0])
                    
                    # メソッド定義らしいパターンをチェック
                    if ("(" in first_cell_text and ")" in first_cell_text and 
                        not self._is_constructor_like(first_cell_text, class_name)):
                        
                        # メソッド情報を解析
                        method = self._parse_method_from_table_cell(first_cell_text, cells, class_name)
                        if method:
                            methods.append(method)
        
        return methods
    
    def _parse_method_from_table_cell(self, method_text: str, cells: List[Tag], class_name: str) -> Optional[MethodInfo]:
        """
        テーブルセルからメソッド情報を解析
        
        Args:
            method_text: メソッドテキスト
            cells: テーブルセルのリスト
            class_name: クラス名
            
        Returns:
            Optional[MethodInfo]: 解析されたメソッド情報
        """
        try:
            # メソッド名とパラメータを抽出
            method_match = re.search(r'(\w+)\s*\(([^)]*)\)', method_text)
            if not method_match:
                return None
            
            method_name = method_match.group(1)
            param_text = method_match.group(2)
            
            # クラス名と同じメソッド名はスキップ
            if method_name.lower() == class_name.lower():
                return None
            
            # パラメータを解析
            parameters = self._parse_parameters_from_definition(f"method({param_text})")
            
            # 戻り値の型を抽出
            return_type = self._extract_return_type_from_text(method_text)
            
            # 説明を取得（2番目のセル）
            description = None
            if len(cells) > 1:
                description = self.html_parser.extract_text_content(cells[1])
                if description and len(description.strip()) < self.MIN_DESCRIPTION_LENGTH:
                    description = None
            
            # 静的メソッドかどうか判定
            is_static = "static" in method_text.lower()
            
            # アクセス修飾子を判定
            access_modifier = "public"
            if "private" in method_text.lower():
                access_modifier = "private"
            elif "protected" in method_text.lower():
                access_modifier = "protected"
            
            return MethodInfo(
                name=method_name,
                return_type=return_type,
                parameters=parameters,
                description=description,
                is_static=is_static,
                access_modifier=access_modifier,
                exceptions=None
            )
            
        except Exception as e:
            self.logger.debug(f"Error parsing method from table cell: {e}")
            return None
    
    def _extract_return_type_from_text(self, text: str) -> str:
        """
        テキストから戻り値の型を抽出
        
        Args:
            text: 解析するテキスト
            
        Returns:
            str: 戻り値の型（見つからない場合は"void"）
        """
        # 戻り値の型のパターンを探す
        # 例: "string GetName()" -> "string"
        return_type_patterns = [
            r'\b(void|string|int|bool|float|double|object|byte\[\]?|char\[\]?)\s+\w+\s*\(',
            r'\b(\w+)\s+\w+\s*\(',  # 一般的な型
        ]
        
        for pattern in return_type_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return_type = match.group(1)
                # C#の予約語でない場合のみ返す
                if return_type.lower() not in ['public', 'private', 'protected', 'static', 'class']:
                    return return_type
        
        return "void"
    
    def _extract_methods_from_code(self, soup: BeautifulSoup, class_name: str) -> List[MethodInfo]:
        """
        コードブロックからメソッド情報を抽出
        
        Args:
            soup: BeautifulSoupオブジェクト
            class_name: クラス名
            
        Returns:
            List[MethodInfo]: 抽出されたメソッド情報のリスト
        """
        methods = []
        seen_signatures = set()
        
        code_elements = soup.select("code, pre, .code, .definition, .memproto")
        
        for element in code_elements:
            text = self.html_parser.extract_text_content(element)
            
            # C#のメソッドパターンを検索
            method_patterns = [
                # 完全なメソッド定義
                r'(public|private|protected|internal)?\s*(static)?\s*(\w+(?:\[\])?(?:\<[^>]+\>)?)\s+(\w+)\s*\(([^)]*)\)',
                # シンプルなメソッド定義
                r'(\w+(?:\[\])?)\s+(\w+)\s*\(([^)]*)\)'
            ]
            
            for pattern in method_patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
                
                for match in matches:
                    groups = match.groups()
                    
                    if len(groups) == 5:  # 完全なパターン
                        access_modifier, is_static, return_type, method_name, params = groups
                        access_modifier = access_modifier or "public"
                        is_static = bool(is_static)
                    elif len(groups) == 3:  # シンプルなパターン
                        return_type, method_name, params = groups
                        access_modifier = "public"
                        is_static = "static" in text.lower()
                    else:
                        continue
                    
                    # コンストラクタやクラス名と同じメソッドはスキップ
                    if (method_name.lower() == class_name.lower() or
                        self._is_constructor_like(match.group(0), class_name)):
                        continue
                    
                    # C#の予約語をスキップ
                    if method_name.lower() in ['get', 'set', 'add', 'remove', 'new', 'static', 'const', 'class']:
                        continue
                    
                    # パラメータを解析
                    parameters = self._parse_parameters_from_definition(f"method({params})")
                    
                    # 重複チェック
                    param_signature = ','.join([f"{p.type} {p.name}" for p in parameters])
                    signature = f"{return_type} {method_name}({param_signature})"
                    
                    if signature not in seen_signatures:
                        seen_signatures.add(signature)
                        
                        method = MethodInfo(
                            name=method_name,
                            return_type=return_type,
                            parameters=parameters,
                            description=None,
                            is_static=is_static,
                            access_modifier=access_modifier,
                            exceptions=None
                        )
                        methods.append(method)
        
        return methods
    
    def _remove_duplicate_methods(self, methods: List[MethodInfo]) -> List[MethodInfo]:
        """
        重複するメソッドを除去
        
        Args:
            methods: メソッド情報のリスト
            
        Returns:
            List[MethodInfo]: 重複を除去したメソッド情報のリスト
        """
        seen_signatures = set()
        unique_methods = []
        
        for method in methods:
            # パラメータのシグネチャを作成
            param_signature = ','.join([f"{p.type} {p.name}" for p in method.parameters])
            signature = f"{method.return_type} {method.name}({param_signature})"
            
            if signature not in seen_signatures:
                seen_signatures.add(signature)
                unique_methods.append(method)
        
        return unique_methods