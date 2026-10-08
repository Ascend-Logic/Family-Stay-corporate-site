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
import html
import json
import os
import re

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(BASE, '_build')
SITE = 'Nowhere Group株式会社'
FONTS = ('https://fonts.googleapis.com/css2?family=Bagel+Fat+One&family=Outfit:wght@500;600;700'
         '&family=Zen+Kaku+Gothic+New:wght@500;700&display=swap')

NAV = [
    ('company', 'Company', 'company/'),
    ('service', 'Service', 'service/'),
    ('column', 'Column', 'column/'),
    ('news', 'News', 'news/'),
]
RECRUIT = 'https://nowhere-group.notion.site/nowhere-group-work-culture?source=copy_link'
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
<div class="ph-img"><img src="{root}images/{h['img']}" alt="{esc(h.get('alt', ''))}"></div>
</div>
</section>'''
    raise SystemExit(f'unknown hero type: {h["type"]}')


T = {
    'ja': {
        'site': SITE, 'tagline': '旅を通して 感動 笑顔 ワクワクを', 'skip': '本文へスキップ',
        'logo_label': 'Nowhere Group トップへ', 'menu_label': 'メインメニュー',
        'cta_text': 'その一言が、世界を変えるかもしれません。', 'cta_btn': 'お問い合わせフォーム',
        'address': '〒164-0013 東京都中野区弥生町2-25-10 弥生町2丁目ビル1F',
        'privacy': 'プライバシーポリシー', 'x_label': 'X（旧Twitter）', 'switch': ('EN', 'English'),
    },
    'en': {
        'site': 'Nowhere Group Inc.', 'tagline': 'Inspiration, Encounters, Excitement through travel', 'skip': 'Skip to content',
        'logo_label': 'Nowhere Group home', 'menu_label': 'Main menu',
        'cta_text': 'Your one word may change our world.', 'cta_btn': 'Contact Form',
        'address': 'Yayoicho 2-chome Bldg. 1F, 2-25-10 Yayoicho, Nakano-ku, Tokyo 164-0013, Japan',
        'privacy': 'Privacy Policy', 'x_label': 'X (formerly Twitter)', 'switch': ('JP', '日本語'),
    },
}
NAV_EN = [('company', 'Company', 'en/company/'), ('service', 'Service', 'en/service/')]
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
    nav += (f'<a href="{root}recruit/"{cur("recruit")}>Recruit</a>' if lang == 'ja'
            else f'<a href="{root}recruit/" lang="ja">Recruit</a>')
    other = counterpart(canonical)
    sw, sw_label = t['switch']
    nav += (f'<a href="{root}{other}" lang="{"ja" if lang == "en" else "en"}" hreflang="{"ja" if lang == "en" else "en"}" '
            f'aria-label="{sw_label}">{sw}</a>')
    nav += f'<a href="{home}contact/" class="nav-contact"{cur("contact")}>Contact</a>'
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
<li><a href="{home}company/">Company</a></li>
<li><a href="{home}service/">Service</a></li>
<li><a href="{root}news/" lang="ja">News (JP)</a></li>
<li><a href="{root}recruit/">Recruit</a></li>
<li><a href="{home}contact/">Contact</a></li>
<li><a href="{home}privacy/">Privacy Policy</a></li>
<li><a href="{root}" lang="ja">日本語</a></li>"""
    else:
        foot_links = f"""<li><a href="{root}">Home</a></li>
<li><a href="{root}company/">Company</a></li>
<li><a href="{root}service/">Service</a></li>
<li><a href="{root}column/">Column</a></li>
<li><a href="{root}news/">News</a></li>
<li><a href="{root}recruit/">Recruit</a></li>
<li><a href="{root}contact/">Contact</a></li>
<li><a href="{root}privacy/">Privacy Policy</a></li>
<li><a href="{root}en/" lang="en">English</a></li>"""
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
<link rel="stylesheet" href="{root}assets/css/header.css">
<link rel="stylesheet" href="{root}assets/css/sub.css">
<script src="{root}assets/js/header.js" defer></script>
<script src="{root}assets/js/sub.js" defer></script>
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
<a href="https://x.com/nowheregroup1" aria-label="{t['x_label']}" target="_blank" rel="noopener">X</a>
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


def build_articles(kind, label_en, label_ja, color):
    arts = load_articles(kind)
    for i, a in enumerate(arts):
        rel_dir = f'{kind}/{a["id"]}/'
        root = root_for(rel_dir)
        newer = arts[i - 1] if i > 0 else None
        older = arts[i + 1] if i + 1 < len(arts) else None
        cat = f'<span class="tag">{esc(a["category"])}</span>' if kind == 'column' and a.get('category') else ''
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
    years = sorted({a['date'][:4] for a in arts}, reverse=True)
    rows = []
    for a in arts:
        cat = f'<span class="tag">{esc(a["category"])}</span>' if kind == 'column' and a.get('category') else ''
        rows.append(f'''<li data-year-item="{a["date"][:4]}"><a href="{root}{kind}/{a["id"]}/">
{thumb_html(a, root)}
<span class="meta"><time datetime="{a["date"].replace(".", "-")}">{a["date"]}</time>{cat}<span class="t">{esc(a["title"])}</span></span>
<span class="go" aria-hidden="true">→</span>
</a></li>''')
    filt = ''
    if kind == 'news' and len(years) > 1:
        btns = '<button type="button" data-year="all" aria-pressed="true">All</button>' + ''.join(
            f'<button type="button" data-year="{y}" aria-pressed="false">{y}</button>' for y in years)
        filt = f'<div class="filter" role="group" aria-label="年で絞り込み">{btns}</div>'
    body = f'''<section class="sec">
<div class="wrap">
{filt}
<ul class="nlist-rows">
{chr(10).join(rows)}
</ul>
</div>
</section>'''
    desc = {'news': 'Nowhere Group株式会社からのお知らせ。新規開業施設、メディア掲載、受賞などの最新情報をお届けします。',
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
            print(f'  (index.html に build:{key} マーカーがないため更新をスキップ)')
            continue
        src = pat.sub(lambda m: m.group(1) + '\n'.join(items) + '\n' + m.group(2), src)
    open(path, 'w', encoding='utf-8').write(src)


# ---------------------------------------------------------------- 採用情報
APPLY_FORM = 'https://nowhere-group.notion.site/2da88671208580b2b482f7e55475e194'
OPEN_FORM = 'https://nowhere-group.notion.site/326886712085803fb9d8e91ca3812749'
BRANDS = [('nowhere', 'Nowhere Group', '宿泊施設のプロデュース・運営・不動産・コーポレート'),
          ('cleanx9', 'CLEANX9', 'ホテル・民泊の清掃代行')]


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
    crumb_top = ('Recruit', 'recruit/')

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
        groups.append(f"""<div class="job-group">
<h3 class="job-brand">{esc(name)}<small>{esc(desc)}・{len(cards)}件</small></h3>
<div class="grid g3" data-rv>
{chr(10).join(cards)}
</div>
</div>""")
    body = f"""<section class="sec">
<div class="wrap">
<div class="outline" data-rv>
<p class="lead">つながりで未来を築き、<br>世界中に笑顔を届ける仲間を<br>募集しています。</p>
<div>
<p class="text">この度はノーウェアグループにご関心をお持ちいただきありがとうございます。</p>
<p class="text">こちらは、ノーウェアグループの求人にご興味をお持ちいただいた方向けに、情報をまとめています。</p>
</div>
</div>
</div>
</section>

<section class="sec">
<div class="wrap">
<div class="sec-head"><h2><span class="num">01</span>Before the interview</h2><p>面談前にご覧いただきたい情報</p></div>
<div class="grid g2" data-rv>
<a class="card" href="{root}service/">
<span class="tag">事業内容</span>
<h3>Nowhere Groupの事業内容</h3>
<p>収益不動産、ホテル、地域ブランド創出、プラットフォームの4つの事業と、これまでにプロデュースした施設をご紹介しています。</p>
<span class="card-more">事業内容を見る →</span>
</a>
<a class="card" href="{root}company/">
<span class="tag">会社概要</span>
<h3>ビジョン・ミッション・バリュー</h3>
<p>私たちが大切にしている考え方や沿革、代表メッセージをご紹介しています。</p>
<span class="card-more">会社概要を見る →</span>
</a>
</div>
</div>
</section>

<section class="sec sec-alt" id="jobs">
<div class="wrap">
<div class="sec-head"><h2><span class="num">02</span>Jobs</h2><p>求人情報・{len(jobs)}件</p></div>
{chr(10).join(groups)}
</div>
</section>

<section class="sec sec-alt">
<div class="wrap">
<div class="sec-head"><h2><span class="num">03</span>Open Position</h2><p>応募先に迷ったら</p></div>
<div class="card" style="gap:18px">
<h3 style="font-size:clamp(20px,2.4vw,26px)">応募先に迷ったら、オープンポジションから。</h3>
<p>経験や志向に合ったポジションをご提案するオープンポジションを設けています。ご応募内容をもとに、現在募集中のポジション、または募集準備中のポジションの中から、マッチの可能性があるものをご案内します。</p>
<div class="btn-row" style="margin-top:4px"><a class="btn btn-dark" href="{OPEN_FORM}" target="_blank" rel="noopener">オープンポジションに応募する <span class="arr">↗</span></a><a class="btn" href="{root}recruit/open-position/">詳しくみる <span class="arr">→</span></a></div>
</div>
</div>
</section>

<section class="sec">
<div class="wrap">
<div class="sec-head"><h2><span class="num">04</span>Privacy</h2><p>応募者の個人情報の取り扱い</p></div>
<p class="text">採用活動で取得する個人情報の取り扱いについては、<a href="{root}recruit/privacy/">採用プライバシーポリシー</a>をご確認ください。</p>
</div>
</section>"""
    meta = {'title': '採用情報', 'description': 'Nowhere Group・CLEANX9の採用情報。募集中の求人、オープンポジション、面談前にご覧いただきたい情報をまとめています。',
            'nav': 'recruit', 'accent': 'c-orange',
            'hero': {'type': 'illust', 'en': 'Recruit', 'ja': '採用情報', 'color': 'orange', 'img': 'bg-company.jpg'},
            'crumbs': [('Recruit', '')]}
    write(rel_dir, layout(meta, body, root, rel_dir))
    return jobs


# ---------------------------------------------------------------- 英語トップ（index.html から生成）
# 日本語トップの文言を置き換えて en/index.html を作る。
# 日本語トップの文言を変えたら、ここの対応表も合わせて直すこと（見つからない場合はビルドが止まる）。
EN_TOP = [
    ('<html lang="ja">', '<html lang="en">'),
    ('<title>Nowhere Group株式会社｜旅を通して 感動 笑顔 ワクワクを</title>',
     '<title>Nowhere Group Inc. | Inspiration, Encounters, Excitement through travel</title>'),
    ('content="Nowhere Group株式会社は、日本全国の小規模型宿泊施設のプロデュースを行なっている企業です。企画・設計・デザイン・運営・管理をワンストップで提供しています。"',
     'content="Nowhere Group Inc. is a one-stop provider of total services across planning, design, operation and management of small-scale lodging facilities throughout Japan."'),
    ('<link rel="canonical" href="https://nowhere.group/">', '<link rel="canonical" href="https://nowhere.group/en/">'),
    ('aria-label="メインメニュー"', 'aria-label="Main menu"'),
    ('<a class="hd-logo" href="./" aria-label="Nowhere Group トップへ">', '<a class="hd-logo" href="./" aria-label="Nowhere Group home">'),
    ('<a href="column/">Column</a>\n<a href="news/">News</a>\n', ''),
    ('<a href="en/" lang="en" hreflang="en" aria-label="English">EN</a>',
     '<a href="../" lang="ja" hreflang="ja" aria-label="日本語">JP</a>'),
    ('class="side-contact">お問い合わせ</a>', 'class="side-contact">Contact</a>'),
    ('alt="温泉旅館、海辺の町、山、祭り、地域の食を旅する人々のイラスト"',
     'alt="Illustration of travelers enjoying hot spring inns, seaside towns, mountains, festivals and local food"'),
    ('旅を通して 感動 笑顔 ワクワクを ─ Create for people all over the world.',
     'Inspiration, Encounters, Excitement through travel ─ Create for people all over the world.'),
    ('alt="古民家の宿で旅人を迎えるスタッフのイラスト"',
     'alt="Illustration of staff welcoming a traveler at a traditional house inn"'),
    ('私たちNowhere Group株式会社は、<br>日本全国の小規模型宿泊施設のプロデュースを<br>行なっている企業です。',
     'Nowhere Group Inc. produces small-scale lodging facilities throughout Japan.'),
    ('宿泊施設の企画・設計・デザイン・運営・管理の<br>各事業領域を横断した、トータルサービスを<br>ワンストップで提供しています。',
     'We are a one-stop provider of total services across planning, design, operation, and management of lodging facilities.'),
    ('ここでしか味わえない体験を創り出す。', 'Creating experiences you can only find here.'),
    ('>会社概要をみる<', '>About us<'),
    ('alt="虹と海辺の町、設計図やスマホ、地域のマルシェを囲む旅人のイラスト"',
     'alt="Illustration of travelers around a rainbow, a seaside town, blueprints, a smartphone and a local market"'),
    ('>私たちの事業<', '>Our business<'),
    ('</svg>収益不動産事業</h3>', '</svg>Profitable real estate</h3>'),
    ('ホテル・民泊の企画・設計・運営の幅広いナレッジで、居住用・投資用不動産に次ぐ第三の選択肢「住居兼ホテル（収益不動産）」づくりを。',
     'With our knowledge of planning, design, and operation of hotels and private accommodations, we create the "residence hotel": a third option after residential and investment real estate.'),
    ('</svg>ホテル事業</h3>', '</svg>Hotel</h3>'),
    ('ICT・IoT・PMSを活用した無人/省人型ホテル・民泊の不動産探し、企画、設計デザイン、許認可、運営、清掃、撮影まで一気通貫で提供。',
     'A full range of services for personless hotels and private accommodations using ICT, IoT, and PMS, from real estate search and planning to design, permits, operation, cleaning, and photography.'),
    ('</svg>地域ブランド創出事業</h3>', '</svg>Regional brand creation</h3>'),
    ('食、ヒト、モノ、場所など地域の魅力を発掘し、設計デザイン・運営に取り込み、ホテルを通して地域のブランドをお届け。',
     'We discover the charms of each region in food, people, goods, and places, and deliver local brands to guests through our hotels.'),
    ('</svg>プラットフォーム事業</h3>', '</svg>Platform</h3>'),
    ('不動産・ホテル・旅行をより便利で身近にするプラットフォームを開発・提供。テクノロジーで旅に新たなイノベーションを。',
     'We develop platforms that make real estate, hotels, and travel more convenient and accessible, creating innovation in travel through technology.'),
    ('>詳しくみる<', '>Read More<'),
    ('>プロデュースのご相談<', '>Consult us on your project<'),
    ('小規模宿泊施設の企画から運営まで、ワンストップでご相談を受け付けております。',
     'From planning to operation of small-scale lodging facilities, we can help you with everything in one place.'),
    ('class="pill pill-ghost">お問い合わせ</a>', 'class="pill pill-ghost">Contact</a>'),
    ('alt="提灯と祭り、夜の温泉街のイラスト"', 'alt="Illustration of lanterns, a festival and a hot spring town at night"'),
    ('>施設・コラム・お知らせ<', '>Hotels, columns and news (columns and news in Japanese)<'),
    ('>HARELIER 山中湖<', '>HARELIER Yamanakako<'),
    ('>ZEN &amp; BED 望月庵<', '>ZEN &amp; BED Bougetsuan<'),
    ('>まるごの宿 耕<', '>Marugonoyado Kou<'),
    ('>Azure Palace 伊豆高原<', '>Azure Palace IZUKOGEN<'),
    ('alt="宿から旅立つ旅人と、灯台のある海辺の町のイラスト"',
     'alt="Illustration of a traveler leaving an inn and a seaside town with a lighthouse"'),
    ('<span class="ft-co">Nowhere Group株式会社</span>', '<span class="ft-co">Nowhere Group Inc.</span>'),
    ('その一言が、世界を変えるかもしれません。', 'Your one word may change our world.'),
    ('>お問い合わせフォーム<', '>Contact Form<'),
    ('aria-label="X（旧Twitter）"', 'aria-label="X (formerly Twitter)"'),
    ('Copyright © 2025 Nowhere Group株式会社', 'Copyright © 2025 Nowhere Group Inc.'),
    ('>プライバシーポリシー</a><a href="en/" lang="en">English</a>', '>Privacy Policy</a><a href="../" lang="ja">日本語</a>'),
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
