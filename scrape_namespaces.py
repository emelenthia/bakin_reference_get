#!/usr/bin/env python3
"""
名前空間スクレイピング実行スクリプト

namespaces.htmlページから全ての名前空間とクラス情報を取得し、
JSONファイルに保存します。
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path

from src.scraper.namespace_scraper import NamespaceScraper


def setup_logging():
    """ログ設定を初期化"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('scraping.log', encoding='utf-8')
        ]
    )


async def main():
    """メイン実行関数"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("Starting Bakin namespace scraping...")
    
    try:
        # 名前空間スクレイパーを初期化
        scraper = NamespaceScraper()
        
        # 名前空間情報を取得
        namespaces = await scraper.scrape_namespaces()
        
        logger.info(f"Successfully scraped {len(namespaces)} namespaces")
        
        # 結果をJSONファイルに保存
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        
        # タイムスタンプ付きファイル名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = output_dir / f"namespaces_list_{timestamp}.json"
        
        # JSONデータを構築
        json_data = {
            "metadata": {
                "scrapedAt": datetime.now().isoformat(),
                "sourceUrl": "https://rpgbakin.com/csreference/doc/ja/namespaces.html",
                "version": "1.0",
                "totalNamespaces": len(namespaces),
                "totalClasses": sum(len(ns.classes) for ns in namespaces)
            },
            "namespaces": [ns.to_dict() for ns in namespaces]
        }
        
        # JSONファイルに保存
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Results saved to: {output_file}")
        
        # サマリーを表示
        print("\n=== Scraping Summary ===")
        print(f"Total namespaces: {len(namespaces)}")
        print(f"Total classes: {sum(len(ns.classes) for ns in namespaces)}")
        print(f"Output file: {output_file}")
        
        print("\n=== Namespaces Found ===")
        for namespace in namespaces:
            print(f"- {namespace.name} ({len(namespace.classes)} classes)")
            for class_info in namespace.classes[:3]:  # 最初の3つのクラスを表示
                print(f"  - {class_info.name}")
            if len(namespace.classes) > 3:
                print(f"  ... and {len(namespace.classes) - 3} more classes")
        
    except Exception as e:
        logger.error(f"Error during scraping: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())