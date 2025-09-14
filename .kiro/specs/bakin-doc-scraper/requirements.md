# Requirements Document

## Introduction

RPG Developer Bakinのドキュメントをローカルに保存し、JSON形式で構造化してからMarkdown形式に変換するツールを開発します。このツールにより、Bakinの独自C#クラスのドキュメントをオフラインで参照でき、開発効率を向上させることができます。

## Requirements

### Requirement 1

**User Story:** 開発者として、BakinのC#ドキュメントをローカルに保存したい。そうすることで、オフラインでもドキュメントを参照できるようになる。

#### Acceptance Criteria

1. WHEN ユーザーがスクレイピングを開始する THEN システムは https://rpgbakin.com/csreference/doc/ja/namespaces.html から開始する
2. WHEN システムがnamespaces.htmlページにアクセスする THEN システムはすべての名前空間リンクを抽出する
3. WHEN システムが各名前空間ページにアクセスする THEN システムはクラス、メソッド、プロパティの情報を抽出する
4. WHEN ドキュメント抽出が完了する THEN システムはJSON形式でデータを保存する

### Requirement 2

**User Story:** 開発者として、抽出したドキュメントをJSON形式で保存したい。そうすることで、構造化されたデータとして後で処理できるようになる。

#### Acceptance Criteria

1. WHEN ドキュメントデータが抽出される THEN システムは階層構造を保持したJSON形式で保存する
2. WHEN JSONファイルが作成される THEN システムは名前空間、クラス、メソッド、プロパティの情報を含む
3. WHEN JSONファイルが保存される THEN システムはファイル名に日付を含める
4. IF 既存のJSONファイルが存在する THEN システムは上書き確認を求める

### Requirement 3

**User Story:** 開発者として、JSONデータをMarkdown形式に変換したい。そうすることで、読みやすい形式でドキュメントを閲覧できるようになる。

#### Acceptance Criteria

1. WHEN ユーザーがMarkdown変換を実行する THEN システムはJSONファイルを読み込む
2. WHEN JSONデータが処理される THEN システムは階層構造を保持したMarkdownを生成する
3. WHEN Markdownファイルが作成される THEN システムは名前空間ごとに分割されたファイル構造を作成する
4. WHEN Markdownファイルが保存される THEN システムは適切なフォルダ構造を作成する

### Requirement 4

**User Story:** 開発者として、スクレイピング処理の進行状況を確認したい。そうすることで、処理の完了を把握できるようになる。

#### Acceptance Criteria

1. WHEN スクレイピングが開始される THEN システムは進行状況を表示する
2. WHEN 各ページが処理される THEN システムは現在処理中のページ名を表示する
3. WHEN エラーが発生する THEN システムはエラー内容とスキップしたページを記録する
4. WHEN 処理が完了する THEN システムは処理結果のサマリーを表示する

### Requirement 5

**User Story:** 開発者として、ネットワークエラーや一時的な障害に対応したい。そうすることで、安定してドキュメントを取得できるようになる。

#### Acceptance Criteria

1. WHEN ネットワークエラーが発生する THEN システムは自動的にリトライを実行する
2. WHEN リトライが失敗する THEN システムはエラーを記録して次のページに進む
3. WHEN レート制限を考慮する THEN システムはリクエスト間に適切な間隔を設ける
4. IF 中断された場合 THEN システムは処理済みのデータを保持して再開できる