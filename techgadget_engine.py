#!/usr/bin/env python3
"""
TechGadgetHQ Content Engine
Groq-powered affiliate content generator
GitHub Actions cron: runs daily, generates product review posts
Amazon tag: prepared75-20
"""

import os
import json
import re
import random
from datetime import datetime, date
from pathlib import Path
from groq import Groq

# ── CONFIG ────────────────────────────────────────────────────────────────────
AMAZON_TAG = "prepared75-20"
SITE_URL   = "https://techgadgethq.online"
SITE_NAME  = "TechGadgetHQ"
OUTPUT_DIR = Path("blog")
CAT_DIR    = Path("categories")
client     = Groq(api_key=os.environ["GROQ_API_KEY"])

CATEGORIES = {
    "smart-home":    {"label": "Smart Home",   "emoji": "🏠", "color": "#00d4ff"},
    "edc":           {"label": "EDC Gear",     "emoji": "🔦", "color": "#ff6b35"},
    "outdoor-tech":  {"label": "Outdoor Tech", "emoji": "🌲", "color": "#00ff88"},
    "survival-tech": {"label": "Survival Tech","emoji": "⚡", "color": "#ffd700"},
    "audio-video":   {"label": "Audio & Video","emoji": "🎧", "color": "#bf5fff"},
}

PRODUCT_SEEDS = {
    "smart-home": [
        "smart home hub", "video doorbell", "smart thermostat",
        "smart lock", "robot vacuum", "smart light bulbs",
        "home security camera", "smart plug", "mesh wifi router",
    ],
    "edc": [
        "tactical flashlight", "multi-tool", "EDC knife",
        "everyday carry bag", "paracord bracelet", "portable charger",
        "titanium pen", "minimalist wallet", "keychain tool",
    ],
    "outdoor-tech": [
        "GPS watch", "solar charger", "satellite communicator",
        "action camera", "trail camera", "rangefinder",
        "weather station", "headlamp", "portable weather radio",
    ],
    "survival-tech": [
        "emergency power station", "water purification device",
        "fire starter kit", "emergency radio", "solar generator",
        "hand crank radio", "survival knife", "emergency beacon",
    ],
    "audio-video": [
        "wireless earbuds", "bone conduction headphones",
        "bluetooth speaker", "dash cam", "body camera",
        "night vision monocular", "thermal monocular",
    ],
}

# ── GROQ CALL ────────────────────────────────────────────────────────────────
def groq_call(prompt: str, max_tokens: int = 1200) -> str:
    resp = client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
        temperature=0.75,
    )
    return resp.choices[0].message.content.strip()

# ── SLUG HELPER ───────────────────────────────────────────────────────────────
def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    return text.strip("-")

# ── GENERATE POST ─────────────────────────────────────────────────────────────
def generate_post(category: str, product_topic: str) -> dict:
    today = date.today().strftime("%B %d, %Y")
    cat_info = CATEGORIES[category]

    meta_prompt = f"""
You are a tech gadget reviewer for {SITE_NAME}. Generate a JSON object for a product review post.
Topic: Best {product_topic} in 2025
Category: {cat_info['label']}
Amazon affiliate tag: {AMAZON_TAG}

Return ONLY valid JSON with these exact keys:
{{
  "title": "SEO-optimized review title (60 chars max)",
  "meta_description": "compelling meta description 150 chars max",
  "excerpt": "2-sentence preview for listing pages",
  "intro": "2-paragraph intro (no markdown, plain text)",
  "top_picks": [
    {{"rank": 1, "name": "Product Name", "price": "$XX", "rating": "4.8/5", "pros": ["pro1","pro2","pro3"], "cons": ["con1"], "verdict": "1-sentence verdict", "amazon_search": "exact amazon search query"}},
    {{"rank": 2, "name": "Product Name", "price": "$XX", "rating": "4.5/5", "pros": ["pro1","pro2"], "cons": ["con1","con2"], "verdict": "1-sentence verdict", "amazon_search": "exact amazon search query"}},
    {{"rank": 3, "name": "Product Name", "price": "$XX", "rating": "4.3/5", "pros": ["pro1","pro2"], "cons": ["con1"], "verdict": "1-sentence verdict", "amazon_search": "exact amazon search query"}}
  ],
  "buying_guide": "3-paragraph buying guide covering what to look for",
  "faq": [
    {{"q": "question", "a": "answer"}},
    {{"q": "question", "a": "answer"}}
  ]
}}
Return only the JSON object, no other text.
"""
    raw = groq_call(meta_prompt, max_tokens=1400)
    # strip possible markdown fences
    raw = re.sub(r"^```json\s*|```\s*$", "", raw.strip())
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        # fallback minimal
        data = {
            "title": f"Best {product_topic.title()} in 2025",
            "meta_description": f"Expert review of the best {product_topic} available in 2025.",
            "excerpt": f"We tested the top {product_topic} options so you can buy with confidence.",
            "intro": f"Finding the right {product_topic} takes research. We've done it for you.",
            "top_picks": [],
            "buying_guide": f"When shopping for a {product_topic}, consider quality, price, and reviews.",
            "faq": [],
        }
    data["category"] = category
    data["product_topic"] = product_topic
    data["date"] = today
    return data

# ── RENDER HTML ───────────────────────────────────────────────────────────────
def render_post_html(post: dict) -> str:
    cat_info   = CATEGORIES[post["category"]]
    slug       = slugify(post["title"])
    picks_html = ""

    for p in post.get("top_picks", []):
        pros_html = "".join(f"<li>{x}</li>" for x in p.get("pros", []))
        cons_html = "".join(f"<li>{x}</li>" for x in p.get("cons", []))
        search_q  = p.get("amazon_search", p.get("name", "")).replace(" ", "+")
        aff_url   = f"https://www.amazon.com/s?k={search_q}&tag={AMAZON_TAG}"
        picks_html += f"""
<div class="pick-card" id="pick-{p['rank']}">
  <div class="pick-header">
    <span class="pick-rank">#{p['rank']}</span>
    <div>
      <h3 class="pick-name">{p.get('name','')}</h3>
      <div class="pick-meta">
        <span class="pick-price">{p.get('price','')}</span>
        <span class="pick-rating">★ {p.get('rating','')}</span>
      </div>
    </div>
  </div>
  <div class="pick-grid">
    <div>
      <h4>Pros</h4>
      <ul class="pros-list">{pros_html}</ul>
    </div>
    <div>
      <h4>Cons</h4>
      <ul class="cons-list">{cons_html}</ul>
    </div>
  </div>
  <p class="pick-verdict">✓ {p.get('verdict','')}</p>
  <a href="{aff_url}" class="btn-amazon" target="_blank" rel="nofollow noopener">
    Check Price on Amazon →
  </a>
</div>
"""

    faq_html = ""
    for faq in post.get("faq", []):
        faq_html += f"""
<div class="faq-item">
  <h4 class="faq-q">{faq.get('q','')}</h4>
  <p class="faq-a">{faq.get('a','')}</p>
</div>
"""

    schema = json.dumps({
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": post["title"],
        "description": post.get("meta_description",""),
        "datePublished": date.today().isoformat(),
        "author": {"@type": "Organization", "name": SITE_NAME},
        "publisher": {"@type": "Organization", "name": SITE_NAME, "url": SITE_URL},
    }, indent=2)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{post['title']} | {SITE_NAME}</title>
<meta name="description" content="{post.get('meta_description','')}">
<link rel="canonical" href="{SITE_URL}/blog/{slug}.html">
<link rel="alternate" type="application/rss+xml" href="{SITE_URL}/feed.xml">
<script type="application/ld+json">{schema}</script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Barlow:wght@300;400;600;800&display=swap" rel="stylesheet">
<style>
:root {{
  --bg:#0a0a0f;--surface:#12121a;--card:#1a1a26;--border:#2a2a3e;
  --accent:{cat_info['color']};--accent2:#ff6b35;--text:#e8e8f0;--muted:#888899;
}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:var(--bg);color:var(--text);font-family:'Barlow',sans-serif;line-height:1.7}}
nav{{position:sticky;top:0;z-index:100;background:rgba(10,10,15,0.92);backdrop-filter:blur(12px);border-bottom:1px solid var(--border);padding:0 1.5rem;display:flex;align-items:center;height:60px}}
.logo{{font-family:'Space Mono',monospace;font-size:1rem;color:var(--accent);text-decoration:none}}
.container{{max-width:760px;margin:0 auto;padding:2.5rem 1.5rem}}
.post-tag{{font-family:'Space Mono',monospace;font-size:0.7rem;color:var(--accent);text-transform:uppercase;letter-spacing:0.1em;margin-bottom:0.8rem;display:block}}
h1{{font-size:clamp(1.6rem,4vw,2.4rem);font-weight:800;line-height:1.2;margin-bottom:1rem}}
.post-date{{font-size:0.8rem;color:var(--muted);margin-bottom:2rem;font-family:'Space Mono',monospace}}
.intro{{font-size:1.05rem;color:var(--muted);margin-bottom:2.5rem}}
h2{{font-size:1.3rem;font-weight:800;margin:2.5rem 0 1rem;padding-bottom:0.5rem;border-bottom:1px solid var(--border)}}
h2 span{{color:var(--accent);font-family:'Space Mono',monospace;font-size:0.7rem;margin-right:0.5rem}}
.pick-card{{background:var(--card);border:1px solid var(--border);border-radius:4px;padding:1.5rem;margin-bottom:1.2rem}}
.pick-header{{display:flex;gap:1rem;align-items:flex-start;margin-bottom:1rem}}
.pick-rank{{font-family:'Space Mono',monospace;font-size:1.8rem;color:var(--accent);font-weight:700;min-width:40px}}
.pick-name{{font-size:1.1rem;font-weight:700;margin-bottom:0.3rem}}
.pick-meta{{display:flex;gap:1rem}}
.pick-price{{color:var(--accent2);font-weight:700;font-size:0.9rem}}
.pick-rating{{color:#ffd700;font-size:0.9rem}}
.pick-grid{{display:grid;grid-template-columns:1fr 1fr;gap:1rem;margin-bottom:1rem}}
.pick-grid h4{{font-size:0.75rem;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:0.5rem;color:var(--muted)}}
.pros-list li{{color:#00ff88;font-size:0.85rem;margin-bottom:0.3rem;padding-left:1rem;position:relative}}
.pros-list li::before{{content:'✓';position:absolute;left:0}}
.cons-list li{{color:#ff6b6b;font-size:0.85rem;margin-bottom:0.3rem;padding-left:1rem;position:relative}}
.cons-list li::before{{content:'✗';position:absolute;left:0}}
.pick-verdict{{font-size:0.9rem;color:var(--muted);font-style:italic;margin-bottom:1rem}}
.btn-amazon{{display:inline-block;background:var(--accent);color:#000;padding:0.65rem 1.4rem;font-weight:800;font-size:0.85rem;letter-spacing:0.05em;text-transform:uppercase;text-decoration:none;border-radius:3px}}
.buying-guide{{background:var(--card);border:1px solid var(--border);border-radius:4px;padding:1.5rem;margin:2rem 0;font-size:0.95rem;color:var(--muted)}}
.faq-item{{border-bottom:1px solid var(--border);padding:1rem 0}}
.faq-q{{font-weight:700;margin-bottom:0.5rem}}
.faq-a{{font-size:0.9rem;color:var(--muted)}}
footer{{background:var(--surface);border-top:1px solid var(--border);padding:2rem 1.5rem;margin-top:4rem;text-align:center}}
footer p{{font-size:0.75rem;color:var(--muted)}}
@media(max-width:600px){{.pick-grid{{grid-template-columns:1fr}}}}
</style>
</head>
<body>
<nav><a href="/" class="logo">TechGadget<span style="color:#ff6b35">HQ</span></a></nav>
<div class="container">
  <span class="post-tag">{cat_info['emoji']} {cat_info['label']}</span>
  <h1>{post['title']}</h1>
  <div class="post-date">// Updated {post['date']}</div>
  <p class="intro">{post.get('intro','')}</p>

  <h2><span>//</span> Top Picks</h2>
  {picks_html}

  <h2><span>//</span> Buying Guide</h2>
  <div class="buying-guide">{post.get('buying_guide','')}</div>

  <h2><span>//</span> FAQ</h2>
  {faq_html}
</div>
<footer>
  <p>© 2025 {SITE_NAME} · <a href="/privacy.html" style="color:var(--muted)">Privacy</a> · <a href="/sitemap.xml" style="color:var(--muted)">Sitemap</a></p>
  <p style="margin-top:0.5rem">As an Amazon Associate we earn from qualifying purchases.</p>
</footer>
</body>
</html>"""

# ── INDEX JSON ────────────────────────────────────────────────────────────────
def update_post_index(posts_meta: list):
    index_path = Path("posts_index.json")
    existing = []
    if index_path.exists():
        with open(index_path) as f:
            existing = json.load(f)
    # prepend new posts
    combined = posts_meta + existing
    # deduplicate by slug
    seen = set()
    unique = []
    for p in combined:
        if p["slug"] not in seen:
            seen.add(p["slug"])
            unique.append(p)
    unique = unique[:200]  # cap
    with open(index_path, "w") as f:
        json.dump(unique, f, indent=2)
    print(f"[index] {len(unique)} total posts indexed")

# ── SITEMAP ───────────────────────────────────────────────────────────────────
def generate_sitemap():
    index_path = Path("posts_index.json")
    posts = []
    if index_path.exists():
        with open(index_path) as f:
            posts = json.load(f)

    urls = [f"  <url><loc>{SITE_URL}/</loc><changefreq>daily</changefreq><priority>1.0</priority></url>"]
    urls.append(f"  <url><loc>{SITE_URL}/blog/</loc><changefreq>daily</changefreq><priority>0.9</priority></url>")
    for cat in CATEGORIES:
        urls.append(f"  <url><loc>{SITE_URL}/categories/{cat}.html</loc><changefreq>weekly</changefreq><priority>0.8</priority></url>")
    for p in posts:
        urls.append(f"  <url><loc>{SITE_URL}/blog/{p['slug']}.html</loc><changefreq>monthly</changefreq><priority>0.7</priority></url>")

    sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    sitemap += "\n".join(urls)
    sitemap += "\n</urlset>"
    with open("sitemap.xml", "w") as f:
        f.write(sitemap)
    print(f"[sitemap] {len(urls)} URLs written")

# ── RSS FEED ──────────────────────────────────────────────────────────────────
def generate_feed():
    index_path = Path("posts_index.json")
    posts = []
    if index_path.exists():
        with open(index_path) as f:
            posts = json.load(f)[:20]

    items = ""
    for p in posts:
        items += f"""  <item>
    <title>{p['title']}</title>
    <link>{SITE_URL}/blog/{p['slug']}.html</link>
    <description>{p.get('excerpt','')}</description>
    <pubDate>{p.get('date','')}</pubDate>
  </item>\n"""

    feed = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
  <title>{SITE_NAME}</title>
  <link>{SITE_URL}</link>
  <description>Expert tech gadget reviews and buying guides</description>
  <language>en-us</language>
{items}</channel>
</rss>"""
    with open("feed.xml", "w") as f:
        f.write(feed)
    print(f"[feed] RSS updated with {len(posts)} items")

# ── MAIN ──────────────────────────────────────────────────────────────────────
def main():
    OUTPUT_DIR.mkdir(exist_ok=True)
    posts_meta = []

    # Generate 2 posts per run (adjust as needed)
    POSTS_PER_RUN = int(os.environ.get("POSTS_PER_RUN", "2"))

    # Rotate through categories
    cat_list = list(CATEGORIES.keys())
    day_of_year = date.today().timetuple().tm_yday
    posts_generated = 0

    for i in range(POSTS_PER_RUN):
        cat = cat_list[(day_of_year + i) % len(cat_list)]
        seeds = PRODUCT_SEEDS[cat]
        topic = seeds[random.randint(0, len(seeds)-1)]

        print(f"[gen] {cat} → {topic}")
        post = generate_post(cat, topic)
        html = render_post_html(post)
        slug = slugify(post["title"])
        out_path = OUTPUT_DIR / f"{slug}.html"
        out_path.write_text(html, encoding="utf-8")
        print(f"[out] {out_path}")

        posts_meta.append({
            "slug": slug,
            "title": post["title"],
            "excerpt": post.get("excerpt", ""),
            "category": cat,
            "date": post["date"],
        })
        posts_generated += 1

    update_post_index(posts_meta)
    generate_sitemap()
    generate_feed()
    print(f"[done] {posts_generated} posts generated")

if __name__ == "__main__":
    main()
