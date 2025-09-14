"""
HTTPクライアントの簡単なテスト
ネットワークアクセスなしでの基本機能テスト
"""

import asyncio
import sys
import os

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.scraper.http_client import HTTPClient


def test_initialization():
    """初期化テスト"""
    print("=== HTTPクライアント初期化テスト ===")
    
    # デフォルト設定でのテスト
    client1 = HTTPClient()
    assert client1.base_url == "https://rpgbakin.com"
    assert client1.timeout.total == 30
    assert client1.rate_limit_delay == 1.0
    assert client1.max_retries == 3
    print("✓ デフォルト初期化成功")
    
    # カスタム設定でのテスト
    client2 = HTTPClient(
        base_url="https://example.com",
        timeout=15,
        rate_limit_delay=0.5,
        max_retries=2,
        user_agent="Test-Agent/1.0"
    )
    assert client2.base_url == "https://example.com"
    assert client2.timeout.total == 15
    assert client2.rate_limit_delay == 0.5
    assert client2.max_retries == 2
    assert client2.user_agent == "Test-Agent/1.0"
    print("✓ カスタム初期化成功")


def test_url_handling():
    """URL処理テスト"""
    print("\n=== URL処理テスト ===")
    
    client = HTTPClient(base_url="https://example.com")
    
    # 絶対URL変換テスト
    test_cases = [
        ("https://other.com/path", "https://other.com/path"),  # 絶対URLはそのまま
        ("/relative/path", "https://example.com/relative/path"),  # 相対URLは変換
        ("relative/path", "https://example.com/relative/path"),  # 相対URLは変換
        ("", "https://example.com"),  # 空文字列
    ]
    
    for input_url, expected in test_cases:
        result = client._make_absolute_url(input_url)
        assert result == expected, f"Expected {expected}, got {result}"
        print(f"✓ URL変換: '{input_url}' -> '{result}'")
    
    # URL妥当性チェックテスト
    valid_urls = [
        "https://example.com",
        "http://test.org/path",
        "ftp://files.example.com",
    ]
    
    invalid_urls = [
        "not-a-url",
        "",
        "just-text",
        "://missing-scheme",
    ]
    
    for url in valid_urls:
        assert client.is_valid_url(url), f"URL should be valid: {url}"
        print(f"✓ 有効URL: {url}")
    
    for url in invalid_urls:
        assert not client.is_valid_url(url), f"URL should be invalid: {url}"
        print(f"✓ 無効URL: {url}")


async def test_rate_limiting():
    """レート制限テスト"""
    print("\n=== レート制限テスト ===")
    
    import time
    
    client = HTTPClient(rate_limit_delay=0.1)  # 100ms間隔
    
    # 最初のリクエスト
    start_time = time.time()
    await client._apply_rate_limit()
    first_time = time.time()
    
    # 2回目のリクエスト（遅延されるはず）
    await client._apply_rate_limit()
    second_time = time.time()
    
    # 時間差をチェック
    time_diff = second_time - first_time
    print(f"リクエスト間隔: {time_diff:.3f}秒")
    
    # レート制限が適用されていることを確認（多少の誤差を許容）
    assert time_diff >= 0.08, f"Rate limiting not working: {time_diff}"
    print("✓ レート制限が正常に動作")
    
    await client.close()


async def test_session_management():
    """セッション管理テスト"""
    print("\n=== セッション管理テスト ===")
    
    client = HTTPClient()
    
    # 初期状態ではセッションは None
    assert client._session is None
    print("✓ 初期状態でセッションなし")
    
    # セッション作成
    await client._ensure_session()
    assert client._session is not None
    assert not client._session.closed
    print("✓ セッション作成成功")
    
    # セッション閉じる
    await client.close()
    assert client._session is None or client._session.closed
    print("✓ セッション終了成功")
    
    # コンテキストマネージャーテスト
    async with HTTPClient() as ctx_client:
        assert ctx_client._session is not None
        assert not ctx_client._session.closed
        print("✓ コンテキストマネージャーでセッション作成")
    
    # コンテキスト終了後はセッションが閉じられる
    assert ctx_client._session is None or ctx_client._session.closed
    print("✓ コンテキスト終了でセッション閉じる")


async def main():
    """メインテスト実行"""
    print("HTTPクライアント基本機能テスト開始\n")
    
    try:
        # 同期テスト
        test_initialization()
        test_url_handling()
        
        # 非同期テスト
        await test_rate_limiting()
        await test_session_management()
        
        print("\n=== テスト結果 ===")
        print("✓ 全てのテストが成功しました")
        
    except Exception as e:
        print(f"\n✗ テストエラー: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())