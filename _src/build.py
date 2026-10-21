#!/usr/bin/env python3
"""TurnuVolt sitesini üretir: her dil için ana sayfa + fikstür oluşturucu, sitemap.xml ve llms.txt.

Kullanım (depo kökünden):  python3 _src/build.py [--app /yol/4.2_ios]

- Sayfa metinleri: _src/i18n/<dil>.json (yalnızca dosyası olan diller üretilir)
- Oyun adları, kategoriler, tablo başlıkları gibi uygulama metinleri: _src/app_strings.json
  (iOS projesinden --app ile yenilenir; yoksa mevcut dosya kullanılır)
- Şablonlar: _src/home.html, _src/fixture.html, stiller: _src/site.css, _src/fixture.css
Jekyll "_" ile başlayan klasörleri yayınlamaz; _src sitede görünmez.
"""
import argparse
import datetime
import html
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, '_src')
SITE = 'https://anbertech.github.io/TurnuVolt/'
APP_ID = '6745177155'
EMAIL = 'destek.anbertech@gmail.com'

# kod, yön, yerel ad, og:locale, oyun panosu tek parça mı (bitişik/birleşen yazı)
LANGS = [
    ('tr', 'ltr', 'Türkçe', 'tr_TR', False),
    ('en', 'ltr', 'English', 'en_US', False),
    ('ar', 'rtl', 'العربية', 'ar_AR', True),
    ('cs', 'ltr', 'Čeština', 'cs_CZ', False),
    ('da', 'ltr', 'Dansk', 'da_DK', False),
    ('de', 'ltr', 'Deutsch', 'de_DE', False),
    ('el', 'ltr', 'Ελληνικά', 'el_GR', False),
    ('es', 'ltr', 'Español', 'es_ES', False),
    ('es-MX', 'ltr', 'Español (México)', 'es_MX', False),
    ('fa', 'rtl', 'فارسی', 'fa_IR', True),
    ('fi', 'ltr', 'Suomi', 'fi_FI', False),
    ('fr', 'ltr', 'Français', 'fr_FR', False),
    ('he', 'rtl', 'עברית', 'he_IL', True),
    ('hi', 'ltr', 'हिन्दी', 'hi_IN', True),
    ('hu', 'ltr', 'Magyar', 'hu_HU', False),
    ('id', 'ltr', 'Bahasa Indonesia', 'id_ID', False),
    ('it', 'ltr', 'Italiano', 'it_IT', False),
    ('ja', 'ltr', '日本語', 'ja_JP', False),
    ('ko', 'ltr', '한국어', 'ko_KR', False),
    ('ms', 'ltr', 'Bahasa Melayu', 'ms_MY', False),
    ('nb', 'ltr', 'Norsk bokmål', 'nb_NO', False),
    ('nl', 'ltr', 'Nederlands', 'nl_NL', False),
    ('pl', 'ltr', 'Polski', 'pl_PL', False),
    ('pt-BR', 'ltr', 'Português (Brasil)', 'pt_BR', False),
    ('pt-PT', 'ltr', 'Português (Portugal)', 'pt_PT', False),
    ('ro', 'ltr', 'Română', 'ro_RO', False),
    ('ru', 'ltr', 'Русский', 'ru_RU', False),
    ('sv', 'ltr', 'Svenska', 'sv_SE', False),
    ('th', 'ltr', 'ไทย', 'th_TH', True),
    ('uk', 'ltr', 'Українська', 'uk_UA', False),
    ('vi', 'ltr', 'Tiếng Việt', 'vi_VN', False),
    ('zh-Hans', 'ltr', '简体中文', 'zh_CN', False),
    ('zh-Hant', 'ltr', '繁體中文', 'zh_TW', False),
]
LANG = {l[0]: l for l in LANGS}

APP_KEYS = [
    'Category.ballSports', 'Category.racketSports', 'Category.combatSports', 'Category.precisionSports',
    'Category.tableGames', 'Category.esports', 'Category.other',
    'TournamentFormat.league', 'FixtureView.tournamentSuffix', 'HomeView.newTournamentButton',
    'ScoreInputView.header.team', 'ScoreInputView.header.Pld', 'ScoreInputView.header.W', 'ScoreInputView.header.D',
    'ScoreInputView.header.L', 'ScoreInputView.header.GF', 'ScoreInputView.header.GA', 'ScoreInputView.header.GD',
    'ScoreInputView.header.Pts',
    'Bracket.tapToSelectWinner', 'Bracket.semiFinal', 'Bracket.final', 'Bracket.quarterFinal', 'Bracket.roundOfFormat',
    'Bracket.championTitle',
]

# Sayfa metinleri: her dil dosyasında bulunması gereken anahtarlar
REQUIRED = {
    'title': str, 'meta_desc': str, 'store_alt': str, 'soon': str, 'scroll_down': str,
    'aria_screens': str, 'ss_podium': str, 'ss_fixture': str, 'ss_new': str, 'ss_home': str, 'ss_saved': str,
    'aria_games': str, 'aria_board': str, 'aria_cats': str, 'random_game': str, 'aria_formats': str, 'tab_ko': str,
    'led_title': str, 'reset_bracket': str, 'aria_langs': str, 'aria_lang': str, 'aria_docs': str,
    'privacy': str, 'support': str, 'aria_download': str,
    'tagline': str, 'hero_tool_link': str,
    'about_eyebrow': str, 'about_h2': str, 'about_lead': str, 'steps': list, 'feats': list,
    'tool_eyebrow': str, 'tool_h2': str, 'tool_text': str, 'tool_btn': str,
    'faq_eyebrow': str, 'faq_h2': str, 'faq_home': list,
    'fx_slug': str, 'fx_name': str, 'fx_title': str, 'fx_desc': str, 'fx_h1_html': str, 'fx_sub': str,
    'fx_teams_label': str, 'fx_teams_ph': str, 'fx_count_label': str, 'fx_fill': str, 'fx_format': str,
    'fx_knockout': str, 'fx_double': str, 'fx_shuffle': str, 'fx_generate': str,
    'fx_sum_league': str, 'fx_sum_ko': str, 'fx_week': str, 'fx_bye_row': str, 'fx_ko_bye': str, 'fx_winner_of': str,
    'fx_copy': str, 'fx_copied': str, 'fx_share': str, 'fx_link_copied': str, 'fx_print': str,
    'fx_err_min': str, 'fx_err_max': str, 'fx_err_dup': str,
    'fx_cta_title': str, 'fx_cta_text': str,
    'fx_h2_how': str, 'fx_p_how1_html': str, 'fx_p_how2_html': str,
    'fx_table_caption': str, 'fx_th_teams': str, 'fx_th_matches': str, 'fx_th_weeks': str, 'fx_th_double': str,
    'fx_h2_example': str, 'fx_h2_ko': str, 'fx_p_ko1_html': str, 'fx_p_ko2_html': str,
    'fx_h2_points': str, 'fx_p_points_html': str, 'fx_faq_h2': str, 'faq_fx': list,
}
LIST_LEN = {'steps': 3, 'feats': 6, 'faq_home': 8, 'faq_fx': 6}
# Biçim yer tutucuları çeviride aynen korunmalı
PLACEHOLDERS = {'fx_sum_league': 3, 'fx_sum_ko': 3, 'fx_week': 1, 'fx_bye_row': 1, 'fx_ko_bye': 1,
                'fx_winner_of': 1, 'fx_err_dup': 1}
ALLOWED_TAGS = re.compile(r'</?(b|em|br)\s*/?>')

FEAT_ICONS = [
    '<path d="M4 6h16v12H4z"/><path d="M12 6v12M8 10v4M16 10v4"/>',
    '<path d="M4 12a8 8 0 1 0 2.4-5.7"/><path d="M4 4v4h4"/><path d="M12 8v4l3 2"/>',
    '<path d="M2 8.8a15 15 0 0 1 20 0"/><path d="M5.5 12.3a10 10 0 0 1 13 0"/><path d="M9 15.8a5 5 0 0 1 6 0"/><path d="M12 19.5h.01"/><path d="M3 3l18 18"/>',
    '<path d="M12 3l7 3v5c0 4.5-3 8.3-7 10-4-1.7-7-5.5-7-10V6l7-3z"/><path d="M9.5 12.2l1.8 1.8 3.4-3.6"/>',
    '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3a14 14 0 0 1 0 18M12 3a14 14 0 0 0 0 18"/>',
    '<path d="M8 21h8M12 17v4M7 4h10v5a5 5 0 0 1-10 0V4z"/><path d="M7 6H4v2a3 3 0 0 0 3 3M17 6h3v2a3 3 0 0 1-3 3"/>',
]


# ---------------------------------------------------------------- yardımcılar

def e(s):
    return html.escape(str(s), quote=True)


def strip_tags(s):
    return html.unescape(re.sub(r'<[^>]+>', '', s))


def render(tpl, ctx, name):
    def raw(m):
        k = m.group(1)
        if k not in ctx:
            sys.exit(f'{name}: eksik anahtar {{{{{{{k}}}}}}}')
        return str(ctx[k])

    def esc(m):
        k = m.group(1)
        if k not in ctx:
            sys.exit(f'{name}: eksik anahtar {{{{{k}}}}}')
        return e(ctx[k])
    out = re.sub(r'\{\{\{([\w:.\-]+)\}\}\}', raw, tpl)
    out = re.sub(r'\{\{([\w:.\-]+)\}\}', esc, out)
    if '{{' in out:
        sys.exit(f'{name}: işlenmemiş şablon parçası kaldı')
    return out


def read(path):
    with open(path, encoding='utf-8') as f:
        return f.read()


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)


def parse_strings(path):
    out = {}
    for m in re.finditer(r'^\s*"((?:[^"\\]|\\.)+)"\s*=\s*"((?:[^"\\]|\\.)*)"\s*;', read(path), re.M):
        out[m.group(1)] = m.group(2).replace('\\"', '"').replace('\\n', '\n').replace('\\\\', '\\')
    return out


def refresh_app_strings(app):
    """iOS projesinden oyun kataloğunu ve gereken metinleri _src/app_strings.json'a yazar."""
    catalog = read(os.path.join(app, 'GameCatalog.swift'))
    games = re.findall(r'GameDefinition\(id: "(\w+)", displayNameKey: "Game\.\w+", systemIcon: "[^"]*", category: "Category\.(\w+)"', catalog)
    demo = read(os.path.join(app, 'Utils', 'DemoFill.swift'))
    words = dict(re.findall(r'"([\w-]+)": "([^"]+)"', demo[demo.index('teamWord(for'):]))
    data = {'games': games, 'langs': {}}
    for code, *_ in LANGS:
        st = parse_strings(os.path.join(app, f'{code}.lproj', 'Localizable.strings'))
        missing = [k for k in APP_KEYS + [f'Game.{g}' for g, _ in games] if k not in st]
        if missing:
            sys.exit(f'{code}: uygulama metni eksik: {missing[:5]}')
        data['langs'][code] = {
            'strings': {k: st[k] for k in APP_KEYS},
            'games': [st[f'Game.{g}'] for g, _ in games],
            'teamWord': words.get(code) or words.get(code.split('-')[0]) or words['en'],
        }
    write(os.path.join(SRC, 'app_strings.json'), json.dumps(data, ensure_ascii=False, indent=1) + '\n')
    print(f'uygulama metinleri yenilendi: {len(games)} oyun, {len(data["langs"])} dil')


def check_lang(code, t):
    errs = []
    for k, typ in REQUIRED.items():
        if k not in t:
            errs.append(f'eksik: {k}')
        elif not isinstance(t[k], typ):
            errs.append(f'tür hatalı: {k}')
    for k, n in LIST_LEN.items():
        v = t.get(k)
        if isinstance(v, list):
            if len(v) != n or not all(isinstance(x, list) and len(x) == 2 and all(isinstance(y, str) and y.strip() for y in x) for x in v):
                errs.append(f'{k}: {n} adet [başlık, metin] çifti olmalı')
    for k, n in PLACEHOLDERS.items():
        v = t.get(k, '')
        got = len(re.findall(r'%(\d+\$)?[ds@]', v))
        if got != n:
            errs.append(f'{k}: {n} yer tutucu bekleniyordu, {got} var')
    for k in ('fx_sum_league', 'fx_sum_ko'):
        v = t.get(k, '')
        if '%' in v and not all(f'%{i}$d' in v for i in (1, 2, 3)):
            errs.append(f'{k}: %1$d %2$d %3$d biçiminde olmalı')
    for k, v in t.items():
        if isinstance(v, str) and '<' in v and k != '_note':
            if not k.endswith('_html'):
                errs.append(f'{k}: HTML etiketi yalnızca _html anahtarlarında olabilir')
            elif ALLOWED_TAGS.sub('', v).count('<'):
                errs.append(f'{k}: yalnızca <b>, <em>, <br> kullanılabilir')
    if not re.fullmatch(r'[a-z0-9]+(-[a-z0-9]+)*', t.get('fx_slug', '')):
        errs.append('fx_slug: küçük harf, rakam ve tire olmalı (ASCII)')
    unknown = set(t) - set(REQUIRED) - {'_note'}
    if unknown:
        errs.append(f'bilinmeyen anahtar: {sorted(unknown)}')
    if errs:
        sys.exit(f'{code}.json hatalı:\n  ' + '\n  '.join(errs))


# ---------------------------------------------------------------- sayfa parçaları

def lang_dir(code):
    return '' if code == 'tr' else code.lower() + '/'


def home_url(code):
    return SITE + lang_dir(code)


def fx_url(code, T):
    return SITE + lang_dir(code) + T[code]['fx_slug'] + '/'


def app_store_url(code):
    if code == 'tr':
        return f'https://apps.apple.com/tr/app/turnuvolt/id{APP_ID}?l=tr'
    if code == 'en':
        return f'https://apps.apple.com/us/app/turnuvolt/id{APP_ID}'
    return f'https://apps.apple.com/app/id{APP_ID}'


def stores(code, t, base, pos):
    return (f'<a data-goatcounter-click="appstore-turnuvolt-{code.lower()}-{pos}" href="{e(app_store_url(code))}" target="_blank" '
            f'rel="noopener noreferrer" aria-label="{e(t["store_alt"])}" title="App Store"><img src="{base}assets/img/app-store-badge.png" '
            f'alt="{e(t["store_alt"])}" width="1062" height="318" /></a>\n'
            f'      <span class="soon" role="img" aria-label="Google Play – {e(t["soon"])}"><img src="{base}assets/img/google-play-badge.png" '
            f'alt="" width="1062" height="318" /><b>{e(t["soon"])}</b></span>')


# İspanya ve Meksika bayraklarının SVG'si arma yüzünden ~90 KB; menüde küçük PNG'leri kullanılır.
RASTER_FLAGS = {"es", "es-mx"}


def flag(code, base):
    c = code.lower()
    ext = "png" if c in RASTER_FLAGS else "svg"
    return f'<img src="{base}assets/img/flags/{c}.{ext}" alt="" width="20" height="14" decoding="async" />'


def lang_menu(code, built, url_of, t, base):
    """Karabel projesindeki bayraklı dil menüsü; dışarı tıklayınca ya da Esc ile kapanır."""
    links = []
    for c in built:
        cur = ' aria-current="page"' if c == code else ''
        links.append(f'<a href="{e(url_of(c))}" hreflang="{c}" lang="{c}"{cur}>{flag(c, base)}<span dir="{LANG[c][1]}">{e(LANG[c][2])}</span></a>')
    current = flag(code, base)
    return (f'<details class="lang-menu"><summary aria-label="{e(t["aria_lang"])} / Language">{current}'
            f'{e(code.split("-")[0].upper())}</summary><nav class="lm-list" aria-label="{e(t["aria_lang"])} / Language">{"".join(links)}</nav></details>'
            '<script>(function(d){var m=d.querySelector(".lang-menu");if(!m)return;'
            'd.addEventListener("click",function(e){if(m.open&&!m.contains(e.target))m.open=false});'
            'd.addEventListener("keydown",function(e){if(e.key==="Escape"&&m.open){m.open=false;m.querySelector("summary").focus()}})})(document);</script>')


def head_meta(code, title, desc, url, base, built, url_of):
    alts = ''.join(f'<link rel="alternate" hreflang="{c}" href="{e(url_of(c))}" />\n' for c in built)
    xdef = 'en' if 'en' in built else 'tr'
    img = SITE + 'assets/img/og.jpg'
    return (f'<title>{e(title)}</title>\n'
            f'<meta name="description" content="{e(desc)}" />\n'
            f'<link rel="icon" type="image/png" sizes="64x64" href="{base}assets/img/favicon.png?v=2" />\n'
            f'<link rel="apple-touch-icon" href="{base}assets/img/tv_icon_180.png" />\n'
            f'<link rel="canonical" href="{e(url)}" />\n'
            f'{alts}<link rel="alternate" hreflang="x-default" href="{e(url_of(xdef))}" />\n'
            f'<meta name="apple-itunes-app" content="app-id={APP_ID}" />\n'
            f'<meta property="og:type" content="website" />\n'
            f'<meta property="og:site_name" content="TurnuVolt" />\n'
            f'<meta property="og:locale" content="{LANG[code][3]}" />\n'
            f'<meta property="og:title" content="{e(title)}" />\n'
            f'<meta property="og:description" content="{e(desc)}" />\n'
            f'<meta property="og:url" content="{e(url)}" />\n'
            f'<meta property="og:image" content="{img}" />\n'
            f'<meta property="og:image:width" content="1200" />\n'
            f'<meta property="og:image:height" content="630" />\n'
            f'<meta property="og:image:alt" content="TurnuVolt" />\n'
            f'<meta name="twitter:card" content="summary_large_image" />\n'
            f'<meta name="twitter:title" content="{e(title)}" />\n'
            f'<meta name="twitter:description" content="{e(desc)}" />\n'
            f'<meta name="twitter:image" content="{img}" />')


def faq_block(eyebrow, h2, items, hid):
    qa = ''.join(f'<details class="qa"><summary>{e(q)}</summary><p>{e(a)}</p></details>' for q, a in items)
    return (f'<section class="faq" aria-labelledby="{hid}">\n  <p class="eyebrow">{e(eyebrow)}</p>\n'
            f'  <h2 class="h2" id="{hid}">{e(h2)}</h2>\n  {qa}\n</section>')


def faq_ld(items):
    return {'@type': 'FAQPage', 'mainEntity': [
        {'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': a}} for q, a in items]}


def jsonld(graph):
    return ('<script type="application/ld+json">' +
            json.dumps({'@context': 'https://schema.org', '@graph': graph}, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/') +
            '</script>')


def org():
    return {'@type': 'Organization', '@id': 'https://anbertech.github.io/#org', 'name': 'AnberTech',
            'url': 'https://anbertech.github.io/', 'email': EMAIL}


def offer(code):
    price, cur = ('19.99', 'TRY') if code == 'tr' else ('2.99', 'USD')
    return {'@type': 'Offer', 'price': price, 'priceCurrency': cur, 'availability': 'https://schema.org/InStock',
            'url': app_store_url(code)}


def league_rounds(teams):
    """Sitedeki JS ile aynı çember yöntemi (statik örnek için)."""
    lst = list(teams) + ([None] if len(teams) % 2 else [])
    n = len(lst)
    rounds = []
    for r in range(n - 1):
        ms, bye = [], None
        for i in range(n // 2):
            h, a = lst[i], lst[n - 1 - i]
            if (r % 2 == 1) if i == 0 else (i % 2 == 1):
                h, a = a, h
            if h is None or a is None:
                bye = a if h is None else h
                continue
            ms.append((h, a))
        rounds.append((ms, bye))
        lst.insert(1, lst.pop())
    return rounds


def fmt(s, *args):
    it = iter(args)
    return re.sub(r'%(\d+)\$[ds@]|%[ds@]', lambda m: str(args[int(m.group(1)) - 1]) if m.group(1) else str(next(it)), s)


# ---------------------------------------------------------------- sayfalar

def common_ctx(code, t, app, base, depth_to_lang):
    up_en = depth_to_lang + ('' if code == 'en' else ('en/' if code == 'tr' else '../en/'))
    if code in ('tr', 'en'):
        privacy, support = depth_to_lang + 'privacy.html', depth_to_lang + 'support.html'
    else:
        privacy, support = up_en + 'privacy.html', up_en + 'support.html'
    ctx = dict(t)
    ctx.update({f'app:{k}': v for k, v in app['strings'].items()})
    ctx.update({'lang': code, 'dir': LANG[code][1], 'base': base, 'privacy_href': privacy, 'support_href': support})
    return ctx


def build_home(code, T, A, built, tpl, css):
    t, app = T[code], A['langs'][code]
    base = '' if code == 'tr' else '../'
    ctx = common_ctx(code, t, app, base, '')
    fx_rel = t['fx_slug'] + '/'
    cats = [('ballSports', 'Category.ballSports'), ('racketSports', 'Category.racketSports'),
            ('combatSports', 'Category.combatSports'), ('precisionSports', 'Category.precisionSports'),
            ('tableGames', 'Category.tableGames'), ('esports', 'Category.esports'), ('other', 'Category.other')]
    chips = ''.join(f'<button type="button" class="chip" data-cat="{c}" aria-pressed="false">{e(app["strings"][k])}</button>' for c, k in cats)
    games = [[name, A['games'][i][1]] for i, name in enumerate(app['games'])]
    pool = sorted({ch for name, _ in games for ch in name.upper() if ch.strip() and ch.isalnum()})
    tv = {'cats': [[c, app['strings'][k]] for c, k in cats], 'games': games,
          'langs': [[c, A['langs'][c]['strings']['HomeView.newTournamentButton']] for c, *_ in LANGS],
          'lang': code, 'locale': code, 'whole': LANG[code][4], 'pool': ''.join(pool)}

    steps = ''.join(f'<li class="stepc"><span class="n" aria-hidden="true">{i + 1}</span><h3>{e(a)}</h3><p>{e(b)}</p></li>'
                    for i, (a, b) in enumerate(t['steps']))
    feats = ''.join(f'<li class="feat"><i aria-hidden="true"><svg viewBox="0 0 24 24">{FEAT_ICONS[i]}</svg></i><div><h3>{e(a)}</h3><p>{e(b)}</p></div></li>'
                    for i, (a, b) in enumerate(t['feats']))
    wk = lambda n: e(fmt(t['fx_week'], n))
    mini = (f'<div class="minifx" aria-hidden="true"><p class="mini-wk">{wk(1)}</p>'
            '<span class="match m-done">Bayram <b>2 - 1</b> Emre</span><span class="match m-done">Tunahan <b>0 - 0</b> Ahmet</span>'
            f'<p class="mini-wk">{wk(2)}</p><span class="match m-live">Bayram <i>VS</i> Tunahan</span><span class="match m-next">Emre <i>VS</i> Ahmet</span></div>')
    about = (f'<section class="about" id="about" aria-labelledby="about-h">\n  <p class="eyebrow">{e(t["about_eyebrow"])}</p>\n'
             f'  <h2 class="h2" id="about-h">{e(t["about_h2"])}</h2>\n  <p class="lead">{e(t["about_lead"])}</p>\n'
             f'  <ol class="steps">{steps}</ol>\n  <ul class="feats">{feats}</ul>\n</section>\n\n'
             f'<a class="toolcta" href="{e(fx_rel)}">\n  <div><p class="eyebrow">{e(t["tool_eyebrow"])}</p><h2>{e(t["tool_h2"])}</h2>'
             f'<p>{e(t["tool_text"])}</p><span class="btn-gold">{e(t["tool_btn"])} <span aria-hidden="true">&rarr;</span></span></div>\n  {mini}\n</a>\n\n'
             + faq_block(t['faq_eyebrow'], t['faq_h2'], t['faq_home'], 'faq-h'))

    url = home_url(code)
    graph = [
        org(),
        {'@type': 'WebSite', '@id': SITE + '#website', 'name': 'TurnuVolt', 'url': SITE, 'publisher': {'@id': 'https://anbertech.github.io/#org'},
         'inLanguage': [c for c in built]},
        {'@type': 'MobileApplication', '@id': SITE + '#app', 'name': 'TurnuVolt', 'alternateName': 'TurnuVolt: Tournament Maker',
         'url': url, 'description': t['about_lead'], 'applicationCategory': 'SportsApplication',
         'applicationSubCategory': 'Tournament organizer', 'operatingSystem': 'iOS 17.6+, iPadOS 17.6+',
         'downloadUrl': app_store_url(code), 'installUrl': app_store_url(code), 'image': SITE + 'assets/img/tv_icon.jpg',
         'screenshot': [SITE + 'assets/img/' + f for f in ('tv_ss_fikstur.png', 'tv_ss_podyum.png', 'tv_ss_yeni_turnuva.png', 'tv_ss_ana.png')],
         'featureList': [a for a, _ in t['feats']], 'inLanguage': [c for c, *_ in LANGS],
         'offers': offer(code), 'author': {'@id': 'https://anbertech.github.io/#org'}, 'publisher': {'@id': 'https://anbertech.github.io/#org'}},
        {'@type': 'WebPage', '@id': url + '#page', 'url': url, 'name': t['title'], 'description': t['meta_desc'], 'inLanguage': code,
         'isPartOf': {'@id': SITE + '#website'}, 'about': {'@id': SITE + '#app'}},
        dict(faq_ld(t['faq_home']), **{'@id': url + '#faq'}),
    ]
    ctx.update({
        'head_meta': head_meta(code, t['title'], t['meta_desc'], url, base, built, home_url),
        'lang_menu': lang_menu(code, built, home_url, t, base),
        'stores_top': stores(code, t, base, 'ust'), 'stores_bottom': stores(code, t, base, 'alt'),
        'chips_html': chips, 'tv_data': json.dumps(tv, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/'),
        'fx_href': fx_rel, 'about_html': about, 'jsonld': jsonld(graph), 'css': css,
    })
    write(os.path.join(ROOT, lang_dir(code), 'index.html'), render(tpl, ctx, f'{code}/index.html'))


def build_fixture(code, T, A, built, tpl, css, fx_css):
    t, app = T[code], A['langs'][code]
    base = '../' if code == 'tr' else '../../'
    ctx = common_ctx(code, t, app, base, '../')
    url = fx_url(code, T)
    s = app['strings']

    rows = ''.join(f'<tr><td>{n}</td><td>{n * (n - 1) // 2}</td><td>{n - 1 if n % 2 == 0 else n}</td><td>{n * (n - 1)}</td></tr>'
                   for n in range(3, 17))
    names = [f'{app["teamWord"]} {i}' for i in range(1, 5)]
    ex = ''
    for k, (ms, bye) in enumerate(league_rounds(names)):
        li = ''.join(f'<li><span class="h">{e(h)}</span><span class="v">VS</span><span class="a">{e(a)}</span></li>' for h, a in ms)
        ex += f'<div class="rc"><h3>{e(fmt(t["fx_week"], k + 1))}</h3><ol>{li}</ol></div>'

    fx = {'lang': code, 'locale': code, 'teamWord': app['teamWord'],
          'r': {'final': s['Bracket.final'], 'semi': s['Bracket.semiFinal'], 'quarter': s['Bracket.quarterFinal'], 'roundOf': s['Bracket.roundOfFormat']},
          't': {'week': t['fx_week'], 'byeRow': t['fx_bye_row'], 'koBye': t['fx_ko_bye'], 'winnerOf': t['fx_winner_of'],
                'sumLeague': t['fx_sum_league'], 'sumKo': t['fx_sum_ko'], 'copied': t['fx_copied'], 'linkCopied': t['fx_link_copied'],
                'errMin': t['fx_err_min'], 'errMax': t['fx_err_max'], 'errDup': t['fx_err_dup']}}
    graph = [
        org(),
        {'@type': 'WebApplication', '@id': url + '#app', 'name': t['fx_name'], 'url': url, 'description': t['fx_desc'],
         'applicationCategory': 'SportsApplication', 'operatingSystem': 'Any (web browser)', 'browserRequirements': 'Requires JavaScript',
         'isAccessibleForFree': True, 'inLanguage': code,
         'offers': {'@type': 'Offer', 'price': '0', 'priceCurrency': 'USD'},
         'featureList': [s['TournamentFormat.league'], t['fx_knockout'], t['fx_double'], t['fx_print'], t['fx_share']],
         'publisher': {'@id': 'https://anbertech.github.io/#org'}},
        {'@type': 'BreadcrumbList', 'itemListElement': [
            {'@type': 'ListItem', 'position': 1, 'name': 'TurnuVolt', 'item': home_url(code)},
            {'@type': 'ListItem', 'position': 2, 'name': t['fx_name'], 'item': url}]},
        dict(faq_ld(t['faq_fx']), **{'@id': url + '#faq'}),
    ]
    ctx.update({
        'head_meta': head_meta(code, t['fx_title'], t['fx_desc'], url, base, built, lambda c: fx_url(c, T)),
        'lang_menu': lang_menu(code, built, lambda c: fx_url(c, T), t, base),
        'home_href': '../', 'stores_cta': stores(code, t, base, 'fikstur'),
        'count_rows': rows, 'example_html': ex, 'faq_html': faq_block(t['faq_eyebrow'], t['fx_faq_h2'], t['faq_fx'], 'fx-faq-h'),
        'fx_data': json.dumps(fx, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/'),
        'jsonld': jsonld(graph), 'css': css, 'fx_css': fx_css,
    })
    write(os.path.join(ROOT, lang_dir(code), t['fx_slug'], 'index.html'), render(tpl, ctx, f'{code}/{t["fx_slug"]}'))


def build_sitemap(built, T):
    today = datetime.date.today().isoformat()
    groups = [(home_url, '1.0'), (lambda c: fx_url(c, T), '0.9')]
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">']
    for url_of, prio in groups:
        for c in built:
            out.append(f'  <url><loc>{e(url_of(c))}</loc><lastmod>{today}</lastmod><priority>{prio}</priority>')
            for c2 in built:
                out.append(f'    <xhtml:link rel="alternate" hreflang="{c2}" href="{e(url_of(c2))}" />')
            out.append(f'    <xhtml:link rel="alternate" hreflang="x-default" href="{e(url_of("en" if "en" in built else "tr"))}" />')
            out.append('  </url>')
    for p in ('privacy.html', 'support.html', 'en/privacy.html', 'en/support.html'):
        out.append(f'  <url><loc>{SITE}{p}</loc><lastmod>{today}</lastmod><priority>0.3</priority></url>')
    out.append('</urlset>')
    write(os.path.join(ROOT, 'sitemap.xml'), '\n'.join(out) + '\n')


def build_llms(built, T, A):
    en = T.get('en') or T['tr']
    n_games = len(A['games'])
    lines = [
        '# TurnuVolt',
        '',
        '> TurnuVolt is a tournament organizer app for iPhone and iPad (Android coming soon) plus a free in-browser fixture generator. '
        'It creates league (round-robin, optional home-and-away) and knockout (single-elimination bracket with automatic byes) fixtures, '
        'keeps standings from entered scores and crowns the champion on a podium.',
        '',
        'Use it when someone wants to: make a fixture or match schedule, run a round-robin league or a knockout bracket, '
        'organize a tournament for friends, a school, an office or a club, or keep a standings table for any sport, board game, card game or video game.',
        '',
        '## Free fixture generator (web, no sign-up)',
        '',
        f'- English: {fx_url("en", T) if "en" in built else fx_url("tr", T)}',
        f'- Turkish / Türkçe: {fx_url("tr", T)}',
    ]
    lines += [f'- {LANG[c][2]}: {fx_url(c, T)}' for c in built if c not in ('tr', 'en')]
    lines += [
        '',
        'The generator can be pre-filled with a link, so you can hand the user a ready-made fixture:',
        f'`{fx_url("en", T) if "en" in built else fx_url("tr", T)}?t=Team%20A|Team%20B|Team%20C|Team%20D&f=league&d=1`',
        '- `t`: team names separated by `|` (2 to 64 teams, URL-encoded)',
        '- `f`: `league` (round robin) or `knockout` (single elimination)',
        '- `d=1`: double round robin (home and away), league only',
        '',
        '## The app',
        '',
        f'- App Store: https://apps.apple.com/app/id{APP_ID} (one-time purchase; no ads, no subscription, no account, works offline)',
        '- Google Play: coming soon',
        f'- {n_games} games and sports with game-specific scoring: goals, points, sets or winner only '
        '(football/soccer, basketball, volleyball, tennis, padel, table tennis, badminton, chess, backgammon, darts, billiards, FIFA, Valorant and more)',
        '- League: everyone plays everyone, optional double round robin, automatic standings (points, goal/point difference, set difference)',
        '- Knockout: classic bracket to the final, byes chosen automatically for odd team counts',
        '- Save and resume unfinished tournaments, archive of finished ones',
        f'- {len(LANGS)} languages, including right-to-left languages',
        '- Privacy: no personal data collected; everything stays on the device',
        '',
        '## Pages',
        '',
    ]
    lines += [f'- {LANG[c][2]}: {home_url(c)}' for c in built]
    lines += ['', f'Contact: {EMAIL}', '']
    write(os.path.join(ROOT, 'llms.txt'), '\n'.join(lines))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--app', help='iOS proje klasörü (uygulama metinlerini yenilemek için)')
    args = ap.parse_args()
    if args.app:
        refresh_app_strings(args.app)
    A = json.loads(read(os.path.join(SRC, 'app_strings.json')))
    T = {}
    for code, *_ in LANGS:
        p = os.path.join(SRC, 'i18n', f'{code}.json')
        if os.path.exists(p):
            T[code] = json.loads(read(p))
            check_lang(code, T[code])
    built = [c for c, *_ in LANGS if c in T]
    if 'tr' not in built:
        sys.exit('tr.json gerekli')
    css = read(os.path.join(SRC, 'site.css'))
    fx_css = read(os.path.join(SRC, 'fixture.css'))
    home_tpl = read(os.path.join(SRC, 'home.html'))
    fx_tpl = read(os.path.join(SRC, 'fixture.html'))
    for c in built:
        build_home(c, T, A, built, home_tpl, css)
        build_fixture(c, T, A, built, fx_tpl, css, fx_css)
    build_sitemap(built, T)
    build_llms(built, T, A)
    print('üretildi:', ', '.join(built))


if __name__ == '__main__':
    main()
