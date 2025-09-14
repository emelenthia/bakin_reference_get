"""
名前空間スクレイパー

namespaces.htmlページから全ての名前空間とクラス情報を一括取得し、
階層構造を保持したデータ構造を構築します。
"""

import asyncio
import logging
from typing import List, Optional, Dict, Tuple
from urllib.parse import urljoin

import aiohttp

from ..models.main_models import NamespaceInfo, ClassInfo
from ..scraper.http_client import HTTPClient
from ..utils.html_parser import HTMLParser
from ..utils.local_file_loader import LocalFileLoader
from ..utils.hierarchy_parser import HierarchyParser
from .exceptions import NetworkError, ParseError, ScrapingError


# 定数定義
NAMESPACE_URL_PATTERNS = {
    'yukar': 'Yukar',
    'sharp': 'SharpKmy',
    'kmy': 'kmyPhysics'
}

TABLE_SELECTORS = {
    'directory': 'table.directory',
    'memberdecls': 'table.memberdecls'
}

LINK_PATTERNS = {
    'namespace': 'namespace',
    'class': 'class'
}


class NamespaceScraper:
    """
    名前空間とクラス情報をスクレイピングするクラス
    
    namespaces.htmlページから全ての名前空間とクラス情報を取得し、
    階層構造を保持したデータ構造を構築します。
    """
    
    def __init__(self, base_url: str = "https://rpgbakin.com", use_local_cache: bool = False):
        """
        NamespaceScraperを初期化
        
        Args:
            base_url: BakinドキュメントのベースURL
            use_local_cache: ローカルキャッシュを使用するかどうか
        """
        self.base_url = base_url
        self.namespaces_url = urljoin(base_url, "/csreference/doc/ja/namespaces.html")
        self.use_local_cache = use_local_cache
        self.logger = logging.getLogger(__name__)
        
        # HTTPクライアントとHTMLパーサーを初期化
        # 適切なUser-Agentヘッダーを設定してボット識別とレート制限回避
        self.http_client = HTTPClient(
            base_url=base_url,
            user_agent="BakinDocScraper/1.0 (+research purposes)"
        )
        self.html_parser = HTMLParser(base_url=base_url)
        
        # ローカルファイルローダーを初期化
        if use_local_cache:
            self.local_loader = LocalFileLoader()
        else:
            self.local_loader = None
        
        # 階層構造パーサーを初期化
        self.hierarchy_parser = HierarchyParser()
    
    async def scrape_namespaces(self) -> List[NamespaceInfo]:
        """
        namespaces.htmlページから全ての名前空間情報を取得
        
        Returns:
            List[NamespaceInfo]: 名前空間情報のリスト
            
        Raises:
            Exception: スクレイピング中にエラーが発生した場合
        """
        if self.use_local_cache:
            self.logger.info("Using local cache for namespace scraping")
            return await self._scrape_from_local_cache()
        else:
            self.logger.info(f"Starting namespace scraping from: {self.namespaces_url}")
            return await self._scrape_from_remote()
    
    async def _scrape_from_local_cache(self) -> List[NamespaceInfo]:
        """
        ローカルキャッシュから名前空間情報を取得
        
        Returns:
            List[NamespaceInfo]: 名前空間情報のリスト
        """
        try:
            # ローカルファイルから読み込み
            html_content = self.local_loader.load_html_file("namespaces.html")
            
            if html_content is None:
                raise FileNotFoundError("Local namespaces.html file not found")
            
            # HTMLを解析
            soup = self.html_parser.parse_html(html_content)
            
            # 階層構造を解析
            class_path_map = self.hierarchy_parser.parse_hierarchy_from_html(soup)
            
            # 名前空間とクラス情報を一括で抽出
            namespaces = self._extract_namespaces_and_classes_from_directory(soup, class_path_map)
            
            self.logger.info(f"Successfully scraped {len(namespaces)} namespaces from local cache")
            return namespaces
            
        except FileNotFoundError as e:
            self.logger.error(f"Local file not found: {e}")
            raise ScrapingError(f"Local cache file not found: {e}") from e
        except (ValueError, AttributeError) as e:
            self.logger.error(f"HTML parsing error: {e}")
            raise ParseError(f"Failed to parse HTML content: {e}") from e
        except Exception as e:
            self.logger.error(f"Unexpected error scraping from local cache: {e}")
            raise ScrapingError(f"Local cache scraping failed: {e}") from e
    
    async def _scrape_from_remote(self) -> List[NamespaceInfo]:
        """
        リモートサーバーから名前空間情報を取得
        
        Returns:
            List[NamespaceInfo]: 名前空間情報のリスト
        """
        try:
            async with self.http_client:
                # namespaces.htmlページを取得
                html_content = await self.http_client.get(self.namespaces_url)
                
                # HTMLを解析
                soup = self.html_parser.parse_html(html_content)
                
                # 階層構造を解析
                class_path_map = self.hierarchy_parser.parse_hierarchy_from_html(soup)
                
                # 名前空間とクラス情報を一括で抽出
                namespaces = self._extract_namespaces_and_classes_from_directory(soup, class_path_map)
                
                self.logger.info(f"Successfully scraped {len(namespaces)} namespaces")
                return namespaces
                
        except aiohttp.ClientError as e:
            self.logger.error(f"Network error during scraping: {e}")
            raise NetworkError(f"Failed to fetch namespaces: {e}") from e
        except (ValueError, AttributeError) as e:
            self.logger.error(f"HTML parsing error: {e}")
            raise ParseError(f"Failed to parse HTML content: {e}") from e
        except Exception as e:
            self.logger.error(f"Unexpected error scraping namespaces: {e}")
            raise ScrapingError(f"Scraping failed: {e}") from e
    
    async def _extract_namespaces_from_html(self, soup) -> List[NamespaceInfo]:
        """
        HTMLから名前空間情報を抽出
        
        Args:
            soup: BeautifulSoupオブジェクト
            
        Returns:
            List[NamespaceInfo]: 名前空間情報のリスト
        """
        namespaces = []
        
        # Bakinドキュメントの実際の構造に基づいて名前空間リンクを検索
        # table.directoryクラスのテーブルから名前空間リンクを抽出
        directory_table = soup.select_one("table.directory")
        
        if directory_table:
            # 名前空間リンクのみを抽出（href属性に'namespace'を含むもの）
            namespace_links = directory_table.select("a[href*='namespace']")
            
            self.logger.info(f"Found {len(namespace_links)} namespace links")
            
            for link in namespace_links:
                try:
                    namespace_info = await self._extract_namespace_info(link)
                    if namespace_info:
                        namespaces.append(namespace_info)
                        self.logger.debug(f"Extracted namespace: {namespace_info.name}")
                except Exception as e:
                    self.logger.warning(f"Error extracting namespace from link {link}: {e}")
                    continue
        else:
            self.logger.warning("Could not find table.directory - using fallback method")
            # フォールバック: 全ての名前空間リンクを検索
            namespace_links = soup.select("a[href*='namespace']")
            
            for link in namespace_links:
                try:
                    namespace_info = await self._extract_namespace_info(link)
                    if namespace_info:
                        namespaces.append(namespace_info)
                        self.logger.debug(f"Extracted namespace: {namespace_info.name}")
                except Exception as e:
                    self.logger.warning(f"Error extracting namespace from link {link}: {e}")
                    continue
        
        # 重複を除去（名前で判定）
        unique_namespaces = self._remove_duplicate_namespaces(namespaces)
        
        return unique_namespaces
    
    def _extract_namespaces_and_classes_from_directory(self, soup, class_path_map: Dict[str, str] = None) -> List[NamespaceInfo]:
        """
        ディレクトリテーブルから名前空間とクラス情報を一括抽出
        
        Args:
            soup: BeautifulSoupオブジェクト
            
        Returns:
            List[NamespaceInfo]: 名前空間情報のリスト
        """
        # ディレクトリテーブルを取得
        directory_table = soup.select_one(TABLE_SELECTORS['directory'])
        
        if not directory_table:
            self.logger.warning("Could not find table.directory")
            return []
        
        # 全てのリンクを取得
        all_links = directory_table.select("a")
        self.logger.info(f"Found {len(all_links)} total links in directory table")
        
        # リンクを分類
        namespace_links = [link for link in all_links if LINK_PATTERNS['namespace'] in link.get('href', '')]
        class_links = [link for link in all_links if LINK_PATTERNS['class'] in link.get('href', '')]
        
        self.logger.info(f"Found {len(namespace_links)} namespace links and {len(class_links)} class links")
        
        # 名前空間を初期化
        namespace_dict = self._initialize_namespaces_from_links(namespace_links)
        
        # クラスを名前空間に割り当て
        self._assign_classes_to_namespaces(class_links, namespace_dict, class_path_map)
        
        # 結果をリストに変換
        namespaces = list(namespace_dict.values())
        
        # 統計情報をログ出力
        total_classes = sum(len(ns.classes) for ns in namespaces)
        self.logger.info(f"Extracted {len(namespaces)} namespaces with {total_classes} total classes")
        
        return namespaces
    
    def _initialize_namespaces_from_links(self, namespace_links: list) -> Dict[str, NamespaceInfo]:
        """
        名前空間リンクから名前空間辞書を初期化
        
        Args:
            namespace_links: 名前空間リンクのリスト
            
        Returns:
            Dict[str, NamespaceInfo]: 名前空間辞書
        """
        namespace_dict = {}
        
        for link in namespace_links:
            try:
                namespace_name = self.html_parser.extract_text_content(link)
                namespace_href = link.get('href')
                
                if namespace_name and namespace_href:
                    namespace_url = self.html_parser.to_absolute_url(namespace_href)
                    description = self._extract_namespace_description(link)
                    
                    namespace_dict[namespace_name] = NamespaceInfo(
                        name=namespace_name,
                        url=namespace_url,
                        classes=[],
                        description=description
                    )
                    
                    self.logger.debug(f"Added namespace: {namespace_name}")
                    
            except Exception as e:
                self.logger.warning(f"Error processing namespace link {link}: {e}")
                continue
        
        return namespace_dict
    
    def _assign_classes_to_namespaces(self, class_links: list, namespace_dict: Dict[str, NamespaceInfo], class_path_map: Dict[str, str] = None) -> None:
        """
        クラスリンクを対応する名前空間に割り当て
        
        Args:
            class_links: クラスリンクのリスト
            namespace_dict: 名前空間辞書
        """
        for link in class_links:
            try:
                class_info = self._extract_class_info_from_link(link, class_path_map)
                if class_info:
                    # クラスの名前空間を推定
                    namespace_name = self._determine_namespace_for_class(class_info, namespace_dict.keys())
                    
                    if namespace_name and namespace_name in namespace_dict:
                        namespace_dict[namespace_name].classes.append(class_info)
                        self.logger.debug(f"Added class {class_info.name} to namespace {namespace_name}")
                    else:
                        # 名前空間が見つからない場合は、新しい名前空間を作成
                        inferred_namespace = self._infer_namespace_from_class(class_info)
                        self._create_inferred_namespace(inferred_namespace, class_info, namespace_dict)
                        
            except Exception as e:
                self.logger.warning(f"Error processing class link {link}: {e}")
                continue
    
    def _create_inferred_namespace(self, inferred_namespace: str, class_info: ClassInfo, 
                                 namespace_dict: Dict[str, NamespaceInfo]) -> None:
        """
        推定された名前空間を作成してクラスを追加
        
        Args:
            inferred_namespace: 推定された名前空間名
            class_info: クラス情報
            namespace_dict: 名前空間辞書
        """
        if inferred_namespace not in namespace_dict:
            namespace_dict[inferred_namespace] = NamespaceInfo(
                name=inferred_namespace,
                url="",  # URLは不明
                classes=[],
                description=f"Inferred namespace for {class_info.name}"
            )
            self.logger.debug(f"Created inferred namespace: {inferred_namespace}")
        
        namespace_dict[inferred_namespace].classes.append(class_info)
        self.logger.debug(f"Added class {class_info.name} to inferred namespace {inferred_namespace}")
    
    def _determine_namespace_for_class(self, class_info: ClassInfo, namespace_names: list) -> Optional[str]:
        """
        クラスが属する名前空間を推定
        
        Args:
            class_info: クラス情報
            namespace_names: 利用可能な名前空間名のリスト
            
        Returns:
            Optional[str]: 推定された名前空間名
        """
        # フルネームから名前空間を抽出
        if '.' in class_info.full_name:
            parts = class_info.full_name.split('.')
            # 最後の部分（クラス名）を除いた部分を名前空間として使用
            namespace_parts = parts[:-1]
            
            # 効率的なマッチングのため事前にlower()変換したセットを使用
            lower_namespace_names = {name.lower(): name for name in namespace_names}
            
            # 段階的に名前空間を検索
            for i in range(len(namespace_parts), 0, -1):
                potential_namespace = '.'.join(namespace_parts[:i])
                potential_lower = potential_namespace.lower()
                
                # 完全一致を優先
                if potential_lower in lower_namespace_names:
                    return lower_namespace_names[potential_lower]
                
                # 部分一致を試す
                for lower_name, original_name in lower_namespace_names.items():
                    if potential_lower in lower_name or lower_name in potential_lower:
                        return original_name
        
        return None
    
    def _infer_namespace_from_class(self, class_info: ClassInfo) -> str:
        """
        クラス情報から名前空間を推定
        
        Args:
            class_info: クラス情報
            
        Returns:
            str: 推定された名前空間名
        """
        if '.' in class_info.full_name:
            parts = class_info.full_name.split('.')
            # 最後の部分（クラス名）を除いた部分を名前空間として使用
            return '.'.join(parts[:-1])
        else:
            # フルネームに名前空間情報がない場合は、URLから推定
            url_lower = class_info.url.lower()
            for pattern, namespace in NAMESPACE_URL_PATTERNS.items():
                if pattern in url_lower:
                    return namespace
            return 'Unknown'
    
    async def _extract_namespace_info(self, link_element) -> Optional[NamespaceInfo]:
        """
        リンク要素から名前空間情報を抽出
        
        Args:
            link_element: BeautifulSoupのリンク要素
            
        Returns:
            Optional[NamespaceInfo]: 名前空間情報（抽出できない場合はNone）
        """
        try:
            # 名前空間名を取得
            namespace_name = self.html_parser.extract_text_content(link_element)
            if not namespace_name:
                return None
            
            # 名前空間URLを取得
            namespace_href = link_element.get('href')
            if not namespace_href:
                return None
            
            namespace_url = self.html_parser.to_absolute_url(namespace_href)
            
            # 名前空間ページからクラス情報を取得
            classes = await self._scrape_classes_from_namespace(namespace_url)
            
            # 名前空間の説明を取得（親要素から）
            description = self._extract_namespace_description(link_element)
            
            return NamespaceInfo(
                name=namespace_name,
                url=namespace_url,
                classes=classes,
                description=description
            )
            
        except Exception as e:
            self.logger.error(f"Error extracting namespace info: {e}")
            return None
    
    async def _scrape_classes_from_namespace(self, namespace_url: str) -> List[ClassInfo]:
        """
        名前空間ページからクラス情報を取得
        
        Args:
            namespace_url: 名前空間ページのURL
            
        Returns:
            List[ClassInfo]: クラス情報のリスト
        """
        classes = []
        
        try:
            # 名前空間ページを取得
            html_content = await self.http_client.get(namespace_url)
            soup = self.html_parser.parse_html(html_content)
            
            # Bakinドキュメントの実際の構造に基づいてクラスリンクを検索
            # table.directoryクラスのテーブルからクラスリンクを抽出
            directory_table = soup.select_one("table.directory")
            
            if directory_table:
                # クラスリンクのみを抽出（href属性に'class'を含むもの）
                class_links = directory_table.select("a[href*='class']")
                
                self.logger.debug(f"Found {len(class_links)} class links in namespace {namespace_url}")
                
                for link in class_links:
                    try:
                        class_info = self._extract_class_info_from_link(link)
                        if class_info:
                            classes.append(class_info)
                            self.logger.debug(f"Extracted class: {class_info.name}")
                    except Exception as e:
                        self.logger.warning(f"Error extracting class from link {link}: {e}")
                        continue
            else:
                # フォールバック: より一般的なセレクター
                class_tables = soup.select("table.memberdecls")
                
                if not class_tables:
                    class_tables = soup.select("table")
                
                for table in class_tables:
                    # テーブル内のクラスリンクを検索
                    class_links = table.select("a[href*='class']")
                    
                    for link in class_links:
                        try:
                            class_info = self._extract_class_info_from_link(link)
                            if class_info:
                                classes.append(class_info)
                                self.logger.debug(f"Extracted class: {class_info.name}")
                        except Exception as e:
                            self.logger.warning(f"Error extracting class from link {link}: {e}")
                            continue
            
            # 重複を除去
            unique_classes = self._remove_duplicate_classes(classes)
            
        except Exception as e:
            self.logger.error(f"Error scraping classes from namespace {namespace_url}: {e}")
        
        return classes
    
    def _extract_class_info_from_link(self, link_element, class_path_map: Dict[str, str] = None) -> Optional[ClassInfo]:
        """
        リンク要素からクラス情報を抽出
        
        Args:
            link_element: BeautifulSoupのリンク要素
            class_path_map: 階層構造解析から得られたクラスパスマップ
            
        Returns:
            Optional[ClassInfo]: クラス情報（抽出できない場合はNone）
        """
        try:
            # クラス名を取得
            class_name = self.html_parser.extract_text_content(link_element)
            if not class_name:
                return None
            
            # クラスURLを取得
            class_href = link_element.get('href')
            if not class_href:
                return None
            
            class_url = self.html_parser.to_absolute_url(class_href)
            
            # フルネームを取得（階層構造解析結果を優先）
            if class_path_map:
                # クラス名とURLの両方で検索を試行
                full_name = class_path_map.get(class_name)
                if not full_name:
                    # URLでも検索
                    full_name = class_path_map.get(class_href)
                if not full_name:
                    # HierarchyParserのメソッドを使用
                    full_name = self.hierarchy_parser.get_correct_full_name(class_name, class_href)
                
                # それでも見つからない場合はURLから推定
                if not full_name or full_name == class_name:
                    full_name = self._extract_full_name_from_url(class_url, class_name)
                    self.logger.debug(f"Using URL-based full name for {class_name}: {full_name}")
                else:
                    self.logger.debug(f"Using hierarchy-based full name for {class_name}: {full_name}")
            else:
                # フォールバック: URLから推定
                full_name = self._extract_full_name_from_url(class_url, class_name)
                self.logger.debug(f"Using fallback URL-based full name for {class_name}: {full_name}")
            
            # クラスの説明を取得（親要素から）
            description = self._extract_class_description(link_element)
            
            return ClassInfo(
                name=class_name,
                full_name=full_name,
                url=class_url,
                description=description
            )
            
        except Exception as e:
            self.logger.error(f"Error extracting class info: {e}")
            return None
    
    def _extract_full_name_from_url(self, class_url: str, class_name: str) -> str:
        """
        URLからクラスのフルネームを推定
        
        Args:
            class_url: クラスページのURL
            class_name: クラス名
            
        Returns:
            str: 推定されたフルネーム
        """
        try:
            # URLからファイル名部分を抽出
            # 例: class_yukar_1_1_engine_1_1_common_1_1_common_terrain_material.html
            # -> Yukar.Engine.Common.CommonTerrainMaterial
            
            if 'class_' in class_url:
                # URLのクラス部分を抽出
                url_parts = class_url.split('class_')[1].split('.html')[0]
                # アンダースコアで分割
                parts = url_parts.split('_')
                
                # 数字（"1"）を除去して名前空間部分を構築
                namespace_parts = []
                for part in parts:
                    if part and not part.isdigit():
                        # 最初の文字を大文字にして追加
                        namespace_parts.append(part.capitalize())
                
                if namespace_parts:
                    return '.'.join(namespace_parts)
            
            # フォールバック: クラス名をそのまま使用
            return class_name
            
        except Exception as e:
            self.logger.warning(f"Error extracting full name from URL {class_url}: {e}")
            return class_name
    
    def _extract_namespace_description(self, link_element) -> Optional[str]:
        """
        名前空間の説明を抽出
        
        Args:
            link_element: BeautifulSoupのリンク要素
            
        Returns:
            Optional[str]: 名前空間の説明
        """
        try:
            # 親のtr要素を取得
            tr_element = link_element.find_parent('tr')
            if tr_element:
                # 説明が含まれるtd要素を検索
                td_elements = tr_element.select('td')
                if len(td_elements) > 1:
                    # 2番目のtd要素に説明がある場合が多い
                    description = self.html_parser.extract_text_content(td_elements[1])
                    return description if description else None
            
            return None
            
        except Exception as e:
            self.logger.debug(f"Could not extract namespace description: {e}")
            return None
    
    def _extract_class_description(self, link_element) -> Optional[str]:
        """
        クラスの説明を抽出
        
        Args:
            link_element: BeautifulSoupのリンク要素
            
        Returns:
            Optional[str]: クラスの説明
        """
        try:
            # 親のtr要素を取得
            tr_element = link_element.find_parent('tr')
            if tr_element:
                # 説明が含まれるtd要素を検索
                td_elements = tr_element.select('td')
                if len(td_elements) > 1:
                    # 2番目のtd要素に説明がある場合が多い
                    description = self.html_parser.extract_text_content(td_elements[1])
                    return description if description else None
            
            return None
            
        except Exception as e:
            self.logger.debug(f"Could not extract class description: {e}")
            return None
    
    def _remove_duplicate_namespaces(self, namespaces: List[NamespaceInfo]) -> List[NamespaceInfo]:
        """
        重複する名前空間を除去
        
        Args:
            namespaces: 名前空間のリスト
            
        Returns:
            List[NamespaceInfo]: 重複を除去した名前空間のリスト
        """
        seen_names = set()
        unique_namespaces = []
        
        for namespace in namespaces:
            if namespace.name not in seen_names:
                seen_names.add(namespace.name)
                unique_namespaces.append(namespace)
            else:
                self.logger.debug(f"Removing duplicate namespace: {namespace.name}")
        
        return unique_namespaces
    
    def _remove_duplicate_classes(self, classes: List[ClassInfo]) -> List[ClassInfo]:
        """
        重複するクラスを除去
        
        Args:
            classes: クラスのリスト
            
        Returns:
            List[ClassInfo]: 重複を除去したクラスのリスト
        """
        seen_names = set()
        unique_classes = []
        
        for class_info in classes:
            if class_info.name not in seen_names:
                seen_names.add(class_info.name)
                unique_classes.append(class_info)
            else:
                self.logger.debug(f"Removing duplicate class: {class_info.name}")
        
        return unique_classes


# 便利な関数として直接使用できるヘルパー関数
async def scrape_bakin_namespaces(base_url: str = "https://rpgbakin.com", use_local_cache: bool = False) -> List[NamespaceInfo]:
    """
    Bakinの名前空間情報をスクレイピング
    
    Args:
        base_url: BakinドキュメントのベースURL
        use_local_cache: ローカルキャッシュを使用するかどうか
        
    Returns:
        List[NamespaceInfo]: 名前空間情報のリスト
    """
    scraper = NamespaceScraper(base_url, use_local_cache=use_local_cache)
    return await scraper.scrape_namespaces()