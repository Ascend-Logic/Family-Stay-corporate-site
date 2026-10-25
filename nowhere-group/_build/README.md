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
  - ニュースの `category`（記事種別）は `build.py` の `NEWS_CATS`（お知らせ / 施設・プロジェクト / プレスリリース / メディア掲載 / 受賞・認定）から選ぶ。一覧ページはこの種別で絞り込める
  - 発信会社は `company`（Nowhere Group / VESTPORT / CLEANX9 / Family Stay）に書く。種別とは別のラベルとして一覧・記事・トップに出る
  - ニュースの `short` を入れると、トップの最新ニュース欄ではその短いタイトルを使う
  - 本文中の `{{root}}` はページ階層に合わせた相対パスに置き換わる（例: `{{root}}images/...`）
- ビルドすると一覧ページと、トップ（index.html）の News 最新3件、`sitemap.xml` も更新される（コラムはナビ・トップに出さない方針。ページ自体は `column/` に残る）

## トップページ（index.html）

- 見た目は `assets/css/top.css`。PC（901px以上）は 1440px 幅のデザインを画面幅に合わせて拡大縮小し、スマホ（900px以下）は同じ CSS の末尾にある1列レイアウトに切り替わる
- 文言を変えるときは `index.html` を直接編集する。英語トップは `build.py` の `EN_TOP` で同じ文言を置き換えて生成しているので、そちらも合わせて直す（合わないとビルドが止まる）
- 既存の5セクション（ヒーロー / Company / Service / Hotel・Works・News / フッター）は 1440px 固定の絶対配置。間に挟んだ追加セクション（経営理念 / バリューチェーン / 事業紹介 / 強み / パートナー・受賞 / 数字 / 代表メッセージ / 採用）は `class="tp"` の通常フローで、スタイルは `top.css` の「追加セクション」の箇所
- 数字で見る Nowhere Group（累計プロデュース実績・展開エリア・累計清掃件数の3指標）は `index.html` の `#numbers` を直接書き換える
- 旧 `#service`・`#business` へのリンクは、BUSINESS 冒頭の空要素（`span.anchor`）で受けている。消さないこと
- ブランドのロゴは `images/brands/`。ロゴは切り抜かず、カードの背景（`--logo-bg`）をロゴの背景色に合わせて収める

## ヘッダー（全ページ共通）

- 見た目は `assets/css/header.css`、スマホメニューの開閉は `assets/js/header.js`。トップ（index.html）と下層ページの両方がこれを読み込む
- トップのヘッダーは、拡大縮小する `.page` の外（body 直下）に置いてある。`.page` の中に戻すと画面幅でヘッダーの大きさが変わるので注意
- メニューは6項目（私たちについて／事業紹介／ブランド・実績／お知らせ／採用情報／お問い合わせ）。変えるときは、トップは `index.html` の `<header>` とフッターの `.ft-menu`、下層は `build.py` の `NAV` / `NAV_EN` とフッターを直す

## 記事を追加するとき

1. `news/` に新しい ID のファイルを作る（既存ファイルをコピーして meta と本文を書き換える）
2. 画像は `images/uploads/年/月/` に置き、`{{root}}images/uploads/...` で参照する
3. `python3 _build/build.py` を実行

## 採用情報（/recruit/）

- 求人は `recruit/<nowhere-01 など>.html` に1件ずつ置く。meta の `order` が一覧の並び順、`company` が雇用主（`nowhere` / `vestport` / `cleanx9` / `familystay`）。採用トップは会社別の4枚カード → `/recruit/jobs/<会社>/`（会社別求人一覧）→ 個別求人の順につながる
- 募集を終えた求人は meta に `"closed": true` を付ける。一覧と件数から外れ、詳細ページは応募ボタンなし・noindex になる
- カジュアル面談の申込先は `build.py` の `CASUAL_FORM`。採用専用で実際に受信できる URL が決まるまで空にしておく（空の間はボタンを出さない）
- 「仕事と人を知る」（お仕事図鑑・社員インタビュー）と「プロジェクトを知る」（宿泊施設プロデュースの裏側）は公式 note の記事カード。`build.py` の `NOTE_WORK` / `NOTE_PEOPLE` / `NOTE_PROJECTS` に記事を足し、見出し画像を `images/uploads/note/<記事キー>.jpg`（幅800px）に保存する
- 「働く環境・制度」の項目は `build.py` の `ENVIRONMENT`
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

- お問い合わせフォームの送信先が未設定（`pages/contact.html` と `pages/en/contact.html` の form の `action`、日英とも同じ URL）。`action="#"` の間は送信せず「準備中」と表示する。**この状態では公開しない**
  - 送信は `assets/js/sub.js` が `fetch` で POST（FormData、`Accept: application/json`）。応答が 2xx のときだけ「送信しました」を出し、それ以外は失敗表示と再送ボタンになる
  - 送る項目：`name` / `email` / `tel`（任意）/ `company`（任意）/ `facility`（任意・プロデュース／運営／宿泊予約のときだけ）/ `type`（種別の値）/ `type_label` / `route`（社内受付先）/ `message` / `agree` / `lang`（ja / en）。`_gotcha` はスパム対策用で、値が入っていたら送らない
  - 送信先側で `type`（または `route`）ごとに通知先を振り分ける。担当不在時の副担当と、誤振り分け時の社内転送先も送信先側で決める

    | type | 種別 | 社内受付先 |
    |---|---|---|
    | produce | 宿泊施設プロデュースについて | Nowhere Group 宿泊事業部 |
    | operation | 宿泊施設運営について | Nowhere Group 宿泊事業部 |
    | real-estate | 不動産・工事・建物管理について | VESTPORT |
    | cleaning | 清掃について | CLEANX9 |
    | supply | ホテルSUPPLYについて | Nowhere Group SUPPLY事業部 |
    | brand | ホテルブランド・共同開発について | グループ事業企画部・営業担当 |
    | family-stay | Family Stay（OTA・リテールメディア）について | Family Stay 事業開発窓口 |
    | partnership | パートナー・事業提携について | グループ営業部／社長室 |
    | reservation | 宿泊予約・施設利用について | 各施設ゲスト専用窓口 |
    | recruit | 採用・カジュアル面談について | 社長室・採用窓口（フォームでは受け付けず採用ページへ案内） |
    | media | 取材・広報について | PR担当 |
    | other | その他 | コーポレート本部 |

  - 公開前に、日本語・英語それぞれのフォームからテスト送信し、指定窓口への実着信、主要種別ごとの振り分け、送信エラー時の表示を確認する。合格するまで公開しない
  - 種別を増減するときは、日英2ファイルの `<option>`（`value` / `data-route` / `data-hint`）と送信先の振り分けを合わせて直す

## 役員紹介・代表SNS・note（素材が揃ったら `build.py` の設定を埋める）

- 役員紹介は `build.py` の `OFFICERS`。会社ごとに `(氏名, 英語名, 役職, 英語役職, 写真ファイル名)` を並べる。氏名が空の行は表示されない（伏字のまま載せないため）。写真は `images/site/people/` に置く
  - 私たちについての `{{officers:all}}` で経営陣一覧（1人1枚、兼務は会社ごとの役職を並記）になる。各社ページには出さない
- 代表メッセージの SNS リンクは `CEO_SNS`（YouTube / X）。URL を入れたものだけ表示
- 公式 note は `NOTE_URL`。お知らせ一覧・下層フッター・採用ページに「公式note」リンクが出る
- お知らせの記事ページには X / LINE / Facebook / リンクコピーのシェアボタンが付く（`assets/js/sub.js`）
