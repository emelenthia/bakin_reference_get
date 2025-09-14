# Bakin Documentation Scraper

RPG Developer Bakinの公式C#リファレンスドキュメントをスクレイピングし、JSON形式で構造化してからMarkdown形式に変換するツールです。

## プロジェクト構造

```
bakin-doc-scraper/
├── src/                    # メインソースコード
│   ├── models/            # データモデル
│   ├── scraper/           # Webスクレイピング機能
│   ├── processor/         # データ処理・変換機能
│   └── utils/             # ユーティリティ関数
├── tests/                 # テストファイル
├── output/                # 出力ファイル（JSON、Markdown）
├── config.yaml           # 設定ファイル
├── requirements.txt      # Python依存関係
├── main.py              # メインエントリーポイント
└── README.md            # このファイル
```

## セットアップ

1. 依存関係をインストール:
```bash
pip install -r requirements.txt
```

2. 設定ファイルを確認・編集:
```bash
# config.yamlを必要に応じて編集
```

3. 実行:
```bash
# ドキュメントをスクレイピング
python main.py --scrape

# JSONをMarkdownに変換
python main.py --convert

# 両方を実行
python main.py --scrape --convert
```

## 機能

- Bakin C#ドキュメントの自動スクレイピング
- 構造化されたJSON形式での保存
- 読みやすいMarkdown形式への変換
- 進行状況の表示
- エラー処理とリトライ機能
- 中断・再開機能

## 設定

`config.yaml`ファイルで以下の設定が可能です:

- スクレイピング対象URL
- HTTP設定（タイムアウト、リトライ等）
- 出力設定
- ログ設定

詳細は`config.yaml`ファイルを参照してください。

## 免責事項

本プロジェクトの開発にはAI（Kiro）が使用されています。

- AIによって生成されたコードは品質保証されていません
- 使用者の責任において動作確認を行ってください
- 予期しない動作やエラーが発生する可能性があります
- 本ツールの使用により生じた損害について、作者は一切の責任を負いません
