#!/usr/bin/env python3
"""GTA VI Content Engine"""

import argparse, json, time, os
from datetime import datetime
from pathlib import Path
from openai import OpenAI

NICHE = {
    "gta6": {
        "persona": "un gamer italiano con 12 anni di esperienza su GTA, ha completato GTA V in 200 ore, ha giocato ogni demo e beta di GTA VI, scrive come se parlasse a un amico al bar",
        "keywords_seed": [
            "GTA VI come farmare soldi nei primi 30 minuti",
            "GTA VI tutte le armi nascoste e dove trovarle",
            "GTA VI mappe: luoghi segreti e grotte nascoste",
            "GTA VI differenze con GTA V: cosa è cambiato davvero",
            "GTA VI requisiti PC: si gira sul tuo PC?",
            "GTA VI multiplayer: tutto quello che sappiamo",
            "GTA VI Lucas e Claire: storia e personalità completi",
            "GTA VI tutti i cheat e codici PS5 Xbox PC",
            "GTA VI vestiti auto e moto nascosti: lista completa",
            "GTA VI quanto tempo per finirlo e cosa fare dopo",
            "GTA VI Leonida: come funziona il nuovo stato",
            "GTA VI missioni principali: ordine e guida senza spoiler",
            "GTA VI side quest più difficili e come farle",
            "GTA VI online: quando esce e cosa aspettarsi",
            "GTA VI vs GTA V: qual è davvero il capolavoro",
        ],
        "affiliate_keywords": [
            "PS5 controller", "Xbox Series X",
            "headset gaming wireless", "monitor 144hz 27 pollici"
        ],
        "affiliate_tag": "iltuosito-21"
    }
}

ARTICLE_PROMPT = """Sei {persona}.

Scrivi una guida SEO in italiano per un blog di gaming. Regole:
- Lunghezza: 1500-2500 parole
- Tono: informale, competente. "Qui a Leonida c'è un nascondiglio con 500k"
- Struttura ESATTA:
  1. H1 = keyword
  2. Intro 3-4 righe: il problema del lettore
  3. 5-8 sezioni H2 con risposta diretta
  4. TABELLA dove ha senso
  5. "Errori che tutti fanno" (3-5 bullet)
  6. FAQ: 4 domande stile People Also Ask
  7. Chiusura 2 righe + link affiliazione
- Inserisci 1-2 link affiliazione Amazon (tag: {affiliate_tag})
- Inserisci 2 link interni (/articles/slug)
- NIENTE "in questo articolo approfondiremo"
- Paragrafi max 4 righe
- Cita dettagli di gioco reali (Leonida, Luigi's Place, Ocean View)

OUTPUT — SOLO JSON valido:
{{
  "slug": "kebab-case",
  "title": "H1",
  "meta_description": "max 155 char",
  "meta_keywords": ["3-5"],
  "content_html": "HTML: h2, p, ul, table, a. SENZA html/body",
  "faq": [{{"q":"...","a":"..."}}],
  "affiliate_links": ["https://..."],
  "internal_links": ["/articles/..."],
  "reading_time_min": 8,
  "target_keyword": "..."
}}
"""


def generate_article(client, niche, keyword, existing_slugs):
    prompt = ARTICLE_PROMPT.format(
        persona=niche["persona"],
        affiliate_tag=niche["affiliate_tag"]
    )
    user_msg = (
        f"Keyword target: {keyword}\n\n"
        f"Altri articoli (per link interni):\n"
        + "\n".join(f"  - /articles/{s}" for s in list(existing_slugs)[:5])
        + "\n\nScrivi la guida."
    )
    resp = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": user_msg},
        ],
        temperature=0.75,
        max_tokens=4500,
    )
    raw = resp.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0]
    return json.loads(raw)


def render_html(data, domain):
    faq = ""
    for item in data.get("faq", []):
        faq += f"""
    <details style="margin:10px 0;padding:14px 16px;background:#f7f7fb;border-radius:8px">
      <summary style="cursor:pointer;font-weight:600">{item['q']}</summary>
      <p style="margin-top:10px;color:#444;line-height:1.7">{item['a']}</p>
    </details>"""

    return f"""<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{data['title']}</title>
<meta name="description" content="{data['meta_description']}">
<meta name="keywords" content="{' ,'.join(data['meta_keywords'])}">
<link rel="canonical" href="https://{domain}/articles/{data['slug']}">
<meta property="og:title" content="{data['title']}">
<meta property="og:description" content="{data['meta_description']}">
<script type="application/ld+json">
{{"@context":"https://schema.org","@type":"Article","headline":"{data['title']}","datePublished":"{datetime.now().isoformat()}","author":{{"@type":"Person","name":"Redazione GTA6 Guide"}},"mainEntityOfPage":"https://{domain}/articles/{data['slug']}"}}
</script>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:system-ui,sans-serif;line-height:1.85;color:#1a1a2e;background:#fff}}
.wrap{{max-width:740px;margin:0 auto;padding:28px 20px 80px}}
h1{{font-size:2.1rem;line-height:1.2;margin-bottom:14px}}
h2{{font-size:1.35rem;margin:36px 0 12px;padding-bottom:8px;border-bottom:1px solid #eee}}
p{{margin:0 0 16px;font-size:1.02rem}}
ul,ol{{margin:0 0 16px 22px}}
li{{margin:5px 0}}
table{{width:100%;border-collapse:collapse;margin:18px 0;font-size:.93rem}}
th,td{{padding:10px 12px;border:1px solid #e0e0e0;text-align:left}}
th{{background:#f4f4f8;font-weight:700}}
.meta{{color:#888;font-size:.87rem;margin-bottom:20px}}
.ad-slot{{margin:28px 0;padding:18px;background:#f9f9fc;border:1px dashed #ccc;border-radius:8px;text-align:center;color:#aaa;font-size:.82rem;min-height:90px;display:flex;align-items:center;justify-content:center}}
.cta-box{{margin:36px 0;padding:24px 28px;background:linear-gradient(135deg,#1a1a2e,#2d2d5e);border-radius:12px;color:#fff}}
.cta-box a{{color:#fff;font-weight:600}}
a{{color:#e74c3c;text-decoration:none}}
a:hover{{text-decoration:underline}}
.badge{{display:inline-block;background:#e74c3c11;color:#e74c3c;padding:2px 10px;border-radius:99px;font-size:.78rem;font-weight:700;margin-bottom:12px}}
footer{{text-align:center;padding:30px 20px;color:#aaa;font-size:.8rem;border-top:1px solid #eee;margin-top:40px}}
@media(max-width:600px){{h1{{font-size:1.5rem}}.wrap{{padding:20px 16px 60px}}}}
</style>
</head>
<body>
<div class="wrap">
  <div style="display:flex;justify-content:space-between;align-items:center;padding-bottom:16px;border-bottom:2px solid #1a1a2e;margin-bottom:24px">
    <strong style="font-size:1.2rem">GTA<span style="color:#e74c3c">6</span> Guide</strong>
    <a href="/" style="font-size:.88rem">← Home</a>
  </div>
  <span class="badge">GUIDA GTA VI</span>
  <p class="meta">📅 {datetime.now().strftime('%d %B %Y')} · ⏱ {data['reading_time_min']} min</p>
  <h1>{data['title']}</h1>
  <div class="ad-slot">Google AdSense — inserisci qui il tuo codice</div>
  {data['content_html']}
  <h2>FAQ</h2>
  {faq}
  <div class="cta-box"><p><strong>Vuoi le prossime guide prima che escano?</strong><br><a href="/newsletter">Iscriviti alla newsletter →</a></p></div>
  <div class="ad-slot">AdSense — footer</div>
</div>
<footer>GTA VI Guide · Non affiliato a Rockstar Games · © {datetime.now().year}</footer>
</div>
</body>
</html>"""


def main():
    # Leggi la key dal .env
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if line.startswith("OPENAI_API_KEY="):
                os.environ["OPENAI_API_KEY"] = line.split("=", 1)[1]

    p = argparse.ArgumentParser()
    p.add_argument("--niche", default="gta6")
    p.add_argument("--count", type=int, default=5)
    p.add_argument("--output", default="./public/articles")
    p.add_argument("--domain", default="gta6-index.com")
    args = p.parse_args()

    niche = NICHE[args.niche]
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)

    existing = set(f.stem for f in out.glob("*.html"))
        client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])  
    client = OpenAI(api_key=api_key)


    done = 0

    print(f"\n🎮 Generando articoli GTA VI…\n")

    for kw in niche["keywords_seed"][:args.count]:
        if kw.replace(" ", "-").lower() in existing:
            print(f"  ⏭  già presente: {kw}")
            continue
        print(f"  ✍  {kw}")
        for attempt in range(2):
            try:
                data = generate_article(client, niche, kw, existing)
                html = render_html(data, args.domain)
                fp = out / f"{data['slug']}.html"
                fp.write_text(html, encoding="utf-8")
                existing.add(data["slug"])
                done += 1
                print(f"     ✓ {fp.name}")
                break
            except json.JSONDecodeError:
                if attempt == 0:
                    print("     retry…")
                    time.sleep(2)
                else:
                    print("     JSON fallito")
            except Exception as e:
                print(f"     ERRORE: {e}")
                break
        time.sleep(1)

    slugs = sorted(f.stem for f in out.glob("*.html"))
    sm = '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    sm += f'  <url><loc>https://{args.domain}/</loc><lastmod>{datetime.now():%Y-%m-%d}</lastmod></url>\n'
    for s in slugs:
        sm += f'  <url><loc>https://{args.domain}/articles/{s}.html</loc><lastmod>{datetime.now():%Y-%m-%d}</lastmod></url>\n'
    sm += '</urlset>'
    (out.parent / "sitemap.xml").write_text(sm)

    print(f"\nFATTO: {done} nuovi, {len(slugs)} totali, sitemap OK\n")


if __name__ == "__main__":
    main()

