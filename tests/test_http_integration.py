"""
HTTPクライアントの統合テスト
実際のHTTPリクエストを行うテスト
"""

import asyncio
import sys
import os

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.scraper.http_client import HTTPClient


async def test_real_http_request():
    """実際のHTTPリクエストのテスト"""
    print("HTTPクライアント統合テスト開始...")
    
    # テスト用の軽量なHTTPサービスを使用
    test_url = "https://httpbin.org/get"
    
    async with HTTPClient(rate_limit_delay=0.5) as client:
        try:
            print(f"リクエスト送信: {test_url}")
            
            # GETリクエストテスト
            response_text = await client.get(test_url)
            
            print(f"レスポンス受信: {len(response_text)} 文字")
            print("✓ HTTPリクエスト成功")
            
            # レスポンスにJSONが含まれていることを確認
            if '"url"' in response_text and 'httpbin.org' in response_text:
                print("✓ レスポンス内容確認成功")
            else:
                print("⚠ レスポンス内容が期待と異なります")
                
        except Exception as e:
            print(f"✗ HTTPリクエストエラー: {e}")
            return False
    
    print("HTTPクライアント統合テスト完了")
    return True


async def test_bakin_site_access():
    """Bakinサイトへのアクセステスト"""
    print("\nBakinサイトアクセステスト開始...")
    
    bakin_url = "/csreference/doc/ja/namespaces.html"
    
    async with HTTPClient() as client:
        try:
            print(f"Bakinサイトにリクエスト送信: {client._make_absolute_url(bakin_url)}")
            
            # Bakinサイトへのリクエスト
            response_text = await client.get(bakin_url)
            
            print(f"レスポンス受信: {len(response_text)} 文字")
            
            # HTMLページの基本的な内容をチェック
            if '<html' in response_text.lower() and 'namespace' in response_text.lower():
                print("✓ Bakinサイトアクセス成功")
                print("✓ 名前空間ページの内容確認成功")
                return True
            else:
                print("⚠ ページ内容が期待と異なります")
                return False
                
        except Exception as e:
            print(f"✗ Bakinサイトアクセスエラー: {e}")
            return False


async def main():
    """メインテスト実行"""
    print("=== HTTPクライアント統合テスト ===\n")
    
    # 基本HTTPリクエストテスト
    success1 = await test_real_http_request()
    
    # Bakinサイトアクセステスト
    success2 = await test_bakin_site_access()
    
    print(f"\n=== テスト結果 ===")
    print(f"基本HTTPリクエスト: {'成功' if success1 else '失敗'}")
    print(f"Bakinサイトアクセス: {'成功' if success2 else '失敗'}")
    
    if success1 and success2:
        print("✓ 全てのテストが成功しました")
    else:
        print("⚠ 一部のテストが失敗しました")


if __name__ == "__main__":
    asyncio.run(main())