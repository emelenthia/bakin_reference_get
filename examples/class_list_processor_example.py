#!/usr/bin/env python3
"""
クラス一覧処理の使用例

このスクリプトは、ClassListProcessorクラスの基本的な使用方法を示します。
名前空間スクレイパーから取得したデータを構造化し、
簡易的なJSON形式でクラス一覧を出力します。
"""

import asyncio
import json
import logging
from pathlib import Path
import sys

# Add the parent directory to the path so we can import from src
sys.path.append(str(Path(__file__).parent.parent))

from src.scraper.namespace_scraper import NamespaceScraper
from src.processor.class_list_processor import ClassListProcessor, process_namespaces_to_class_list


async def example_basic_usage():
    """基本的な使用例"""
    print("=== Basic Class List Processor Example ===")
    
    # ログ設定
    logging.basicConfig(level=logging.INFO)
    
    # 名前空間データを取得
    print("Scraping namespace data...")
    scraper = NamespaceScraper()
    namespaces = await scraper.scrape_namespaces()
    
    if not namespaces:
        print("No namespace data available. Exiting.")
        return None
    
    print(f"Scraped {len(namespaces)} namespaces")
    
    # クラス一覧処理を実行
    print("\nProcessing class list...")
    processor = ClassListProcessor()
    
    output_file = "examples/output/classes_list_basic.json"
    class_list_data = processor.process_namespaces_to_class_list(
        namespaces=namespaces,
        output_file=output_file,
        show_progress=True
    )
    
    # 結果の概要を表示
    metadata = class_list_data["metadata"]
    print(f"\nProcessing completed!")
    print(f"  Output file: {output_file}")
    print(f"  Total namespaces: {metadata['total_namespaces']}")
    print(f"  Namespaces with classes: {metadata['namespaces_with_classes']}")
    print(f"  Total classes: {metadata['total_classes']}")
    
    return class_list_data


async def example_helper_function():
    """ヘルパー関数の使用例"""
    print("\n=== Helper Function Example ===")
    
    # 名前空間データを取得
    print("Scraping namespace data...")
    scraper = NamespaceScraper()
    namespaces = await scraper.scrape_namespaces()
    
    if not namespaces:
        print("No namespace data available. Exiting.")
        return None
    
    # ヘルパー関数を使用
    print("Processing with helper function...")
    output_file = "examples/output/classes_list_helper.json"
    
    class_list_data = process_namespaces_to_class_list(
        namespaces=namespaces,
        output_file=output_file,
        show_progress=True
    )
    
    print(f"Helper function completed! Output: {output_file}")
    return class_list_data


def example_analyze_class_list(class_list_data):
    """クラス一覧データの分析例"""
    print("\n=== Class List Analysis Example ===")
    
    if not class_list_data:
        print("No class list data to analyze")
        return
    
    namespaces = class_list_data["namespaces"]
    
    # 統計情報を計算
    namespace_stats = []
    for namespace in namespaces:
        stats = {
            "name": namespace["name"],
            "class_count": namespace["class_count"],
            "has_description": bool(namespace.get("description")),
            "classes_with_description": sum(1 for cls in namespace["classes"] if cls.get("description"))
        }
        namespace_stats.append(stats)
    
    # 最大のクラス数を持つ名前空間
    largest_namespace = max(namespace_stats, key=lambda x: x["class_count"])
    print(f"Largest namespace: {largest_namespace['name']} ({largest_namespace['class_count']} classes)")
    
    # 説明を持つ名前空間の数
    namespaces_with_desc = sum(1 for stats in namespace_stats if stats["has_description"])
    print(f"Namespaces with descriptions: {namespaces_with_desc}/{len(namespace_stats)}")
    
    # クラス数の分布
    class_counts = [stats["class_count"] for stats in namespace_stats]
    if class_counts:
        avg_classes = sum(class_counts) / len(class_counts)
        print(f"Average classes per namespace: {avg_classes:.1f}")
        print(f"Class count range: {min(class_counts)} - {max(class_counts)}")
    
    # 上位5つの名前空間を表示
    top_namespaces = sorted(namespace_stats, key=lambda x: x["class_count"], reverse=True)[:5]
    print("\nTop 5 namespaces by class count:")
    for i, stats in enumerate(top_namespaces, 1):
        print(f"  {i}. {stats['name']}: {stats['class_count']} classes")


def example_filter_and_export(class_list_data):
    """フィルタリングとエクスポートの例"""
    print("\n=== Filter and Export Example ===")
    
    if not class_list_data:
        print("No class list data to filter")
        return
    
    # Yukarで始まる名前空間のみをフィルタ
    yukar_namespaces = [
        ns for ns in class_list_data["namespaces"] 
        if ns["name"].startswith("Yukar")
    ]
    
    if yukar_namespaces:
        # フィルタされたデータを作成
        filtered_data = {
            "metadata": {
                **class_list_data["metadata"],
                "filter_applied": "Yukar namespaces only",
                "original_namespace_count": class_list_data["metadata"]["total_namespaces"],
                "filtered_namespace_count": len(yukar_namespaces),
                "filtered_class_count": sum(ns["class_count"] for ns in yukar_namespaces)
            },
            "namespaces": yukar_namespaces
        }
        
        # フィルタされたデータを保存
        output_file = "examples/output/classes_list_yukar_only.json"
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(filtered_data, f, ensure_ascii=False, indent=2)
        
        print(f"Filtered Yukar namespaces: {len(yukar_namespaces)}")
        print(f"Total classes in Yukar namespaces: {filtered_data['metadata']['filtered_class_count']}")
        print(f"Saved filtered data to: {output_file}")
    else:
        print("No Yukar namespaces found")


def example_validate_urls(class_list_data):
    """URL検証の例"""
    print("\n=== URL Validation Example ===")
    
    if not class_list_data:
        print("No class list data to validate")
        return
    
    total_classes = 0
    valid_urls = 0
    invalid_urls = []
    
    for namespace in class_list_data["namespaces"]:
        for class_info in namespace["classes"]:
            total_classes += 1
            url = class_info.get("url", "")
            
            if url and url.startswith("http"):
                valid_urls += 1
            else:
                invalid_urls.append({
                    "namespace": namespace["name"],
                    "class": class_info["name"],
                    "url": url
                })
    
    print(f"URL validation results:")
    print(f"  Total classes: {total_classes}")
    print(f"  Valid URLs: {valid_urls}")
    print(f"  Invalid URLs: {len(invalid_urls)}")
    
    if invalid_urls:
        print("\nFirst 5 invalid URLs:")
        for i, invalid in enumerate(invalid_urls[:5], 1):
            print(f"  {i}. {invalid['namespace']}.{invalid['class']}: '{invalid['url']}'")


async def main():
    """メイン実行関数"""
    print("Class List Processor Examples")
    print("=" * 50)
    
    # 出力ディレクトリを作成
    output_dir = Path("examples/output")
    output_dir.mkdir(exist_ok=True)
    
    # 基本的な使用例
    class_list_data = await example_basic_usage()
    
    # ヘルパー関数の例（既にデータがある場合はスキップ）
    if not class_list_data:
        class_list_data = await example_helper_function()
    
    # データ分析の例
    example_analyze_class_list(class_list_data)
    
    # フィルタリングとエクスポートの例
    example_filter_and_export(class_list_data)
    
    # URL検証の例
    example_validate_urls(class_list_data)
    
    print("\n" + "=" * 50)
    print("Examples completed!")


if __name__ == "__main__":
    asyncio.run(main())