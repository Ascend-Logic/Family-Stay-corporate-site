# Nowhere Group サイトの更新方法

下層ページ（about / company / service / group / brand / news / column / recruit / contact / privacy）はこのフォルダのソースから生成しています。
生成済みの `*/index.html` を直接編集せず、ここを編集してからビルドしてください。トップ（index.html）は直接編集します。

サイト構成は「コーポレートサイトアウトライン」（2026年10月）に沿っています。
グローバルナビ: 私たちについて / 事業紹介 / グループ会社 / ブランド・実績 / お知らせ / 採用情報 / お問い合わせ（英語はデザイン上のサブ見出しのみ）

```
cd nowhere-group
python3 _build/build.py
```

- `pages/` … 固定ページの本文。先頭行の `<!--meta {...} -->` にタイトル・説明文・ヒーロー画像などを書く
  - `about.html` 私たちについて（経営理念・代表メッセージ・歩み・グループ体制・組織体制・役員）
  - `company.html` 会社概要（法人情報のみ）
  - `service.html` + `service/produce.html` `operation.html` `supply.html` 事業紹介（宿泊事業部 / SUPPLY事業部）
  - `group.html` + `group/nowhere.html` `vestport.html` `cleanx9.html` `family-stay.html` グループ会社
  - `brand.html` ブランド・実績（ホテルブランド / 実績・プロジェクト / プロデュース施設一覧 / パートナー / 評価・受賞）
  - 旧構成の `service/hotel.html` などはナビから外れているが、URL を残すためそのまま生成している
- `news/<id>.html` / `column/<id>.html` … 記事。meta に `date`（2026.06.05 形式）・`title`・`thumb`・`category`
  - ニュースの `category` は `build.py` の `NEWS_CATEGORIES`（グループ / Nowhere Group / VESTPORT / CLEANX9 / Family Stay / プレスリリース / メディア掲載 / 受賞・認定）から選ぶ。一覧ページのカテゴリ絞り込みに使う
  - ニュースの `short` を入れると、トップの最新ニュース欄ではその短いタイトルを使う
  - コラムはナビ・トップから外した（アウトラインの方針）。記事ページ自体は URL 維持のため生成している
- 本文中の `{{root}}` はページ階層に合わせた相対パスに置き換わる（例: `{{root}}images/...`）
- ビルドすると一覧ページと、トップ（index.html）の Column / News 最新3件も更新される

## トップページ（index.html）

- 見た目は `assets/css/top.css`。PC（901px以上）は 1440px 幅のデザインを画面幅に合わせて拡大縮小し、スマホ（900px以下）は同じ CSS の末尾にある1列レイアウトに切り替わる
- 文言を変えるときは `index.html` を直接編集する。英語トップは `build.py` の `EN_TOP` で同じ文言を置き換えて生成しているので、そちらも合わせて直す（合わないとビルドが止まる）
- 英語版がないページ（私たちについて / グループ会社 / ブランド・実績 / お知らせ / 採用）へのリンクは、英語トップでは日本語ページへ `lang="ja"` 付きでリンクする

## ヘッダー（全ページ共通）

- 見た目は `assets/css/header.css`、スマホメニューの開閉は `assets/js/header.js`。トップ（index.html）と下層ページの両方がこれを読み込む
- トップのヘッダーは、拡大縮小する `.page` の外（body 直下）に置いてある。`.page` の中に戻すと画面幅でヘッダーの大きさが変わるので注意
- メニュー項目を変えるときは、トップは `index.html` の `<header>`、下層は `build.py` の `NAV` / `NAV_EN`（採用情報・お問い合わせ・言語切替は `layout()` 内）

## 記事を追加するとき

1. `news/` に新しい ID のファイルを作る（既存ファイルをコピーして meta と本文を書き換える）
2. 画像は `images/uploads/年/月/` に置き、`{{root}}images/uploads/...` で参照する
3. `python3 _build/build.py` を実行

## 採用情報（/recruit/）

- 採用トップの構成（まだない宿泊の未来を、一緒につくる / 私たちが目指す未来 / 仕事を知る / プロジェクトを知る / 募集職種 / オープンポジション）は `build.py` の `build_recruit()`
  - アウトラインにある「人を知る（社員インタビュー）」「働く環境・制度」は原稿が揃ってから追加する
- 求人は `recruit/<nowhere-01 など>.html` に1件ずつ置く。meta の `order` が一覧の並び順、`company` が `nowhere` / `vestport` / `cleanx9` / `family-stay` のどれに載るか（`BRANDS`）
- 一覧のカードには meta の `summary`（業務内容）・`place`（就業場所）・`salary`（賃金）を表示する
- `_open-position.html` と `_privacy.html` はオープンポジションと採用プライバシーポリシーの本文
- 応募の受付は、これまでどおり Notion の応募フォームを使う（URL は `build.py` の `APPLY_FORM` / `OPEN_FORM`）
- 求人を追加・終了したら、Notion の応募フォームの「ご希望の求人」の選択肢も合わせて直す

## 英語版（/en/）

- 下層ページは `pages/en/` の本文から `en/` 以下に生成する（About / Business / Contact / Privacy と旧 service 下層）。本文中の `{{home}}` は英語トップ（en/）への相対パスになる
- 英語トップ `en/index.html` は日本語トップ `index.html` から自動生成する。文言の対応表は `build.py` の `EN_TOP`
  - 日本語トップの文言を変えると対応表と合わなくなり、ビルドがエラーで止まる。そのときは `EN_TOP` の該当行を直す
- ニュース・コラムは英語版がないため、英語ページからは日本語の記事にリンクしている

## 未対応・要設定

- お問い合わせフォームの送信先が未設定（`pages/contact.html` と `pages/en/contact.html` の form の `action`）。現状は送信せずに案内文を表示する
- 公式 note への外部リンク（お知らせ）は URL が未確認のため未設置
- グループ各社の役員（VESTPORT 高橋氏 / CLEANX9 八木氏 / Family Stay 山下氏・早乙女氏）は姓のみ掲載。フルネーム確定後に `pages/group/*.html` を直す
- VESTPORT / CLEANX9 のロゴ画像がないため文字ロゴで表示している（`co-logo-text`）。ロゴが揃ったら `pages/group.html` / `pages/about.html` を差し替える
- ブランド・実績の各プロジェクト詳細ページ（課題→企画→実装→結果のケーススタディ）は原稿待ち。現状は施設サイトへの外部リンク
