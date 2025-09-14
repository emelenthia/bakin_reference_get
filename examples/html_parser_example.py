"""
HTML解析ユーティリティの使用例

このファイルは、HTML解析ユーティリティの基本的な使用方法を示します。
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.utils.html_parser import HTMLParser, parse_html, to_absolute_url


def main():
    """HTML解析ユーティリティの使用例を実行します"""
    
    # サンプルHTML（Bakinドキュメントの構造を模擬）
    sample_html = """
    <html>
        <head>
            <title>Bakin C# Reference - Namespace List</title>
        </head>
        <body>
            <div class="content">
                <h1>Namespaces</h1>
                <div class="namespace-list">
                    <h2><a href="namespace_yukar_1_1_engine.html">Yukar.Engine</a></h2>
                    <p>Core engine functionality</p>
                    <ul class="class-list">
                        <li><a href="class_yukar_1_1_engine_1_1_game_object.html">GameObject</a></li>
                        <li><a href="class_yukar_1_1_engine_1_1_component.html">Component</a></li>
                    </ul>
                    
                    <h2><a href="namespace_yukar_1_1_common.html">Yukar.Common</a></h2>
                    <p>Common utilities and data structures</p>
                    <ul class="class-list">
                        <li><a href="class_yukar_1_1_common_1_1_vector3.html">Vector3</a></li>
                        <li><a href="class_yukar_1_1_common_1_1_color.html">Color</a></li>
                    </ul>
                </div>
                
                <table class="method-table">
                    <thead>
                        <tr><th>Method</th><th>Return Type</th><th>Description</th></tr>
                    </thead>
                    <tbody>
                        <tr><td>Initialize</td><td>void</td><td>Initializes the system</td></tr>
                        <tr><td>Update</td><td>bool</td><td>Updates the system state</td></tr>
                    </tbody>
                </table>
            </div>
        </body>
    </html>
    """
    
    # HTMLParserを初期化
    base_url = "https://rpgbakin.com/csreference/doc/ja/"
    parser = HTMLParser(base_url)
    
    print("=== HTML解析ユーティリティの使用例 ===\n")
    
    # 1. HTMLを解析
    print("1. HTML解析:")
    soup = parser.parse_html(sample_html)
    title = soup.title.string if soup.title else "No title"
    print(f"   ページタイトル: {title}")
    
    # 2. リンクを抽出（絶対URLに変換）
    print("\n2. リンク抽出（絶対URL変換）:")
    links = parser.extract_links(soup, make_absolute=True)
    for i, link in enumerate(links, 1):
        print(f"   {i}. {link}")
    
    # 3. 相対URLを絶対URLに変換
    print("\n3. 相対URL変換の例:")
    relative_urls = [
        "class_example.html",
        "../parent/file.html",
        "/root/absolute.html",
        "https://external.com/already-absolute.html"
    ]
    
    for url in relative_urls:
        absolute = parser.to_absolute_url(url)
        print(f"   {url} -> {absolute}")
    
    # 4. テーブルデータを抽出
    print("\n4. テーブルデータ抽出:")
    table_data = parser.extract_table_data(soup, ".method-table")
    for row in table_data:
        print(f"   {row}")
    
    # 5. テキストコンテンツを抽出
    print("\n5. テキストコンテンツ抽出:")
    h1_element = soup.select_one("h1")
    if h1_element:
        text = parser.extract_text_content(h1_element)
        print(f"   H1テキスト: {text}")
    
    # 6. 特定のテキストで要素を検索
    print("\n6. テキストによる要素検索:")
    element = parser.find_element_by_text(soup, "Namespaces")
    if element:
        print(f"   見つかった要素: <{element.name}>{element.string}</{element.name}>")
    
    # 7. ヘルパー関数の使用例
    print("\n7. ヘルパー関数の使用例:")
    
    # 簡単なHTML解析
    simple_html = "<p>Hello, World!</p>"
    simple_soup = parse_html(simple_html)
    print(f"   簡単な解析: {simple_soup.p.string}")
    
    # 簡単なURL変換
    simple_absolute = to_absolute_url("test.html", "https://example.com/")
    print(f"   簡単なURL変換: test.html -> {simple_absolute}")
    
    # 8. テキストクリーンアップ
    print("\n8. テキストクリーンアップ:")
    dirty_text = "  This   has    multiple   spaces  \n\t  "
    clean_text = parser.clean_html_text(dirty_text)
    print(f"   元のテキスト: '{dirty_text}'")
    print(f"   クリーンアップ後: '{clean_text}'")
    
    print("\n=== 使用例完了 ===")


if __name__ == "__main__":
    main()