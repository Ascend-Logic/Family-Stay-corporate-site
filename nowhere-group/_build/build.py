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

NAV = [
    ('company', '私たちについて', 'company/'),
    ('service', '事業紹介', 'service/'),
    ('group', 'グループ会社', 'service/#group'),
    ('brand', 'ブランド・実績', 'service/regional-brand-creation/'),
    ('news', 'お知らせ', 'news/'),
]
RECRUIT = 'https://nowhere-group.notion.site/nowhere-group-work-culture?source=copy_link'
NOTE_URL = 'https://note.com/nowhere_group'  # 公式 note の URL。設定するとお知らせ一覧・採用ページ・下層フッターに「公式note」リンクを出す
CEO_SNS = [  # 代表メッセージに出す代表の SNS。URL を入れたものだけ表示
    ('YouTube', ''),
    ('X', ''),
]
# 役員紹介（会社別）。name が空のものは表示しない（氏名確定後に入れる）。photo は images/site/people/ のファイル名（なければ空）
OFFICERS = {
    'nowhere': [('竹内 剛', 'Go Takeuchi', '代表取締役 CEO', 'CEO', 'takeuchi-sq.jpg')],
    'vestport': [('竹内 剛', 'Go Takeuchi', '代表取締役 CEO', 'CEO', 'takeuchi-sq.jpg'),
                 ('髙橋 悠太', 'Yuta Takahashi', '執行役員', 'Executive Officer', 'takahashi.jpg')],
    'cleanx9': [('竹内 剛', 'Go Takeuchi', '代表取締役 CEO', 'CEO', 'takeuchi-sq.jpg'),
                ('', 'Yagi', '副社長 COO', 'Vice President, COO', '')],
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
            company = COMPANY_NAMES[key][1 if lang == 'en' else 0]
            people[ja]['roles'].append((company, role_en if lang == 'en' else role_ja))
    cards = []
    for ja in order:
        pr = people[ja]
        name = pr['en'] if lang == 'en' else ja
        img = (f'<span class="officer-photo"><img src="{photo_src(root, pr["photo"])}" alt="" loading="lazy"></span>' if pr['photo']
               else '<span class="officer-photo noimg" aria-hidden="true"></span>')
        roles = ''.join(f'<li><span class="officer-co">{esc(c)}</span><span class="officer-role">{esc(r)}</span></li>' for c, r in pr['roles'])
        cards.append(f'<div class="officer officer-merged">{img}<strong class="officer-name">{esc(name)}</strong><ul class="officer-roles">{roles}</ul></div>')
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
NEWS_CATS = ['グループ', 'Nowhere Group', 'VESTPORT', 'CLEANX9', 'Family Stay', 'プレスリリース', 'メディア掲載', '受賞・認定']
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
        'address': '〒169-0075 東京都新宿区高田馬場3-12-2 OCビル4階',
        'privacy': 'プライバシーポリシー', 'x_label': 'X（旧Twitter）', 'switch': ('EN', 'English'),
    },
    'en': {
        'site': 'Nowhere Group Inc.', 'tagline': 'Travel as the starting point for another sky in every heart', 'skip': 'Skip to content',
        'logo_label': 'Nowhere Group home', 'menu_label': 'Main menu',
        'cta_text': 'Inquiries for every group company are handled here, in one place.', 'cta_btn': 'Contact Form',
        'address': 'OC Bldg. 4F, 3-12-2 Takadanobaba, Shinjuku-ku, Tokyo 169-0075, Japan',
        'privacy': 'Privacy Policy', 'x_label': 'X (formerly Twitter)', 'switch': ('JP', '日本語'),
    },
}
NAV_EN = [('company', 'About', 'en/company/'), ('service', 'Business', 'en/service/'),
          ('group', 'Group', 'en/service/#group'), ('brand', 'Brands', 'en/service/regional-brand-creation/')]
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
    nav = ''.join(f'<a href="{root}{href}"{cur(key)}>{label}</a>'
                  for key, label, href in (NAV_EN if lang == 'en' else NAV))
    nav += (f'<a href="{root}recruit/"{cur("recruit")}>採用情報</a>' if lang == 'ja'
            else f'<a href="{root}recruit/" lang="ja">Recruit</a>')
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
<li><a href="{home}service/#group">Group</a></li>
<li><a href="{home}service/regional-brand-creation/">Brands</a></li>
<li><a href="{root}news/" lang="ja">News (JP)</a></li>
<li><a href="{root}recruit/">Recruit</a></li>
<li><a href="{home}contact/">Contact</a></li>
<li><a href="{home}privacy/">Privacy Policy</a></li>
<li><a href="{root}" lang="ja">日本語</a></li>"""
    else:
        foot_links = f"""<li><a href="{root}">ホーム</a></li>
<li><a href="{root}company/">私たちについて</a></li>
<li><a href="{root}service/">事業紹介</a></li>
<li><a href="{root}service/#group">グループ会社</a></li>
<li><a href="{root}service/regional-brand-creation/">ブランド・実績</a></li>
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
<meta property="og:type" content="{'article' if meta.get('article') else 'website'}">
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
<a class="ft-logo" href="{home}">NOW<br>HERE<br>GROUP</a>
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


def write(rel_dir, content):
    out_dir = os.path.join(BASE, rel_dir)
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(content)


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
        cat = f'<span class="tag">{esc(a["category"])}</span>' if a.get('category') else ''
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
        cat = f'<span class="tag">{esc(a["category"])}</span>' if a.get('category') else ''
        rows.append(f'''<li data-cat-item="{esc(a.get("category", ""))}"><a href="{root}{kind}/{a["id"]}/">
{thumb_html(a, root)}
<span class="meta"><time datetime="{a["date"].replace(".", "-")}">{a["date"]}</time>{cat}<span class="t">{esc(a["title"])}</span></span>
<span class="go" aria-hidden="true">→</span>
</a></li>''')
    filt = note = ''
    if kind == 'news':
        used = {a.get('category') for a in arts}
        btns = '<button type="button" data-cat="all" aria-pressed="true">すべて</button>' + ''.join(
            f'<button type="button" data-cat="{esc(c)}" aria-pressed="false">{esc(c)}</button>' for c in NEWS_CATS if c in used)
        filt = f'<div class="filter" role="group" aria-label="カテゴリで絞り込み">{btns}</div>'
        if NOTE_URL:
            note = f'<div class="btn-row" style="margin-top:32px"><a class="btn" href="{NOTE_URL}" target="_blank" rel="noopener">公式noteを見る <span class="arr">↗</span></a></div>'
    body = f'''<section class="sec">
<div class="wrap">
{filt}
<ul class="nlist-rows">
{chr(10).join(rows)}
</ul>
{note}
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
                f'<span class="li-body"><span class="li-date">{a["date"]}</span>'
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
BRANDS = [('nowhere', 'Nowhere Group株式会社', '企画・プロデュース・運営・SUPPLY'),
          ('vestport', 'VESTPORT株式会社', '不動産・工事・建物管理・資産活用・案件創出'),
          ('cleanx9', 'CLEANX9株式会社', '清掃・現地オペレーション'),
          ('familystay', '株式会社Family Stay', '販売・集客・顧客接点・Travel Tech')]
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
    jobs = []
    for fn in sorted(os.listdir(d)):
        if fn.endswith('.html') and not fn.startswith('_'):
            meta, body = read_meta(os.path.join(d, fn))
            meta['slug'] = fn[:-5]
            meta['body'] = body.strip()
            jobs.append(meta)
    jobs.sort(key=lambda j: j['order'])
    crumb_top = ('採用情報', 'recruit/')

    def job_tags(j):
        return (f'<span class="tag">{esc(j["brand"])}</span>'
                f'<span class="tag tag-line">{esc(j["employment"] or j["type"])}</span>')

    # 求人詳細
    for i, j in enumerate(jobs):
        rel_dir = f'recruit/{j["slug"]}/'
        root = root_for(rel_dir)
        body = f"""<div class="ph-simple"></div>
<article class="sec" style="padding-top:0">
<div class="wrap">
<div class="art">
<header class="art-head">
{crumbs_html([crumb_top, (j['title'], '')], root)}
<div class="row">{job_tags(j)}</div>
<h1>{esc(j['title'])}</h1>
<p class="job-lead">{esc(j['summary'])}</p>
<div class="btn-row" style="margin-top:8px"><a class="btn btn-dark" href="{APPLY_FORM}" target="_blank" rel="noopener">この求人に応募する <span class="arr">↗</span></a></div>
</header>
<div class="prose job">
{j['body']}
</div>
<nav class="art-nav" aria-label="求人の移動"><a class="btn" href="{root}recruit/#jobs"><span class="arr">←</span> 求人一覧へ戻る</a><a class="btn" href="{root}recruit/open-position/">オープンポジション <span class="arr">→</span></a></nav>
</div>
</div>
</article>"""
        meta = {'title': f'{j["title"]}（{j["type"]}）｜採用情報', 'description': f'{j["full"]}の求人。{j["summary"]}',
                'nav': 'recruit', 'accent': 'c-orange' if j['company'] == 'nowhere' else 'c-blue'}
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
    groups = []
    for key, name, desc in BRANDS:
        cards = []
        for j in [x for x in jobs if x['company'] == key]:
            cards.append(f"""<a class="card job-card" href="{root}recruit/{j['slug']}/">
<div class="row">{job_tags(j)}</div>
<h3>{esc(j['title'])}</h3>
<p>{esc(j['summary'])}</p>
<dl class="job-meta"><div><dt>就業場所</dt><dd>{esc(j['place'])}</dd></div><div><dt>{'報酬' if '業務委託' in j['employment'] else '賃金'}</dt><dd>{esc(j['salary'])}</dd></div></dl>
<span class="card-more">詳しくみる →</span>
</a>""")
        if not cards:
            cards.append(f"""<div class="card"><p>現在、募集中の求人はありません。ご興味のある方は<a href="{root}recruit/open-position/">オープンポジション</a>からご応募ください。</p></div>""")
        groups.append(f"""<div class="job-group">
<h3 class="job-brand">{esc(name)}<small>{esc(desc)}・{len([x for x in jobs if x['company'] == key])}件</small></h3>
<div class="grid g3" data-rv>
{chr(10).join(cards)}
</div>
</div>""")
    body = f"""<section class="sec">
<div class="wrap">
<div class="outline" data-rv>
<p class="lead">まだない宿泊の未来を、<br>一緒につくる。</p>
<div>
<p class="text" style="font-weight:700">Nowhere Groupで働くということ</p>
<p class="text">不動産だけでもない。<br>ホテル運営だけでもない。<br>清掃だけでも、テクノロジーだけでもない。</p>
<p class="text">異なる専門性を持つメンバーが、会社や部署の境界を越えて一つの宿泊事業をつくる。<br>それがNowhere Groupの仕事です。</p>
</div>
</div>
</div>
</section>

<section class="sec" id="future">
<div class="wrap">
<div class="sec-head"><h2><span class="num">01</span>Our Future</h2><p>私たちが目指す未来</p></div>
<div class="grid g2" data-rv>
<div class="card">
<span class="tag">Group Mission</span>
<h3>旅を起点に、<br>人々の心にアナザースカイを創る。</h3>
<p>旅には、日常では出会えない景色、人、文化、時間があります。私たちは宿泊を起点に、新しい体験と出会いを生み出し、人々の心にもうひとつの大切な場所を創っていきます。</p>
</div>
<div class="card">
<span class="tag">Group Vision</span>
<h3>2030年までに、<br>旅行の満足度で選ばれる宿泊グループになる。</h3>
<p>施設をつくることだけが、私たちの仕事ではありません。旅をする人、宿を持つ人、地域で暮らす人、宿泊を支える人。それぞれに価値が生まれる宿泊事業をつくり、日本の宿泊産業をより豊かなものにしていきます。</p>
</div>
</div>
<div class="btn-row" style="margin-top:28px"><a class="btn" href="{root}company/#philosophy">経営理念・グループ共通指針を見る <span class="arr">→</span></a></div>
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
<p class="text">空き家、相続した土地、中古別荘、お寺。眠っていた不動産が、選ばれる宿に生まれ変わるまでには、企画からプロデュース、運営、清掃、地域連携まで、会社や部署の境界を越えた多くのメンバーが関わっています。</p>
<p class="text" style="margin-top:12px">施設ごとのプロデュースの裏側を、公式noteで公開しています。</p>
</div>
</div>
{note_cards(root, NOTE_PROJECTS)}
<div class="btn-row" style="margin-top:28px"><a class="btn" href="{root}service/regional-brand-creation/#brands">ブランド・実績を見る <span class="arr">→</span></a></div>
</div>
</section>

<section class="sec sec-alt" id="environment">
<div class="wrap">
<div class="sec-head"><h2><span class="num">05</span>Environment</h2><p>働く環境・制度</p></div>
<div class="grid g4" data-rv>
{chr(10).join(f'<div class="card" style="gap:6px"><span class="tag">{i + 1:02}</span><h3>{esc(t)}</h3></div>' for i, t in enumerate(ENVIRONMENT))}
</div>
<p class="text" style="margin-top:24px">各制度の詳細は、面談の際にご説明します。</p>
</div>
</section>

<section class="sec" id="jobs">
<div class="wrap">
<div class="sec-head"><h2><span class="num">06</span>Jobs</h2><p>募集職種（会社別）・{len(jobs)}件</p></div>
{chr(10).join(groups)}
</div>
</section>

<section class="sec sec-alt">
<div class="wrap">
<div class="sec-head"><h2><span class="num">07</span>Open Position</h2><p>応募先に迷ったら</p></div>
<div class="card" style="gap:18px">
<h3 style="font-size:clamp(20px,2.4vw,26px)">応募先に迷ったら、オープンポジションから。</h3>
<p>経験や志向に合ったポジションをご提案するオープンポジションを設けています。ご応募内容をもとに、現在募集中のポジション、または募集準備中のポジションの中から、マッチの可能性があるものをご案内します。</p>
<div class="btn-row" style="margin-top:4px"><a class="btn btn-dark" href="{OPEN_FORM}" target="_blank" rel="noopener">オープンポジションに応募する <span class="arr">↗</span></a><a class="btn" href="{root}recruit/open-position/">詳しくみる <span class="arr">→</span></a></div>
</div>
</div>
</section>

<section class="sec">
<div class="wrap">
<div class="sec-head"><h2><span class="num">08</span>Privacy</h2><p>応募者の個人情報の取り扱い</p></div>
<p class="text">採用活動で取得する個人情報の取り扱いについては、<a href="{root}recruit/privacy/">採用プライバシーポリシー</a>をご確認ください。</p>
</div>
</section>"""
    counter = iter(range(1, 20))
    body = re.sub(r'<span class="num">\d+</span>', lambda m: f'<span class="num">{next(counter):02}</span>', body)
    meta = {'title': '採用情報', 'description': 'Nowhere Groupの採用情報。まだない宿泊の未来を、一緒につくる。私たちが目指す未来、仕事を知る、会社別の募集職種、オープンポジションをまとめています。',
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
     'content="Nowhere Group is a lodging business group that starts from accommodation and covers real estate, planning and development, operation, cleaning, sales and marketing across its group companies."'),
    ('<link rel="canonical" href="https://nowhere.group/">',
     '<link rel="canonical" href="https://nowhere.group/en/">'),
    ('aria-label="メインメニュー"',
     'aria-label="Main menu"'),
    ('<a class="hd-logo" href="./" aria-label="Nowhere Group トップへ">',
     '<a class="hd-logo" href="./" aria-label="Nowhere Group home">'),
    ('<a href="company/">私たちについて</a>\n<a href="service/">事業紹介</a>\n<a href="service/#group">グループ会社</a>\n<a href="service/regional-brand-creation/">ブランド・実績</a>\n<a href="news/">お知らせ</a>\n<a href="recruit/">採用情報</a>\n',
     '<a href="company/">About</a>\n<a href="service/">Business</a>\n<a href="service/#group">Group</a>\n<a href="service/regional-brand-creation/">Brands</a>\n<a href="recruit/">Recruit</a>\n'),
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
    ('alt="古民家の宿で旅人を迎えるスタッフのイラスト"',
     'alt="Illustration of staff welcoming a traveler at a traditional house inn"'),
    ('Nowhere Groupは、宿泊を起点に、<br>不動産、企画・開発、運営、清掃、販売・集客<br>までをグループで展開する宿泊事業グループです。',
     'Nowhere Group is a lodging business group that starts from accommodation and covers real estate, planning and development, operation, cleaning, sales and marketing across its group companies.'),
    ('宿泊事業に必要な機能をグループ内に持ち、<br>現場で得た知見を次の企画・開発へ還元する<br>ことで、施設の価値を継続的に高めていきます。',
     'We keep every function a lodging business needs within the group, and feed what we learn on site back into the next project to keep raising the value of each property.'),
    ('宿泊施設の「入口から出口まで」を、グループで。',
     'From entrance to exit of a lodging facility, as one group.'),
    ('>Nowhere Groupについて<',
     '>About Nowhere Group<'),
    ('alt="虹と海辺の町、設計図やスマホ、地域のマルシェを囲む旅人のイラスト"',
     'alt="Illustration of travelers around a rainbow, a seaside town, blueprints, a smartphone and a local market"'),
    ('</svg>宿泊施設の価値を、企画から運営までつくる。</h3>',
     '</svg>Creating the value of lodging facilities, from planning to operation.</h3>'),
    ('宿泊施設の企画・プロデュース、開業支援、運営、ホテルSUPPLYを担う、Nowhere Groupの中核会社。宿泊プロデュース／宿泊施設運営／ホテルSUPPLY',
     'The core company of Nowhere Group, responsible for planning and producing lodging facilities, opening support, operation and hotel supply. Produce / Operation / Hotel Supply'),
    ('</svg>宿泊投資を、もっと身近に。</h3>',
     '</svg>Making lodging investment more accessible.</h3>'),
    ('宿泊不動産の仕入れ・販売・流通から、工事、建物管理、資産活用、売却・出口戦略までを担う宿泊不動産会社。不動産／工事／プロパティマネジメント／再流通・出口支援',
     'A lodging real estate company covering sourcing, sales and distribution of lodging properties, construction, building management, asset utilization, sale and exit strategy. Real estate / Construction / Property management / Resale and exit support'),
    ('</svg>宿泊体験の品質を、現場から支える。</h3>',
     '</svg>Supporting the quality of every stay, from the field.</h3>'),
    ('ホテル・民泊清掃を中心に、リネン配送、ハウスクリーニング、現地設営、各種現地対応など、宿泊施設の現地オペレーションを支える会社。',
     'A company supporting on-site operations of lodging facilities: hotel and vacation rental cleaning, linen delivery, house cleaning, on-site setup and other local services.'),
    ('</svg>旅する人と、旅を支える人をつなぐ。</h3>',
     '</svg>Connecting travelers with the people who support travel.</h3>'),
    ('AI・SNS・OTAを融合し、旅行者には新しい旅行発見・予約体験を、宿泊事業者には販売・集客・広告・顧客獲得の仕組みを提供するTravel Tech企業。',
     'A travel tech company combining AI, social media and OTAs to give travelers a new way to discover and book trips, and to give lodging operators tools for sales, marketing, advertising and customer acquisition.'),
    ('>詳しく見る<',
     '>Read More<'),
    ('>宿泊事業のご相談<',
     '>Consult us on your lodging business<'),
    ('宿泊施設の企画・運営から、不動産、清掃、SUPPLY、販売・集客まで。お問い合わせはグループ窓口でまとめて承ります。',
     'From planning and operation of lodging facilities to real estate, cleaning, supply, sales and marketing: one contact point for the whole group.'),
    ('class="pill pill-ghost">お問い合わせ</a>',
     'class="pill pill-ghost">Contact</a>'),
    ('alt="提灯と祭り、夜の温泉街のイラスト"',
     'alt="Illustration of lanterns, a festival and a hot spring town at night"'),
    ('alt="宿から旅立つ旅人と、灯台のある海辺の町のイラスト"',
     'alt="Illustration of a traveler leaving an inn and a seaside town with a lighthouse"'),
    ('<span class="ft-co">Nowhere Group株式会社</span>',
     '<span class="ft-co">Nowhere Group Inc.</span>'),
    ('グループ各社へのお問い合わせは、こちらで一括して承ります。',
     'Inquiries for every group company are handled here, in one place.'),
    ('>お問い合わせフォーム<',
     '>Contact Form<'),
    ('aria-label="X（旧Twitter）"',
     'aria-label="X (formerly Twitter)"'),
    ('Copyright © 2025 Nowhere Group株式会社',
     'Copyright © 2025 Nowhere Group Inc.'),
    ('>プライバシーポリシー</a><a href="en/" lang="en">English</a>',
     '>Privacy Policy</a><a href="../" lang="ja">日本語</a>'),
    ('>経営理念<',
     '>Our philosophy<'),
    ('<h3>旅を起点に、<br>人々の心にアナザースカイを創る。</h3>',
     '<h3>Travel as the starting point for another sky in every heart.</h3>'),
    ('旅には、日常では出会えない景色、人、文化、時間があります。',
     'Travel brings scenery, people, culture and time you never meet in everyday life.'),
    ('私たちは宿泊を起点に、新しい体験と出会いを生み出し、人々の心にもうひとつの大切な場所を創っていきます。',
     "Starting from accommodation, we create new experiences and encounters, and build one more cherished place in people's hearts."),
    ('<h3>2030年までに、<br>旅行の満足度で選ばれる宿泊グループになる。</h3>',
     '<h3>By 2030, become the lodging group chosen for travel satisfaction.</h3>'),
    ('施設をつくることだけが、私たちの仕事ではありません。',
     'Building facilities is not all we do.'),
    ('旅をする人、宿を持つ人、地域で暮らす人、宿泊を支える人。それぞれに価値が生まれる宿泊事業をつくり、日本の宿泊産業をより豊かなものにしていきます。',
     "Travelers, property owners, local residents and the people who support lodging: we build a lodging business that creates value for each of them, and make Japan's lodging industry richer."),
    ('>経営理念を見る →<',
     '>Our philosophy →<'),
    ('<p>それぞれの専門性をつなぎ、<br>宿泊の価値を最大化する。</p>',
     "<p>Connecting each company's expertise<br>to maximize the value of lodging.</p>"),
    ('>宿泊バリューチェーン<',
     '>The lodging value chain<'),
    ('<p class="tp-lead">宿泊施設の入口から出口まで。</p>',
     '<p class="tp-lead">From the entrance to the exit of a lodging facility.</p>'),
    ('<h3>物件を見つける・取得する</h3>',
     '<h3>Find and acquire the property</h3>'),
    ('<p>物件仕入れ／売買／賃貸／事業承継</p>',
     '<p>Property sourcing / Sales / Leasing / Business succession</p>'),
    ('<h3>事業を企画する</h3>',
     '<h3>Plan the business</h3>'),
    ('<p>市場調査／事業性判断／収支計画／事業スキーム／コンセプト</p>',
     '<p>Market research / Feasibility / Business plan / Business scheme / Concept</p>'),
    ('<h3>宿泊施設をつくる</h3>',
     '<h3>Build the facility</h3>'),
    ('<p>宿泊プロデュース／ブランド・コンセプト設計／空間・デザイン／工事／許認可支援／開業準備</p>',
     '<p>Lodging production / Brand and concept design / Space and design / Construction / Licensing support / Opening preparation</p>'),
    ('<h3>宿泊施設を運営する</h3>',
     '<h3>Operate the facility</h3>'),
    ('<p>宿泊施設運営／ゲスト対応／価格・在庫管理／清掃／現地オペレーション／建物管理／緊急対応</p>',
     '<p>Hotel operation / Guest service / Pricing and inventory / Cleaning / On-site operations / Building management / Emergency response</p>'),
    ('<h3>施設に必要なものを届ける</h3>',
     '<h3>Deliver what the facility needs</h3>'),
    ('<span class="who">Nowhere Group / SUPPLY事業部</span>',
     '<span class="who">Nowhere Group / Supply Division</span>'),
    ('<p>家具／家電／寝具／備品／アメニティ／消耗品／清掃用品</p>',
     '<p>Furniture / Appliances / Bedding / Equipment / Amenities / Consumables / Cleaning supplies</p>'),
    ('<h3>旅行者へ届ける</h3>',
     '<h3>Reach travelers</h3>'),
    ('<p>宿泊販売／集客／マーケティング／AI／OTA／顧客接点</p>',
     '<p>Lodging sales / Marketing / AI / OTA / Customer touchpoints</p>'),
    ('<h3>売る・引き継ぐ</h3>',
     '<h3>Sell and hand over</h3>'),
    ('<p>売却／事業承継／再流通／出口支援</p>',
     '<p>Sale / Business succession / Resale / Exit support</p>'),
    ('<p class="tp-center">現場で得た知見を、<br>次の施設づくりへ。</p>',
     '<p class="tp-center">Knowledge from the field,<br>into the next facility.</p>'),
    ('>Nowhere Group株式会社の事業紹介<',
     '>Business of Nowhere Group Inc.<'),
    ('<span class="lbl">宿泊事業部</span>',
     '<span class="lbl">Lodging Division</span>'),
    ('<span class="lbl">SUPPLY事業部</span>',
     '<span class="lbl">Supply Division</span>'),
    ('<h3>宿泊プロデュース</h3>',
     '<h3>Lodging production</h3>'),
    ('<p class="catch">事業として成立する宿泊施設を、企画から形にする。</p>',
     '<p class="catch">Turning a viable lodging business into reality, from the plan.</p>'),
    ('市場、競合、立地、物件特性を分析し、ターゲット、収支計画、コンセプト、空間、宿泊体験までを設計します。企画だけで終わらず、実際の運営・清掃現場で蓄積した知見を施設づくりへ反映することで、ゲスト満足度、収益性、運営効率を両立した宿泊施設をつくります。',
     'We analyze the market, competitors, location and property, then design the target, business plan, concept, space and guest experience. By feeding knowledge from our operation and cleaning teams into facility design, we build properties that balance guest satisfaction, profitability and operational efficiency.'),
    ('<h3>宿泊施設運営</h3>',
     '<h3>Hotel operation</h3>'),
    ('<p class="catch">開業した施設の価値を、育て続ける。</p>',
     '<p class="catch">Growing the value of a property after opening.</p>'),
    ('ホテル、民泊、一棟貸しなどの宿泊施設について、販売、予約管理、価格調整、ゲスト対応、現地オペレーションまで、日々の施設運営を総合的に支援します。売上、レビュー、ゲスト対応、清掃現場などから得られる情報を分析し、継続的な施設改善へつなげます。',
     'For hotels, vacation rentals and whole-house rentals, we support daily operation from sales, reservation management and pricing to guest service and on-site operations. We analyze revenue, reviews, guest service and cleaning data to drive continuous improvement.'),
    ('<h3>ホテルSUPPLYサービス</h3>',
     '<h3>Hotel supply service</h3>'),
    ('<p class="catch">宿泊施設に必要なものを、まとめて届ける。</p>',
     '<p class="catch">Delivering everything a lodging facility needs, in one package.</p>'),
    ('Nowhere Groupが宿泊施設の開発・運営を通じて培ってきたノウハウと調達ネットワークを活用し、宿泊施設に必要な商品を提供します。開業時の一括調達から、運営開始後の補充・継続供給まで対応します。',
     'We use the know-how and procurement network built through developing and operating lodging facilities to supply the products they need, from bulk procurement at opening to replenishment after launch.'),
    ('>Nowhere Groupの強み<',
     '>What makes Nowhere Group different<'),
    ('<p class="tp-lead">現場から、宿をつくる。</p>',
     '<p class="tp-lead">Building hotels from the field.</p>'),
    ('<h3>清掃</h3><p>施設が実際にどう使われるのかを知る。汚れ方、動線、備品の消耗、清掃時間などを現場で知る。</p>',
     '<h3>Cleaning</h3><p>Knowing how facilities are actually used: wear patterns, traffic flow, consumption of supplies and cleaning time, learned on site.</p>'),
    ('<h3>運営</h3><p>ゲストが何に満足し、何に困るのかを知る。問い合わせ、レビュー、トラブル、予約動向から体験価値を理解する。</p>',
     '<h3>Operation</h3><p>Knowing what satisfies guests and what troubles them, through inquiries, reviews, incidents and booking trends.</p>'),
    ('<h3>プロデュース</h3><p>現場で起きる問題を、企画・設計段階で解決する。</p>',
     '<h3>Production</h3><p>Solving the problems that arise on site at the planning and design stage.</p>'),
    ('<h3>不動産</h3><p>事業性と出口から、物件を判断する。</p>',
     '<h3>Real estate</h3><p>Judging properties by business viability and exit.</p>'),
    ('清掃しにくい施設をつくらない。<br>ゲストが迷う施設をつくらない。<br>運営しにくい施設をつくらない。<br><span class="sub">現場を知っているからこそ、施設づくりの段階から解決できる。</span>',
     'We don\'t build facilities that are hard to clean.<br>We don\'t build facilities where guests get lost.<br>We don\'t build facilities that are hard to operate.<br><span class="sub">Because we know the field, we can solve problems at the design stage.</span>'),
    ('>ホテルブランド・実績・お知らせ<',
     '>Hotel brands, works and news (news in Japanese)<'),
    ('<p class="nw-lead">宿泊すること自体が、旅の目的になる場所をつくる。</p>',
     '<p class="nw-lead">Creating places where the stay itself is the purpose of the trip.</p>'),
    ('<small>365日、日本のお祭りを体験できる宿。</small>',
     '<small>Experience Japanese festivals 365 days a year.</small>'),
    ('<small>家族の「また来たい」をつくる宿。</small>',
     '<small>A stay that makes families want to come back.</small>'),
    ('<span>由楽</span><small>今後展開予定</small>',
     '<span>Yuraku</span><small>Coming soon</small>'),
    ('<span>墨武 -BOKUBU-</span><small>今後展開予定</small>',
     '<span>BOKUBU</span><small>Coming soon</small>'),
    ('<p class="nw-lead">宿泊施設に、そこに泊まる理由をつくる。</p>',
     '<p class="nw-lead">Giving every lodging facility a reason to stay there.</p>'),
    ('<span class="li-date">家族 × 遊び</span>',
     '<span class="li-date">Family × Play</span>'),
    ('<span class="li-title">タイムトリップOTOWA</span><span class="li-date">空き家 × 昭和レトロ</span>',
     '<span class="li-title">Time Trip OTOWA</span><span class="li-date">Vacant house × Showa retro</span>'),
    ('<span class="li-title">ZEN &amp; BED 望月庵</span><span class="li-date">寺 × 日本文化</span>',
     '<span class="li-title">ZEN &amp; BED Bougetsuan</span><span class="li-date">Temple × Japanese culture</span>'),
    ('<span class="li-title">Azure Palace 伊豆高原</span><span class="li-date">中古別荘 × 大人の遊び場</span>',
     '<span class="li-title">Azure Palace IZUKOGEN</span><span class="li-date">Used villa × Adult playground</span>'),
    ('alt="地域未来にぎわい工房"', 'alt="Chiiki Mirai Nigiwai Kobo"'),
    ('>パートナー・アライアンス<',
     '>Partners and alliances<'),
    ('<p class="tp-lead">一社ではできないことを、<br>共につくる。</p>',
     '<p class="tp-lead">Creating together<br>what no single company can.</p>'),
    ('Nowhere Groupは、旅行・観光・地域・不動産など、さまざまな企業・団体と連携しながら、新しい宿泊体験と事業機会を生み出しています。',
     'Nowhere Group works with companies and organizations in travel, tourism, regional development and real estate to create new lodging experiences and business opportunities.'),
    ('<p class="catch">Airbnb公式パートナープログラムに参画</p>',
     '<p class="catch">Member of the official Airbnb partner program</p>'),
    ('宿泊施設の企画・開発から運営、集客、収益改善まで、Nowhere Groupが蓄積してきた宿泊事業の知見を生かし、宿泊事業者を支援します。',
     'We support lodging operators with the knowledge Nowhere Group has built across planning, development, operation, marketing and revenue improvement.'),
    ('<h3>地域未来にぎわい工房</h3><p class="catch">地域資源を、新しい宿泊体験へ。</p>',
     '<h3>Chiiki Mirai Nigiwai Kobo</h3><p class="catch">Turning regional resources into new lodging experiences.</p>'),
    ('地域が持つ文化、食、自然、人などの資源を、宿泊施設や旅行体験とつなげ、新しい地域価値を生み出す取り組みを推進しています。',
     'A JTB-led initiative connecting the culture, food, nature and people of each region with lodging facilities and travel experiences to create new regional value.'),
    ('>評価・受賞・公的指定<',
     '>Awards and public designations<'),
    ('<p class="tp-lead">私たちの取り組みへの評価</p>',
     '<p class="tp-lead">Recognition of our work</p>'),
    ('<p class="catch">総合グランプリ</p>',
     '<p class="catch">Grand Prix</p>'),
    ('<h3>東京都</h3><p class="catch">東京観光案内窓口 指定</p><p>OMATSURI BASE 中野新橋</p>',
     '<h3>Tokyo Metropolitan Government</h3><p class="catch">Designated Tokyo tourist information center</p><p>OMATSURI BASE Nakanoshimbashi</p>'),
    ('>数字で見るNowhere Group<',
     '>Nowhere Group in numbers<'),
    ('<strong>100<small>施設以上</small></strong><span>宿泊プロデュース実績</span>',
     '<strong>100<small>+ facilities</small></strong><span>Lodging facilities produced</span>'),
    ('<strong>30<small>エリア以上</small></strong><span>展開エリア</span>',
     '<strong>30<small>+ areas</small></strong><span>Areas</span>'),
    ('<strong>50,000<small>件超</small></strong><span>CLEANX9 累計清掃件数</span>',
     '<strong>50,000<small>+ cleanings</small></strong><span>CLEANX9 total cleanings</span>'),
    ('<strong>150<small>施設</small></strong><span>SUPPLY 累計導入施設</span>',
     '<strong>150<small> facilities</small></strong><span>Facilities supplied</span>'),
    ('<strong>4<small>社</small></strong><span>グループ会社</span>',
     '<strong>4<small> companies</small></strong><span>Group companies</span>'),
    ('>代表メッセージ<',
     '>Message from the CEO<'),
    ('alt="代表取締役 CEO 竹内 剛"',
     'alt="Go Takeuchi, CEO"'),
    ('<h3>現場から積み上げた知見で、<br>宿泊産業の未来をつくる。</h3>',
     '<h3>Building the future of the lodging industry<br>on knowledge earned in the field.</h3>'),
    ('<p>私たちは、清掃や運営といった現場から宿泊事業を学んできました。</p>',
     '<p>We learned the lodging business from the ground up, through cleaning and operation.</p>'),
    ('<p>現場で生まれる課題を企画へ戻し、不動産、施設づくり、運営、清掃、販売までをつなげる。</p>',
     '<p>We bring the issues that arise on site back into planning, and connect real estate, facility development, operation, cleaning and sales.</p>'),
    ('<p>宿泊を起点に、旅する人、地域、事業者に新しい価値を生み出し続けます。</p>',
     '<p>Starting from accommodation, we keep creating new value for travelers, regions and operators.</p>'),
    ('<p class="name"><small>Nowhere Group株式会社 代表取締役 CEO</small>竹内 剛</p>',
     '<p class="name"><small>CEO, Nowhere Group Inc.</small>Go Takeuchi</p>'),
    ('>代表メッセージを見る →<',
     '>Read the full message →<'),
    ('>採用情報<',
     '>Careers (Japanese)<'),
    ('<p class="tp-lead">まだない宿泊の未来を、<br>一緒につくる。</p>',
     '<p class="tp-lead">Let\'s build a future of lodging<br>that doesn\'t exist yet.</p>'),
    ('不動産だけでもない。ホテル運営だけでもない。清掃だけでも、テクノロジーだけでもない。',
     'Not just real estate. Not just hotel operation. Not just cleaning, and not just technology.'),
    ('異なる専門性を持つメンバーが、会社や部署の境界を越えて一つの宿泊事業をつくる。それがNowhere Groupの仕事です。',
     'Members with different expertise cross company and department lines to build one lodging business. That is the work of Nowhere Group.'),
    ('>採用情報を見る →<',
     '>See open positions →<'),
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


def main():
    n = build_pages()
    news = build_articles('news', 'News', 'お知らせ', 'pink')
    columns = build_articles('column', 'Column', 'コラム', 'purple')
    jobs = build_recruit()
    update_top(news, columns)
    left = build_en_top()
    print(f'pages: {n}, news: {len(news)}, column: {len(columns)}, recruit: {len(jobs)}, en top: ok')
    if left:
        print('  英語トップに日本語の文言が残っています（ニュース・コラムの記事タイトル以外）:')
        for t in left:
            print('   -', t.strip()[:60])


if __name__ == '__main__':
    main()
