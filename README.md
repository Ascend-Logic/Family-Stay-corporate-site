# Family-Stay-corporate-site

株式会社Family Stay のコーポレートサイト（静的HTML）。GitHub Pages（main ブランチ / ルート）で公開。

- `index.html` トップ / `company.html` 会社概要 / `partner.html` パートナー募集
- `assets/css/style.css` スタイル（900px 以下でスマホレイアウト）
- `assets/js/main.js` スマホメニュー・スクロール表示・雲や鳥のパララックス（`prefers-reduced-motion` で停止）
- `[要確認]` の箇所は確定情報に差し替えてください
- パートナー募集フォームは送信先未設定（Formspree / Googleフォーム等を `action` に設定）

## ローカル確認

```
python3 -m http.server 8000
```
