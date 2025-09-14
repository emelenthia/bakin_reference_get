"""
クラス一覧処理モジュール

名前空間スクレイパーから取得したデータを構造化し、
簡易的なJSON形式でクラス一覧を出力します。
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Set, Optional
from urllib.parse import urlparse, urljoin

from ..models.main_models import NamespaceInfo, ClassInfo
from ..utils.progress_tracker import ProgressTracker


class ClassListProcessor:
    """
    クラス一覧の構造化と簡易JSON出力を処理するクラス
    
    名前空間スクレイパーから取得したデータを整理し、
    重複チェックとデータクリーニングを行って、
    簡易的なJSON形式で出力します。
    """
    
    def __init__(self, base_url: str = "https://rpgbakin.com"):
        """
        ClassListProcessorを初期化
        
        Args:
            base_url: BakinドキュメントのベースURL
        """
        self.base_url = base_url
        self.logger = logging.getLogger(__name__)
        
    def process_namespaces_to_class_list(self, namespaces: List[NamespaceInfo], 
                                       output_file: str = "classes_list.json",
                                       show_progress: bool = True) -> Dict[str, Any]:
        """
        名前空間データをクラス一覧JSON形式に変換
        
        Args:
            namespaces: 名前空間情報のリスト
            output_file: 出力ファイルパス
            show_progress: 進行状況表示の有無
            
        Returns:
            Dict[str, Any]: 処理されたクラス一覧データ
        """
        self.logger.info(f"Starting class list processing for {len(namespaces)} namespaces")
        
        # 進行状況トラッカーを初期化
        progress_tracker = None
        if show_progress:
            progress_tracker = ProgressTracker()
            total_classes = sum(len(ns.classes) for ns in namespaces)
            progress_tracker.start_operation("Processing class list", total_classes)
        
        try:
            # 1. 名前空間ごとにクラス情報を整理
            organized_data = self._organize_classes_by_namespace(namespaces, progress_tracker)
            
            # 2. クラスURLの正規化と検証
            self._normalize_and_validate_urls(organized_data, progress_tracker)
            
            # 3. 重複チェックとデータクリーニング
            cleaned_data = self._perform_duplicate_check_and_cleaning(organized_data, progress_tracker)
            
            # 4. 簡易JSON形式でデータを構築
            class_list_data = self._build_class_list_json(cleaned_data, namespaces)
            
            # 5. ファイルに保存
            self._save_class_list_json(class_list_data, output_file)
            
            if progress_tracker:
                summary = progress_tracker.complete_operation()
                self.logger.info(f"Class list processing completed: {summary}")
            
            return class_list_data
            
        except Exception as e:
            if progress_tracker:
                progress_tracker.log_error(str(e), "Class list processing")
                progress_tracker.complete_operation()
            raise
        finally:
            if progress_tracker:
                progress_tracker.close()
    
    def _organize_classes_by_namespace(self, namespaces: List[NamespaceInfo], 
                                     progress_tracker: Optional[ProgressTracker] = None) -> Dict[str, List[ClassInfo]]:
        """
        名前空間ごとにクラス情報を整理
        
        Args:
            namespaces: 名前空間情報のリスト
            progress_tracker: 進行状況トラッカー
            
        Returns:
            Dict[str, List[ClassInfo]]: 名前空間名をキーとするクラス情報辞書
        """
        organized_data = {}
        processed_classes = 0
        
        for namespace in namespaces:
            if namespace.classes:
                organized_data[namespace.name] = []
                
                for class_info in namespace.classes:
                    # クラス情報を追加
                    organized_data[namespace.name].append(class_info)
                    processed_classes += 1
                    
                    if progress_tracker:
                        progress_tracker.update_progress(
                            completed_items=processed_classes,
                            current_item=f"{namespace.name}.{class_info.name}"
                        )
                
                self.logger.debug(f"Organized {len(namespace.classes)} classes for namespace: {namespace.name}")
            else:
                # クラスがない名前空間も記録
                organized_data[namespace.name] = []
                self.logger.debug(f"Empty namespace: {namespace.name}")
        
        self.logger.info(f"Organized {processed_classes} classes across {len(organized_data)} namespaces")
        return organized_data
    
    def _normalize_and_validate_urls(self, organized_data: Dict[str, List[ClassInfo]], 
                                   progress_tracker: Optional[ProgressTracker] = None) -> None:
        """
        クラスURLの正規化と検証
        
        Args:
            organized_data: 整理されたクラスデータ
            progress_tracker: 進行状況トラッカー
        """
        total_classes = sum(len(classes) for classes in organized_data.values())
        processed_classes = 0
        invalid_urls = 0
        
        for namespace_name, classes in organized_data.items():
            for class_info in classes:
                processed_classes += 1
                
                # URLを正規化
                original_url = class_info.url
                normalized_url = self._normalize_url(original_url)
                
                if normalized_url != original_url:
                    class_info.url = normalized_url
                    self.logger.debug(f"Normalized URL for {class_info.name}: {original_url} -> {normalized_url}")
                
                # URLを検証
                if not self._validate_url(normalized_url):
                    invalid_urls += 1
                    if progress_tracker:
                        progress_tracker.log_error(
                            f"Invalid URL for class {class_info.name}: {normalized_url}",
                            f"{namespace_name}.{class_info.name}"
                        )
                
                if progress_tracker:
                    progress_tracker.update_progress(
                        completed_items=processed_classes,
                        current_item=f"Validating {namespace_name}.{class_info.name}"
                    )
        
        if invalid_urls > 0:
            self.logger.warning(f"Found {invalid_urls} invalid URLs out of {total_classes} classes")
        else:
            self.logger.info(f"All {total_classes} class URLs are valid")
    
    def _normalize_url(self, url: str) -> str:
        """
        URLを正規化
        
        Args:
            url: 正規化するURL
            
        Returns:
            str: 正規化されたURL
        """
        if not url:
            return url
        
        # 相対URLを絶対URLに変換
        if url.startswith('/'):
            return urljoin(self.base_url, url)
        elif not url.startswith('http'):
            return urljoin(self.base_url, url)
        
        # 既に絶対URLの場合はそのまま返す
        return url
    
    def _validate_url(self, url: str) -> bool:
        """
        URLの妥当性を検証
        
        Args:
            url: 検証するURL
            
        Returns:
            bool: URLが妥当な場合True
        """
        if not url:
            return False
        
        try:
            parsed = urlparse(url)
            # スキーム、ネットロケーション、パスが存在することを確認
            return bool(parsed.scheme and parsed.netloc and parsed.path)
        except Exception:
            return False
    
    def _perform_duplicate_check_and_cleaning(self, organized_data: Dict[str, List[ClassInfo]], 
                                            progress_tracker: Optional[ProgressTracker] = None) -> Dict[str, List[ClassInfo]]:
        """
        重複チェックとデータクリーニング
        
        Args:
            organized_data: 整理されたクラスデータ
            progress_tracker: 進行状況トラッカー
            
        Returns:
            Dict[str, List[ClassInfo]]: クリーニング済みのクラスデータ
        """
        cleaned_data = {}
        total_classes = sum(len(classes) for classes in organized_data.values())
        processed_classes = 0
        removed_duplicates = 0
        
        # 全体での重複チェック用セット
        global_class_names: Set[str] = set()
        global_class_urls: Set[str] = set()
        
        for namespace_name, classes in organized_data.items():
            cleaned_classes = []
            namespace_class_names: Set[str] = set()
            
            for class_info in classes:
                processed_classes += 1
                is_duplicate = False
                
                # 名前空間内での重複チェック
                if class_info.name in namespace_class_names:
                    is_duplicate = True
                    if progress_tracker:
                        progress_tracker.log_skip(
                            f"{namespace_name}.{class_info.name}",
                            "Duplicate class name within namespace"
                        )
                
                # 全体での重複チェック（より厳密）
                elif class_info.full_name in global_class_names:
                    is_duplicate = True
                    if progress_tracker:
                        progress_tracker.log_skip(
                            f"{namespace_name}.{class_info.name}",
                            "Duplicate full class name globally"
                        )
                
                # URLでの重複チェック
                elif class_info.url in global_class_urls:
                    is_duplicate = True
                    if progress_tracker:
                        progress_tracker.log_skip(
                            f"{namespace_name}.{class_info.name}",
                            "Duplicate class URL"
                        )
                
                if not is_duplicate:
                    # データクリーニング
                    cleaned_class = self._clean_class_info(class_info)
                    cleaned_classes.append(cleaned_class)
                    
                    # 重複チェック用セットに追加
                    namespace_class_names.add(class_info.name)
                    global_class_names.add(class_info.full_name)
                    global_class_urls.add(class_info.url)
                else:
                    removed_duplicates += 1
                
                if progress_tracker:
                    progress_tracker.update_progress(
                        completed_items=processed_classes,
                        current_item=f"Cleaning {namespace_name}.{class_info.name}"
                    )
            
            cleaned_data[namespace_name] = cleaned_classes
            self.logger.debug(f"Cleaned namespace {namespace_name}: {len(cleaned_classes)} classes (removed {len(classes) - len(cleaned_classes)} duplicates)")
        
        self.logger.info(f"Data cleaning completed: {total_classes - removed_duplicates} classes remaining (removed {removed_duplicates} duplicates)")
        return cleaned_data
    
    def _clean_class_info(self, class_info: ClassInfo) -> ClassInfo:
        """
        クラス情報をクリーニング
        
        Args:
            class_info: クリーニングするクラス情報
            
        Returns:
            ClassInfo: クリーニング済みのクラス情報
        """
        # 文字列フィールドの空白を除去
        cleaned_name = class_info.name.strip() if class_info.name else ""
        cleaned_full_name = class_info.full_name.strip() if class_info.full_name else ""
        cleaned_url = class_info.url.strip() if class_info.url else ""
        cleaned_description = class_info.description.strip() if class_info.description else None
        
        # 空の説明をNoneに変換
        if cleaned_description == "":
            cleaned_description = None
        
        return ClassInfo(
            name=cleaned_name,
            full_name=cleaned_full_name,
            url=cleaned_url,
            description=cleaned_description,
            inheritance=class_info.inheritance,
            constructors=class_info.constructors,
            methods=class_info.methods,
            properties=class_info.properties,
            fields=class_info.fields,
            events=class_info.events
        )
    
    def _build_class_list_json(self, cleaned_data: Dict[str, List[ClassInfo]], 
                             original_namespaces: List[NamespaceInfo]) -> Dict[str, Any]:
        """
        簡易JSON形式でクラス一覧データを構築
        
        Args:
            cleaned_data: クリーニング済みのクラスデータ
            original_namespaces: 元の名前空間情報
            
        Returns:
            Dict[str, Any]: クラス一覧JSONデータ
        """
        # 統計情報を計算
        total_namespaces = len(cleaned_data)
        total_classes = sum(len(classes) for classes in cleaned_data.values())
        namespaces_with_classes = len([ns for ns, classes in cleaned_data.items() if classes])
        
        # メタデータを構築
        metadata = {
            "generated_at": datetime.now().isoformat(),
            "source_url": "https://rpgbakin.com/csreference/doc/ja/namespaces.html",
            "total_namespaces": total_namespaces,
            "namespaces_with_classes": namespaces_with_classes,
            "total_classes": total_classes,
            "version": "1.0"
        }
        
        # 名前空間データを構築
        namespaces_data = []
        
        for namespace_name, classes in cleaned_data.items():
            # 元の名前空間情報を検索
            original_namespace = next((ns for ns in original_namespaces if ns.name == namespace_name), None)
            
            namespace_data = {
                "name": namespace_name,
                "url": original_namespace.url if original_namespace else "",
                "description": original_namespace.description if original_namespace else None,
                "class_count": len(classes),
                "classes": []
            }
            
            # クラスデータを構築
            for class_info in classes:
                class_data = {
                    "name": class_info.name,
                    "full_name": class_info.full_name,
                    "url": class_info.url,
                    "description": class_info.description
                }
                namespace_data["classes"].append(class_data)
            
            namespaces_data.append(namespace_data)
        
        # 名前空間を名前でソート
        namespaces_data.sort(key=lambda x: x["name"])
        
        # 各名前空間内のクラスをfull_nameでソート（パッケージごとにグループ化）
        for namespace_data in namespaces_data:
            namespace_data["classes"].sort(key=lambda x: (x["full_name"], x["name"]))
        
        return {
            "metadata": metadata,
            "namespaces": namespaces_data
        }
    
    def _save_class_list_json(self, class_list_data: Dict[str, Any], output_file: str) -> None:
        """
        クラス一覧JSONをファイルに保存
        
        Args:
            class_list_data: クラス一覧データ
            output_file: 出力ファイルパス
        """
        output_path = Path(output_file)
        
        # 出力ディレクトリを作成
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # JSONファイルに保存
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(class_list_data, f, ensure_ascii=False, indent=2)
        
        file_size = output_path.stat().st_size
        self.logger.info(f"Saved class list to: {output_path} ({file_size:,} bytes)")
        
        # 統計情報をログ出力
        metadata = class_list_data["metadata"]
        self.logger.info(f"Class list statistics:")
        self.logger.info(f"  Total namespaces: {metadata['total_namespaces']}")
        self.logger.info(f"  Namespaces with classes: {metadata['namespaces_with_classes']}")
        self.logger.info(f"  Total classes: {metadata['total_classes']}")


# 便利な関数として直接使用できるヘルパー関数
def process_namespaces_to_class_list(namespaces: List[NamespaceInfo], 
                                   output_file: str = "classes_list.json",
                                   show_progress: bool = True) -> Dict[str, Any]:
    """
    名前空間データをクラス一覧JSON形式に変換
    
    Args:
        namespaces: 名前空間情報のリスト
        output_file: 出力ファイルパス
        show_progress: 進行状況表示の有無
        
    Returns:
        Dict[str, Any]: 処理されたクラス一覧データ
    """
    processor = ClassListProcessor()
    return processor.process_namespaces_to_class_list(namespaces, output_file, show_progress)