"""
HTTPクライアントの使用例

このスクリプトは、実装したHTTPクライアントの基本的な使用方法を示します。
"""

import asyncio
import sys
import os

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.scraper import HTTPClient


async def example_basic_usage():
    """基本的な使用例"""
    print("=== HTTPクライアント基本使用例 ===\n")
    
    # HTTPクライアントを作成（コンテキストマネージャーとして使用）
    async with HTTPClient(rate_limit_delay=0.5) as client:
        print(f"ベースURL: {client.base_url}")
        print(f"タイムアウト: {client.timeout.total}秒")
        print(f"レート制限: {client.rate_limit_delay}秒間隔")
        print(f"最大リトライ: {client.max_retries}回")
        print(f"User-Agent: {client.user_agent}")
        
        # URL変換の例
        print(f"\nURL変換例:")
        relative_url = "/csreference/doc/ja/namespaces.html"
        absolute_url = client._make_absolute_url(relative_url)
        print(f"相対URL: {relative_url}")
        print(f"絶対URL: {absolute_url}")
        
        # URL妥当性チェックの例
        print(f"\nURL妥当性チェック例:")
        test_urls = [
            "https://rpgbakin.com/csreference/doc/ja/namespaces.html",
            "/relative/path",
            "not-a-valid-url",
            ""
        ]
        
        for url in test_urls:
            is_valid = client.is_valid_url(url)
            print(f"'{url}' -> {'有効' if is_valid else '無効'}")


async def example_configuration():
    """設定のカスタマイズ例"""
    print("\n=== HTTPクライアント設定カスタマイズ例 ===\n")
    
    # カスタム設定でHTTPクライアントを作成
    custom_client = HTTPClient(
        base_url="https://example.com",
        timeout=15,  # 15秒タイムアウト
        rate_limit_delay=2.0,  # 2秒間隔
        max_retries=5,  # 最大5回リトライ
        user_agent="Custom-Scraper/2.0"
    )
    
    print("カスタム設定:")
    print(f"  ベースURL: {custom_client.base_url}")
    print(f"  タイムアウト: {custom_client.timeout.total}秒")
    print(f"  レート制限: {custom_client.rate_limit_delay}秒")
    print(f"  最大リトライ: {custom_client.max_retries}回")
    print(f"  User-Agent: {custom_client.user_agent}")
    
    await custom_client.close()


async def example_error_handling():
    """エラーハンドリングの例"""
    print("\n=== エラーハンドリング例 ===\n")
    
    async with HTTPClient() as client:
        # 無効なURLでのリクエスト例
        invalid_urls = [
            "https://nonexistent-domain-12345.com",
            "/invalid/path/that/does/not/exist"
        ]
        
        for url in invalid_urls:
            try:
                print(f"リクエスト試行: {url}")
                # 実際のリクエストは行わず、URL処理のみ確認
                absolute_url = client._make_absolute_url(url)
                is_valid = client.is_valid_url(absolute_url)
                print(f"  絶対URL: {absolute_url}")
                print(f"  妥当性: {'有効' if is_valid else '無効'}")
                
                if not is_valid:
                    print(f"  ⚠ 無効なURLのため、リクエストをスキップ")
                else:
                    print(f"  ℹ 有効なURLですが、実際のリクエストは行いません")
                    
            except Exception as e:
                print(f"  ✗ エラー: {e}")
            
            print()


async def main():
    """メイン実行関数"""
    print("HTTPクライアント使用例デモ\n")
    
    try:
        await example_basic_usage()
        await example_configuration()
        await example_error_handling()
        
        print("=== デモ完了 ===")
        print("HTTPクライアントが正常に実装され、使用可能です。")
        
    except Exception as e:
        print(f"デモ実行エラー: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())