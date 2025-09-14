#!/usr/bin/env python3
"""
コンストラクタ抽出機能のテスト

ClassDetailScraperのコンストラクタ抽出機能をテストします。
"""

import unittest
from unittest.mock import Mock
from bs4 import BeautifulSoup

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from src.scraper.class_detail_scraper import ClassDetailScraper
from src.models.basic_models import ConstructorInfo, ParameterInfo


class TestConstructorExtraction(unittest.TestCase):
    """コンストラクタ抽出機能のテストクラス"""
    
    def setUp(self):
        """テストセットアップ"""
        # モックHTTPクライアントを作成
        mock_http_client = Mock()
        self.scraper = ClassDetailScraper(mock_http_client)
    
    def test_parse_parameters_from_definition(self):
        """パラメータ解析のテスト"""
        # テストケース1: 単一パラメータ
        params = self.scraper._parse_parameters_from_definition("TestClass(int value)")
        print(f"Test 1 - Expected: 1, Got: {len(params)}, Params: {[(p.name, p.type) for p in params]}")
        self.assertEqual(len(params), 1)
        self.assertEqual(params[0].name, "value")
        self.assertEqual(params[0].type, "int")
        
        # テストケース2: 複数パラメータ
        params = self.scraper._parse_parameters_from_definition("TestClass(string name, int age, bool active)")
        print(f"Test 2 - Expected: 3, Got: {len(params)}, Params: {[(p.name, p.type) for p in params]}")
        self.assertEqual(len(params), 3)
        self.assertEqual(params[0].name, "name")
        self.assertEqual(params[0].type, "string")
        self.assertEqual(params[1].name, "age")
        self.assertEqual(params[1].type, "int")
        self.assertEqual(params[2].name, "active")
        self.assertEqual(params[2].type, "bool")
        
        # テストケース3: パラメータなし
        params = self.scraper._parse_parameters_from_definition("TestClass()")
        print(f"Test 3 - Expected: 0, Got: {len(params)}, Params: {[(p.name, p.type) for p in params]}")
        self.assertEqual(len(params), 0)
        
        # テストケース4: 複雑な型
        params = self.scraper._parse_parameters_from_definition("TestClass(List<string> items, Dictionary<int, string> map)")
        print(f"Test 4 - Expected: 2, Got: {len(params)}, Params: {[(p.name, p.type) for p in params]}")
        self.assertEqual(len(params), 2)
        self.assertEqual(params[0].name, "items")
        self.assertEqual(params[0].type, "List<string>")
        self.assertEqual(params[1].name, "map")
        self.assertEqual(params[1].type, "Dictionary<int, string>")
    
    def test_parse_single_parameter(self):
        """単一パラメータ解析のテスト"""
        # 基本的なパラメータ
        param = self.scraper._parse_single_parameter("int value")
        self.assertIsNotNone(param)
        self.assertEqual(param.name, "value")
        self.assertEqual(param.type, "int")
        
        # デフォルト値付きパラメータ
        param = self.scraper._parse_single_parameter("string name = \"default\"")
        self.assertIsNotNone(param)
        self.assertEqual(param.name, "name")
        self.assertEqual(param.type, "string")
        
        # 配列型
        param = self.scraper._parse_single_parameter("int[] values")
        self.assertIsNotNone(param)
        self.assertEqual(param.name, "values")
        self.assertEqual(param.type, "int[]")
        
        # ref/out修飾子
        param = self.scraper._parse_single_parameter("ref int value")
        self.assertIsNotNone(param)
        self.assertEqual(param.name, "value")
        self.assertEqual(param.type, "int")
    
    def test_extract_constructors_from_code_with_mock_html(self):
        """モックHTMLを使用したコンストラクタ抽出のテスト"""
        # テスト用のHTML
        html_content = """
        <div class="memproto">
            <div class="definition">
                public TestClass(int id, string name)
            </div>
        </div>
        <div class="code">
            private TestClass()
        </div>
        <div class="static-field">
            static readonly Guid TestId = new Guid("12345");
        </div>
        """
        
        soup = BeautifulSoup(html_content, 'html.parser')
        constructors = self.scraper._extract_constructors_from_code(soup, "TestClass")
        
        print(f"Found {len(constructors)} constructors:")
        for i, c in enumerate(constructors):
            print(f"  {i+1}. {c.access_modifier} {c.name}({', '.join([f'{p.type} {p.name}' for p in c.parameters])})")
        
        # 2つのコンストラクタが見つかることを確認
        self.assertEqual(len(constructors), 2)
        
        # 最初のコンストラクタ（public）
        public_constructor = next((c for c in constructors if c.access_modifier == "public"), None)
        self.assertIsNotNone(public_constructor)
        self.assertEqual(public_constructor.name, "TestClass")
        self.assertEqual(len(public_constructor.parameters), 2)
        self.assertEqual(public_constructor.parameters[0].name, "id")
        self.assertEqual(public_constructor.parameters[0].type, "int")
        self.assertEqual(public_constructor.parameters[1].name, "name")
        self.assertEqual(public_constructor.parameters[1].type, "string")
        
        # 2番目のコンストラクタ（private）
        private_constructor = next((c for c in constructors if c.access_modifier == "private"), None)
        self.assertIsNotNone(private_constructor)
        self.assertEqual(private_constructor.name, "TestClass")
        self.assertEqual(len(private_constructor.parameters), 0)
    
    def test_extract_constructors_from_table_with_mock_html(self):
        """モックHTMLテーブルを使用したコンストラクタ抽出のテスト"""
        html_content = """
        <table>
            <tr>
                <td>TestClass(int value)</td>
                <td>値を指定してインスタンスを初期化します</td>
            </tr>
            <tr>
                <td>TestClass()</td>
                <td>デフォルトコンストラクタ</td>
            </tr>
            <tr>
                <td>static readonly Guid Id = new Guid("123")</td>
                <td>静的フィールド</td>
            </tr>
        </table>
        """
        
        soup = BeautifulSoup(html_content, 'html.parser')
        constructors = self.scraper._extract_constructors_from_table(soup, "TestClass")
        
        # 2つのコンストラクタが見つかることを確認（静的フィールドは除外）
        self.assertEqual(len(constructors), 2)
        
        # パラメータ付きコンストラクタ
        param_constructor = next((c for c in constructors if len(c.parameters) > 0), None)
        self.assertIsNotNone(param_constructor)
        self.assertEqual(param_constructor.name, "TestClass")
        self.assertEqual(len(param_constructor.parameters), 1)
        self.assertEqual(param_constructor.parameters[0].name, "value")
        self.assertEqual(param_constructor.parameters[0].type, "int")
        self.assertEqual(param_constructor.description, "値を指定してインスタンスを初期化します")
        
        # デフォルトコンストラクタ
        default_constructor = next((c for c in constructors if len(c.parameters) == 0), None)
        self.assertIsNotNone(default_constructor)
        self.assertEqual(default_constructor.name, "TestClass")
        self.assertEqual(default_constructor.description, "デフォルトコンストラクタ")
    
    def test_filter_static_fields(self):
        """静的フィールドの除外テスト"""
        html_content = """
        <div class="code">
            static readonly Guid TestId = new Guid("12345");
            public static TestClass Instance = new TestClass();
            const int MaxValue = 100;
            public TestClass(int value)
        </div>
        """
        
        soup = BeautifulSoup(html_content, 'html.parser')
        constructors = self.scraper._extract_constructors_from_code(soup, "TestClass")
        
        print(f"Found {len(constructors)} constructors:")
        for i, c in enumerate(constructors):
            print(f"  {i+1}. {c.access_modifier} {c.name}({', '.join([f'{p.type} {p.name}' for p in c.parameters])})")
        
        # 静的フィールドは除外され、コンストラクタのみが抽出されることを確認
        self.assertEqual(len(constructors), 1)
        self.assertEqual(constructors[0].name, "TestClass")
        self.assertEqual(len(constructors[0].parameters), 1)
        self.assertEqual(constructors[0].parameters[0].name, "value")
        self.assertEqual(constructors[0].parameters[0].type, "int")


if __name__ == '__main__':
    unittest.main()