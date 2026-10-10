# Nowhere Group 下層ページの更新方法

下層ページ（company / service / column / news / contact / privacy）はこのフォルダのソースから生成しています。
生成済みの `*/index.html` を直接編集せず、ここを編集してからビルドしてください。

```
cd nowhere-group
python3 _build/build.py
```

- `pages/` … 固定ページの本文。先頭行の `<!--meta {...} -->` にタイトル・説明文・ヒーロー画像などを書く
  - 写真ヒーロー（`hero.type: photo`）で顔などが切れるときは `hero.pos` に `center top` のように切り抜き位置を書く
- `news/<id>.html` / `column/<id>.html` … 記事。meta に `date`（2026.06.05 形式）・`title`・`thumb`・`category`
  - ニュースの `category` は `build.py` の `NEWS_CATS`（グループ / Nowhere Group / VESTPORT / CLEANX9 / Family Stay / プレスリリース / メディア掲載 / 受賞・認定）から選ぶ。一覧ページはこのカテゴリで絞り込める
  - ニュースの `short` を入れると、トップの最新ニュース欄ではその短いタイトルを使う
  - 公式 note へのリンクを出すときは `build.py` の `NOTE_URL` に URL を入れる
- 本文中の `{{root}}` はページ階層に合わせた相対パスに置き換わる（例: `{{root}}images/...`）
- ビルドすると一覧ページと、トップ（index.html）の News 最新3件も更新される（コラムはナビ・トップに出さない方針。ページ自体は `column/` に残る）

## トップページ（index.html）

- 見た目は `assets/css/top.css`。PC（901px以上）は 1440px 幅のデザインを画面幅に合わせて拡大縮小し、スマホ（900px以下）は同じ CSS の末尾にある1列レイアウトに切り替わる
- 文言を変えるときは `index.html` を直接編集する。英語トップは `build.py` の `EN_TOP` で同じ文言を置き換えて生成しているので、そちらも合わせて直す（合わないとビルドが止まる）
- 既存の5セクション（ヒーロー / Company / Service / Hotel・Works・News / フッター）は 1440px 固定の絶対配置。間に挟んだ追加セクション（経営理念 / バリューチェーン / 事業紹介 / 強み / パートナー・受賞 / 数字 / 代表メッセージ / 採用）は `class="tp"` の通常フローで、スタイルは `top.css` の「追加セクション」の箇所
- 数字で見る Nowhere Group（施設数・エリア数・清掃件数など）は `index.html` の `#numbers` を直接書き換える

## ヘッダー（全ページ共通）

- 見た目は `assets/css/header.css`、スマホメニューの開閉は `assets/js/header.js`。トップ（index.html）と下層ページの両方がこれを読み込む
- トップのヘッダーは、拡大縮小する `.page` の外（body 直下）に置いてある。`.page` の中に戻すと画面幅でヘッダーの大きさが変わるので注意
- メニュー項目を変えるときは、トップは `index.html` の `<header>`、下層は `build.py` の `NAV` / `NAV_EN` を直す

## 記事を追加するとき

1. `news/` に新しい ID のファイルを作る（既存ファイルをコピーして meta と本文を書き換える）
2. 画像は `images/uploads/年/月/` に置き、`{{root}}images/uploads/...` で参照する
3. `python3 _build/build.py` を実行

## 採用情報（/recruit/）

- 求人は `recruit/<nowhere-01 など>.html` に1件ずつ置く。meta の `order` が一覧の並び順、`company` が `nowhere` / `vestport` / `cleanx9` / `familystay` のどこに載るか（求人がない会社はオープンポジションへの案内を出す）
- 「仕事を知る」の職種、「人を知る」のインタビュー枠、「働く環境・制度」の項目は `build.py` の `JOB_TYPES` / `PEOPLE` / `ENVIRONMENT`。インタビュー記事はまだないので「準備中」表示
- 一覧のカードには meta の `summary`（業務内容）・`place`（就業場所）・`salary`（賃金）を表示する
- `_open-position.html` と `_privacy.html` はオープンポジションと採用プライバシーポリシーの本文
- 応募の受付は、これまでどおり Notion の応募フォームを使う（URL は `build.py` の `APPLY_FORM` / `OPEN_FORM`）
- 求人を追加・終了したら、Notion の応募フォームの「ご希望の求人」の選択肢も合わせて直す

## 英語版（/en/）

- 下層ページは `pages/en/` の本文から `en/` 以下に生成する。本文中の `{{home}}` は英語トップ（en/）への相対パスになる
- 英語トップ `en/index.html` は日本語トップ `index.html` から自動生成する。文言の対応表は `build.py` の `EN_TOP`
  - 日本語トップの文言を変えると対応表と合わなくなり、ビルドがエラーで止まる。そのときは `EN_TOP` の該当行を直す
- ニュース・コラムは英語版がないため、英語ページからは日本語の記事にリンクしている

## 未対応・要設定

- お問い合わせフォームの送信先が未設定（`pages/contact.html` と `pages/en/contact.html` の form の `action`）。現状は送信せずに案内文を表示する
