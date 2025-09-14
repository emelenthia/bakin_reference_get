"""
HTTPクライアントのテスト
"""

import asyncio
import sys
import os

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.scraper.http_client import HTTPClient


def test_basic_functionality():
    """基本機能のテスト（pytest不要版）"""
    
    def test_init():
        """初期化のテスト"""
        client = HTTPClient(
            base_url="https://test.com",
            timeout=15,
            rate_limit_delay=2.0,
            max_retries=5,
            user_agent="Test-Agent/1.0"
        )
        
        assert client.base_url == "https://test.com"
        assert client.timeout.total == 15
        assert client.rate_limit_delay == 2.0
        assert client.max_retries == 5
        assert client.user_agent == "Test-Agent/1.0"
        assert client._session is None
        print("✓ 初期化テスト成功")
    
    def test_make_absolute_url():
        """URL変換のテスト"""
        client = HTTPClient(base_url="https://example.com")
        
        # 絶対URLはそのまま
        absolute_url = "https://other.com/path"
        assert client._make_absolute_url(absolute_url) == absolute_url
        
        # 相対URLは絶対URLに変換
        relative_url = "/path/to/page"
        expected = "https://example.com/path/to/page"
        assert client._make_absolute_url(relative_url) == expected
        print("✓ URL変換テスト成功")
    
    def test_is_valid_url():
        """URL妥当性チェックのテスト"""
        client = HTTPClient()
        
        # 有効なURL
        assert client.is_valid_url("https://example.com") is True
        assert client.is_valid_url("http://test.org/path") is True
        
        # 無効なURL
        assert client.is_valid_url("not-a-url") is False
        assert client.is_valid_url("") is False
        assert client.is_valid_url("ftp://example.com") is True  # スキームがあれば有効
        print("✓ URL妥当性チェックテスト成功")
    
    # テスト実行
    test_init()
    test_make_absolute_url()
    test_is_valid_url()
    print("基本機能テスト完了")


if __name__ == "__main__":
    # 簡単な動作確認
    async def test_basic_functionality():
        """基本機能の動作確認"""
        client = HTTPClient(rate_limit_delay=0.1)
        
        # URL変換テスト
        print("URL変換テスト:")
        print(f"相対URL: {client._make_absolute_url('/test')}")
        print(f"絶対URL: {client._make_absolute_url('https://other.com/test')}")
        
        # URL妥当性テスト
        print("\nURL妥当性テスト:")
        print(f"有効URL: {client.is_valid_url('https://example.com')}")
        print(f"無効URL: {client.is_valid_url('not-a-url')}")
        
        # レート制限テスト
        print("\nレート制限テスト:")
        import time
        start = time.time()
        await client._apply_rate_limit()
        await client._apply_rate_limit()
        end = time.time()
        print(f"2回のリクエスト間隔: {end - start:.2f}秒")
        
        await client.close()
        print("\nHTTPクライアントの基本機能テスト完了")
    
    # テスト実行
    asyncio.run(test_basic_functionality())