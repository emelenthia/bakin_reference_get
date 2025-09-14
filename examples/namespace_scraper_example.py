#!/usr/bin/env python3
"""
名前空間スクレイパーの使用例

このスクリプトは、NamespaceScraperクラスの基本的な使用方法を示します。
"""

import asyncio
import json
import logging
from pathlib import Path

import sys
from pathlib import Path

# Add the parent directory to the path so we can import from src
sys.path.append(str(Path(__file__).parent.parent))

from src.scraper.namespace_scraper import NamespaceScraper, scrape_bakin_namespaces


async def example_basic_usage():
    """基本的な使用例"""
    print("=== Basic Namespace Scraper Example ===")
    
    # ログ設定
    logging.basicConfig(level=logging.INFO)
    
    # スクレイパーを作成
    scraper = NamespaceScraper()
    
    try:
        # 名前空間情報を取得
        namespaces = await scraper.scrape_namespaces()
        
        print(f"\nSuccessfully scraped {len(namespaces)} namespaces")
        
        # 結果の概要を表示
        for namespace in namespaces[:5]:  # 最初の5つの名前空間を表示
            print(f"\nNamespace: {namespace.name}")
            print(f"  URL: {namespace.url}")
            print(f"  Classes: {len(namespace.classes)}")
            
            # 最初の3つのクラスを表示
            for class_info in namespace.classes[:3]:
                print(f"    - {class_info.name} ({class_info.full_name})")
            
            if len(namespace.classes) > 3:
                print(f"    ... and {len(namespace.classes) - 3} more classes")
        
        if len(namespaces) > 5:
            print(f"\n... and {len(namespaces) - 5} more namespaces")
        
        return namespaces
        
    except Exception as e:
        print(f"Error during scraping: {e}")
        return []


async def example_helper_function():
    """ヘルパー関数の使用例"""
    print("\n=== Helper Function Example ===")
    
    try:
        # ヘルパー関数を使用
        namespaces = await scrape_bakin_namespaces()
        
        print(f"Scraped {len(namespaces)} namespaces using helper function")
        
        # 統計情報を表示
        total_classes = sum(len(ns.classes) for ns in namespaces)
        print(f"Total classes across all namespaces: {total_classes}")
        
        # 最大のクラス数を持つ名前空間を検索
        if namespaces:
            largest_namespace = max(namespaces, key=lambda ns: len(ns.classes))
            print(f"Largest namespace: {largest_namespace.name} with {len(largest_namespace.classes)} classes")
        
        return namespaces
        
    except Exception as e:
        print(f"Error using helper function: {e}")
        return []


async def example_save_to_file(namespaces):
    """ファイル保存の例"""
    print("\n=== Save to File Example ===")
    
    if not namespaces:
        print("No namespaces to save")
        return
    
    # 出力ディレクトリを作成
    output_dir = Path("examples/output")
    output_dir.mkdir(exist_ok=True)
    
    # JSONファイルに保存
    output_file = output_dir / "example_namespaces.json"
    
    json_data = {
        "metadata": {
            "description": "Example output from namespace scraper",
            "totalNamespaces": len(namespaces),
            "totalClasses": sum(len(ns.classes) for ns in namespaces)
        },
        "namespaces": [ns.to_dict() for ns in namespaces]
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)
    
    print(f"Saved namespaces to: {output_file}")
    print(f"File size: {output_file.stat().st_size} bytes")


async def example_filter_namespaces(namespaces):
    """名前空間のフィルタリング例"""
    print("\n=== Namespace Filtering Example ===")
    
    if not namespaces:
        print("No namespaces to filter")
        return
    
    # Yukarで始まる名前空間をフィルタ
    yukar_namespaces = [ns for ns in namespaces if ns.name.startswith('Yukar')]
    print(f"Yukar namespaces: {len(yukar_namespaces)}")
    
    # クラスを持つ名前空間のみをフィルタ
    namespaces_with_classes = [ns for ns in namespaces if ns.classes]
    print(f"Namespaces with classes: {len(namespaces_with_classes)}")
    
    # 特定のクラス数以上の名前空間をフィルタ
    large_namespaces = [ns for ns in namespaces if len(ns.classes) >= 10]
    print(f"Namespaces with 10+ classes: {len(large_namespaces)}")
    
    # 結果を表示
    for ns in large_namespaces:
        print(f"  - {ns.name}: {len(ns.classes)} classes")


async def main():
    """メイン実行関数"""
    print("Namespace Scraper Examples")
    print("=" * 50)
    
    # 基本的な使用例
    namespaces = await example_basic_usage()
    
    # ヘルパー関数の例（既にデータがある場合はスキップ）
    if not namespaces:
        namespaces = await example_helper_function()
    
    # ファイル保存の例
    await example_save_to_file(namespaces)
    
    # フィルタリングの例
    await example_filter_namespaces(namespaces)
    
    print("\n" + "=" * 50)
    print("Examples completed!")


if __name__ == "__main__":
    asyncio.run(main())