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

# グローバルナビ（日本語で統一。英語はデザイン上のサブ見出しのみ）
NAV = [
    ('about', '私たちについて', 'about/'),
    ('service', '事業紹介', 'service/'),
    ('group', 'グループ会社', 'group/'),
    ('brand', 'ブランド・実績', 'brand/'),
    ('news', 'お知らせ', 'news/'),
]
NEWS_CATEGORIES = ['グループ', 'Nowhere Group', 'VESTPORT', 'CLEANX9', 'Family Stay', 'プレスリリース', 'メディア掲載', '受賞・認定']
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
    items = [f'<li><a href="{home}">{"Home" if lang == "en" else "トップ"}</a></li>']
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
{('<p class="ph-en">' + esc(h['en']) + '</p><h1 class="ph-title ph-title-ja">' + esc(h['ja']) + '</h1>') if lang == 'ja' else ('<h1 class="ph-title">' + esc(h['en']) + '</h1><p class="ph-ja">' + esc(h['ja']) + '</p>')}
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
        'site': SITE, 'tagline': '旅を起点に、人々の心にアナザースカイを創る。', 'skip': '本文へスキップ',
        'logo_label': 'Nowhere Group トップへ', 'menu_label': 'メインメニュー',
        'cta_text': '宿泊施設の企画・運営・不動産・清掃・SUPPLY・販売集客まで、お問い合わせはグループ窓口で承ります。', 'cta_btn': 'お問い合わせフォーム',
        'address': '〒164-0013 東京都中野区弥生町2-25-10 弥生町2丁目ビル1F',
        'privacy': 'プライバシーポリシー', 'x_label': 'X（旧Twitter）', 'switch': ('EN', 'English'),
    },
    'en': {
        'site': 'Nowhere Group Inc.', 'tagline': 'Creating another sky in people\'s hearts, starting with travel.', 'skip': 'Skip to content',
        'logo_label': 'Nowhere Group home', 'menu_label': 'Main menu',
        'cta_text': 'From planning and operation to real estate, cleaning, supply and sales: one window for the whole group.', 'cta_btn': 'Contact Form',
        'address': 'Yayoicho 2-chome Bldg. 1F, 2-25-10 Yayoicho, Nakano-ku, Tokyo 164-0013, Japan',
        'privacy': 'Privacy Policy', 'x_label': 'X (formerly Twitter)', 'switch': ('JP', '日本語'),
    },
}
NAV_EN = [('company', 'About', 'en/company/'), ('service', 'Business', 'en/service/')]
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
            else f'<a href="{root}recruit/" lang="ja">Careers</a>')
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
    extra_css = ''.join(f'<link rel="stylesheet" href="{root}assets/css/{c}">\n' for c in meta.get('css', []))
    extra_js = ''.join(f'<script src="{root}assets/js/{j}" defer></script>\n' for j in meta.get('js', []))
    cta = '' if meta.get('cta') is False else f"""
<section class="cta" aria-labelledby="cta-title">
<img src="{root}images/bg-news.jpg" alt="" loading="lazy" width="1672" height="941">
<div class="wrap">
<h2 id="cta-title">Make it <span data-spin style="color:#FFD84A">✸</span><br>together</h2>
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
<li><a href="{root}group/" lang="ja">Group Companies (JP)</a></li>
<li><a href="{root}brand/" lang="ja">Brands (JP)</a></li>
<li><a href="{root}news/" lang="ja">News (JP)</a></li>
<li><a href="{root}recruit/" lang="ja">Careers (JP)</a></li>
<li><a href="{home}contact/">Contact</a></li>
<li><a href="{home}privacy/">Privacy Policy</a></li>
<li><a href="{root}" lang="ja">日本語</a></li>"""
    else:
        foot_links = f"""<li><a href="{root}">トップ</a></li>
<li><a href="{root}about/">私たちについて</a></li>
<li><a href="{root}service/">事業紹介</a></li>
<li><a href="{root}group/">グループ会社</a></li>
<li><a href="{root}brand/">ブランド・実績</a></li>
<li><a href="{root}news/">お知らせ</a></li>
<li><a href="{root}recruit/">採用情報</a></li>
<li><a href="{root}contact/">お問い合わせ</a></li>
<li><a href="{root}company/">会社概要</a></li>
<li><a href="{root}privacy/">プライバシーポリシー</a></li>
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
{extra_css}<script src="{root}assets/js/header.js" defer></script>
<script src="{root}assets/js/sub.js" defer></script>
{extra_js}</head>
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
        cat = f'<span class="tag">{esc(a["category"])}</span>' if a.get('category') else ''
        rows.append(f'''<li data-year-item="{a["date"][:4]}" data-cat-item="{esc(a.get("category", ""))}"><a href="{root}{kind}/{a["id"]}/">
{thumb_html(a, root)}
<span class="meta"><time datetime="{a["date"].replace(".", "-")}">{a["date"]}</time>{cat}<span class="t">{esc(a["title"])}</span></span>
<span class="go" aria-hidden="true">→</span>
</a></li>''')
    filt = ''
    if kind == 'news':
        used = {a.get('category') for a in arts}
        cats = [c for c in NEWS_CATEGORIES if c in used]
        btns = '<button type="button" data-cat="all" aria-pressed="true">すべて</button>' + ''.join(
            f'<button type="button" data-cat="{esc(c)}" aria-pressed="false">{esc(c)}</button>' for c in cats)
        filt = f'<div class="filter" role="group" aria-label="カテゴリで絞り込み">{btns}</div>'
        if len(years) > 1:
            ybtns = '<button type="button" data-year="all" aria-pressed="true">All</button>' + ''.join(
                f'<button type="button" data-year="{y}" aria-pressed="false">{y}</button>' for y in years)
            filt += f'<div class="filter filter-year" role="group" aria-label="年で絞り込み">{ybtns}</div>'
    body = f'''<section class="sec">
<div class="wrap">
{filt}
<p class="filter-empty note" hidden>該当するお知らせはありません。</p>
<ul class="nlist-rows">
{chr(10).join(rows)}
</ul>
</div>
</section>'''
    desc = {'news': 'Nowhere Groupからのお知らせ。グループ各社のニュース、プレスリリース、メディア掲載、受賞・認定などの最新情報をお届けします。',
            'column': '宿泊施設プロデュース、民泊投資、不動産売買・M&Aなど、宿泊・観光業界に関するNowhere Groupのコラムです。'}[kind]
    meta = {'title': label_en, 'description': desc, 'nav': kind, 'accent': f'c-{color}',
            'hero': {'type': 'illust', 'en': label_en, 'ja': label_ja, 'color': color,
                     'img': 'bg-footer.jpg'},
            'crumbs': [(label_en, '')]}
    write(rel_dir, layout(meta, body, root, rel_dir))
    return arts


# ---------------------------------------------------------------- トップ（_build/top.html から生成）
def short_title(t, n=44):
    return t if len(t) <= n else t[:n] + '…'


def top_news_rows(news, root, lang='ja'):
    rows = []
    for a in news[:3]:
        extra = ' lang="ja"' if lang == 'en' else ''
        rows.append(f'<a href="{root}news/{a["id"]}/" class="news-row"{extra}>'
                    f'<time datetime="{a["date"].replace(".", "-")}">{a["date"]}</time>'
                    f'<span class="tag">{esc(a.get("category", ""))}</span>'
                    f'<span class="t">{esc(a.get("short") or short_title(a["title"]))}</span></a>')
    return '\n'.join(rows)


# ---------------------------------------------------------------- 採用情報
APPLY_FORM = 'https://nowhere-group.notion.site/2da88671208580b2b482f7e55475e194'
OPEN_FORM = 'https://nowhere-group.notion.site/326886712085803fb9d8e91ca3812749'
BRANDS = [('nowhere', 'Nowhere Group株式会社', '企画・プロデュース・運営・SUPPLY・コーポレート'),
          ('vestport', 'VESTPORT株式会社', '不動産・工事・建物管理・資産活用'),
          ('cleanx9', 'CLEANX9株式会社', '清掃・現地オペレーション'),
          ('family-stay', '株式会社Family Stay', '販売・集客・顧客接点・Travel Tech')]
JOB_TYPES = ['宿泊プロデュース', '宿泊施設運営', 'グループ営業', '事業企画', '不動産', '工事', '建物管理', '清掃',
             '現地オペレーション', 'SUPPLY', 'Travel Tech', 'マーケティング', 'コーポレート']


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
        if cards:
            grid = f'<div class="grid g3" data-rv>\n{chr(10).join(cards)}\n</div>'
        else:
            grid = '<p class="text" style="color:var(--sub)">現在、募集中の求人はありません。オープンポジションからご応募ください。</p>'
        groups.append(f"""<div class="job-group">
<h3 class="job-brand">{esc(name)}<small>{esc(desc)}・{len(cards)}件</small></h3>
{grid}
</div>""")
    jobs_html = ''.join(f'<li>{esc(x)}</li>' for x in JOB_TYPES)
    body = f"""<section class="sec">
<div class="wrap">
<div class="outline" data-rv>
<p class="lead">まだない宿泊の未来を、<br>一緒につくる。</p>
<div>
<p class="text" style="font-weight:700;margin-bottom:12px">Nowhere Groupで働くということ</p>
<p class="text">不動産だけでもない。ホテル運営だけでもない。清掃だけでも、テクノロジーだけでもない。<br>異なる専門性を持つメンバーが、会社や部署の境界を越えて一つの宿泊事業をつくる。<br>それがNowhere Groupの仕事です。</p>
</div>
</div>
</div>
</section>

<section class="sec" id="future">
<div class="wrap">
<div class="sh"><span class="sh-en">01 OUR FUTURE</span><h2>私たちが目指す未来</h2></div>
<div class="grid g2" data-rv>
<div class="card">
<span class="tag">グループミッション</span>
<h3>旅を起点に、人々の心にアナザースカイを創る。</h3>
<p>旅には、日常では出会えない景色、人、文化、時間があります。私たちは宿泊を起点に、新しい体験と出会いを生み出し、人々の心にもうひとつの大切な場所を創っていきます。</p>
</div>
<div class="card">
<span class="tag">グループビジョン</span>
<h3>2030年までに、旅行の満足度で選ばれる宿泊グループになる。</h3>
<p>施設をつくることだけが、私たちの仕事ではありません。旅をする人、宿を持つ人、地域で暮らす人、宿泊を支える人。それぞれに価値が生まれる宿泊事業をつくり、日本の宿泊産業をより豊かなものにしていきます。</p>
</div>
</div>
<p class="text" style="margin-top:24px"><a href="{root}about/#philosophy">経営理念・グループ共通指針を見る →</a></p>
</div>
</section>

<section class="sec sec-alt" id="work">
<div class="wrap">
<div class="sh"><span class="sh-en">02 OUR WORK</span><h2>仕事を知る</h2></div>
<p class="text" style="margin-bottom:24px">宿泊施設の「入口から出口まで」をグループで担うため、職種は多岐にわたります。異なる専門性が、ひとつの施設づくりの中でつながります。</p>
<ul class="chips" data-rv>
{jobs_html}
</ul>
</div>
</section>

<section class="sec sec-alt" id="project">
<div class="wrap">
<div class="sh"><span class="sh-en">03 PROJECT STORY</span><h2>プロジェクトを知る</h2></div>
<div class="card" style="gap:18px">
<span class="tag">OMATSURI BASEができるまで</span>
<h3 style="font-size:clamp(20px,2.4vw,26px)">ひとつの宿は、ひとつの職種ではつくれない。</h3>
<p>「365日、日本のお祭りを体験できる宿」OMATSURI BASEは、企画、プロデュース、運営、清掃、地域連携、マーケティングと、グループ内の複数のメンバーが関わって生まれました。市場調査と事業性判断から始まり、コンセプトと空間をかたちにし、開業後は運営・清掃の現場で得た気づきを日々の改善へ。地域の飲食店・銭湯・神社・商店街との連携や、旅行者への発信も、それぞれの専門性を持つメンバーが担っています。</p>
<ol class="flow" aria-label="関わる役割">
<li>企画</li><li>プロデュース</li><li>運営</li><li>清掃</li><li>地域連携</li><li>マーケティング</li>
</ol>
<div class="btn-row"><a class="btn" href="{root}brand/#omatsuri-base">OMATSURI BASEを見る <span class="arr">→</span></a></div>
</div>
</div>
</section>

<section class="sec" id="jobs">
<div class="wrap">
<div class="sh"><span class="sh-en">04 JOBS</span><h2>募集職種・{len(jobs)}件（会社別）</h2></div>
{chr(10).join(groups)}
</div>
</section>

<section class="sec sec-alt">
<div class="wrap">
<div class="sh"><span class="sh-en">05 OPEN POSITION</span><h2>応募先に迷ったら</h2></div>
<div class="card" style="gap:18px">
<h3 style="font-size:clamp(20px,2.4vw,26px)">応募先に迷ったら、オープンポジションから。</h3>
<p>経験や志向に合ったポジションをご提案するオープンポジションを設けています。ご応募内容をもとに、現在募集中のポジション、または募集準備中のポジションの中から、マッチの可能性があるものをご案内します。</p>
<div class="btn-row" style="margin-top:4px"><a class="btn btn-dark" href="{OPEN_FORM}" target="_blank" rel="noopener">オープンポジションに応募する <span class="arr">↗</span></a><a class="btn" href="{root}recruit/open-position/">詳しくみる <span class="arr">→</span></a></div>
</div>
</div>
</section>

<section class="sec">
<div class="wrap">
<div class="sh"><span class="sh-en">06 PRIVACY</span><h2>応募者の個人情報の取り扱い</h2></div>
<p class="text">採用活動で取得する個人情報の取り扱いについては、<a href="{root}recruit/privacy/">採用プライバシーポリシー</a>をご確認ください。</p>
</div>
</section>"""
    meta = {'title': '採用情報', 'description': 'Nowhere Groupの採用情報。まだない宿泊の未来を、一緒につくる仲間を募集しています。グループ各社の募集職種、オープンポジションをご案内します。',
            'nav': 'recruit', 'accent': 'c-orange',
            'hero': {'type': 'illust', 'en': 'Recruit', 'ja': '採用情報', 'color': 'orange', 'img': 'bg-company.jpg'},
            'crumbs': [('採用情報', '')]}
    write(rel_dir, layout(meta, body, root, rel_dir))
    return jobs


# ---------------------------------------------------------------- トップ（日本語・英語）
# 英語トップは _build/top.html の文言を EN_TOP の対応表で置き換えて生成する。
# 日本語トップの文言を変えたら、ここの対応表も合わせて直すこと（見つからない場合はビルドが止まる）。
import importlib.util as _ilu
_spec = _ilu.spec_from_file_location('en_top', os.path.join(SRC, 'en_top.py'))
_mod = _ilu.module_from_spec(_spec); _spec.loader.exec_module(_mod)
EN_TOP = _mod.EN_TOP
EN_TOP_META = {
    'title': '', 'nav': '', 'accent': 'c-orange', 'cta': False, 'css': ['top.css'], 'js': ['top.js'],
    'description': 'Nowhere Group is a lodging business group that spans real estate, planning and development, operation, cleaning, sales and marketing, starting from accommodation. Creating another sky in people\'s hearts, starting with travel.',
}


def build_top(news):
    meta, body = read_meta(os.path.join(SRC, 'top.html'))
    write('', layout(meta, body.replace('{{news}}', top_news_rows(news, '')), '', ''))

    src = body
    for ja, en in EN_TOP:
        if src.count(ja) == 0:
            raise SystemExit(f'英語トップ: 置き換え元が見つかりません（top.html の文言が変わった可能性）: {ja[:60]}')
        src = src.replace(ja, en)
    src = src.replace('{{news}}', top_news_rows(news, '../', 'en'))
    # 英語版があるページは英語版へ、それ以外は日本語ページへ（lang="ja" を付ける）
    def en_link(m):
        path = m.group(1)
        return '{{home}}' + path if ('en/' + path) in PAGE_DIRS else m.group(0)
    src = re.sub(r'\{\{root\}\}((?!images/)[a-z0-9\-/]+/)', en_link, src)
    src = re.sub(r'<a class="([^"]*)" href="\{\{root\}\}(?!images/)', r'<a class="\1" lang="ja" href="{{root}}', src)
    src = re.sub(r'<a href="\{\{root\}\}(?!images/)', r'<a lang="ja" href="{{root}}', src)
    write('en/', layout(EN_TOP_META, src, '../', 'en/'))
    # 日本語が残っていないか確認（lang="ja" のリンク内と画像の alt は除く）
    body_wo_ja = re.sub(r'<a[^>]*lang="ja".*?</a>', '', src, flags=re.S)
    body_wo_ja = re.sub(r'alt="[^"]*"', '', body_wo_ja)
    remain = re.findall(r'>([^<]*[぀-ヿ一-鿿][^<]*)<', body_wo_ja)
    return [r for r in remain if r.strip()]


def main():
    n = build_pages()
    news = build_articles('news', 'News', 'お知らせ', 'pink')
    columns = build_articles('column', 'Column', 'コラム', 'purple')
    jobs = build_recruit()
    left = build_top(news)
    print(f'pages: {n}, news: {len(news)}, column: {len(columns)}, recruit: {len(jobs)}, top: ok')
    if left:
        print('  英語トップに日本語の文言が残っています（日本語ページへのリンク以外）:')
        for t in left:
            print('   -', t.strip()[:60])


if __name__ == '__main__':
    main()
