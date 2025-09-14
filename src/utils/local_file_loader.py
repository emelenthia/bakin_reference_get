"""
ローカルファイル読み込みユーティリティ

開発中にサーバーへの負荷を避けるため、
ローカルに保存されたHTMLファイルを読み込むためのユーティリティ
"""

import logging
from pathlib import Path
from typing import Optional
from urllib.parse import urljoin


class LocalFileLoader:
    """
    ローカルHTMLファイル読み込みクラス
    
    workspace/html_cache/ ディレクトリからHTMLファイルを読み込み、
    開発中のテストやデバッグに使用します。
    """
    
    def __init__(self, cache_dir: str = "workspace/html_cache"):
        """
        LocalFileLoaderを初期化
        
        Args:
            cache_dir: HTMLキャッシュディレクトリのパス
        """
        self.cache_dir = Path(cache_dir)
        self.logger = logging.getLogger(__name__)
        
        # キャッシュディレクトリが存在しない場合は作成
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def load_html_file(self, filename: str) -> Optional[str]:
        """
        ローカルHTMLファイルを読み込み
        
        Args:
            filename: 読み込むHTMLファイル名
            
        Returns:
            Optional[str]: HTMLコンテンツ（ファイルが存在しない場合はNone）
        """
        file_path = self.cache_dir / filename
        
        if not file_path.exists():
            self.logger.error(f"HTML file not found: {file_path}")
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            self.logger.info(f"Loaded HTML file: {file_path} ({len(content):,} characters)")
            return content
            
        except Exception as e:
            self.logger.error(f"Error reading HTML file {file_path}: {e}")
            return None
    
    def save_html_file(self, filename: str, content: str) -> bool:
        """
        HTMLコンテンツをローカルファイルに保存
        
        Args:
            filename: 保存するファイル名
            content: HTMLコンテンツ
            
        Returns:
            bool: 保存が成功した場合True
        """
        file_path = self.cache_dir / filename
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.logger.info(f"Saved HTML file: {file_path} ({len(content):,} characters)")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving HTML file {file_path}: {e}")
            return False
    
    def list_cached_files(self) -> list[str]:
        """
        キャッシュされているHTMLファイルの一覧を取得
        
        Returns:
            list[str]: HTMLファイル名のリスト
        """
        if not self.cache_dir.exists():
            return []
        
        html_files = [f.name for f in self.cache_dir.glob("*.html")]
        self.logger.debug(f"Found {len(html_files)} cached HTML files")
        return sorted(html_files)
    
    def get_file_info(self, filename: str) -> Optional[dict]:
        """
        ファイル情報を取得
        
        Args:
            filename: ファイル名
            
        Returns:
            Optional[dict]: ファイル情報（存在しない場合はNone）
        """
        file_path = self.cache_dir / filename
        
        if not file_path.exists():
            return None
        
        stat = file_path.stat()
        return {
            'filename': filename,
            'path': str(file_path),
            'size_bytes': stat.st_size,
            'size_kb': stat.st_size / 1024,
            'modified_time': stat.st_mtime
        }
    
    def file_exists(self, filename: str) -> bool:
        """
        ファイルが存在するかチェック
        
        Args:
            filename: ファイル名
            
        Returns:
            bool: ファイルが存在する場合True
        """
        return (self.cache_dir / filename).exists()


# 便利な関数として直接使用できるヘルパー関数
def load_namespaces_html() -> Optional[str]:
    """
    namespaces.htmlファイルを読み込み
    
    Returns:
        Optional[str]: HTMLコンテンツ
    """
    loader = LocalFileLoader()
    return loader.load_html_file("namespaces.html")


def save_html_to_cache(filename: str, content: str) -> bool:
    """
    HTMLコンテンツをキャッシュに保存
    
    Args:
        filename: ファイル名
        content: HTMLコンテンツ
        
    Returns:
        bool: 保存が成功した場合True
    """
    loader = LocalFileLoader()
    return loader.save_html_file(filename, content)