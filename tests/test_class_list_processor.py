#!/usr/bin/env python3
"""
クラス一覧処理のテスト

ClassListProcessorクラスの機能をテストします。
"""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
import sys

# Add the parent directory to the path so we can import from src
sys.path.append(str(Path(__file__).parent.parent))

from src.models.main_models import NamespaceInfo, ClassInfo
from src.processor.class_list_processor import ClassListProcessor, process_namespaces_to_class_list


class TestClassListProcessor(unittest.TestCase):
    """ClassListProcessorのテストクラス"""
    
    def setUp(self):
        """テストセットアップ"""
        self.processor = ClassListProcessor()
        
        # テスト用のサンプルデータを作成
        self.sample_classes = [
            ClassInfo(
                name="TestClass1",
                full_name="Yukar.Engine.TestClass1",
                url="https://rpgbakin.com/csreference/doc/ja/class_yukar_1_1_engine_1_1_test_class1.html",
                description="Test class 1 description"
            ),
            ClassInfo(
                name="TestClass2",
                full_name="Yukar.Engine.TestClass2",
                url="https://rpgbakin.com/csreference/doc/ja/class_yukar_1_1_engine_1_1_test_class2.html",
                description="Test class 2 description"
            ),
            ClassInfo(
                name="DuplicateClass",
                full_name="Yukar.Engine.DuplicateClass",
                url="https://rpgbakin.com/csreference/doc/ja/class_yukar_1_1_engine_1_1_duplicate_class.html",
                description="Duplicate class description"
            )
        ]
        
        self.sample_namespaces = [
            NamespaceInfo(
                name="Yukar.Engine",
                url="https://rpgbakin.com/csreference/doc/ja/namespace_yukar_1_1_engine.html",
                classes=self.sample_classes[:2],  # 最初の2つのクラス
                description="Yukar Engine namespace"
            ),
            NamespaceInfo(
                name="Yukar.Common",
                url="https://rpgbakin.com/csreference/doc/ja/namespace_yukar_1_1_common.html",
                classes=[self.sample_classes[2]],  # 3番目のクラス
                description="Yukar Common namespace"
            ),
            NamespaceInfo(
                name="Empty.Namespace",
                url="https://rpgbakin.com/csreference/doc/ja/namespace_empty.html",
                classes=[],  # 空の名前空間
                description="Empty namespace for testing"
            )
        ]
    
    def test_organize_classes_by_namespace(self):
        """名前空間ごとのクラス整理をテスト"""
        organized_data = self.processor._organize_classes_by_namespace(self.sample_namespaces)
        
        # 名前空間の数を確認
        self.assertEqual(len(organized_data), 3)
        
        # 各名前空間のクラス数を確認
        self.assertEqual(len(organized_data["Yukar.Engine"]), 2)
        self.assertEqual(len(organized_data["Yukar.Common"]), 1)
        self.assertEqual(len(organized_data["Empty.Namespace"]), 0)
        
        # クラス名を確認
        engine_class_names = [cls.name for cls in organized_data["Yukar.Engine"]]
        self.assertIn("TestClass1", engine_class_names)
        self.assertIn("TestClass2", engine_class_names)
        
        common_class_names = [cls.name for cls in organized_data["Yukar.Common"]]
        self.assertIn("DuplicateClass", common_class_names)
    
    def test_normalize_url(self):
        """URL正規化をテスト"""
        # 絶対URLはそのまま
        absolute_url = "https://rpgbakin.com/csreference/doc/ja/test.html"
        self.assertEqual(self.processor._normalize_url(absolute_url), absolute_url)
        
        # 相対URLは絶対URLに変換
        relative_url = "/csreference/doc/ja/test.html"
        expected = "https://rpgbakin.com/csreference/doc/ja/test.html"
        self.assertEqual(self.processor._normalize_url(relative_url), expected)
        
        # 空文字列はそのまま
        self.assertEqual(self.processor._normalize_url(""), "")
    
    def test_validate_url(self):
        """URL検証をテスト"""
        # 有効なURL
        valid_url = "https://rpgbakin.com/csreference/doc/ja/test.html"
        self.assertTrue(self.processor._validate_url(valid_url))
        
        # 無効なURL
        self.assertFalse(self.processor._validate_url(""))
        self.assertFalse(self.processor._validate_url("invalid-url"))
        self.assertFalse(self.processor._validate_url("http://"))
    
    def test_clean_class_info(self):
        """クラス情報クリーニングをテスト"""
        # 空白を含むクラス情報
        dirty_class = ClassInfo(
            name="  TestClass  ",
            full_name="  Yukar.Engine.TestClass  ",
            url="  https://example.com/test.html  ",
            description="  Test description  "
        )
        
        cleaned_class = self.processor._clean_class_info(dirty_class)
        
        self.assertEqual(cleaned_class.name, "TestClass")
        self.assertEqual(cleaned_class.full_name, "Yukar.Engine.TestClass")
        self.assertEqual(cleaned_class.url, "https://example.com/test.html")
        self.assertEqual(cleaned_class.description, "Test description")
        
        # 空の説明はNoneに変換
        empty_desc_class = ClassInfo(
            name="TestClass",
            full_name="Yukar.Engine.TestClass",
            url="https://example.com/test.html",
            description=""
        )
        
        cleaned_empty = self.processor._clean_class_info(empty_desc_class)
        self.assertIsNone(cleaned_empty.description)
    
    def test_perform_duplicate_check_and_cleaning(self):
        """重複チェックとクリーニングをテスト"""
        # 重複を含むテストデータを作成
        duplicate_class = ClassInfo(
            name="TestClass1",  # 既存のクラスと同じ名前
            full_name="Yukar.Engine.TestClass1",  # 既存のクラスと同じフルネーム
            url="https://rpgbakin.com/csreference/doc/ja/class_yukar_1_1_engine_1_1_test_class1.html",
            description="Duplicate class"
        )
        
        test_namespaces = [
            NamespaceInfo(
                name="Yukar.Engine",
                url="https://rpgbakin.com/csreference/doc/ja/namespace_yukar_1_1_engine.html",
                classes=[self.sample_classes[0], duplicate_class],  # 重複を含む
                description="Test namespace"
            )
        ]
        
        organized_data = self.processor._organize_classes_by_namespace(test_namespaces)
        cleaned_data = self.processor._perform_duplicate_check_and_cleaning(organized_data)
        
        # 重複が除去されていることを確認
        self.assertEqual(len(cleaned_data["Yukar.Engine"]), 1)
        self.assertEqual(cleaned_data["Yukar.Engine"][0].name, "TestClass1")
    
    def test_build_class_list_json(self):
        """クラス一覧JSON構築をテスト"""
        organized_data = self.processor._organize_classes_by_namespace(self.sample_namespaces)
        cleaned_data = self.processor._perform_duplicate_check_and_cleaning(organized_data)
        
        class_list_data = self.processor._build_class_list_json(cleaned_data, self.sample_namespaces)
        
        # メタデータを確認
        self.assertIn("metadata", class_list_data)
        metadata = class_list_data["metadata"]
        self.assertIn("generated_at", metadata)
        self.assertIn("total_namespaces", metadata)
        self.assertIn("total_classes", metadata)
        
        # 名前空間データを確認
        self.assertIn("namespaces", class_list_data)
        namespaces = class_list_data["namespaces"]
        self.assertEqual(len(namespaces), 3)
        
        # 名前空間がソートされていることを確認
        namespace_names = [ns["name"] for ns in namespaces]
        self.assertEqual(namespace_names, sorted(namespace_names))
        
        # 各名前空間の構造を確認
        for namespace in namespaces:
            self.assertIn("name", namespace)
            self.assertIn("url", namespace)
            self.assertIn("class_count", namespace)
            self.assertIn("classes", namespace)
            
            # クラスがソートされていることを確認
            if namespace["classes"]:
                class_names = [cls["name"] for cls in namespace["classes"]]
                self.assertEqual(class_names, sorted(class_names))
    
    def test_save_class_list_json(self):
        """クラス一覧JSON保存をテスト"""
        # テスト用の一時ファイル
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            # テストデータを作成
            test_data = {
                "metadata": {
                    "generated_at": "2025-01-14T10:00:00",
                    "total_namespaces": 1,
                    "namespaces_with_classes": 1,
                    "total_classes": 1
                },
                "namespaces": [
                    {
                        "name": "Test.Namespace",
                        "url": "https://example.com/test",
                        "class_count": 1,
                        "classes": [
                            {
                                "name": "TestClass",
                                "full_name": "Test.Namespace.TestClass",
                                "url": "https://example.com/test_class.html",
                                "description": "Test class"
                            }
                        ]
                    }
                ]
            }
            
            # ファイルに保存
            self.processor._save_class_list_json(test_data, temp_path)
            
            # ファイルが作成されていることを確認
            self.assertTrue(Path(temp_path).exists())
            
            # ファイル内容を確認
            with open(temp_path, 'r', encoding='utf-8') as f:
                loaded_data = json.load(f)
            
            self.assertEqual(loaded_data, test_data)
            
        finally:
            # 一時ファイルを削除
            Path(temp_path).unlink(missing_ok=True)
    
    @patch('src.processor.class_list_processor.ProgressTracker')
    def test_process_namespaces_to_class_list_with_progress(self, mock_progress_tracker):
        """進行状況表示ありでの処理をテスト"""
        # モックの設定
        mock_tracker_instance = Mock()
        mock_progress_tracker.return_value = mock_tracker_instance
        
        # 一時ファイル
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            # 処理を実行
            result = self.processor.process_namespaces_to_class_list(
                namespaces=self.sample_namespaces,
                output_file=temp_path,
                show_progress=True
            )
            
            # ProgressTrackerが呼び出されたことを確認
            mock_progress_tracker.assert_called_once()
            mock_tracker_instance.start_operation.assert_called_once()
            mock_tracker_instance.complete_operation.assert_called_once()
            mock_tracker_instance.close.assert_called_once()
            
            # 結果を確認
            self.assertIsInstance(result, dict)
            self.assertIn("metadata", result)
            self.assertIn("namespaces", result)
            
        finally:
            # 一時ファイルを削除
            Path(temp_path).unlink(missing_ok=True)
    
    def test_process_namespaces_to_class_list_without_progress(self):
        """進行状況表示なしでの処理をテスト"""
        # 一時ファイル
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            # 処理を実行
            result = self.processor.process_namespaces_to_class_list(
                namespaces=self.sample_namespaces,
                output_file=temp_path,
                show_progress=False
            )
            
            # 結果を確認
            self.assertIsInstance(result, dict)
            self.assertIn("metadata", result)
            self.assertIn("namespaces", result)
            
            # ファイルが作成されていることを確認
            self.assertTrue(Path(temp_path).exists())
            
        finally:
            # 一時ファイルを削除
            Path(temp_path).unlink(missing_ok=True)
    
    def test_helper_function(self):
        """ヘルパー関数をテスト"""
        # 一時ファイル
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            # ヘルパー関数を実行
            result = process_namespaces_to_class_list(
                namespaces=self.sample_namespaces,
                output_file=temp_path,
                show_progress=False
            )
            
            # 結果を確認
            self.assertIsInstance(result, dict)
            self.assertIn("metadata", result)
            self.assertIn("namespaces", result)
            
        finally:
            # 一時ファイルを削除
            Path(temp_path).unlink(missing_ok=True)


if __name__ == '__main__':
    unittest.main()