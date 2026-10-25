#!/usr/bin/env python3
"""Nowhere Group 下層ページ生成スクリプト

使い方（nowhere-group ディレクトリで実行）:
    python3 _build/build.py

- _build/pages/**.html   … 各ページの本文。先頭行の <!--meta {...} --> にタイトル等を書く
- _build/news/<id>.html   … ニュース記事（先頭行 meta に date/title/thumb/category）
- _build/column/<id>.html … コラム記事（同上）
本文中の {{root}} はページ階層に応じた相対パス（../ 等）に置き換わる。
ニュース・コラムの一覧ページと、トップ(index.html)の最新3件もこのスクリプトが更新する。
英語版は _build/pages/en/ から en/ 以下に生成し、英語トップ(en/index.html)は index.html を元に EN_TOP の対応表で生成する。
"""
import hashlib
import html
import json
import os
import re

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(BASE, '_build')


def asset_ver():
    """CSS/JS の内容から短いバージョン文字列を作る（?v= に付けてブラウザキャッシュを確実に更新させる）"""
    h = hashlib.md5()
    for rel in ('assets/css/header.css', 'assets/css/sub.css', 'assets/css/top.css', 'assets/js/header.js', 'assets/js/sub.js'):
        with open(os.path.join(BASE, rel), 'rb') as f:
            h.update(f.read())
    return h.hexdigest()[:8]


def photo_src(root, photo):
    """役員写真の URL。差し替え後にブラウザキャッシュが残らないよう、ファイル内容から ?v= を付ける"""
    with open(os.path.join(BASE, 'images/site/people', photo), 'rb') as f:
        return f'{root}images/site/people/{photo}?v={hashlib.md5(f.read()).hexdigest()[:8]}'


VER = asset_ver()
SITE = 'Nowhere Group株式会社'
FONTS = ('https://fonts.googleapis.com/css2?family=Bagel+Fat+One&family=Outfit:wght@500;600;700'
         '&family=Zen+Kaku+Gothic+New:wght@500;700&display=swap')

# グローバルメニュー（6項目。日英とも同じ並び。お問い合わせは layout() で右端のボタンとして出す）
NAV = [
    ('company', '私たちについて', 'company/'),
    ('service', '事業紹介', 'service/'),
    ('brand', 'ブランド・実績', 'service/regional-brand-creation/#brands'),
    ('news', 'お知らせ', 'news/'),
    ('recruit', '採用情報', 'recruit/'),
]
NOTE_URL = 'https://note.com/nowhere_group'  # 公式 note の URL。設定すると採用ページ・下層フッターに「公式note」リンクを出す
CEO_SNS = [  # 代表メッセージに出す代表個人の SNS（私たちについての代表欄とトップの代表欄だけに出す）。URL を入れたものだけ表示
    ('X', 'https://x.com/nowhere_take_'),
    ('Instagram', 'https://www.instagram.com/takeuchi_nowhere/'),
    ('YouTube', 'https://www.youtube.com/@takeuchi-no-kaitaku'),
]
# 役員紹介（会社別）。name が空のものは表示しない（氏名確定後に入れる）。photo は images/site/people/ のファイル名（なければ空）
OFFICERS = {
    'nowhere': [('竹内 剛', 'Go Takeuchi', '代表取締役 CEO', 'CEO', 'takeuchi-sq.jpg')],
    'vestport': [('竹内 剛', 'Go Takeuchi', '代表取締役 CEO', 'CEO', 'takeuchi-sq.jpg'),
                 ('髙橋 悠汰', 'Yuta Takahashi', '執行役員', 'Executive Officer', 'takahashi.jpg')],
    'cleanx9': [('竹内 剛', 'Go Takeuchi', '代表取締役 CEO', 'CEO', 'takeuchi-sq.jpg'),
                ('八木 洋平', 'Yohei Yagi', '副社長 COO', 'Vice President, COO', 'yagi.jpg')],
    'familystay': [('竹内 剛', 'Go Takeuchi', '代表取締役 CEO', 'CEO', 'takeuchi-sq.jpg'),
                   ('山下 拓朗', 'Takuro Yamashita', '取締役副社長 COO', 'Vice President, COO', 'yamashita.jpg'),
                   ('早乙女 琉真', 'Ryuma Saotome', '取締役 CTO', 'Director, CTO', 'saotome.jpg')],
}
COMPANY_NAMES = {'nowhere': ('Nowhere Group株式会社', 'Nowhere Group Inc.'), 'vestport': ('VESTPORT株式会社', 'VESTPORT Inc.'),
                 'cleanx9': ('CLEANX9株式会社', 'CLEANX9 Inc.'), 'familystay': ('株式会社Family Stay', 'Family Stay Inc.')}


def officers_html(keys, root, lang='ja'):
    """役員カード一覧（keys: 会社キーのリスト。複数なら会社ごとに見出しを付ける）"""
    out = []
    for key in keys:
        cards = []
        for ja, en, role_ja, role_en, photo in OFFICERS.get(key, []):
            if not ja:
                continue
            name, role = (en, role_en) if lang == 'en' else (ja, role_ja)
            img = (f'<span class="officer-photo"><img src="{photo_src(root, photo)}" alt="" loading="lazy"></span>' if photo
                   else '<span class="officer-photo noimg" aria-hidden="true"></span>')
            cards.append(f'<div class="officer">{img}<span class="officer-role">{esc(role)}</span><strong class="officer-name">{esc(name)}</strong></div>')
        if not cards:
            continue
        head = ''
        if len(keys) > 1:
            head = f'<h3 class="officer-company">{esc(COMPANY_NAMES[key][1 if lang == "en" else 0])}</h3>'
        out.append(f'<div class="officer-group">{head}<div class="officers">{"".join(cards)}</div></div>')
    return '\n'.join(out)


# 経営陣カードで兼務先の社名を並べる順
ROLE_COMPANY_ORDER = ('nowhere', 'familystay', 'cleanx9', 'vestport')
# 経営陣カードの並び順（ここにない人は末尾に OFFICERS の会社順で並ぶ）
OFFICER_ORDER = ('竹内 剛', '山下 拓朗', '早乙女 琉真', '八木 洋平', '髙橋 悠汰')


def officers_merged_html(root, lang='ja'):
    """経営陣一覧: 1人1枚にまとめ、兼務している会社の役職を並記する"""
    people = {}
    order = []
    for key in ('nowhere', 'vestport', 'cleanx9', 'familystay'):
        for ja, en, role_ja, role_en, photo in OFFICERS.get(key, []):
            if not ja:
                continue
            if ja not in people:
                people[ja] = {'en': en, 'photo': photo, 'roles': []}
                order.append(ja)
            if photo and not people[ja]['photo']:
                people[ja]['photo'] = photo
            people[ja]['roles'].append((key, role_en if lang == 'en' else role_ja))
    order.sort(key=lambda ja: OFFICER_ORDER.index(ja) if ja in OFFICER_ORDER else len(OFFICER_ORDER))
    cards = []
    for ja in order:
        pr = people[ja]
        name = pr['en'] if lang == 'en' else ja
        # カード用の横長写真（_build/tools/officer_wide.swift で作る <名前>-wide.jpg）。なければ正方形の写真を使う
        photo = pr['photo']
        if photo and os.path.exists(os.path.join(BASE, 'images/site/people', photo.replace('.jpg', '-wide.jpg'))):
            photo = photo.replace('.jpg', '-wide.jpg')
        img = (f'<span class="officer-photo"><img src="{photo_src(root, photo)}" alt="" width="1330" height="700" loading="lazy"></span>' if photo
               else '<span class="officer-photo noimg" aria-hidden="true"></span>')
        # 同じ役職の兼務は1行にまとめ、会社名を並べる
        grouped = {}
        for key, r in sorted(pr['roles'], key=lambda kr: ROLE_COMPANY_ORDER.index(kr[0])):
            grouped.setdefault(r, []).append(COMPANY_NAMES[key][1 if lang == 'en' else 0])
        roles = ''.join(f'<li><span class="officer-role">{esc(r)}</span><span class="officer-co">{esc(" ／ ".join(cs))}</span></li>' for r, cs in grouped.items())
        cards.append(f'<div class="officer officer-merged">{img}<div class="officer-body"><strong class="officer-name">{esc(name)}</strong><ul class="officer-roles">{roles}</ul></div></div>')
    return f'<div class="officers officers-list">{"".join(cards)}</div>'


def ceo_sns_html(lang='ja'):
    items = [f'<a href="{esc(u)}" target="_blank" rel="noopener">{esc(n)} <span class="arr">↗</span></a>' for n, u in CEO_SNS if u]
    if not items:
        return ''
    label = 'Follow the CEO' if lang == 'en' else '代表のSNS'
    return f'<div class="ceo-sns"><span>{label}</span>{"".join(items)}</div>'


def note_html(root, lang='ja'):
    """note へのリンク（URL 未設定なら空）"""
    if not NOTE_URL:
        return ''
    return (f'<div class="btn-row"><a class="btn" href="{NOTE_URL}" target="_blank" rel="noopener">'
            f'{"Read our note (Japanese)" if lang == "en" else "公式noteを見る"} <span class="arr">↗</span></a></div>')


def note_cards(root, articles):
    """note 記事カード。サムネイルは images/uploads/note/<記事キー>.jpg（note の見出し画像を保存したもの）"""
    cards = []
    for a in articles:
        cards.append(f'<a class="card note-card" href="{NOTE_URL}/n/{a["key"]}" target="_blank" rel="noopener">'
                     f'<span class="thumb"><img src="{root}images/uploads/note/{a["key"]}.jpg" alt="" loading="lazy" width="800" height="419"></span>'
                     f'<div class="row"><span class="tag">{esc(a["label"])}</span><span class="li-date">{esc(a["date"])}</span></div>'
                     f'<h3>{esc(a["title"])}</h3><span class="card-more">note で読む ↗</span></a>')
    return f'<div class="grid g3" data-rv>\n{chr(10).join(cards)}\n</div>'


def fill_tokens(body, root, lang='ja'):
    """ページ本文の {{officers:nowhere,vestport}} / {{ceo_sns}} / {{note}} を置き換える"""
    def off(m):
        keys = [k.strip() for k in m.group(1).split(',')]
        if keys == ['all']:
            return officers_merged_html(root, lang)
        return officers_html(keys, root, lang)
    body = re.sub(r'\{\{officers:([a-z0-9, ]+)\}\}', off, body)
    body = body.replace('{{ceo_sns}}', ceo_sns_html(lang))
    body = body.replace('{{note}}', note_html(root, lang))
    return body
# ニュースの記事種別（一覧の絞り込み）。発信会社は記事 meta の company に別ラベルとして書く
NEWS_CATS = ['お知らせ', '施設・プロジェクト', 'プレスリリース', 'メディア掲載', '受賞・認定']
NEWS_COMPANIES = ['Nowhere Group', 'VESTPORT', 'CLEANX9', 'Family Stay']
COLORS = {'orange': '#C94A1A', 'blue': '#2F6FD6', 'purple': '#7A5BD9', 'green': '#1B7F5A',
          'pink': '#E0689E', 'yellow': '#FFD84A'}


def esc(s):
    return html.escape(s, quote=True)


def squiggle(color='blue', size=30):
    c = COLORS.get(color, color)
    h = round(size * 26 / 30)
    return (f'<svg class="squiggle" width="{size}" height="{h}" viewBox="0 0 30 26" fill="none" '
            f'stroke="{c}" stroke-width="3.5" stroke-linecap="round" aria-hidden="true">'
            '<path d="M3 14 Q3 4 11 6 Q17 8 12 15 Q8 21 16 21 Q26 21 27 8"></path></svg>')


def read_meta(path):
    raw = open(path, encoding='utf-8').read()
    m = re.match(r'\s*<!--meta (.*?) -->\n?', raw, re.S)
    if not m:
        raise SystemExit(f'meta がありません: {path}')
    return json.loads(m.group(1)), raw[m.end():]


def lang_of(canonical):
    return 'en' if canonical.startswith('en/') else 'ja'


def crumbs_html(crumbs, root, lang='ja'):
    home = root + ('en/' if lang == 'en' else '')
    aria = 'Breadcrumb' if lang == 'en' else 'パンくずリスト'
    items = [f'<li><a href="{home}">Home</a></li>']
    for i, (label, href) in enumerate(crumbs):
        if i == len(crumbs) - 1 or not href:
            items.append(f'<li aria-current="page">{esc(label)}</li>')
        else:
            items.append(f'<li><a href="{root}{href}">{esc(label)}</a></li>')
    return f'<ol class="crumbs" aria-label="{aria}">' + ''.join(items) + '</ol>'


def hero_html(meta, root, lang='ja'):
    h = meta.get('hero')
    if not h:
        return ''
    crumbs = crumbs_html(meta.get('crumbs', []), root, lang)
    if h['type'] == 'illust':
        img = h.get('img', 'bg-company.jpg')
        return f'''<section class="ph">
<div class="ph-illust">
<img src="{root}images/{img}" alt="" width="1774" height="887">
<div class="ph-text">
<h1 class="ph-title">{esc(h['en'])}</h1>
<p class="ph-ja">{esc(h['ja'])}</p>
{crumbs}
</div>
</div>
</section>'''
    if h['type'] == 'photo':
        return f'''<section class="ph ph-photo">
<div class="wrap">
<div class="ph-head">
<div class="ph-left">
<span class="ph-en">{esc(h['en'])}</span>
<h1 class="ph-title">{esc(h['ja'])}</h1>
</div>
{crumbs}
</div>
<div class="ph-img"><img src="{root}images/{h['img']}" alt="{esc(h.get('alt', ''))}"{' style="object-position:' + esc(h['pos']) + '"' if h.get('pos') else ''}></div>
</div>
</section>'''
    raise SystemExit(f'unknown hero type: {h["type"]}')


T = {
    'ja': {
        'site': SITE, 'tagline': '旅を起点に、人々の心にアナザースカイを創る。', 'skip': '本文へスキップ',
        'logo_label': 'Nowhere Group トップへ', 'menu_label': 'メインメニュー',
        'cta_text': 'グループ各社へのお問い合わせは、こちらで一括して承ります。', 'cta_btn': 'お問い合わせフォーム',
        'address': '〒169-0075 東京都新宿区高田馬場3丁目12-2 高田馬場OCビル4階',
        'privacy': 'プライバシーポリシー', 'x_label': 'X（旧Twitter）', 'switch': ('EN', 'English'),
    },
    'en': {
        'site': 'Nowhere Group Inc.', 'tagline': 'Travel as the starting point for another sky in every heart', 'skip': 'Skip to content',
        'logo_label': 'Nowhere Group home', 'menu_label': 'Main menu',
        'cta_text': 'Inquiries for every group company are handled here, in one place.', 'cta_btn': 'Contact Form',
        'address': 'Takadanobaba OC Bldg. 4F, 3-12-2 Takadanobaba, Shinjuku-ku, Tokyo 169-0075, Japan',
        'privacy': 'Privacy Policy', 'x_label': 'X (formerly Twitter)', 'switch': ('JP', '日本語'),
    },
}
NAV_EN = [('company', 'About', 'en/company/'), ('service', 'Business', 'en/service/'),
          ('brand', 'Brands & Works', 'en/service/regional-brand-creation/#brands'), ('news', 'News', 'news/'),
          ('recruit', 'Careers', 'recruit/')]
PAGE_DIRS = set()  # build_pages で埋める（言語切替リンクの対応ページ判定用）


def counterpart(canonical):
    """反対言語の対応ページ（なければその言語のトップ）"""
    if lang_of(canonical) == 'en':
        other = canonical[3:]
        return other if (other == '' or other in PAGE_DIRS or other.split('/')[0] in ('news', 'column', 'recruit')) else ''
    other = 'en/' + canonical
    return other if other in PAGE_DIRS else 'en/'


def layout(meta, body, root, canonical):
    lang = lang_of(canonical)
    t = T[lang]
    home = root + ('en/' if lang == 'en' else '')
    current = meta.get('nav', '')
    cur = lambda key: ' aria-current="page"' if key == current else ''
    # 英語版のお知らせ・採用は日本語ページへのリンクなので lang="ja" を付ける
    ja_attr = lambda href: ' lang="ja"' if lang == 'en' and not href.startswith('en/') else ''
    nav = ''.join(f'<a href="{root}{href}"{cur(key)}{ja_attr(href)}>{label}</a>'
                  for key, label, href in (NAV_EN if lang == 'en' else NAV))
    other = counterpart(canonical)
    sw, sw_label = t['switch']
    nav += (f'<a href="{root}{other}" lang="{"ja" if lang == "en" else "en"}" hreflang="{"ja" if lang == "en" else "en"}" '
            f'aria-label="{sw_label}">{sw}</a>')
    nav += f'<a href="{home}contact/" class="nav-contact"{cur("contact")}>{"Contact" if lang == "en" else "お問い合わせ"}</a>'
    title = meta['title']
    full_title = f'{title}｜{t["site"]}' if title else f'{t["site"]}｜{t["tagline"]}'
    if lang == 'en' and title:
        full_title = f'{title} | {t["site"]}'
    desc = meta.get('description', '')
    accent = meta.get('accent', '')
    cta = '' if meta.get('cta') is False else f"""
<section class="cta" aria-labelledby="cta-title">
<img src="{root}images/bg-news.jpg" alt="" loading="lazy" width="1672" height="941">
<div class="wrap">
<h2 id="cta-title">Contact <span data-spin style="color:#FFD84A">✸</span></h2>
<p>{t['cta_text']}</p>
<a class="btn" href="{home}contact/">{t['cta_btn']} <span class="arr">→</span></a>
</div>
</section>"""
    if lang == 'ja':
        alt_ja, alt_en = canonical, (other if other != 'en/' or canonical == '' else None)
    else:
        alt_en, alt_ja = canonical, (other if other != '' or canonical == 'en/' else None)
    alternates = ''
    if alt_ja is not None and alt_en is not None:
        alternates = (f'<link rel="alternate" hreflang="ja" href="https://nowhere.group/{alt_ja}">\n'
                      f'<link rel="alternate" hreflang="en" href="https://nowhere.group/{alt_en}">\n')
    if lang == 'en':
        foot_links = f"""<li><a href="{home}">Home</a></li>
<li><a href="{home}company/">About</a></li>
<li><a href="{home}service/">Business</a></li>
<li><a href="{home}service/regional-brand-creation/#brands">Brands &amp; Works</a></li>
<li><a href="{root}news/" lang="ja">News (JP)</a></li>
<li><a href="{root}recruit/" lang="ja">Careers (JP)</a></li>
<li><a href="{home}contact/">Contact</a></li>
<li><a href="{home}privacy/">Privacy Policy</a></li>
<li><a href="{root}" lang="ja">日本語</a></li>"""
    else:
        foot_links = f"""<li><a href="{root}">ホーム</a></li>
<li><a href="{root}company/">私たちについて</a></li>
<li><a href="{root}service/">事業紹介</a></li>
<li><a href="{root}service/regional-brand-creation/#brands">ブランド・実績</a></li>
<li><a href="{root}news/">お知らせ</a></li>
<li><a href="{root}recruit/">採用情報</a></li>
<li><a href="{root}contact/">お問い合わせ</a></li>
<li><a href="{root}privacy/">プライバシーポリシー</a></li>
<li><a href="{root}en/" lang="en">English</a></li>"""
    body = fill_tokens(body, root, lang)
    body = body.replace('{{root}}', root).replace('{{home}}', home)
    return f"""<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(full_title)}</title>
<meta name="description" content="{esc(desc)}">
{'<meta name="robots" content="noindex">' + chr(10) if meta.get('noindex') else ''}<meta property="og:type" content="{'article' if meta.get('article') else 'website'}">
<meta property="og:title" content="{esc(full_title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:site_name" content="{t['site']}">
<meta property="og:locale" content="{'en_US' if lang == 'en' else 'ja_JP'}">
<meta property="og:url" content="https://nowhere.group/{canonical}">
<link rel="canonical" href="https://nowhere.group/{canonical}">
{alternates}<link rel="icon" href="{root}images/logo/favicon.png" type="image/png">
<link rel="apple-touch-icon" href="{root}images/logo/apple-touch-icon.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="{FONTS.replace('&', '&amp;')}" rel="stylesheet">
<link rel="stylesheet" href="{root}assets/css/header.css?v={VER}">
<link rel="stylesheet" href="{root}assets/css/sub.css?v={VER}">
<script src="{root}assets/js/header.js?v={VER}" defer></script>
<script src="{root}assets/js/sub.js?v={VER}" defer></script>
</head>
<body class="{accent} lang-{lang}">
<a class="skip" href="#main">{t['skip']}</a>
<header class="hd">
<a class="hd-logo" href="{home}" aria-label="{t['logo_label']}"><img src="{root}images/logo/nowhere-group-logo.png" alt="Nowhere Group" width="800" height="157"></a>
<button class="menu-btn" type="button" aria-expanded="false" aria-controls="gnav"><span class="bars" aria-hidden="true"></span>Menu</button>
<nav id="gnav" class="site-nav" aria-label="{t['menu_label']}">{nav}</nav>
</header>
<main id="main">
{hero_html(meta, root, lang)}
{body}
</main>{cta}
<footer class="ft">
<div class="wrap">
<div class="ft-top">
<div>
<a class="ft-logo" href="{home}"><img src="{root}images/logo/nowhere-group-logo.png" alt="Nowhere Group" width="800" height="157" loading="lazy"></a>
<p class="ft-co">{t['site']}<br>{t['address']}<br>TEL 03-6454-7875</p>
</div>
<div>
<ul class="ft-nav">
{foot_links}
</ul>
<div class="ft-sns">
{f'<a href="{NOTE_URL}" aria-label="note" target="_blank" rel="noopener" class="ft-note">note</a>' if NOTE_URL else ''}<a href="https://x.com/nowheregroup1" aria-label="{t['x_label']}" target="_blank" rel="noopener">X</a>
<a href="https://www.facebook.com/nowhere.group" aria-label="Facebook" target="_blank" rel="noopener" style="color:#2F6FD6">f</a>
<a href="https://www.instagram.com/nowhere_group/" aria-label="Instagram" target="_blank" rel="noopener"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#C94A1A" stroke-width="2" aria-hidden="true"><rect x="3" y="3" width="18" height="18" rx="5"></rect><circle cx="12" cy="12" r="4"></circle><circle cx="17.5" cy="6.5" r="1" fill="#C94A1A"></circle></svg></a>
</div>
</div>
</div>
<div class="ft-bottom">
<span>Copyright © 2025 {t['site']}</span>
<a href="{home}privacy/">{t['privacy']}</a>
</div>
</div>
</footer>
</body>
</html>
"""


WRITTEN = []  # 生成したページ（sitemap.xml 用）


def write(rel_dir, content):
    if 'name="robots" content="noindex' not in content:
        WRITTEN.append(rel_dir)
    out_dir = os.path.join(BASE, rel_dir)
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(content)


def redirect_html(url):
    """meta の "redirect" を指定したページ: 本文の代わりに指定 URL へ転送するだけのページを出す"""
    u = esc(url)
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="robots" content="noindex">
<meta http-equiv="refresh" content="0; url={u}">
<link rel="canonical" href="{u}">
<title>Nowhere Group</title>
<script>location.replace({json.dumps(url)})</script>
</head>
<body><p><a href="{u}">{u}</a></p></body>
</html>
"""


def root_for(rel_dir):
    depth = len([p for p in rel_dir.strip('/').split('/') if p])
    return '../' * depth


# ---------------------------------------------------------------- 固定ページ
def build_pages():
    pages_dir = os.path.join(SRC, 'pages')
    count = 0
    for dirpath, _, files in os.walk(pages_dir):
        for fn in files:
            if fn.endswith('.html'):
                PAGE_DIRS.add(os.path.relpath(os.path.join(dirpath, fn), pages_dir)[:-5] + '/')
    PAGE_DIRS.update({'', 'en/', 'news/', 'column/', 'recruit/'})
    for dirpath, _, files in os.walk(pages_dir):
        for fn in files:
            if not fn.endswith('.html'):
                continue
            path = os.path.join(dirpath, fn)
            rel = os.path.relpath(path, pages_dir)[:-5]  # company / service/hotel ...
            rel_dir = rel + '/'
            meta, body = read_meta(path)
            if meta.get('redirect'):
                write(rel_dir, redirect_html(meta['redirect']))
            else:
                write(rel_dir, layout(meta, body, root_for(rel_dir), rel_dir))
            count += 1
    return count


# ---------------------------------------------------------------- 記事
def load_articles(kind):
    d = os.path.join(SRC, kind)
    arts = []
    for fn in os.listdir(d):
        if fn.endswith('.html'):
            meta, body = read_meta(os.path.join(d, fn))
            meta['id'] = fn[:-5]
            meta['body'] = body.strip()
            arts.append(meta)
    # 日付の新しい順（同日は ID の大きい順）
    arts.sort(key=lambda a: (a['date'], int(a['id'])), reverse=True)
    return arts


def plain(s, n=110):
    t = re.sub(r'<[^>]+>', ' ', s)
    t = html.unescape(re.sub(r'\s+', ' ', t)).strip()
    return t[:n] + ('…' if len(t) > n else '')


def labels_html(a):
    """記事種別と発信会社のラベル（発信会社は種別と別のラベルにする）"""
    out = f'<span class="tag">{esc(a["category"])}</span>' if a.get('category') else ''
    if a.get('company'):
        out += f'<span class="tag tag-line">{esc(a["company"])}</span>'
    return out


def thumb_html(a, root, cls='thumb'):
    if a.get('thumb'):
        src = a['thumb'].replace('{{root}}', root)
        return f'<span class="{cls}"><img src="{src}" alt="" loading="lazy"></span>'
    return f'<span class="{cls} noimg" aria-hidden="true">NOWHERE</span>'


def share_html(title):
    """X / LINE / Facebook / リンクコピーのシェアボタン（URL は sub.js が現在のページから組み立てる）"""
    return f'''<div class="share" data-share data-title="{esc(title)}">
<span class="share-label">この記事をシェア</span>
<a class="share-btn" data-share-x href="#" target="_blank" rel="noopener" aria-label="Xでシェア">X</a>
<a class="share-btn" data-share-line href="#" target="_blank" rel="noopener" aria-label="LINEで送る">LINE</a>
<a class="share-btn" data-share-fb href="#" target="_blank" rel="noopener" aria-label="Facebookでシェア">Facebook</a>
<button class="share-btn" type="button" data-share-copy aria-label="リンクをコピー">リンクをコピー</button>
</div>'''


def build_articles(kind, label_en, label_ja, color):
    arts = load_articles(kind)
    for i, a in enumerate(arts):
        rel_dir = f'{kind}/{a["id"]}/'
        root = root_for(rel_dir)
        newer = arts[i - 1] if i > 0 else None
        older = arts[i + 1] if i + 1 < len(arts) else None
        cat = labels_html(a)
        thumb = ''
        if a.get('thumb'):
            thumb = (f'<div class="art-thumb"><img src="{a["thumb"].replace("{{root}}", root)}" '
                     f'alt="{esc(a["category"] or "")}"></div>')
        nav = ''
        if newer:
            nav += f'<a class="btn" href="{root}{kind}/{newer["id"]}/"><span class="arr">←</span> 新しい記事</a>'
        nav += f'<a class="btn btn-dark" href="{root}{kind}/">一覧へ戻る</a>'
        if older:
            nav += f'<a class="btn" href="{root}{kind}/{older["id"]}/">前の記事 <span class="arr">→</span></a>'
        body = f'''<div class="ph-simple"></div>
<article class="sec" style="padding-top:0">
<div class="wrap">
<div class="art">
<header class="art-head">
{crumbs_html([(label_en, f"{kind}/"), (a["title"], "")], root)}
<div class="row"><time datetime="{a["date"].replace(".", "-")}">{a["date"]}</time>{cat}</div>
<h1>{esc(a["title"])}</h1>
</header>
{thumb}
<div class="prose">
{a["body"]}
</div>
{share_html(a["title"]) if kind == 'news' else ''}
<nav class="art-nav" aria-label="記事の移動">{nav}</nav>
</div>
</div>
</article>'''
        meta = {'title': a['title'], 'description': plain(a['body']), 'nav': kind,
                'accent': f'c-{color}', 'article': True}
        write(rel_dir, layout(meta, body, root, rel_dir))

    # 一覧
    rel_dir = f'{kind}/'
    root = root_for(rel_dir)
    rows = []
    for a in arts:
        cat = labels_html(a)
        rows.append(f'''<li data-cat-item="{esc(a.get("category", ""))}"><a href="{root}{kind}/{a["id"]}/">
{thumb_html(a, root)}
<span class="meta"><time datetime="{a["date"].replace(".", "-")}">{a["date"]}</time>{cat}<span class="t">{esc(a["title"])}</span></span>
<span class="go" aria-hidden="true">→</span>
</a></li>''')
    filt = ''
    if kind == 'news':
        unknown = {a.get('category') for a in arts} - set(NEWS_CATS)
        if unknown:
            raise SystemExit(f'ニュースの category は NEWS_CATS から選んでください: {unknown}')
        btns = '<button type="button" data-cat="all" aria-pressed="true">すべて</button>' + ''.join(
            f'<button type="button" data-cat="{esc(c)}" aria-pressed="false">{esc(c)}</button>' for c in NEWS_CATS)
        filt = f'<div class="filter" role="group" aria-label="記事種別で絞り込み">{btns}</div>'
    body = f'''<section class="sec">
<div class="wrap">
{filt}
<ul class="nlist-rows">
{chr(10).join(rows)}
</ul>
</div>
</section>'''
    desc = {'news': 'Nowhere Groupからのお知らせ。グループ各社（Nowhere Group・VESTPORT・CLEANX9・Family Stay）のプレスリリース、メディア掲載、受賞・認定などの最新情報をお届けします。',
            'column': '宿泊施設プロデュース、民泊投資、不動産売買・M&Aなど、宿泊・観光業界に関するNowhere Groupのコラムです。'}[kind]
    meta = {'title': label_en, 'description': desc, 'nav': kind, 'accent': f'c-{color}',
            'hero': {'type': 'illust', 'en': label_en, 'ja': label_ja, 'color': color,
                     'img': 'bg-footer.jpg'},
            'crumbs': [(label_en, '')]}
    write(rel_dir, layout(meta, body, root, rel_dir))
    return arts


# ---------------------------------------------------------------- トップの最新3件
def short_title(t, n=44):
    return t if len(t) <= n else t[:n] + '…'


def update_top(news, columns):
    path = os.path.join(BASE, 'index.html')
    src = open(path, encoding='utf-8').read()

    def col_row(a):
        return (f'<a href="column/{a["id"]}/" class="li-row li-col"><span class="li-badge">C</span>'
                f'<span class="li-body"><span class="li-title">{esc(a.get("short") or short_title(a["title"]))}</span>'
                f'<span class="li-date">{a["date"]}</span></span></a>')

    def news_row(a):
        return (f'<a href="news/{a["id"]}/" class="li-row li-news"><span class="li-badge">N</span>'
                f'<span class="li-body"><span class="li-date">{a["date"]}<span class="li-tag">{esc(a["category"])}</span>'
                f'<span class="li-tag li-co">{esc(a["company"])}</span></span>'
                f'<span class="li-title">{esc(a.get("short") or short_title(a["title"]))}</span></span></a>')

    for key, items in (('column', [col_row(a) for a in columns[:3]]), ('news', [news_row(a) for a in news[:3]])):
        pat = re.compile(rf'(<!-- build:{key} -->\n)(?:.*?\n)?(<!-- /build:{key} -->)', re.S)
        if not pat.search(src):
            continue  # トップにコラム欄はない（お知らせのみ更新）
        src = pat.sub(lambda m: m.group(1) + '\n'.join(items) + '\n' + m.group(2), src)
    src = re.sub(r'(assets/(?:css|js)/[a-z]+\.(?:css|js))(\?v=\w+)?', rf'\1?v={VER}', src)
    open(path, 'w', encoding='utf-8').write(src)


# ---------------------------------------------------------------- 採用情報
APPLY_FORM = 'https://nowhere-group.notion.site/2da88671208580b2b482f7e55475e194'
OPEN_FORM = 'https://nowhere-group.notion.site/326886712085803fb9d8e91ca3812749'
# 採用の会社別求人ページ（key, 会社名, 事業領域, /recruit/jobs/<slug>/）
BRANDS = [('nowhere', 'Nowhere Group株式会社', '宿泊施設のプロデュース・運営', 'nowhere'),
          ('vestport', 'VESTPORT株式会社', '不動産・工事・建物管理', 'vestport'),
          ('cleanx9', 'CLEANX9株式会社', '清掃', 'cleanx9'),
          ('familystay', '株式会社Family Stay', 'OTA・リテールメディア【開発準備中】', 'family-stay')]
CASUAL_FORM = ''  # カジュアル面談の申込先（採用専用で実際に受信できるもの）。空の間は申込ボタンを出さない
# 採用ページで紹介する公式 note の記事。key は記事 URL（note.com/nowhere_group/n/<key>）の末尾
# 追加するときは見出し画像を images/uploads/note/<key>.jpg（幅800px）に保存する
NOTE_WORK = [  # 仕事と人を知る：お仕事図鑑
    {'key': 'nde1b35067607', 'label': 'お仕事図鑑 #1', 'date': '2026.09.03', 'title': '宿泊施設運営スタッフ編'},
    {'key': 'n369704bf519b', 'label': 'お仕事図鑑 #2', 'date': '2026.10.17', 'title': '清掃スタッフ編'},
]
NOTE_PEOPLE = [  # 仕事と人を知る：社員インタビュー
    {'key': 'nffae73231a0c', 'label': '社員インタビュー', 'date': '2026.07.31', 'title': '変化と未経験、知らない世界に向き合う面白さ'},
    {'key': 'nbaa738f44b78', 'label': '社長対談', 'date': '2026.09.26', 'title': '「継続は力」”生意気くらいがちょうどいい”を体現した若き経営幹部'},
]
NOTE_PROJECTS = [  # プロジェクトを知る：宿泊施設プロデュースの裏側
    {'key': 'nb0cd50727c70', 'label': 'OMATSURI BASE', 'date': '2026.03.18', 'title': '【”日本一の民泊”受賞】OMATSURI BASE Nakanoshimbashi 誕生の裏側と戦略'},
    {'key': 'n6284e3f11d20', 'label': "Kids' Play Villa", 'date': '2026.03.21', 'title': '眠っていた土地を子供達の「住みたい」に。'},
    {'key': 'na984c8a98200', 'label': 'FUWARI 阿蘇', 'date': '2026.03.28', 'title': '相続案件から生まれた地域再生モデル。'},
    {'key': 'n435a26d71c44', 'label': 'Azure Palace 伊豆高原', 'date': '2026.03.29', 'title': '中古別荘リノベーションから生まれた新しい価値。'},
    {'key': 'n396f422f7e86', 'label': 'ZEN＆BED 望月庵', 'date': '2026.03.30', 'title': 'お寺に宿泊、日本の伝統の活かし方。'},
    {'key': 'n2f5ef9b08ff3', 'label': 'HARELIER 山中湖', 'date': '2026.04.30', 'title': '「帰りたくない」と泣く居心地の良さ'},
    {'key': 'necd2721fb866', 'label': 'タイムトリップOTOWA', 'date': '2026.05.29', 'title': '制約だらけの空き家が”昭和レトロ代表”に生まれ変わるまで'},
    {'key': 'ne1e04b169279', 'label': '由楽 焼津', 'date': '2026.06.27', 'title': '立地の常識を覆した、体験価値設計の全記録。'},
]
ENVIRONMENT = ['評価制度', 'キャリア', '研修', '福利厚生', '働き方', 'オフィス', 'グループ内キャリア']


def build_recruit():
    d = os.path.join(SRC, 'recruit')
    all_jobs = []
    for fn in sorted(os.listdir(d)):
        if fn.endswith('.html') and not fn.startswith('_'):
            meta, body = read_meta(os.path.join(d, fn))
            meta['slug'] = fn[:-5]
            meta['body'] = body.strip()
            all_jobs.append(meta)
    all_jobs.sort(key=lambda j: j['order'])
    jobs = [j for j in all_jobs if not j.get('closed')]  # 募集終了（closed）の求人は一覧・件数に含めない
    crumb_top = ('採用情報', 'recruit/')
    slug_of = {key: slug for key, _, _, slug in BRANDS}
    name_of = {key: name for key, name, _, _ in BRANDS}

    def job_tags(j):
        return (f'<span class="tag">{esc(name_of[j["company"]])}</span>'
                f'<span class="tag tag-line">{esc(j["employment"] or j["type"])}</span>')

    def job_meta(j):
        """雇用主と配属先（就業場所）は別の項目として出す"""
        return (f'<dl class="job-meta"><div><dt>雇用主</dt><dd>{esc(name_of[j["company"]])}</dd></div>'
                f'<div><dt>配属先・就業場所</dt><dd>{esc(j["place"])}</dd></div>'
                f'<div><dt>{"報酬" if "業務委託" in j["employment"] else "賃金"}</dt><dd>{esc(j["salary"])}</dd></div></dl>')

    # 求人詳細
    for j in all_jobs:
        rel_dir = f'recruit/{j["slug"]}/'
        root = root_for(rel_dir)
        list_href = f'{root}recruit/jobs/{slug_of[j["company"]]}/'
        if j.get('closed'):
            apply = '<p class="job-closed">この求人の募集は終了しました。新規のご応募は受け付けていません。</p>'
        else:
            apply = f'<div class="btn-row" style="margin-top:8px"><a class="btn btn-dark" href="{APPLY_FORM}" target="_blank" rel="noopener">この求人に応募する <span class="arr">↗</span></a></div>'
        body = f"""<div class="ph-simple"></div>
<article class="sec" style="padding-top:0">
<div class="wrap">
<div class="art">
<header class="art-head">
{crumbs_html([crumb_top, (name_of[j['company']], f'recruit/jobs/{slug_of[j["company"]]}/'), (j['title'], '')], root)}
<div class="row">{job_tags(j)}</div>
<h1>{esc(j['title'])}</h1>
<p class="job-lead">{esc(j['summary'])}</p>
{job_meta(j)}
{apply}
</header>
<div class="prose job">
{j['body']}
</div>
<nav class="art-nav" aria-label="求人の移動"><a class="btn" href="{list_href}"><span class="arr">←</span> {esc(name_of[j['company']])}の求人一覧へ</a><a class="btn" href="{root}recruit/open-position/">オープンポジション <span class="arr">→</span></a></nav>
</div>
</div>
</article>"""
        meta = {'title': f'{j["title"]}（{j["type"]}）｜採用情報', 'description': f'{name_of[j["company"]]}の求人。{j["summary"]}',
                'nav': 'recruit', 'accent': 'c-orange' if j['company'] == 'nowhere' else 'c-blue',
                'noindex': bool(j.get('closed'))}
        write(rel_dir, layout(meta, body, root, rel_dir))

    # 会社別の求人一覧
    for key, name, desc, slug in BRANDS:
        rel_dir = f'recruit/jobs/{slug}/'
        root = root_for(rel_dir)
        mine = [j for j in jobs if j['company'] == key]
        cards = [f"""<a class="card job-card" href="{root}recruit/{j['slug']}/">
<div class="row">{job_tags(j)}</div>
<h3>{esc(j['title'])}</h3>
<p>{esc(j['summary'])}</p>
{job_meta(j)}
<span class="card-more">詳しくみる →</span>
</a>""" for j in mine]
        if not cards:
            cards.append(f'<div class="card"><p>現在、募集中の求人はありません。ご興味のある方は<a href="{root}recruit/open-position/">オープンポジション</a>からご応募ください。</p></div>')
        body = f"""<div class="ph-simple"></div>
<section class="sec" style="padding-top:0">
<div class="wrap">
<header class="art-head">
{crumbs_html([crumb_top, (name, '')], root)}
<p class="ph-en" style="font-family:var(--f-en);font-weight:600;color:var(--accent)">Jobs</p>
<h1>{esc(name)}の求人</h1>
<p class="job-lead">{esc(desc)}・募集中 {len(mine)}件</p>
</header>
<div class="grid g3" data-rv>
{chr(10).join(cards)}
</div>
<nav class="art-nav" aria-label="ページの移動"><a class="btn" href="{root}recruit/#jobs"><span class="arr">←</span> 会社別の求人へ戻る</a></nav>
</div>
</section>"""
        meta = {'title': f'{name}の求人｜採用情報', 'description': f'{name}（{desc}）の募集中の求人一覧です。',
                'nav': 'recruit', 'accent': 'c-orange'}
        write(rel_dir, layout(meta, body, root, rel_dir))

    # オープンポジション・採用プライバシーポリシー
    for slug, title, en in (('open-position', 'オープンポジション', 'Open Position'),
                            ('privacy', '採用プライバシーポリシー', 'Recruit Privacy Policy')):
        rel_dir = f'recruit/{slug}/'
        root = root_for(rel_dir)
        src = open(os.path.join(d, f'_{slug}.html'), encoding='utf-8').read()
        body = f"""<div class="ph-simple"></div>
<article class="sec" style="padding-top:0">
<div class="wrap">
<div class="art">
<header class="art-head">
{crumbs_html([crumb_top, (title, '')], root)}
<p class="ph-en" style="font-family:var(--f-en);font-weight:600;color:var(--accent)">{en}</p>
<h1>{title}</h1>
</header>
<div class="prose">
{src}
</div>
<nav class="art-nav" aria-label="ページの移動"><a class="btn" href="{root}recruit/"><span class="arr">←</span> 採用情報トップへ</a></nav>
</div>
</div>
</article>"""
        meta = {'title': f'{title}｜採用情報', 'description': f'Nowhere Groupの{title}です。', 'nav': 'recruit',
                'accent': 'c-orange'}
        write(rel_dir, layout(meta, body, root, rel_dir))

    # 採用トップ
    rel_dir = 'recruit/'
    root = root_for(rel_dir)
    company_cards = []
    for key, name, desc, slug in BRANDS:
        n = len([j for j in jobs if j['company'] == key])
        company_cards.append(f"""<a class="card job-card" href="{root}recruit/jobs/{slug}/">
<span class="tag">{'募集中 ' + str(n) + '件' if n else '現在募集なし'}</span>
<h3>{esc(name)}</h3>
<p>{esc(desc)}</p>
<span class="card-more">求人一覧を見る →</span>
</a>""")
    if CASUAL_FORM:
        casual_cta = f'<div class="btn-row" style="margin-top:4px"><a class="btn btn-dark" href="{CASUAL_FORM}" target="_blank" rel="noopener">カジュアル面談について相談する <span class="arr">↗</span></a></div>'
    else:
        casual_cta = ''  # 実際に受信できる申込先が決まるまでボタンは出さない（ダミー URL は置かない）
    body = f"""<section class="sec" id="why">
<div class="wrap">
<div class="sec-head"><h2><span class="num">01</span>Why Nowhere Group</h2><p>Nowhere Groupで働くということ</p></div>
<div class="outline" data-rv>
<p class="lead">まだない宿泊の未来を、<br>一緒につくる。</p>
<div>
<p class="text">旅の満足度を高める仕事は、一つの職種だけでは完結しません。不動産の可能性を見つけ、宿泊施設をプロデュースし、運営・清掃の現場で品質を磨く。そこで生まれた気づきを、次の施設づくりへ生かす。</p>
<p class="text" style="margin-top:12px">Nowhere Groupでは、異なる専門性を持つ仲間が会社や部署の枠を越えて協力し、一つひとつの宿泊事業を形にしています。私たちが大切にしているのは、目の前の課題を自分ごととして考え、学び、改善し、チームで前に進めること。</p>
<p class="text" style="margin-top:12px;font-weight:700">旅する人の記憶に残る場所を、日本中に。そんな仕事に、あなたの力を生かしてみませんか。</p>
</div>
</div>
</div>
</section>

<section class="sec sec-alt" id="work">
<div class="wrap">
<div class="sec-head"><h2><span class="num">02</span>Work &amp; People</h2><p>仕事と人を知る</p></div>
<p class="text" style="margin-bottom:28px">宿泊施設の運営や清掃の現場で、どんな人が、どんな想いで働いているのか。公式noteの「お仕事図鑑」と社員インタビューでご紹介しています。</p>
<div class="job-group">
<h3 class="job-brand">お仕事図鑑<small>仕事の中身を、現場のメンバーが紹介</small></h3>
{note_cards(root, NOTE_WORK)}
</div>
<div class="job-group">
<h3 class="job-brand">社員インタビュー<small>メンバーのキャリアと仕事観</small></h3>
{note_cards(root, NOTE_PEOPLE)}
</div>
<div style="margin-top:28px">{note_html(root)}</div>
</div>
</section>

<section class="sec" id="project">
<div class="wrap">
<div class="sec-head"><h2><span class="num">03</span>Project</h2><p>プロジェクトを知る</p></div>
<div class="outline" data-rv style="margin-bottom:clamp(28px,4vw,48px)">
<p class="lead">宿泊施設プロデュースの<br>裏側。</p>
<div>
<p class="text">空き家、相続した土地、中古別荘、お寺。眠っていた不動産が、選ばれる宿に生まれ変わるまでには、宿泊施設プロデュース、運営、清掃、地域連携まで、会社や部署の境界を越えた多くのメンバーが関わっています。</p>
<p class="text" style="margin-top:12px">施設ごとのプロデュースの裏側を、公式noteで公開しています。</p>
</div>
</div>
{note_cards(root, NOTE_PROJECTS)}
<div class="btn-row" style="margin-top:28px"><a class="btn" href="{root}service/regional-brand-creation/#brands">ブランド・実績を見る <span class="arr">→</span></a></div>
</div>
</section>

<section class="sec sec-alt" id="environment">
<div class="wrap">
<div class="sec-head"><h2><span class="num">04</span>Environment</h2><p>働く環境・制度</p></div>
<div class="grid g4" data-rv>
{chr(10).join(f'<div class="card" style="gap:6px"><span class="tag">{i + 1:02}</span><h3>{esc(t)}</h3></div>' for i, t in enumerate(ENVIRONMENT))}
</div>
<p class="text" style="margin-top:24px">各制度の詳細は、面談の際にご説明します。</p>
</div>
</section>

<section class="sec" id="jobs">
<div class="wrap">
<div class="sec-head"><h2><span class="num">05</span>Jobs</h2><p>会社別の求人・募集中 {len(jobs)}件</p></div>
<div class="grid g4" data-rv>
{chr(10).join(company_cards)}
</div>
</div>
</section>

<section class="sec sec-alt" id="open-position">
<div class="wrap">
<div class="sec-head"><h2><span class="num">06</span>Open Position</h2><p>応募先に迷ったら</p></div>
<div class="card" style="gap:18px">
<h3 style="font-size:clamp(20px,2.4vw,26px)">応募先に迷ったら、オープンポジションから。</h3>
<p>経験や志向に合ったポジションをご提案するオープンポジションを設けています。ご応募内容をもとに、現在募集中のポジション、または募集準備中のポジションの中から、マッチの可能性があるものをご案内します。</p>
<div class="btn-row" style="margin-top:4px"><a class="btn btn-dark" href="{OPEN_FORM}" target="_blank" rel="noopener">オープンポジションに応募する <span class="arr">↗</span></a><a class="btn" href="{root}recruit/open-position/">詳しくみる <span class="arr">→</span></a></div>
</div>
</div>
</section>

<section class="sec" id="casual">
<div class="wrap">
<div class="sec-head"><h2><span class="num">07</span>Casual Interview</h2><p>カジュアル面談</p></div>
<div class="card" style="gap:18px">
<h3 style="font-size:clamp(20px,2.4vw,26px)">まずは、お互いを知るところから。</h3>
<p>仕事内容やチームの雰囲気、これから取り組む事業について、気になることを気軽にお話しできるカジュアル面談の機会を設けています。応募を決める前に話を聞いてみたい方、どの職種が合うか相談したい方も歓迎します。ご希望の内容と募集状況を確認のうえ、ご案内します。</p>
{casual_cta}
</div>
</div>
</section>

<section class="sec sec-alt" id="privacy">
<div class="wrap">
<div class="sec-head"><h2><span class="num">08</span>Privacy</h2><p>応募者の個人情報の取り扱い</p></div>
<p class="text">ご応募いただいた個人情報は、求人ごとの雇用主となるグループ会社が、採用選考とご連絡のためにのみ利用します。グループ内での共同利用、保存、外部への委託、お問い合わせ窓口については、<a href="{root}recruit/privacy/">採用プライバシーポリシー</a>をご確認ください。応募の受付は一般のお問い合わせとは別の窓口で管理しています。</p>
</div>
</section>"""
    meta = {'title': '採用情報', 'description': 'Nowhere Groupの採用情報。まだない宿泊の未来を、一緒につくる。仕事と人、プロジェクト、働く環境、会社別の求人、オープンポジション、カジュアル面談をご紹介します。',
            'nav': 'recruit', 'accent': 'c-orange',
            'hero': {'type': 'illust', 'en': 'Recruit', 'ja': '採用情報', 'color': 'orange', 'img': 'bg-company.jpg'},
            'crumbs': [('採用情報', '')]}
    write(rel_dir, layout(meta, body, root, rel_dir))
    return jobs


# ---------------------------------------------------------------- 英語トップ（index.html から生成）
# 日本語トップの文言を置き換えて en/index.html を作る。
# 日本語トップの文言を変えたら、ここの対応表も合わせて直すこと（見つからない場合はビルドが止まる）。
EN_TOP = [
    ('<html lang="ja">',
     '<html lang="en">'),
    ('<title>Nowhere Group株式会社｜旅を起点に、人々の心にアナザースカイを創る。</title>',
     '<title>Nowhere Group Inc. | Travel as the starting point for another sky in every heart</title>'),
    ('content="Nowhere Groupは、宿泊を起点に、不動産、企画・開発、運営、清掃、販売・集客までをグループで展開する宿泊事業グループです。"',
     'content="Nowhere Group is a lodging business group that connects the expertise of its group companies, from real estate and accommodation development to operations, cleaning, sales and the next use of each asset."'),
    ('<link rel="canonical" href="https://nowhere.group/">',
     '<link rel="canonical" href="https://nowhere.group/en/">'),
    ('aria-label="メインメニュー"',
     'aria-label="Main menu"'),
    ('<a class="hd-logo" href="./" aria-label="Nowhere Group トップへ">',
     '<a class="hd-logo" href="./" aria-label="Nowhere Group home">'),
    ('<a href="company/">私たちについて</a>\n<a href="service/">事業紹介</a>\n<a href="service/regional-brand-creation/#brands">ブランド・実績</a>\n<a href="news/">お知らせ</a>\n<a href="recruit/">採用情報</a>\n',
     '<a href="company/">About</a>\n<a href="service/">Business</a>\n<a href="service/regional-brand-creation/#brands">Brands &amp; Works</a>\n<a href="news/" lang="ja">News</a>\n<a href="recruit/" lang="ja">Careers</a>\n'),
    ('<a href="en/" lang="en" hreflang="en" aria-label="English">EN</a>',
     '<a href="../" lang="ja" hreflang="ja" aria-label="日本語">JP</a>'),
    ('<a href="contact/" class="nav-contact">お問い合わせ</a>',
     '<a href="contact/" class="nav-contact">Contact</a>'),
    ('class="side-contact">お問い合わせ</a>',
     'class="side-contact">Contact</a>'),
    ('alt="温泉旅館、海辺の町、山、祭り、地域の食を旅する人々のイラスト"',
     'alt="Illustration of travelers enjoying hot spring inns, seaside towns, mountains, festivals and local food"'),
    ('旅を起点に、人々の心にアナザースカイを創る。 ─ Create for people all over the world.',
     'Travel as the starting point for another sky in every heart ─ Create for people all over the world.'),
    ('<p>グループ理念</p>',
     '<p>Our group philosophy</p>'),
    ('<h3>旅を起点に、<br>人々の心にアナザースカイを創る。</h3>',
     '<h3>Travel as the starting point<br>for another sky in every heart.</h3>'),
    ('<h3>2030年までに、<br>旅行の満足度で選ばれる宿泊グループになる。</h3>',
     '<h3>By 2030, become the lodging group<br>chosen for travel satisfaction.</h3>'),
    ('alt="古民家の宿で旅人を迎えるスタッフのイラスト"',
     'alt="Illustration of staff welcoming a traveler at a traditional house inn"'),
    ('<p>不動産の活用から宿泊施設プロデュース、運営・清掃、販売・集客、資産の次の活用まで。グループ各社の専門性をつなぐ宿泊事業グループです。</p>',
     '<p>From real estate utilization to accommodation development, operations and cleaning, sales and marketing, and the next use of each asset: a lodging business group that connects the expertise of its group companies.</p>'),
    ('<p>現場で得た知見を次の施設づくりへ生かし、宿の価値を継続して育てていきます。</p>',
     '<p>We feed what we learn on site into the next property, and keep growing the value of every stay.</p>'),
    ('>会社の想いと、宿泊事業における強みを見る<',
     '>Our story and our strengths in lodging<'),
    ('alt="虹と海辺の町、設計図やスマホ、地域のマルシェを囲む旅人のイラスト"',
     'alt="Illustration of travelers around a rainbow, a seaside town, blueprints, a smartphone and a local market"'),
    ('<p>不動産から宿泊施設のプロデュース・運営、清掃、ホテルSUPPLY、そして新たな旅行販売の仕組みづくりまで。専門性の異なるグループ4社が連携し、宿泊の価値を生み出しています。</p>',
     '<p>From real estate to accommodation development and operations, cleaning, hotel supply and new ways of selling travel, four group companies with different expertise work together to create value in lodging.</p>'),
    ('<span class="en">OUR GROUP</span>グループ各社の専門領域',
     '<span class="en">OUR GROUP</span>What each group company does'),
    ('</svg>宿泊施設のプロデュース・運営</h3>',
     '</svg>Hotel development &amp; operations</h3>'),
    ('<p><span class="sv-co">Nowhere Group株式会社</span>宿泊施設プロデュース、宿泊施設運営、ホテルSUPPLYを中核に、宿の価値をつくり、育てる。</p>',
     '<p><span class="sv-co">Nowhere Group Inc.</span>Creating and growing the value of each stay through hotel development &amp; production, hotel operations and hotel supply.</p>'),
    ('</svg>不動産・工事・建物管理</h3>',
     '</svg>Real estate, construction &amp; property management</h3>'),
    ('<p><span class="sv-co">VESTPORT株式会社</span>不動産・資産活用の相談から工事・改修、建物管理まで、宿泊事業の不動産領域を支える。</p>',
     '<p><span class="sv-co">VESTPORT Inc.</span>Supporting the real estate side of lodging, from property and asset consultation to construction, renovation and property management.</p>'),
    ('</svg>清掃</h3>',
     '</svg>Cleaning</h3>'),
    ('<p><span class="sv-co">CLEANX9株式会社</span>清掃とリネン・現地対応を通じ、宿泊施設の品質を現場から支える。</p>',
     '<p><span class="sv-co">CLEANX9 Inc.</span>Supporting the quality of every property on site through cleaning, linen and local support.</p>'),
    ('</svg>OTA・リテールメディア【開発準備中】</h3>',
     '</svg>OTA &amp; retail media [in development]</h3>'),
    ('<p><span class="sv-co">株式会社Family Stay</span>家族旅行に特化したOTA・リテールメディアの事業開発を進める。</p>',
     '<p><span class="sv-co">Family Stay Inc.</span>Developing an OTA and retail media business specialized in family travel.</p>'),
    ('>詳しく見る<',
     '>Read More<'),
    ('<span class="en">NOWHERE GROUP SERVICES</span>Nowhere Group株式会社の主なサービス',
     '<span class="en">NOWHERE GROUP SERVICES</span>Main services of Nowhere Group Inc.'),
    ('<strong>宿泊施設プロデュース</strong><span class="txt">施設の可能性を見極め、事業性と宿泊体験を一体で設計する。</span>',
     '<strong>Hotel development &amp; production</strong><span class="txt">Assessing each property\'s potential and designing business viability and guest experience as one.</span>'),
    ('<strong>宿泊施設運営</strong><span class="txt">既存OTAの販売管理からゲスト対応、現地オペレーションまで、開業後の価値を育てる。</span>',
     '<strong>Hotel operations</strong><span class="txt">Growing value after opening, from sales management on existing OTAs to guest service and on-site operations.</span>'),
    ('<strong>ホテルSUPPLY</strong><span class="txt">開業準備の一括調達から、運営中の備品・消耗品の継続補充まで。</span>',
     '<strong>Hotel supply</strong><span class="txt">From bulk procurement before opening to ongoing replenishment of equipment and consumables.</span>'),
    ('<span class="more">詳しく見る →</span>',
     '<span class="more">Read more →</span>'),
    ('>グループ4社の体制を見る →<',
     '>See our four group companies →<'),
    ('<p>宿泊バリューチェーン</p>',
     '<p>The lodging value chain</p>'),
    ('<h3>不動産・資産活用</h3>',
     '<h3>Real estate &amp; asset use</h3>'),
    ('<h3>宿泊施設プロデュース</h3>',
     '<h3>Hotel development &amp; production</h3>'),
    ('<h3>開業・運営・清掃</h3>',
     '<h3>Opening, operations &amp; cleaning</h3>'),
    ('<h3>資産の次の活用</h3>',
     '<h3>The next use of the asset</h3>'),
    ('>詳しい宿泊バリューチェーンを見る →<',
     '>See the full value chain →<'),
    ('<p>Nowhere Groupの強み</p>',
     '<p>What makes Nowhere Group different</p>'),
    ('<p class="tp-lead">当社の強みは、清掃・宿泊運営の現場から得られる課題や知見を、次の施設の宿泊施設プロデュースに反映できることです。</p>',
     '<p class="tp-lead">Our strength is that we feed the issues and insights from cleaning and hotel operations directly into the development of the next property.</p>'),
    ('alt="提灯と祭り、夜の温泉街のイラスト"',
     'alt="Illustration of lanterns, a festival and a hot spring town at night"'),
    ('<p>ブランド・宿泊施設・お知らせ</p>',
     '<p>Brands, hotels &amp; stays, and news (news in Japanese)</p>'),
    ('<small>365日、日本のお祭りを体験できる宿。</small><em class="st">営業中</em>',
     '<small>Experience Japanese festivals 365 days a year.</small><em class="st">Open</em>'),
    ('<small>家族みんなが主役の、思い出をつくるホテル。</small><em class="st">開業準備中</em>',
     '<small>A hotel where every family member is the star.</small><em class="st">Opening soon</em>'),
    ('alt="墨武"', 'alt="BOKUBU"'),
    ('<span>墨武</span><small>墨で描かれた武士の世界に泊まる。</small><em class="st">開業準備中</em>',
     '<span>BOKUBU</span><small>Stay in a samurai world drawn in ink.</small><em class="st">Opening soon</em>'),
    ('alt="由楽"', 'alt="YURA"'),
    ('<span>由楽</span><small>人目を気にせず、自由にくつろぐ。</small>',
     '<span>YURA</span><small>Relax freely, away from prying eyes.</small>'),
    ('>すべてのブランドを見る<',
     '>See all brands<'),
    ('alt="ZEN &amp; BED 望月庵"', 'alt="ZEN &amp; BED Bougetsuan"'),
    ('<strong>ZEN &amp; BED 望月庵</strong><small>山梨｜体験型ホテル（寺泊）</small>',
     '<strong>ZEN &amp; BED Bougetsuan</strong><small>Yamanashi | Experience hotel (temple stay)</small>'),
    ('<small>千葉｜ヴィラ型無人ホテル</small>',
     '<small>Chiba | Unstaffed villa hotel</small>'),
    ('<small>静岡｜アパートメント型無人ホテル</small>',
     '<small>Shizuoka | Unstaffed apartment hotel</small>'),
    ('>主な宿泊施設を見る<',
     '>See our main properties<'),
    ('>すべてのお知らせを見る<',
     '>See all news<'),
    ('<p>パートナー・アライアンス</p>',
     '<p>Partners and alliances</p>'),
    ('<p class="catch">Airbnb公式パートナープログラムに参画</p>',
     '<p class="catch">Member of the official Airbnb partner program</p>'),
    ('alt="JTB「地域未来にぎわい工房」"', 'alt="JTB Chiiki Mirai Nigiwai Kobo"'),
    ('<h3>JTB「地域未来にぎわい工房」</h3><p class="catch">地域資源を、新しい宿泊体験へ。</p>',
     '<h3>JTB Chiiki Mirai Nigiwai Kobo</h3><p class="catch">Turning regional resources into new lodging experiences.</p>'),
    ('<p>その他の取り組み</p>',
     '<p>Other works</p>'),
    ('<h3>タイムトリップ OTOWA</h3><p class="catch">空き家 × 昭和レトロ</p><p>使われなくなった建物を、昭和の体験を楽しめる宿へ。</p>',
     '<h3>Time Trip OTOWA</h3><p class="catch">Vacant house × Showa retro</p><p>Turning an unused building into a stay where guests enjoy the Showa era.</p>'),
    ('<h3>Azure Palace 伊豆高原</h3><p class="catch">中古別荘 × 大人の遊び場</p><p>既存別荘に、温泉・サウナ・エンタメを組み合わせた滞在価値を。</p>',
     '<h3>Azure Palace Izu-Kogen</h3><p class="catch">Used villa × Adult playground</p><p>Adding hot springs, a sauna and entertainment to an existing villa.</p>'),
    ('>その他の取り組みを見る →<',
     '>See other works →<'),
    ('<p>受賞・認定・公的指定</p>',
     '<p>Awards, certifications and public designations</p>'),
    ('<span class="lbl">［受賞］</span>',
     '<span class="lbl">[Award]</span>'),
    ('<p class="catch">総合グランプリ</p>',
     '<p class="catch">Grand Prix</p>'),
    ('<span class="lbl">［公的指定］</span><h3>東京都「東京観光案内窓口」</h3><p>OMATSURI BASE 中野新橋 1階</p>',
     '<span class="lbl">[Public designation]</span><h3>Tokyo Metropolitan Government "Tokyo Tourist Information Center"</h3><p>OMATSURI BASE Nakano-shimbashi, 1F</p>'),
    ('>受賞・認定・公的指定を見る →<',
     '>See awards and designations →<'),
    ('<p>数字で見るNowhere Group</p>',
     '<p>Nowhere Group in numbers</p>'),
    ('<strong>100<small>施設以上</small></strong><span>宿泊施設の累計プロデュース実績</span>',
     '<strong>100<small>+ properties</small></strong><span>Accommodation properties developed</span>'),
    ('<strong>30<small>エリア以上</small></strong><span>全国展開エリア</span>',
     '<strong>30<small>+ areas</small></strong><span>Areas across Japan</span>'),
    ('<strong>80,000<small>件以上</small></strong><span>宿泊施設の累計清掃件数</span>',
     '<strong>80,000<small>+ cleanings</small></strong><span>Total accommodation cleanings</span>'),
    ('<p>代表メッセージ</p>',
     '<p>Message from the CEO</p>'),
    ('alt="代表取締役 CEO 竹内 剛"',
     'alt="Go Takeuchi, CEO"'),
    ('<h3>旅の記憶から、<br>人生に新しい景色を。</h3>',
     '<h3>From the memories of travel,<br>a new view on life.</h3>'),
    ('<p>旅先での出会いや体験が、人生の記憶に残り、いつかまた帰りたいと思える場所になる。私たちは、そんな一人ひとりの「アナザースカイ」を、日本中につくりたいと考えています。</p>',
     '<p>The people you meet and the things you experience on a trip stay with you, and become a place you want to return to someday. We want to create that "another sky" for each person, all across Japan.</p>'),
    ('<p>Nowhere Groupは、清掃・宿泊運営の現場から事業を学び、そこで培った知見を宿泊施設プロデュースへとつなげてきました。一つひとつの宿から、日本の宿泊産業の未来をつくっていきます。</p>',
     '<p>Nowhere Group learned this business from the field of cleaning and hotel operations, and has carried that knowledge into accommodation development. One stay at a time, we are building the future of Japan\'s lodging industry.</p>'),
    ('<p class="name"><small>Nowhere Group株式会社 代表取締役 CEO</small>竹内 剛</p>',
     '<p class="name"><small>CEO, Nowhere Group Inc.</small>Go Takeuchi</p>'),
    ('<span>代表のSNS</span>',
     '<span>Follow the CEO</span>'),
    ('>代表メッセージを見る →<',
     '>Read the full message →<'),
    ('<p>採用情報</p>',
     '<p>Careers (in Japanese)</p>'),
    ('<p class="tp-lead">まだない宿泊の未来を、<br>一緒につくる。</p>',
     '<p class="tp-lead">Let\'s build a future of lodging<br>that doesn\'t exist yet.</p>'),
    ('<p class="tp-text">旅の満足度を高める仕事は、一つの職種だけでは完結しません。不動産の可能性を見つけ、宿泊施設をプロデュースし、運営・清掃の現場で品質を磨く。そこで生まれた気づきを、次の施設づくりへ生かす。</p>',
     '<p class="tp-text">Raising travel satisfaction takes more than one kind of job. We find the potential in real estate, develop accommodation, polish quality in operations and cleaning, and bring what we learn into the next property.</p>'),
    ('<p class="tp-text">異なる専門性を持つ仲間が、会社や部署の枠を越えて協力し、一つひとつの宿泊事業を形にしています。</p>',
     '<p class="tp-text">Colleagues with different expertise work across companies and departments to bring each lodging business to life.</p>'),
    ('>採用情報を見る →<',
     '>See open positions →<'),
    ('<span class="ft-co">Nowhere Group株式会社</span>',
     '<span class="ft-co">Nowhere Group Inc.</span>'),
    ('グループ各社へのお問い合わせは、こちらで一括して承ります。',
     'Inquiries for every group company are handled here, in one place.'),
    ('>お問い合わせフォーム<',
     '>Contact Form<'),
    ('aria-label="フッターメニュー"><a href="company/">私たちについて</a><a href="service/">事業紹介</a><a href="service/regional-brand-creation/#brands">ブランド・実績</a><a href="news/">お知らせ</a><a href="recruit/">採用情報</a><a href="contact/">お問い合わせ</a>',
     'aria-label="Footer menu"><a href="company/">About</a><a href="service/">Business</a><a href="service/regional-brand-creation/#brands">Brands &amp; Works</a><a href="news/" lang="ja">News (JP)</a><a href="recruit/" lang="ja">Careers (JP)</a><a href="contact/">Contact</a>'),
    ('aria-label="X（旧Twitter）"',
     'aria-label="X (formerly Twitter)"'),
    ('Copyright © 2025 Nowhere Group株式会社',
     'Copyright © 2025 Nowhere Group Inc.'),
    ('>プライバシーポリシー</a><a href="en/" lang="en">English</a>',
     '>Privacy Policy</a><a href="../" lang="ja">日本語</a>'),
    ('alt="宿から旅立つ旅人と、灯台のある海辺の町のイラスト"',
     'alt="Illustration of a traveler leaving an inn and a seaside town with a lighthouse"'),
]
EN_PAGES = ('company', 'service', 'contact', 'privacy')


def build_en_top():
    src = open(os.path.join(BASE, 'index.html'), encoding='utf-8').read()
    for ja, en in EN_TOP:
        n = src.count(ja)
        if n == 0:
            raise SystemExit(f'英語トップ: 置き換え元が見つかりません（index.html の文言が変わった可能性）: {ja[:60]}')
        src = src.replace(ja, en)

    def fix(m):
        attr, url = m.group(1), m.group(2)
        if url == './' or re.match(r'(https?:|mailto:|tel:|#|data:|\.\./)', url):
            return m.group(0)
        first = url.split('/')[0]
        return f'{attr}="{url}"' if first in EN_PAGES else f'{attr}="../{url}"'
    src = re.sub(r'(href|src)="([^"]*)"', fix, src)
    # 日本語記事へのリンクに lang="ja" を付ける
    src = re.sub(r'<a href="\.\./(news|column)/(\d+)/"', r'<a lang="ja" href="../\1/\2/"', src)
    # 日本語が残っていないか確認（日本語記事へのリンクと「日本語」切替リンクは除く）
    body_wo_ja = re.sub(r'<a lang="ja".*?</a>', '', src.split('<body>')[1], flags=re.S)
    remain = re.findall(r'>([^<]*[぀-ヿ一-鿿][^<]*)<', body_wo_ja)
    left = [r for r in remain if r.strip() != '日本語']
    os.makedirs(os.path.join(BASE, 'en'), exist_ok=True)
    open(os.path.join(BASE, 'en', 'index.html'), 'w', encoding='utf-8').write(src)
    return left


def build_sitemap():
    """sitemap.xml（トップ・英語トップと、このスクリプトが生成したページ）"""
    urls = ['', 'en/'] + sorted(set(WRITTEN))
    body = ''.join(f'<url><loc>https://nowhere.group/{u}</loc></url>\n' for u in urls)
    with open(os.path.join(BASE, 'sitemap.xml'), 'w', encoding='utf-8') as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n'
                f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{body}</urlset>\n')
    return len(urls)


def main():
    n = build_pages()
    news = build_articles('news', 'News', 'お知らせ', 'pink')
    columns = build_articles('column', 'Column', 'コラム', 'purple')
    jobs = build_recruit()
    update_top(news, columns)
    left = build_en_top()
    build_sitemap()
    print(f'pages: {n}, news: {len(news)}, column: {len(columns)}, recruit: {len(jobs)}, en top: ok')
    if left:
        print('  英語トップに日本語の文言が残っています（ニュース・コラムの記事タイトル以外）:')
        for t in left:
            print('   -', t.strip()[:60])


if __name__ == '__main__':
    main()
