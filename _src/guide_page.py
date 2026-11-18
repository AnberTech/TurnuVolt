"""Rehber sayfası üretici (WeddingInvite ve NobetFormal ortak; iki depoda aynı dosya, değişiklik ikisine de uygulanmalı).

Bir rehber: başlık + giriş, 5 bölüm, 4 adım (HowTo), 5 SSS (FAQPage), canlı ürüne çağrı, diğer rehberler, dil menüsü.
Metinler: _src/guides/<dil>.json (anahtarlar: <x>_slug/_name/_title/_desc/_h1/_lead/_card/_body/_steps/_faq + g_*).
"""
import html
import json
import re

TOPIC_KEYS = ('slug', 'name', 'title', 'desc', 'h1', 'lead', 'card', 'body', 'steps', 'faq')
LIST_LEN = {'body': 5, 'steps': 4, 'faq': 5}
COMMON = ('g_steps_h2', 'g_faq_h2', 'g_cta_h2', 'g_cta_p', 'g_cta_btn', 'g_contact', 'g_other_h2', 'g_lang', 'g_home')
LIMITS = {'title': 60, 'desc': 155, 'name': 32, 'card': 90}
B_TAG = re.compile(r'</?b>')


def e(s):
    return html.escape(str(s), quote=True)


def check(code, t, ref, topics):
    """Hata listesi döndürür (boşsa geçerli)."""
    errs = []
    need = {f'{x}_{k}' for x in topics for k in TOPIC_KEYS} | set(COMMON)
    if set(t) != need:
        errs.append(f'eksik {sorted(need - set(t))} fazla {sorted(set(t) - need)}')
        return errs
    for x in topics:
        if not re.fullmatch(r'[a-z0-9]+(-[a-z0-9]+)*', t[f'{x}_slug']):
            errs.append(f'{x}_slug: ASCII küçük harf/rakam/tire olmalı')
        for k, n in LIMITS.items():
            if len(t[f'{x}_{k}']) > n:
                errs.append(f'{x}_{k}: {len(t[f"{x}_{k}"])} > {n}')
        for k, n in LIST_LEN.items():
            v = t[f'{x}_{k}']
            if not (isinstance(v, list) and len(v) == n and all(isinstance(p, list) and len(p) == 2 and all(isinstance(s, str) and s.strip() for s in p) for p in v)):
                errs.append(f'{x}_{k}: {n} adet [başlık, metin] olmalı')
                continue
            for h, p in v:
                rest = B_TAG.sub('', p) if k == 'body' else p
                if '<' in h or '<' in rest or '>' in rest:
                    errs.append(f'{x}_{k}: yalnız body paragraflarında <b> kullanılabilir')
                    break
        if ref is not None and code != 'tr':
            for i, ((_, p), (_, rp)) in enumerate(zip(t[f'{x}_body'], ref[f'{x}_body'])):
                if len(B_TAG.findall(p)) % 2:
                    errs.append(f'{x}_body[{i}]: <b> kapanmamış')
    if len({t[f'{x}_slug'] for x in topics}) != len(topics):
        errs.append('slug çakışması')
    return errs


def plain_len(t, x):
    parts = [t[f'{x}_lead']] + [h + ' ' + B_TAG.sub('', p) for h, p in t[f'{x}_body']] + [a + ' ' + b for a, b in t[f'{x}_steps'] + t[f'{x}_faq']]
    return len(' '.join(parts))


CSS = '''*{box-sizing:border-box}html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--ink);font:400 17px/1.65 var(--f-text);-webkit-font-smoothing:antialiased}
a{color:var(--acc)}
.top{display:flex;align-items:center;justify-content:space-between;gap:12px;max-width:780px;margin:0 auto;padding:16px 20px}
.brand{font:600 18px/1 var(--f-head);color:var(--ink);text-decoration:none;letter-spacing:.01em}
.lm summary{cursor:pointer;list-style:none;font:500 13px/1 var(--f-ui);padding:8px 12px;border:1px solid var(--line);border-radius:999px;background:var(--card)}
.lm summary::-webkit-details-marker{display:none}
.lm{position:relative}.lm nav{position:absolute;z-index:5;inset-inline-end:0;top:calc(100% + 6px);display:grid;grid-template-columns:1fr 1fr;gap:2px;
  padding:8px;min-width:240px;background:var(--card);border:1px solid var(--line);border-radius:14px;box-shadow:0 12px 30px -12px rgba(0,0,0,.25)}
.lm nav a{padding:6px 8px;border-radius:8px;text-decoration:none;color:var(--ink);font:400 14px/1.3 var(--f-ui)}
.lm nav a[aria-current]{background:var(--soft);font-weight:600}
main{max-width:780px;margin:0 auto;padding:8px 20px 40px}
.crumbs{font:400 13px/1.4 var(--f-ui);color:var(--muted);margin:8px 0 0}.crumbs a{color:var(--muted)}
h1{font:600 clamp(30px,6vw,44px)/1.12 var(--f-head);margin:10px 0 12px;letter-spacing:-.01em}
.lead{font-size:19px;color:var(--muted);margin:0 0 26px}
h2{font:600 clamp(22px,4.4vw,27px)/1.22 var(--f-head);margin:34px 0 10px}
.content p{margin:0 0 6px}
.box{margin-top:34px;padding:22px 20px;border-radius:18px;background:var(--card);border:1px solid var(--line)}
.box h2{margin-top:0}
.steps{display:grid;gap:12px;counter-reset:s}
.step{display:grid;grid-template-columns:34px 1fr;gap:4px 12px;counter-increment:s}
.step::before{content:counter(s);grid-row:span 2;width:34px;height:34px;border-radius:50%;display:grid;place-items:center;background:var(--acc);color:#fff;font:600 15px/1 var(--f-ui)}
.step b{font:600 17px/1.35 var(--f-text)}.step span{color:var(--muted)}
.faq details{border-top:1px solid var(--line);padding:12px 0}.faq details:last-child{border-bottom:1px solid var(--line)}
.faq summary{cursor:pointer;font-weight:600}.faq details p{margin:8px 0 0;color:var(--muted)}
.cta{text-align:center}.cta p{color:var(--muted);margin:0 0 16px}
.btn{display:inline-block;padding:13px 24px;border-radius:999px;background:var(--acc);color:#fff;text-decoration:none;font:600 15px/1 var(--f-ui)}
.contact{margin-top:14px;font:400 14px/1.4 var(--f-ui);color:var(--muted)}
.topics{display:grid;gap:12px}
.tcard{display:block;padding:16px 18px;border-radius:14px;border:1px solid var(--line);background:var(--card);text-decoration:none;color:var(--ink)}
.tcard b{display:block;font:600 17px/1.3 var(--f-head)}.tcard span{color:var(--muted);font-size:15px}
footer{max-width:780px;margin:0 auto;padding:20px 20px 40px;font:400 13px/1.5 var(--f-ui);color:var(--muted)}
@media (min-width:640px){.topics{grid-template-columns:1fr 1fr}}
[dir=rtl] .step{direction:rtl}
h1,h2{text-wrap:balance}
html[lang=ko] body{word-break:keep-all;overflow-wrap:anywhere}
html[lang=ja] body{line-break:strict}
html[lang=ja] :is(h1,h2),html[lang^=zh] :is(h1,h2),html[lang=th] :is(h1,h2){text-wrap:wrap}'''


def render(*, code, dirn, og_locale, lang_names, built, x, t, topics, url_of, home_url, cta_url, brand, site_name, org,
           email, theme_css, analytics='', extra_head='', icon=''):
    """Bir rehber sayfasının tam HTML'i. url_of(code, x) -> mutlak adres; home_url(code) -> sitenin o dildeki ana sayfası."""
    u = url_of(code, x)
    alts = ''.join(f'<link rel="alternate" hreflang="{c}" href="{url_of(c, x)}">\n' for c in built)
    xdef = url_of('en' if 'en' in built else built[0], x)
    menu = ''
    if len(built) > 1:
        links = ''.join(f'<a href="{url_of(c, x)}" hreflang="{c}" lang="{c}"{" aria-current=" + chr(34) + "page" + chr(34) if c == code else ""}>'
                        f'{e(lang_names[c])}</a>' for c in built)
        menu = f'<details class="lm"><summary aria-label="{e(t["g_lang"])}">{e(code.split("-")[0].upper())} ▾</summary><nav>{links}</nav></details>'
    body = ''.join(f'<h2>{e(h)}</h2><p>{p}</p>' for h, p in t[f'{x}_body'])
    steps = ''.join(f'<div class="step"><b>{e(h)}</b><span>{e(p)}</span></div>' for h, p in t[f'{x}_steps'])
    faq = ''.join(f'<details><summary>{e(q)}</summary><p>{e(a)}</p></details>' for q, a in t[f'{x}_faq'])
    others = ''.join(f'<a class="tcard" href="{url_of(code, y)}"><b>{e(t[f"{y}_name"])}</b><span>{e(t[f"{y}_card"])}</span></a>' for y in topics if y != x)
    graph = [org,
             {'@type': 'WebPage', '@id': u + '#page', 'url': u, 'name': t[f'{x}_title'], 'description': t[f'{x}_desc'], 'inLanguage': code,
              'publisher': {'@id': org['@id']},
              'mainEntity': {'@type': 'HowTo', 'name': t[f'{x}_h1'],
                             'step': [{'@type': 'HowToStep', 'position': i + 1, 'name': h, 'text': p} for i, (h, p) in enumerate(t[f'{x}_steps'])]}},
             {'@type': 'BreadcrumbList', 'itemListElement': [
                 {'@type': 'ListItem', 'position': 1, 'name': site_name, 'item': home_url(code)},
                 {'@type': 'ListItem', 'position': 2, 'name': t[f'{x}_name'], 'item': u}]},
             {'@type': 'FAQPage', '@id': u + '#faq', 'inLanguage': code, 'mainEntity': [
                 {'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': a}} for q, a in t[f'{x}_faq']]}]
    ld = json.dumps({'@context': 'https://schema.org', '@graph': graph}, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
    return f'''<!doctype html>
<html lang="{code}" dir="{dirn}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(t[f"{x}_title"])}</title>
<meta name="description" content="{e(t[f"{x}_desc"])}">
<link rel="canonical" href="{u}">
{alts}<link rel="alternate" hreflang="x-default" href="{xdef}">
<meta property="og:type" content="article">
<meta property="og:site_name" content="{e(site_name)}">
<meta property="og:url" content="{u}">
<meta property="og:locale" content="{og_locale}">
<meta property="og:title" content="{e(t[f"{x}_title"])}">
<meta property="og:description" content="{e(t[f"{x}_desc"])}">
<meta name="twitter:card" content="summary">
{f'<link rel="icon" href="{icon}">' + chr(10) if icon else ''}{extra_head}<style>{theme_css}
{CSS}</style>
{analytics}<script type="application/ld+json">{ld}</script>
</head>
<body>
<header class="top"><a class="brand" href="{home_url(code)}">{brand}</a>{menu}</header>
<main>
<p class="crumbs"><a href="{home_url(code)}">{e(t["g_home"])}</a> <span aria-hidden="true">›</span> {e(t[f"{x}_name"])}</p>
<h1>{e(t[f"{x}_h1"])}</h1>
<p class="lead">{e(t[f"{x}_lead"])}</p>
<article class="content">{body}</article>
<section class="box"><h2>{e(t["g_steps_h2"])}</h2><div class="steps">{steps}</div></section>
<section class="faq"><h2>{e(t["g_faq_h2"])}</h2>{faq}</section>
<section class="box cta"><h2>{e(t["g_cta_h2"])}</h2><p>{e(t["g_cta_p"])}</p><a class="btn" href="{cta_url}">{e(t["g_cta_btn"])}</a>
<p class="contact">{e(t["g_contact"])} <a href="mailto:{email}">{email}</a></p></section>
<section><h2>{e(t["g_other_h2"])}</h2><div class="topics">{others}</div></section>
</main>
<footer>© 2026 {e(site_name)} · <a href="https://anbertech.github.io/">AnberTech</a></footer>
</body>
</html>
'''
