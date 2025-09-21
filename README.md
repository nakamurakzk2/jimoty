# Jimoty Zero Yen Watcher

ジモティーの全国新着「0円」投稿を素早く収集するための小さなツールセットです。HTTPクライアントで検索一覧を取得し、構造化データ（JSON-LD）やDOMを解析して投稿情報を抽出します。JSON キャッシュを使って「未読」のみを抽出することもできます。

> **注意**: 実際のジモティーサイトはアクセス制限や利用規約があります。自動取得を行う前に最新の利用規約を必ず確認し、過剰なリクエストを避けてください。必要であれば User-Agent やアクセス間隔を調整してください。

## 使い方

### セットアップ

任意ですが仮想環境を作成すると便利です。追加ライブラリは不要なので、標準ライブラリだけで実行できます。

### CLI で最新 0 円投稿を取得

```bash
python -m jimoty_zero_yen.cli --pages 2 --cache data/cache.json --json
```

- `--pages`: 取得したいページ数（デフォルト 1）。
- `--cache`: 指定すると、同じ投稿 ID を持つアイテムはスキップされます。
- `--json`: JSON 形式で出力します。省略時は人間が読みやすいテキスト形式。

### Python から利用

```python
from jimoty_zero_yen import JimotyClient

client = JimotyClient()
listings = client.fetch_zero_yen_listings(pages=1)
for listing in listings:
    print(listing.title, listing.url)
```

### AI 連携のヒント

抽出した `Listing` オブジェクトはプレーンな Python データクラスです。例えば OpenAI API や埋め込みモデルに渡して要約・タグ付け・レコメンドといった AI 処理を追加することができます。`Listing` オブジェクトを辞書に変換するヘルパー関数 `_listing_to_dict` は CLI に含まれているので、同様の処理を参考にしてください。

## テスト

```bash
python -m unittest discover
```

## ライセンス

MIT
