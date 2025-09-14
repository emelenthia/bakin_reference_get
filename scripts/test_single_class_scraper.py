#!/usr/bin/env python3
"""
単一クラス詳細取得のテストスクリプト

classes_list.jsonから1つのクラスを選択して詳細情報を取得し、
single_class_test.jsonに保存します。
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from src.scraper.http_client import HTTPClient
from src.scraper.class_detail_scraper import ClassDetailScraper


async def test_single_class_scraping():
    """単一クラスの詳細情報取得をテスト"""
    
    # ログ設定
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    # classes_list.jsonを読み込み
    classes_list_path = Path(__file__).parent.parent / "output/classes_list.json"
    if not classes_list_path.exists():
        logger.error(f"Classes list file not found: {classes_list_path}")
        return
    
    logger.info("Loading classes list...")
    with open(classes_list_path, 'r', encoding='utf-8') as f:
        classes_data = json.load(f)
    
    # 特定のクラスをテスト対象として選択
    test_class = None
    test_namespace = None
    
    # SoundResourceクラスを探す
    target_class_name = 'SoundResource'
    
    for namespace in classes_data.get('namespaces', []):
        if namespace.get('classes'):
            for cls in namespace['classes']:
                if cls['name'] == target_class_name:
                    test_class = cls
                    test_namespace = namespace['name']
                    logger.info(f"Found target class: {cls['name']} in namespace: {namespace['name']}")
                    break
            if test_class:
                break
    
    # SoundResourceが見つからない場合は、フォールバック処理
    if not test_class:
        logger.warning(f"Target class '{target_class_name}' not found, using fallback selection")
        for namespace in classes_data.get('namespaces', []):
            if namespace.get('name') == 'Yukar' and namespace.get('classes') and len(namespace['classes']) > 0:
                # 最初のクラスを使用
                test_class = namespace['classes'][0]
                test_namespace = namespace['name']
                break
    
    if not test_class:
        logger.error("No classes found in the classes list")
        return
    
    logger.info(f"Selected test class: {test_class['name']} from namespace: {test_namespace}")
    logger.info(f"Class URL: {test_class['url']}")
    
    # HTTPクライアントとスクレイパーを初期化
    async with HTTPClient() as http_client:
        scraper = ClassDetailScraper(http_client)
        
        # URLを修正
        corrected_url = scraper._fix_class_url(test_class['url'])
        
        # クラス詳細情報を取得
        logger.info("Scraping class details...")
        class_info = await scraper.scrape_class_details(
            class_url=test_class['url'],
            class_name=test_class['name'],
            full_name=test_class['full_name']
        )
        
        if class_info:
            logger.info("Successfully scraped class details!")
            
            # 結果をJSONファイルに保存
            output_data = {
                'metadata': {
                    'scraped_at': datetime.now().isoformat(),
                    'test_class': test_class['name'],
                    'namespace': test_namespace,
                    'source_url': corrected_url  # 修正されたURLを使用
                },
                'class_details': class_info.to_dict()
            }
            
            output_path = Path(__file__).parent.parent / "workspace/soundresource_test.json"
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Class details saved to: {output_path}")
            
            # 取得した情報を表示
            print("\n" + "="*70)
            print("SCRAPED CLASS DETAILS")
            print("="*70)
            print(f"Name: {class_info.name}")
            print(f"Full Name: {class_info.full_name}")
            print(f"Source URL: {corrected_url}")
            print(f"Description: {class_info.description or 'Not found'}")
            print(f"Inheritance: {class_info.inheritance or 'Not found'}")
            print(f"\nConstructors found: {len(class_info.constructors)}")
            print(f"Methods found: {len(class_info.methods)}")
            print(f"Properties found: {len(class_info.properties)}")
            print(f"Fields found: {len(class_info.fields)}")
            print(f"Events found: {len(class_info.events)}")
            
            # メソッド詳細を表示
            if class_info.methods:
                print(f"\n--- METHODS ({len(class_info.methods)}) ---")
                for i, method in enumerate(class_info.methods, 1):
                    print(f"{i}. {method.access_modifier} {'static ' if method.is_static else ''}{method.return_type} {method.name}({', '.join([f'{p.type} {p.name}' for p in method.parameters])})")
                    if method.description:
                        print(f"   Description: {method.description[:100]}{'...' if len(method.description) > 100 else ''}")
                    if method.exceptions:
                        print(f"   Exceptions: {', '.join([e.type for e in method.exceptions])}")
            
            # コンストラクタ詳細を表示
            if class_info.constructors:
                print(f"\n--- CONSTRUCTORS ({len(class_info.constructors)}) ---")
                for i, ctor in enumerate(class_info.constructors, 1):
                    print(f"{i}. {ctor.access_modifier} {ctor.name}({', '.join([f'{p.type} {p.name}' for p in ctor.parameters])})")
                    if ctor.description:
                        print(f"   Description: {ctor.description[:100]}{'...' if len(ctor.description) > 100 else ''}")
            
            print("="*70)
            
        else:
            logger.error("Failed to scrape class details")


if __name__ == "__main__":
    asyncio.run(test_single_class_scraping())