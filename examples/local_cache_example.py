#!/usr/bin/env python3
"""
ローカルキャッシュ使用例

このスクリプトは、ローカルに保存されたHTMLファイルを使用して
名前空間とクラス情報を取得する方法を示します。
開発中にサーバーへの負荷を避けるために使用します。
"""

import asyncio
import logging
from pathlib import Path
import sys

# Add the parent directory to the path so we can import from src
sys.path.append(str(Path(__file__).parent.parent))

from src.scraper.namespace_scraper import NamespaceScraper
from src.utils.local_file_loader import LocalFileLoader, load_namespaces_html


async def example_local_cache_usage():
    """ローカルキャッシュを使用した基本例"""
    print("=== Local Cache Usage Example ===")
    
    # ログ設定
    logging.basicConfig(level=logging.INFO)
    
    # ローカルファイルローダーでファイル存在確認
    loader = LocalFileLoader()
    
    if not loader.file_exists("namespaces.html"):
        print("Error: namespaces.html not found in workspace/html_cache/")
        print("Please run the following command to download it:")
        print('curl -o workspace/html_cache/namespaces.html "https://rpgbakin.com/csreference/doc/ja/namespaces.html"')
        return None
    
    # ファイル情報を表示
    file_info = loader.get_file_info("namespaces.html")
    print(f"Using cached file: {file_info['filename']}")
    print(f"File size: {file_info['size_kb']:.1f} KB")
    
    # ローカルキャッシュを使用してスクレイピング
    scraper = NamespaceScraper(use_local_cache=True)
    
    try:
        namespaces = await scraper.scrape_namespaces()
        
        print(f"\nSuccessfully loaded {len(namespaces)} namespaces from local cache")
        
        # 結果の概要を表示
        total_classes = sum(len(ns.classes) for ns in namespaces)
        print(f"Total classes: {total_classes}")
        
        # 上位3つの名前空間を表示
        namespaces_with_classes = [ns for ns in namespaces if ns.classes]
        namespaces_with_classes.sort(key=lambda x: len(x.classes), reverse=True)
        
        print("\nTop namespaces by class count:")
        for i, namespace in enumerate(namespaces_with_classes[:3], 1):
            print(f"  {i}. {namespace.name}: {len(namespace.classes)} classes")
        
        return namespaces
        
    except Exception as e:
        print(f"Error during local cache scraping: {e}")
        return None


async def example_helper_function():
    """ヘルパー関数を使用した例"""
    print("\n=== Helper Function with Local Cache Example ===")
    
    try:
        # ヘルパー関数を使用してローカルキャッシュから読み込み
        html_content = load_namespaces_html()
        
        if html_content:
            print(f"Loaded HTML content: {len(html_content):,} characters")
            
            # HTMLの一部を表示
            lines = html_content.split('\n')
            print(f"HTML preview (first 5 lines):")
            for i, line in enumerate(lines[:5], 1):
                print(f"  {i}: {line[:80]}{'...' if len(line) > 80 else ''}")
        else:
            print("Failed to load HTML content from local cache")
            
    except Exception as e:
        print(f"Error using helper function: {e}")


def example_cache_management():
    """キャッシュ管理の例"""
    print("\n=== Cache Management Example ===")
    
    loader = LocalFileLoader()
    
    # キャッシュされているファイル一覧
    cached_files = loader.list_cached_files()
    print(f"Cached HTML files: {len(cached_files)}")
    
    for filename in cached_files:
        file_info = loader.get_file_info(filename)
        print(f"  - {filename}: {file_info['size_kb']:.1f} KB")
    
    # 特定ファイルの詳細情報
    if "namespaces.html" in cached_files:
        file_info = loader.get_file_info("namespaces.html")
        print(f"\nnamespaces.html details:")
        print(f"  Path: {file_info['path']}")
        print(f"  Size: {file_info['size_bytes']:,} bytes")
        print(f"  Modified: {file_info['modified_time']}")


async def example_performance_comparison():
    """パフォーマンス比較の例"""
    print("\n=== Performance Comparison Example ===")
    
    import time
    
    # ローカルキャッシュのテスト
    print("Testing local cache performance...")
    start_time = time.time()
    
    scraper_local = NamespaceScraper(use_local_cache=True)
    try:
        namespaces_local = await scraper_local.scrape_namespaces()
        local_time = time.time() - start_time
        print(f"Local cache: {len(namespaces_local)} namespaces in {local_time:.3f} seconds")
    except Exception as e:
        print(f"Local cache failed: {e}")
        return
    
    # リモートアクセスとの比較（実際にはアクセスしない）
    print("\nNote: Remote access would typically take 0.5-2.0 seconds")
    print(f"Local cache is significantly faster and doesn't burden the server!")


async def main():
    """メイン実行関数"""
    print("Local Cache Examples")
    print("=" * 50)
    
    # キャッシュ管理の例
    example_cache_management()
    
    # 基本的な使用例
    namespaces = await example_local_cache_usage()
    
    # ヘルパー関数の例
    await example_helper_function()
    
    # パフォーマンス比較の例
    await example_performance_comparison()
    
    print("\n" + "=" * 50)
    print("Local cache examples completed!")
    
    if namespaces:
        print(f"\nSuccessfully processed {len(namespaces)} namespaces from local cache")
        print("This approach avoids server load during development and testing.")


if __name__ == "__main__":
    asyncio.run(main())