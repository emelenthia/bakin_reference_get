#!/usr/bin/env python3
"""
クラス一覧生成スクリプト

Bakinドキュメントから名前空間とクラス情報を取得し、
構造化されたJSON形式でクラス一覧を出力します。

このスクリプトは以下の処理を実行します：
1. namespaces.htmlページから名前空間とクラス情報を取得
2. 取得したデータを名前空間ごとに整理
3. クラスURLの正規化と検証
4. 重複チェックとデータクリーニング
5. 簡易的なJSON形式でクラス一覧を出力（classes_list.json）
6. 進行状況の表示
"""

import asyncio
import argparse
import logging
import sys
from pathlib import Path
from datetime import datetime

# Add the src directory to the path
sys.path.append(str(Path(__file__).parent))

from src.scraper.namespace_scraper import NamespaceScraper
from src.processor.class_list_processor import ClassListProcessor


def setup_logging(log_level: str = "INFO", log_file: str = None) -> None:
    """
    ログ設定をセットアップ
    
    Args:
        log_level: ログレベル (DEBUG, INFO, WARNING, ERROR)
        log_file: ログファイルパス（オプション）
    """
    # ログレベルを設定
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # ログフォーマットを設定
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # ログ設定
    logging.basicConfig(
        level=numeric_level,
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # ファイルハンドラーを追加（指定された場合）
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(logging.Formatter(log_format))
        logging.getLogger().addHandler(file_handler)


async def main():
    """メイン実行関数"""
    # コマンドライン引数の解析
    parser = argparse.ArgumentParser(
        description="Bakinドキュメントからクラス一覧を生成",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  python generate_class_list.py
  python generate_class_list.py --output my_classes.json
  python generate_class_list.py --base-url https://rpgbakin.com --log-level DEBUG
  python generate_class_list.py --no-progress --log-file scraping.log
        """
    )
    
    parser.add_argument(
        '--output', '-o',
        default='output/classes_list.json',
        help='出力JSONファイルパス (デフォルト: output/classes_list.json)'
    )
    
    parser.add_argument(
        '--base-url',
        default='https://rpgbakin.com',
        help='BakinドキュメントのベースURL (デフォルト: https://rpgbakin.com)'
    )
    
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='ログレベル (デフォルト: INFO)'
    )
    
    parser.add_argument(
        '--log-file',
        help='ログファイルパス（指定しない場合はコンソールのみ）'
    )
    
    parser.add_argument(
        '--no-progress',
        action='store_true',
        help='進行状況表示を無効にする'
    )
    
    parser.add_argument(
        '--use-local-cache',
        action='store_true',
        help='ローカルキャッシュを使用する（workspace/html_cache/namespaces.html）'
    )
    
    args = parser.parse_args()
    
    # ログ設定
    setup_logging(args.log_level, args.log_file)
    logger = logging.getLogger(__name__)
    
    # 開始メッセージ
    logger.info("=" * 60)
    logger.info("Bakin Documentation Class List Generator")
    logger.info("=" * 60)
    logger.info(f"Base URL: {args.base_url}")
    logger.info(f"Output file: {args.output}")
    logger.info(f"Progress display: {'Disabled' if args.no_progress else 'Enabled'}")
    logger.info(f"Local cache: {'Enabled' if args.use_local_cache else 'Disabled'}")
    logger.info(f"Log level: {args.log_level}")
    if args.log_file:
        logger.info(f"Log file: {args.log_file}")
    
    try:
        # ステップ1: 名前空間とクラス情報をスクレイピング
        if args.use_local_cache:
            logger.info("\nStep 1: Loading namespace and class information from local cache...")
        else:
            logger.info("\nStep 1: Scraping namespace and class information...")
        scraper = NamespaceScraper(base_url=args.base_url, use_local_cache=args.use_local_cache)
        
        start_time = datetime.now()
        namespaces = await scraper.scrape_namespaces()
        scraping_duration = (datetime.now() - start_time).total_seconds()
        
        if not namespaces:
            logger.error("No namespace data was scraped. Exiting.")
            return 1
        
        total_classes = sum(len(ns.classes) for ns in namespaces)
        logger.info(f"Scraping completed in {scraping_duration:.2f} seconds")
        logger.info(f"Scraped {len(namespaces)} namespaces with {total_classes} total classes")
        
        # ステップ2: クラス一覧の構造化と簡易JSON出力
        logger.info("\nStep 2: Processing class list and generating JSON...")
        processor = ClassListProcessor(base_url=args.base_url)
        
        processing_start_time = datetime.now()
        class_list_data = processor.process_namespaces_to_class_list(
            namespaces=namespaces,
            output_file=args.output,
            show_progress=not args.no_progress
        )
        processing_duration = (datetime.now() - processing_start_time).total_seconds()
        
        logger.info(f"Processing completed in {processing_duration:.2f} seconds")
        
        # 結果サマリー
        metadata = class_list_data["metadata"]
        total_duration = (datetime.now() - start_time).total_seconds()
        
        logger.info("\n" + "=" * 60)
        logger.info("PROCESSING SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total execution time: {total_duration:.2f} seconds")
        logger.info(f"  - Scraping time: {scraping_duration:.2f} seconds")
        logger.info(f"  - Processing time: {processing_duration:.2f} seconds")
        logger.info("")
        logger.info("Data Statistics:")
        logger.info(f"  - Total namespaces: {metadata['total_namespaces']}")
        logger.info(f"  - Namespaces with classes: {metadata['namespaces_with_classes']}")
        logger.info(f"  - Total classes: {metadata['total_classes']}")
        logger.info("")
        logger.info(f"Output file: {args.output}")
        
        # ファイルサイズを表示
        output_path = Path(args.output)
        if output_path.exists():
            file_size = output_path.stat().st_size
            logger.info(f"File size: {file_size:,} bytes ({file_size / 1024:.1f} KB)")
        
        # 上位5つの名前空間を表示
        namespaces_by_class_count = sorted(
            class_list_data["namespaces"],
            key=lambda x: x["class_count"],
            reverse=True
        )
        
        if namespaces_by_class_count:
            logger.info("\nTop 5 namespaces by class count:")
            for i, ns in enumerate(namespaces_by_class_count[:5], 1):
                logger.info(f"  {i}. {ns['name']}: {ns['class_count']} classes")
        
        logger.info("\n" + "=" * 60)
        logger.info("Class list generation completed successfully!")
        logger.info("=" * 60)
        
        return 0
        
    except KeyboardInterrupt:
        logger.warning("\nOperation interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"\nError during class list generation: {e}")
        logger.debug("Full error details:", exc_info=True)
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)