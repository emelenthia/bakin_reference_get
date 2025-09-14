"""
非同期HTTPクライアント実装

aiohttpを使用した基本HTTPクライアントクラスで、
リトライ機構とレート制限を実装
"""

import asyncio
import logging
import hashlib
import re
from pathlib import Path
from typing import Optional, Dict, Any
from urllib.parse import urljoin, urlparse, quote
from datetime import datetime, timedelta

import aiohttp
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log
)


class HTTPClient:
    """
    非同期HTTPクライアント
    
    Features:
    - aiohttpを使用した非同期HTTP処理
    - 指数バックオフによるリトライ機構
    - レート制限（リクエスト間隔制御）
    - 適切なUser-Agentとヘッダー設定
    - タイムアウト制御
    """
    
    def __init__(
        self,
        base_url: str = "https://rpgbakin.com",
        timeout: int = 30,
        rate_limit_delay: float = 1.0,
        max_retries: int = 3,
        user_agent: str = "Bakin-Doc-Scraper/1.0",
        cache_dir: Optional[str] = None,
        cache_enabled: bool = True
    ):
        """
        HTTPクライアントを初期化
        
        Args:
            base_url: ベースURL
            timeout: リクエストタイムアウト（秒）
            rate_limit_delay: リクエスト間の遅延（秒）
            max_retries: 最大リトライ回数
            user_agent: User-Agentヘッダー
            cache_dir: キャッシュディレクトリ（デフォルトはworkspace/html_cache）
            cache_enabled: キャッシュ機能の有効/無効
        """
        self.base_url = base_url
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.rate_limit_delay = rate_limit_delay
        self.max_retries = max_retries
        self.user_agent = user_agent
        
        # キャッシュ設定
        self.cache_enabled = cache_enabled
        if cache_dir is None:
            # デフォルトのキャッシュディレクトリを設定
            current_dir = Path(__file__).parent.parent.parent
            self.cache_dir = current_dir / "workspace" / "html_cache"
        else:
            self.cache_dir = Path(cache_dir)
        
        # キャッシュディレクトリを作成
        if self.cache_enabled:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # セッション管理
        self._session: Optional[aiohttp.ClientSession] = None
        self._last_request_time: float = 0.0
        
        # ログ設定
        self.logger = logging.getLogger(__name__)
        
        # デフォルトヘッダー
        self.default_headers = {
            'User-Agent': self.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ja,en-US;q=0.7,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
    
    async def __aenter__(self):
        """非同期コンテキストマネージャーのエントリー"""
        await self._ensure_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """非同期コンテキストマネージャーの終了"""
        await self.close()
    
    async def _ensure_session(self):
        """セッションが存在することを確認し、必要に応じて作成"""
        if self._session is None or self._session.closed:
            connector = aiohttp.TCPConnector(
                limit=10,  # 同時接続数制限
                limit_per_host=5,  # ホスト毎の同時接続数制限
                ttl_dns_cache=300,  # DNS キャッシュTTL
                use_dns_cache=True,
            )
            
            self._session = aiohttp.ClientSession(
                connector=connector,
                timeout=self.timeout,
                headers=self.default_headers
            )
    
    async def close(self):
        """セッションを閉じる"""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None
    
    async def _apply_rate_limit(self):
        """レート制限を適用（リクエスト間隔制御）"""
        current_time = asyncio.get_event_loop().time()
        time_since_last_request = current_time - self._last_request_time
        
        if time_since_last_request < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last_request
            self.logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
            await asyncio.sleep(sleep_time)
        
        self._last_request_time = asyncio.get_event_loop().time()
    
    def _make_absolute_url(self, url: str) -> str:
        """相対URLを絶対URLに変換"""
        if url.startswith(('http://', 'https://')):
            return url
        return urljoin(self.base_url, url)
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((
            aiohttp.ClientError,
            aiohttp.ServerTimeoutError,
            asyncio.TimeoutError
        )),
        before_sleep=before_sleep_log(logging.getLogger(__name__), logging.WARNING)
    )
    async def _make_request_with_retry(
        self,
        method: str,
        url: str,
        **kwargs
    ) -> tuple[int, str]:
        """
        リトライ機構付きHTTPリクエスト実行
        
        Args:
            method: HTTPメソッド
            url: リクエストURL
            **kwargs: aiohttpのリクエストパラメータ
            
        Returns:
            tuple[int, str]: (ステータスコード, レスポンステキスト)
            
        Raises:
            aiohttp.ClientError: HTTPクライアントエラー
            asyncio.TimeoutError: タイムアウトエラー
        """
        await self._ensure_session()
        await self._apply_rate_limit()
        
        absolute_url = self._make_absolute_url(url)
        
        self.logger.debug(f"Making {method} request to: {absolute_url}")
        
        async with self._session.request(method, absolute_url, **kwargs) as response:
            # HTTPステータスコードをチェック
            if response.status >= 400:
                self.logger.warning(
                    f"HTTP {response.status} error for URL: {absolute_url}"
                )
                response.raise_for_status()
            
            # レスポンステキストを取得
            try:
                text = await response.text(encoding='utf-8')
                return response.status, text
            except UnicodeDecodeError as e:
                self.logger.error(f"Unicode decode error for URL {absolute_url}: {e}")
                # フォールバック: エラーを無視してデコード
                text = await response.text(encoding='utf-8', errors='ignore')
                self.logger.warning(f"Used fallback decoding for URL {absolute_url}")
                return response.status, text
    
    async def get(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        use_cache: bool = True,
        **kwargs
    ) -> str:
        """
        GETリクエストを実行してHTMLテキストを取得
        
        Args:
            url: リクエストURL
            params: クエリパラメータ
            headers: 追加ヘッダー
            use_cache: キャッシュを使用するかどうか
            **kwargs: その他のaiohttpパラメータ
            
        Returns:
            str: レスポンスのHTMLテキスト
            
        Raises:
            aiohttp.ClientError: HTTPエラー
            UnicodeDecodeError: 文字エンコーディングエラー
        """
        # パラメータがある場合はキャッシュを使用しない
        # （動的コンテンツの可能性があるため）
        if params:
            use_cache = False
        
        # キャッシュからの読み込みを試行
        if use_cache:
            cached_content = await self._load_from_cache(url)
            if cached_content is not None:
                self.logger.info(f"Using cached content for: {url}")
                return cached_content
        
        # キャッシュにない場合はWebから取得
        request_headers = self.default_headers.copy()
        if headers:
            request_headers.update(headers)
        
        self.logger.info(f"Fetching from web: {url}")
        status, text = await self._make_request_with_retry(
            'GET',
            url,
            params=params,
            headers=request_headers,
            **kwargs
        )
        
        # キャッシュに保存
        if use_cache:
            await self._save_to_cache(url, text)
        
        self.logger.debug(f"Successfully retrieved {len(text)} characters from {url}")
        return text
    
    async def get_status_and_text(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        use_cache: bool = True,
        **kwargs
    ) -> tuple[int, str]:
        """
        GETリクエストを実行してステータスコードとテキストを取得
        
        Args:
            url: リクエストURL
            params: クエリパラメータ
            headers: 追加ヘッダー
            use_cache: キャッシュを使用するかどうか
            **kwargs: その他のaiohttpパラメータ
            
        Returns:
            tuple[int, str]: (ステータスコード, レスポンステキスト)
        """
        # パラメータがある場合はキャッシュを使用しない
        if params:
            use_cache = False
        
        # キャッシュからの読み込みを試行
        if use_cache:
            cached_content = await self._load_from_cache(url)
            if cached_content is not None:
                self.logger.info(f"Using cached content for: {url}")
                return 200, cached_content  # キャッシュの場合は常に200を返す
        
        # キャッシュにない場合はWebから取得
        request_headers = self.default_headers.copy()
        if headers:
            request_headers.update(headers)
        
        self.logger.info(f"Fetching from web: {url}")
        status, text = await self._make_request_with_retry(
            'GET',
            url,
            params=params,
            headers=request_headers,
            **kwargs
        )
        
        # キャッシュに保存（成功時のみ）
        if use_cache and status == 200:
            await self._save_to_cache(url, text)
        
        return status, text
    
    def is_valid_url(self, url: str) -> bool:
        """
        URLの妥当性をチェック
        
        Args:
            url: チェック対象のURL
            
        Returns:
            bool: URLが妥当かどうか
        """
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False
    
    def _url_to_cache_path(self, url: str) -> Path:
        """
        URLを構造化されたキャッシュパスに変換
        
        Args:
            url: URL
            
        Returns:
            Path: 構造化されたキャッシュファイルパス
        """
        # 絶対URLに変換
        absolute_url = self._make_absolute_url(url)
        parsed = urlparse(absolute_url)
        path = parsed.path.strip('/')
        
        # namespaces.html の場合
        if 'namespaces.html' in path:
            return self.cache_dir / 'namespaces' / 'index.html'
        
        # クラスページの場合: class_yukar_1_1_common_1_1_resource_1_1_sound_resource.html
        if 'class_' in path and path.endswith('.html'):
            # class_yukar_1_1_common_1_1_resource_1_1_sound_resource.html から
            # classes/Yukar/Common/Resource/SoundResource.html に変換
            
            # ファイル名部分を抽出
            filename = Path(path).name  # class_yukar_1_1_common_1_1_resource_1_1_sound_resource.html
            
            if filename.startswith('class_'):
                # class_ を除去
                class_part = filename[6:]  # yukar_1_1_common_1_1_resource_1_1_sound_resource.html
                
                # .html を除去
                class_part = class_part[:-5]  # yukar_1_1_common_1_1_resource_1_1_sound_resource
                
                # _1_1_ を / に変換してパス構造を作成
                parts = class_part.split('_1_1_')
                
                if len(parts) > 1:
                    # ['yukar', 'common', 'resource', 'sound_resource'] のような形
                    # 最後の部分がクラス名、それ以前が名前空間
                    namespace_parts = parts[:-1]
                    class_name_part = parts[-1]
                    
                    # アンダースコアをキャメルケースに変換
                    def to_camel_case(snake_str):
                        components = snake_str.split('_')
                        return ''.join(word.capitalize() for word in components)
                    
                    # 名前空間部分を処理
                    namespace_dirs = [to_camel_case(part) for part in namespace_parts]
                    class_name = to_camel_case(class_name_part)
                    
                    # パスを構築
                    cache_path = self.cache_dir / 'classes'
                    for ns_dir in namespace_dirs:
                        cache_path = cache_path / ns_dir
                    
                    return cache_path / f'{class_name}.html'
        
        # その他のページの場合は元の方式
        safe_path = re.sub(r'[^\w.-]', '_', path)
        if not safe_path:
            safe_path = 'index.html'
        elif not safe_path.endswith('.html'):
            safe_path += '.html'
        
        return self.cache_dir / 'pages' / safe_path
    
    def _get_cache_file_path(self, url: str) -> Path:
        """
        URLのキャッシュファイルパスを取得
        
        Args:
            url: URL
            
        Returns:
            Path: キャッシュファイルパス
        """
        return self._url_to_cache_path(url)
    
    def _is_cache_valid(self, cache_file: Path) -> bool:
        """
        キャッシュファイルが存在するかどうかをチェック
        
        Args:
            cache_file: キャッシュファイルパス
            
        Returns:
            bool: キャッシュファイルが存在するかどうか
        """
        return cache_file.exists()
    
    async def _load_from_cache(self, url: str) -> Optional[str]:
        """
        キャッシュからHTMLを読み込み
        
        Args:
            url: URL
            
        Returns:
            Optional[str]: キャッシュされたHTMLコンテンツ（無い場合はNone）
        """
        if not self.cache_enabled:
            return None
        
        cache_file = self._get_cache_file_path(url)
        
        if not self._is_cache_valid(cache_file):
            return None
        
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            self.logger.debug(f"Loaded content from cache: {cache_file}")
            return content
        
        except Exception as e:
            self.logger.warning(f"Failed to load cache file {cache_file}: {e}")
            return None
    
    async def _save_to_cache(self, url: str, content: str) -> None:
        """
        HTMLをキャッシュに保存
        
        Args:
            url: URL
            content: HTMLコンテンツ
        """
        if not self.cache_enabled:
            return
        
        cache_file = self._get_cache_file_path(url)
        
        try:
            # キャッシュディレクトリが存在することを確認
            cache_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.logger.debug(f"Saved content to cache: {cache_file}")
        
        except Exception as e:
            self.logger.warning(f"Failed to save cache file {cache_file}: {e}")
    
    def get_cache_info(self) -> Dict[str, Any]:
        """
        キャッシュ情報を取得
        
        Returns:
            Dict[str, Any]: キャッシュ情報
        """
        if not self.cache_enabled:
            return {"cache_enabled": False}
        
        # すべての.htmlファイルを再帰的に検索
        cache_files = list(self.cache_dir.glob("**/*.html"))
        total_size = sum(f.stat().st_size for f in cache_files if f.is_file())
        
        existing_files = [f for f in cache_files if f.is_file()]
        
        # 構造化された情報も含める
        structure_info = {}
        if (self.cache_dir / 'classes').exists():
            structure_info['classes'] = len(list((self.cache_dir / 'classes').glob("**/*.html")))
        if (self.cache_dir / 'namespaces').exists():
            structure_info['namespaces'] = len(list((self.cache_dir / 'namespaces').glob("**/*.html")))
        if (self.cache_dir / 'pages').exists():
            structure_info['pages'] = len(list((self.cache_dir / 'pages').glob("**/*.html")))
        
        return {
            "cache_enabled": True,
            "cache_dir": str(self.cache_dir),
            "total_files": len(existing_files),
            "total_size_mb": total_size / (1024 * 1024),
            "structure": structure_info
        }