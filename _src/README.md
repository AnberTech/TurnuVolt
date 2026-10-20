# Site kaynağı

Ana sayfalar (`index.html`, `<dil>/index.html`) ve fikstür oluşturucu sayfaları (`fikstur/`, `<dil>/<slug>/`) bu klasördeki şablonlardan üretilir. **Üretilen HTML dosyalarını elle düzenleme**; değişikliği burada yap, sonra scripti çalıştır.

```
python3 _src/build.py
```

iOS uygulamasındaki oyun adları ya da çeviriler değiştiyse önce uygulama metinlerini yenile:

```
python3 _src/build.py --app ~/Encephala/TurnuVolt_Local/4.2_ios
```

## Dosyalar

| Dosya | Ne işe yarar |
|---|---|
| `home.html` | Ana sayfa şablonu |
| `fixture.html` | Fikstür oluşturucu şablonu (lig ve eleme hesabı bu dosyadaki JS'te) |
| `site.css`, `fixture.css` | Ortak stil ve fikstür sayfası stili (sayfalara gömülür) |
| `i18n/<dil>.json` | Sayfa metinleri. Hangi dilin dosyası varsa o dil üretilir. Ana dil `tr.json` |
| `app_strings.json` | Uygulamadan alınan metinler: oyun adları, kategoriler, tablo başlıkları, tur adları |
| `og.html` | Paylaşım görseli `assets/img/og.jpg` için kaynak |

Script ayrıca `sitemap.xml` ve `llms.txt` dosyalarını üretir. Dil dosyasında eksik anahtar, bozuk yer tutucu (`%d`, `%1$d`, `%s`) ya da izin verilmeyen HTML varsa hata verip durur.

## Çeviri kuralları

- `_html` ile biten anahtarlarda yalnızca `<b>`, `<em>`, `<br>` kullanılır; diğerleri düz metindir.
- `fx_slug`: fikstür sayfasının adresi; küçük harf, rakam ve tire (ASCII).
- `steps` 3, `feats` 6, `faq_home` 8, `faq_fx` 6 adet `[başlık, metin]` çiftidir.
- Fiyat yapılandırılmış veride sabit: TR sayfası 19,99 TRY, diğerleri 2,99 USD. App Store fiyatı değişirse `build.py` içindeki `offer()` güncellenmeli.

## Paylaşım görseli

```
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --hide-scrollbars \
  --window-size=1200,630 --virtual-time-budget=4000 --screenshot=/tmp/og.png "file://$PWD/_src/og.html"
sips -s format jpeg -s formatOptions 86 /tmp/og.png --out assets/img/og.jpg
```

## Fikstür bağlantısı

Fikstür sayfası adresle doldurulabilir: `?t=A|B|C|D&f=league&d=1`
(`t` takımlar, `f` = `league` ya da `knockout`, `d=1` rövanşlı). Bu biçim `llms.txt` içinde yapay zekâ asistanlarına da anlatılıyor.
