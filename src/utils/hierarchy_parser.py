"""
階層構造解析ユーティリティ

DoxygenのHTMLから階層構造を正確に解析し、
正しいクラスパスを生成するためのユーティリティ
"""

import logging
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class HierarchyNode:
    """階層構造のノード"""
    name: str
    full_path: str
    url: str
    level: int
    node_type: str  # 'namespace' or 'class'
    parent: Optional['HierarchyNode'] = None
    children: List['HierarchyNode'] = None
    
    def __post_init__(self):
        if self.children is None:
            self.children = []


class HierarchyParser:
    """
    DoxygenのHTMLから階層構造を解析するクラス
    
    HTMLのインデント情報（style="width:Npx"）を使用して
    正確な階層構造を構築し、正しいクラスパスを生成します。
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.hierarchy_stack: List[HierarchyNode] = []
        self.all_nodes: List[HierarchyNode] = []
        self.class_path_map: Dict[str, str] = {}
    
    def parse_hierarchy_from_html(self, soup) -> Dict[str, str]:
        """
        HTMLから階層構造を解析してクラスパスマップを生成
        
        Args:
            soup: BeautifulSoupオブジェクト
            
        Returns:
            Dict[str, str]: クラス名 -> 正しいフルパスのマッピング
        """
        self.logger.info("Starting hierarchy parsing from HTML")
        
        # ディレクトリテーブルを取得
        directory_table = soup.select_one("table.directory")
        if not directory_table:
            self.logger.warning("Could not find table.directory")
            return {}
        
        # 全ての行を取得
        rows = directory_table.select("tr")
        self.logger.info(f"Found {len(rows)} rows in directory table")
        
        # 各行を解析
        for row in rows:
            self._parse_row(row)
        
        # クラスパスマップを構築
        self._build_class_path_map()
        
        self.logger.info(f"Generated class path map with {len(self.class_path_map)} entries")
        return self.class_path_map
    
    def _parse_row(self, row) -> None:
        """
        テーブル行を解析してノードを作成
        
        Args:
            row: BeautifulSoupの行要素
        """
        try:
            # インデントレベルを取得
            level = self._extract_indent_level(row)
            if level is None:
                return
            
            # リンク要素を取得
            link = row.select_one("a.el")
            if not link:
                return
            
            # ノード情報を抽出
            name = self._extract_node_name(link)
            url = link.get('href', '')
            node_type = self._determine_node_type(row, url)
            
            if not name:
                return
            
            # 次の行のレベルをチェックして、このノードが子を持つかどうか判定
            has_children = self._check_if_has_children(row)
            
            # ノードを作成
            node = HierarchyNode(
                name=name,
                full_path="",  # 後で設定
                url=url,
                level=level,
                node_type=node_type
            )
            
            # 階層スタックを更新
            self._update_hierarchy_stack(node, has_children)
            
            # フルパスを設定
            node.full_path = self._build_full_path(node)
            
            # ノードを記録
            self.all_nodes.append(node)
            
            self.logger.debug(f"Parsed node: {node.name} (level={level}, type={node_type}, path={node.full_path}, has_children={has_children})")
            
        except Exception as e:
            self.logger.warning(f"Error parsing row: {e}")
    
    def _extract_indent_level(self, row) -> Optional[int]:
        """
        行からインデントレベルを抽出
        
        Args:
            row: BeautifulSoupの行要素
            
        Returns:
            Optional[int]: インデントレベル（ピクセル値を16で割った値）
        """
        try:
            # style属性からwidth値を抽出
            span_elements = row.select("span[style*='width:']")
            
            for span in span_elements:
                style = span.get('style', '')
                width_match = re.search(r'width:(\d+)px', style)
                if width_match:
                    width_px = int(width_match.group(1))
                    # 16pxが1レベルのインデント
                    level = width_px // 16
                    return level
            
            return 0  # インデントなし
            
        except Exception as e:
            self.logger.debug(f"Error extracting indent level: {e}")
            return None
    
    def _extract_node_name(self, link) -> str:
        """
        リンク要素からノード名を抽出
        
        Args:
            link: BeautifulSoupのリンク要素
            
        Returns:
            str: ノード名
        """
        return link.get_text(strip=True)
    
    def _determine_node_type(self, row, url: str) -> str:
        """
        ノードタイプを判定
        
        Args:
            row: BeautifulSoupの行要素
            url: ノードのURL
            
        Returns:
            str: 'namespace' または 'class'
        """
        # アイコンから判定
        icon_span = row.select_one("span.icon")
        if icon_span:
            icon_text = icon_span.get_text(strip=True)
            if icon_text == 'N':
                return 'namespace'
            elif icon_text == 'C':
                return 'class'
        
        # URLから判定
        if 'namespace' in url:
            return 'namespace'
        elif 'class' in url:
            return 'class'
        
        return 'unknown'
    
    def _update_hierarchy_stack(self, node: HierarchyNode, has_children: bool = False) -> None:
        """
        階層スタックを更新
        
        Args:
            node: 新しいノード
            has_children: このノードが子を持つかどうか
        """
        # 現在のレベル以上のノードをスタックから削除
        while self.hierarchy_stack and self.hierarchy_stack[-1].level >= node.level:
            self.hierarchy_stack.pop()
        
        # 親ノードを設定
        if self.hierarchy_stack:
            parent = self.hierarchy_stack[-1]
            node.parent = parent
            parent.children.append(node)
        
        # スタックに追加するかどうかを判定
        # 名前空間は常に追加、クラスは子を持つ場合のみ追加
        if node.node_type == 'namespace' or has_children:
            self.hierarchy_stack.append(node)
    
    def _build_full_path(self, node: HierarchyNode) -> str:
        """
        ノードのフルパスを構築
        
        Args:
            node: ノード
            
        Returns:
            str: フルパス
        """
        path_parts = []
        current = node
        
        while current:
            path_parts.append(current.name)
            current = current.parent
        
        path_parts.reverse()
        return '.'.join(path_parts)
    
    def _build_class_path_map(self) -> None:
        """
        クラスパスマップを構築
        """
        for node in self.all_nodes:
            if node.node_type == 'class':
                # クラス名をキーとして、正しいフルパスをマッピング
                self.class_path_map[node.name] = node.full_path
                
                # URLからも検索できるようにする
                if node.url:
                    self.class_path_map[node.url] = node.full_path
    
    def get_correct_full_name(self, class_name: str, class_url: str = "") -> str:
        """
        正しいフルネームを取得
        
        Args:
            class_name: クラス名
            class_url: クラスURL（オプション）
            
        Returns:
            str: 正しいフルネーム
        """
        # クラス名で検索
        if class_name in self.class_path_map:
            return self.class_path_map[class_name]
        
        # URLで検索
        if class_url and class_url in self.class_path_map:
            return self.class_path_map[class_url]
        
        # 見つからない場合はクラス名をそのまま返す
        self.logger.debug(f"Could not find correct path for class: {class_name}")
        return class_name
    
    def get_hierarchy_stats(self) -> Dict[str, int]:
        """
        階層構造の統計情報を取得
        
        Returns:
            Dict[str, int]: 統計情報
        """
        stats = {
            'total_nodes': len(self.all_nodes),
            'namespaces': len([n for n in self.all_nodes if n.node_type == 'namespace']),
            'classes': len([n for n in self.all_nodes if n.node_type == 'class']),
            'max_level': max([n.level for n in self.all_nodes]) if self.all_nodes else 0
        }
        return stats
    
    def print_hierarchy_tree(self, max_depth: int = 3) -> None:
        """
        階層構造をツリー形式で出力（デバッグ用）
        
        Args:
            max_depth: 最大表示深度
        """
        root_nodes = [n for n in self.all_nodes if n.parent is None]
        
        for root in root_nodes:
            self._print_node_tree(root, 0, max_depth)
    
    def _print_node_tree(self, node: HierarchyNode, depth: int, max_depth: int) -> None:
        """
        ノードツリーを再帰的に出力
        
        Args:
            node: ノード
            depth: 現在の深度
            max_depth: 最大深度
        """
        if depth > max_depth:
            return
        
        indent = "  " * depth
        type_symbol = "📁" if node.node_type == 'namespace' else "📄"
        print(f"{indent}{type_symbol} {node.name} ({node.full_path})")
        
        for child in node.children:
            self._print_node_tree(child, depth + 1, max_depth)


    def _check_if_has_children(self, current_row) -> bool:
        """
        現在の行のノードが子を持つかどうかをチェック
        
        Args:
            current_row: 現在の行要素
            
        Returns:
            bool: 子を持つ場合True
        """
        try:
            # 現在の行のレベルを取得
            current_level = self._extract_indent_level(current_row)
            if current_level is None:
                return False
            
            # 次の行を取得
            next_row = current_row.find_next_sibling('tr')
            if not next_row:
                return False
            
            # 次の行のレベルを取得
            next_level = self._extract_indent_level(next_row)
            if next_level is None:
                return False
            
            # 次の行のレベルが現在より深い場合、子を持つ
            return next_level > current_level
            
        except Exception:
            return False


def parse_class_hierarchy(soup) -> Dict[str, str]:
    """
    HTMLから階層構造を解析してクラスパスマップを生成
    
    Args:
        soup: BeautifulSoupオブジェクト
        
    Returns:
        Dict[str, str]: クラス名 -> 正しいフルパスのマッピング
    """
    parser = HierarchyParser()
    return parser.parse_hierarchy_from_html(soup)