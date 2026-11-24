#!/usr/bin/env python3
"""GTA VI Content Engine (EN)"""

import argparse, json, time, os
from datetime import datetime
from pathlib import Path
from openai import OpenAI

NICHE = {
    "gta6": {
        "persona": "A gamer with 12 years of GTA experience. Beat GTA V in 200 hours, played the GTA VI demo, and writes like they're talking to a mate at the pub. Not a journalist. A player who's been through it and is just telling you how it went.",
        "keywords_seed": [
            "GTA VI PC requirements: can it run on your PC",
            "GTA VI all hidden weapons and where to find them",
            "GTA VI map: secret locations and hidden caves",
            "GTA VI vs GTA V: what actually changed",
            "GTA VI how to farm money in the first 30 minutes",
            "GTA VI multiplayer: everything we know so far",
            "GTA VI Lucas and Claire: full story and character breakdown",
            "GTA VI all cheat codes PS5 Xbox PC",
            "GTA VI hidden outfits cars and bikes: complete list",
            "GTA VI how long to beat and what to do after",
            "GTA VI Leonida: how the new state works",
            "GTA VI main missions: order and spoiler-free guide",
            "GTA VI hardest side quests and how to beat them",
            "GTA VI Online: release date and what to expect",
            "GTA VI vs GTA V: which is the real masterpiece",
        ],
        "affiliate_keywords": [
            "PS5 DualSense controller", "Xbox Series X",
            "wireless gaming headset", "144Hz 27 inch monitor"
        ],
        "affiliate_tag": "gta6index-21"
    }
}

ARTICLE_PROMPT = """You are {persona}.

Write an English page that answers a specific question a player has about GTA VI. It's NOT a generic SEO article. It's an honest, direct answer with personality.

CONTENT RULES (NON-NEGOTIABLE):
- BEFORE writing, SEARCH THE WEB for the latest confirmed information on this topic. Use at least 2-3 searches to gather current facts, official announcements, and verified details. Base your article on what you find.
- ONLY talk about CONFIRMED facts: official trailers, Rockstar announcements, publicly shown gameplay, developer quotes in interviews.
- If something is NOT confirmed (PC specs, mission details, prices, unshown features), say it clearly: "Rockstar hasn't confirmed this yet" or "As of now we don't know, but based on GTA V you'd expect..."
- DO NOT invent: no specific money amounts, no exact weapon locations unless shown in a trailer, no hardware specs unless officially announced.
- You CAN have opinions: "Honestly, Rockstar nailed it this time, and here's why."
- You CAN show uncertainty: "I haven't seen it in action yet, but..."
- If the question is "PC requirements" and the game isn't out on PC yet, the title becomes "Will It Run on PC? What We Actually Know" and the content is honest.

STYLE RULES:
- Write how you'd text a friend. Short sentences. Sometimes one line. Sometimes two words: "It's insane."
- NO: "in this article", "in conclusion", "firstly", "it's important to note that", "it's worth mentioning that", "discover more"
- NO brochure language: "maximize your experience", "an unparalleled adventure"
- Use "you". Ask questions: "Ever wondered why..."
- Be opinionated. Be skeptical. Push back if a claim feels off.
- Vary structure: not always 5 sections. Sometimes 3. Sometimes one long and two short.
- If the topic is thin, the text is thin. 800 words is fine. Don't pad.
- Length: 800–2000 words. Less is better.
- NO emojis in the text.
- Paragraphs: max 4 lines. Sometimes one.

LINKS:
- Insert 1 Amazon affiliate link (tag: {affiliate_tag}) placed NATURALLY mid-article.
  Example: "for long sessions I stick with the DualSense, grab one [here](https://www.amazon.com/s?k=PS5+controller&tag={affiliate_tag})"
  Use amazon.com (US store), NOT amazon.it.
- Insert 1-2 internal links to other blog posts (format: /articles/slug.html).
- Use a table ONLY if it actually helps (comparison, spec list). Don't force it.

STRUCTURE:
- H1: the question or a natural title
- 2-3 sentence intro: the short answer, upfront
- Body: 3-7 sections, each hitting one aspect
- Closing: 1-2 lines. Optional link. NO "hope you found this helpful"
- End with: "Want more GTA VI intel before it drops? Grab the newsletter — no spam, just the good stuff."

OUTPUT — STRICT JSON only, no markdown fences:
{{
  "slug": "kebab-case-slug",
  "title": "Natural title, under 60 chars, not clickbait",
  "meta_description": "150-155 chars, keyword-rich, direct",
  "meta_keywords": ["3-5 keywords"],
  "content_html": "HTML body: h2, p, ul, table, a. NO html/body/head tags. No emojis.",
  "faq": [{{"q":"...","a":"..."}}],
  "affiliate_links": ["https://www.amazon.com/...?tag={affiliate_tag}"],
  "internal_links": ["/articles/..."],
  "reading_time_min": 5,
  "target_keyword": "..."
}}
"""


def generate_article(client, niche, keyword, existing_slugs):
    prompt = ARTICLE_PROMPT.format(
        persona=niche["persona"],
        affiliate_tag=niche["affiliate_tag"]
    )
    user_msg = (
        f"Target keyword: {keyword}\n\n"
        f"Other articles on this site (pick 1-2 for internal links):\n"
        + "\n".join(f"  - /articles/{s}.html" for s in list(existing_slugs)[:5])
        + "\n\nWrite the page. Remember: confirmed facts only. If you don't know, say so."
    )
    resp = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": user_msg},
        ],
        temperature=0.8,
        max_tokens=4500,
        tools=[{"type": "web_search"}],
    )
    raw = resp.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0]
    data = json.loads(raw)
    # Force Amazon US store (GPT sometimes defaults to .it)
    data["content_html"] = data["content_html"].replace("amazon.it", "amazon.com")
    if "affiliate_links" in data:
        data["affiliate_links"] = [link.replace("amazon.it", "amazon.com") for link in data["affiliate_links"]]
    return data


def render_html(data, domain):
    faq_html = ""
    for item in data.get("faq", []):
        faq_html += f"""
    <details style="margin:10px 0;padding:14px 16px;background:#f7f7fb;border-radius:8px">
      <summary style="cursor:pointer;font-weight:600">{item['q']}</summary>
      <p style="margin-top:10px;color:#444;line-height:1.7">{item['a']}</p>
    </details>"""

    # Build FAQ JSON-LD OUTSIDE the f-string (avoids brace conflict)
    faq_entities = [
        {"@type": "Question", "name": item["q"],
         "acceptedAnswer": {"@type": "Answer", "text": item["a"]}}
        for item in data.get("faq", [])
    ]
    faq_jsonld = '{"@context":"https://schema.org","@type":"FAQPage","mainEntity":' + json.dumps(faq_entities) + '}'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-9593748009949134" crossorigin="anonymous"></script>
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{data['title']}</title>
<meta name="description" content="{data['meta_description']}">
<meta name="keywords" content="{' ,'.join(data['meta_keywords'])}">
<link rel="canonical" href="https://{domain}/articles/{data['slug']}.html">
<meta property="og:title" content="{data['title']}">
<meta property="og:description" content="{data['meta_description']}">
<meta property="og:type" content="article">
<meta property="og:url" content="https://{domain}/articles/{data['slug']}.html">
<script type="application/ld+json">
{{"@context":"https://schema.org","@type":"Article","headline":"{data['title']}","description":"{data['meta_description']}","datePublished":"{datetime.now().isoformat()}","author":{{"@type":"Person","name":"GTA6 Index Team"}},"mainEntityOfPage":"https://{domain}/articles/{data['slug']}.html"}}
</script>
<script type="application/ld+json">
{faq_jsonld}
</script>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:system-ui,-apple-system,sans-serif;line-height:1.85;color:#1a1a2e;background:#fff}}
.wrap{{max-width:740px;margin:0 auto;padding:28px 20px 80px}}
h1{{font-size:2.1rem;line-height:1.2;margin-bottom:14px}}
h2{{font-size:1.35rem;margin:36px 0 12px;padding-bottom:8px;border-bottom:1px solid #eee}}
h3{{font-size:1.1rem;margin:24px 0 10px}}
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
    <strong style="font-size:1.2rem">GTA<span style="color:#e74c3c">6</span> Index</strong>
    <a href="/" style="font-size:.88rem">← Home</a>
  </div>
  <span class="badge">GTA VI GUIDE</span>
  <p class="meta">{datetime.now().strftime('%d %B %Y')} · {data['reading_time_min']} min read</p>
  <h1>{data['title']}</h1>
  <div class="ad-slot">Google AdSense</div>
  {data['content_html']}
  <h2>FAQ</h2>
  {faq_html}
  <div class="cta-box"><p><strong>Want more GTA VI intel before it drops?</strong><br><a href="/newsletter.html">Join the newsletter — no spam, just the good stuff →</a></p></div>
  <div class="ad-slot">AdSense — footer</div>
</div>
<footer>GTA6 Index · Not affiliated with Rockstar Games or Take-Two Interactive · © {datetime.now().year}</footer>
</div>
</body>
</html>"""


def generate_keywords(client, niche, done_keywords, count=15):
    done_list = "\n".join(sorted(done_keywords)) if done_keywords else "(none yet)"
    prompt = f"""Generate exactly {count} NEW search keyword ideas for a GTA VI content website.

ALREADY USED (do NOT repeat these):
{done_list}

RULES:
- Long-tail questions a player would Google (not generic "GTA VI news")
- Mix of: guides, comparisons, "what to expect", "how to", specs, tips
- English only
- One keyword per line, no numbering
- Must be DIFFERENT from the used list
- Focus on what will be searched in the NEXT few months (game is pre-release)
"""
    resp = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.9,
        max_tokens=500,
        tools=[{"type": "web_search"}],
    )
    raw = resp.choices[0].message.content.strip()
    keywords = [line.strip().lstrip("0123456789.-) ").strip() for line in raw.splitlines() if line.strip()]
    keywords = [k for k in keywords if k and k not in done_keywords][:count]
    return keywords


def main():
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if line.startswith("OPENAI_API_KEY="):
                os.environ["OPENAI_API_KEY"] = line.split("=", 1)[1]

    p = argparse.ArgumentParser()
    p.add_argument("--niche", default="gta6")
    p.add_argument("--count", type=int, default=5)
    p.add_argument("--output", default="./docs/articles")
    p.add_argument("--domain", default="gta6-index.com")
    args = p.parse_args()

    niche = NICHE[args.niche]
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)

    kw_file = out / ".keywords_done"
    done_keywords = set(kw_file.read_text().splitlines()) if kw_file.exists() else set()
    existing = set(f.stem for f in out.glob("*.html"))

    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

    done = 0

    print(f"\n🎮 Generating GTA VI articles (EN)...\n")

        # Generate new keywords if seed list is exhausted
    seed_available = [k for k in niche["keywords_seed"] if k not in done_keywords]
    if len(seed_available) >= args.count:
        target_keywords = seed_available[:args.count]
    else:
        print("  Generating new keywords via GPT...")
        new_kws = generate_keywords(client, niche, done_keywords, count=args.count)
        target_keywords = new_kws + seed_available
        target_keywords = target_keywords[:args.count]
        if not target_keywords:
            print("  No new keywords generated. Exiting.")
            return

    for kw in target_keywords:

        if kw in done_keywords:
            print(f"  ⏭  already done: {kw}")
            continue
        print(f"  ✍  {kw}")
        for attempt in range(2):
            try:
                data = generate_article(client, niche, kw, existing)
                html = render_html(data, args.domain)
                fp = out / f"{data['slug']}.html"
                fp.write_text(html, encoding="utf-8")
                existing.add(data["slug"])
                with open(kw_file, "a") as kf:
                    kf.write(kw + "\n")
                done += 1
                print(f"     ✓ {fp.name}")
                break
            except json.JSONDecodeError:
                if attempt == 0:
                    print("     retry...")
                    time.sleep(2)
                else:
                    print("     JSON parse failed")
            except Exception as e:
                print(f"     ERROR: {e}")
                break
        time.sleep(1)

    slugs = sorted(f.stem for f in out.glob("*.html"))
    sm = '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    sm += f'  <url><loc>https://{args.domain}/</loc><lastmod>{datetime.now():%Y-%m-%d}</lastmod></url>\n'
    sm += f'  <url><loc>https://{args.domain}/newsletter.html</loc><lastmod>{datetime.now():%Y-%m-%d}</lastmod></url>\n'
    for s in slugs:
        sm += f'  <url><loc>https://{args.domain}/articles/{s}.html</loc><lastmod>{datetime.now():%Y-%m-%d}</lastmod></url>\n'
    sm += '</urlset>'
    (out.parent / "sitemap.xml").write_text(sm)

    print(f"\nDONE: {done} new, {len(slugs)} total, sitemap updated\n")


if __name__ == "__main__":
    main()
