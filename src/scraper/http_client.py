"""
非同期HTTPクライアント実装

aiohttpを使用した基本HTTPクライアントクラスで、
リトライ機構とレート制限を実装
"""

import asyncio
import logging
from typing import Optional, Dict, Any
from urllib.parse import urljoin, urlparse

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
        user_agent: str = "Bakin-Doc-Scraper/1.0"
    ):
        """
        HTTPクライアントを初期化
        
        Args:
            base_url: ベースURL
            timeout: リクエストタイムアウト（秒）
            rate_limit_delay: リクエスト間の遅延（秒）
            max_retries: 最大リトライ回数
            user_agent: User-Agentヘッダー
        """
        self.base_url = base_url
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.rate_limit_delay = rate_limit_delay
        self.max_retries = max_retries
        self.user_agent = user_agent
        
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
        **kwargs
    ) -> str:
        """
        GETリクエストを実行してHTMLテキストを取得
        
        Args:
            url: リクエストURL
            params: クエリパラメータ
            headers: 追加ヘッダー
            **kwargs: その他のaiohttpパラメータ
            
        Returns:
            str: レスポンスのHTMLテキスト
            
        Raises:
            aiohttp.ClientError: HTTPエラー
            UnicodeDecodeError: 文字エンコーディングエラー
        """
        request_headers = self.default_headers.copy()
        if headers:
            request_headers.update(headers)
        
        status, text = await self._make_request_with_retry(
            'GET',
            url,
            params=params,
            headers=request_headers,
            **kwargs
        )
        
        self.logger.debug(f"Successfully retrieved {len(text)} characters from {url}")
        return text
    
    async def get_status_and_text(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> tuple[int, str]:
        """
        GETリクエストを実行してステータスコードとテキストを取得
        
        Args:
            url: リクエストURL
            params: クエリパラメータ
            headers: 追加ヘッダー
            **kwargs: その他のaiohttpパラメータ
            
        Returns:
            tuple[int, str]: (ステータスコード, レスポンステキスト)
        """
        request_headers = self.default_headers.copy()
        if headers:
            request_headers.update(headers)
        
        return await self._make_request_with_retry(
            'GET',
            url,
            params=params,
            headers=request_headers,
            **kwargs
        )
    
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