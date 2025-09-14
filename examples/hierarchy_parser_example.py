#!/usr/bin/env python3
"""
階層構造解析の使用例

このスクリプトは、HierarchyParserクラスの基本的な使用方法を示します。
正確なクラスパスの生成をテストします。
"""

import asyncio
import logging
from pathlib import Path
import sys

# Add the parent directory to the path so we can import from src
sys.path.append(str(Path(__file__).parent.parent))

from src.utils.local_file_loader import LocalFileLoader
from src.utils.html_parser import HTMLParser
from src.utils.hierarchy_parser import HierarchyParser


def example_hierarchy_parsing():
    """階層構造解析の基本例"""
    print("=== Hierarchy Parser Example ===")
    
    # ログ設定
    logging.basicConfig(level=logging.INFO)
    
    # ローカルファイルから読み込み
    loader = LocalFileLoader()
    html_content = loader.load_html_file("namespaces.html")
    
    if not html_content:
        print("Error: namespaces.html not found. Please run:")
        print('curl -o workspace/html_cache/namespaces.html "https://rpgbakin.com/csreference/doc/ja/namespaces.html"')
        return
    
    # HTMLを解析
    html_parser = HTMLParser()
    soup = html_parser.parse_html(html_content)
    
    # 階層構造を解析
    hierarchy_parser = HierarchyParser()
    class_path_map = hierarchy_parser.parse_hierarchy_from_html(soup)
    
    print(f"Generated class path map with {len(class_path_map)} entries")
    
    # 統計情報を表示
    stats = hierarchy_parser.get_hierarchy_stats()
    print(f"\nHierarchy Statistics:")
    print(f"  Total nodes: {stats['total_nodes']}")
    print(f"  Namespaces: {stats['namespaces']}")
    print(f"  Classes: {stats['classes']}")
    print(f"  Max level: {stats['max_level']}")
    
    return hierarchy_parser, class_path_map


def example_class_path_correction(hierarchy_parser, class_path_map):
    """クラスパス修正の例"""
    print("\n=== Class Path Correction Examples ===")
    
    # 問題のあるクラスパスの例
    test_cases = [
        ("KeyValue", "class_yukar_1_1_common_1_1_resource_1_1_blend_shape_1_1_clip_1_1_key_value.html"),
        ("Sound", "class_sharp_kmy_audio_1_1_sound.html"),
        ("AutoPeriod", "class_sharp_kmy_base_1_1_performance_meter_1_1_auto_period.html"),
        ("BlendShape", "class_yukar_1_1_common_1_1_resource_1_1_blend_shape.html"),
    ]
    
    print("Class path corrections:")
    for class_name, url in test_cases:
        # 従来の方法（URLから推定）
        old_path = extract_full_name_from_url_old_method(url, class_name)
        
        # 新しい方法（階層構造解析）
        new_path = hierarchy_parser.get_correct_full_name(class_name, url)
        
        print(f"\nClass: {class_name}")
        print(f"  URL: {url}")
        print(f"  Old method: {old_path}")
        print(f"  New method: {new_path}")
        print(f"  Improved: {'✅' if new_path != old_path else '❌'}")


def extract_full_name_from_url_old_method(class_url: str, class_name: str) -> str:
    """
    従来の方法でURLからフルネームを推定（比較用）
    """
    try:
        if 'class_' in class_url:
            url_parts = class_url.split('class_')[1].split('.html')[0]
            parts = url_parts.split('_')
            
            namespace_parts = []
            for part in parts:
                if part and not part.isdigit():
                    namespace_parts.append(part.capitalize())
            
            if namespace_parts:
                return '.'.join(namespace_parts)
        
        return class_name
        
    except Exception:
        return class_name


def example_hierarchy_tree(hierarchy_parser):
    """階層構造ツリーの表示例"""
    print("\n=== Hierarchy Tree Example ===")
    print("Displaying hierarchy tree (max depth: 3):")
    print()
    
    hierarchy_parser.print_hierarchy_tree(max_depth=3)


def example_specific_class_lookup(class_path_map):
    """特定クラスの検索例"""
    print("\n=== Specific Class Lookup Examples ===")
    
    # 特定のクラスを検索
    search_classes = ["KeyValue", "BlendShape", "Sound", "AutoPeriod", "PerformanceMeter"]
    
    print("Class path lookup results:")
    for class_name in search_classes:
        if class_name in class_path_map:
            full_path = class_path_map[class_name]
            print(f"  {class_name} -> {full_path}")
        else:
            print(f"  {class_name} -> Not found")


def main():
    """メイン実行関数"""
    print("Hierarchy Parser Examples")
    print("=" * 50)
    
    # 基本的な階層構造解析
    hierarchy_parser, class_path_map = example_hierarchy_parsing()
    
    if not hierarchy_parser:
        return
    
    # クラスパス修正の例
    example_class_path_correction(hierarchy_parser, class_path_map)
    
    # 階層構造ツリーの表示
    example_hierarchy_tree(hierarchy_parser)
    
    # 特定クラスの検索
    example_specific_class_lookup(class_path_map)
    
    print("\n" + "=" * 50)
    print("Hierarchy parser examples completed!")


if __name__ == "__main__":
    main()