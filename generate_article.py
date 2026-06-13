"""
generate_article.py (Gemini version)

Runs on a schedule (via GitHub Actions). Each run:
1. Loads topics already covered (data/used_topics.json)
2. Picks the next category in rotation (data/category_index.json)
3. Asks Gemini for ONE article in that category
4. Saves article as articles/article-<timestamp>.html
5. Updates data/articles.json, data/used_topics.json, data/category_index.json
"""

import json
import os
import re
import urllib.request
from datetime import datetime, timezone

API_KEY = os.environ["GEMINI_API_KEY"]
MODEL = "gemini-2.5-flash"
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={API_KEY}"

DATA_DIR = "data"
ARTICLES_DIR = "articles"
ARTICLES_JSON = os.path.join(DATA_DIR, "articles.json")
USED_TOPICS_JSON = os.path.join(DATA_DIR, "used_topics.json")
CATEGORY_INDEX_FILE = os.path.join(DATA_DIR, "category_index.json")

CATEGORIES = ["trending", "sports", "film", "news", "money", "tech", "howto"]


def load_json(path, default):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_google_trends():
    """Fetch current trending search terms from Google Trends RSS (US feed)."""
    url = "https://trends.google.com/trending/rss?geo=US"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            xml = resp.read().decode("utf-8")
        titles = re.findall(r"<title>(.*?)</title>", xml)
        return [t.strip() for t in titles[1:] if t.strip()]
    except Exception as e:
        print(f"Could not fetch Google Trends: {e}")
        return []


def call_gemini(used_topics, category):
    avoid_list = ", ".join(used_topics[-100:]) if used_topics else "none yet"

    trends = get_google_trends()
    fresh_trends = [t for t in trends if t not in used_topics]
    trends_list = ", ".join(fresh_trends[:15]) if fresh_trends else "none available right now"

    category_briefs = {
        "trending": "a currently trending topic on Google (general interest)",
        "sports": "sports news — results, athletes, events, leagues",
        "film": "movie/TV/celebrity/entertainment news",
        "news": "general current world/national news",
        "money": "personal finance, saving money, budgeting tips, smart spending",
        "tech": "technology news, gadgets, apps, AI tools, reviews",
        "howto": "a practical solution to a common everyday life problem"
    }

    brief = category_briefs.get(category, category_briefs["howto"])

    prompt = f"""You write engaging articles for a general-audience website.

Write ONE article for the category: "{category}" — meaning: {brief}

Currently trending on Google (use if relevant to this category): {trends_list}

Topics already covered (do NOT repeat or write something too similar to any of these): {avoid_list}

Article should be around 300-500 words, informative and engaging.

Respond ONLY with valid JSON in this exact format, with no extra text, no markdown fences:
{{
  "topic": "short topic name used to track duplicates",
  "title": "Article title",
  "category": "{category}",
  "html": "<p>Article body as HTML paragraphs, using <h2> for subheadings and <p> for paragraphs, <ul><li> for lists if helpful.</p>"
}}"""

    body = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}]
    }).encode("utf-8")

    req = urllib.request.Request(
        API_URL,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    text = data["candidates"][0]["content"]["parts"][0]["text"].strip()

    text = re.sub(r"^```json|```$", "", text.strip()).strip()
    text = re.sub(r"^```|```$", "", text.strip()).strip()

    return json.loads(text)


def category_badge(category):
    return {
        "trending": "🔥 Trending",
        "sports": "⚽ Sports",
        "film": "🎬 Film & TV",
        "news": "📰 News",
        "money": "💰 Money",
        "tech": "💻 Tech",
        "howto": "💡 How-To"
    }.get(category, "💡 How-To")


def slugify(text):
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")[:60]


def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(ARTICLES_DIR, exist_ok=True)

    articles = load_json(ARTICLES_JSON, [])
    used_topics = load_json(USED_TOPICS_JSON, [])
    idx_data = load_json(CATEGORY_INDEX_FILE, {"index": 0})
    idx = idx_data.get("index", 0) % len(CATEGORIES)
    category = CATEGORIES[idx]

    result = call_gemini(used_topics, category)

    topic = result["topic"]
    title = result["title"]
    html_body = result["html"]

    now = datetime.now(timezone.utc)
    date_str = now.strftime("%Y-%m-%d %H:%M UTC")
    slug = slugify(topic) or "article"
    timestamp = now.strftime("%Y%m%d-%H%M%S")
    filename = f"article-{timestamp}-{slug}.html"

    article_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <link rel="stylesheet" href="../style.css">
</head>
<body>
  <a class="back-link" href="../index.html">&larr; Back to all articles</a>
  <div class="article-body">
    <h1>{title}</h1>
    <span class="date">{date_str} &middot; {category_badge(category)}</span>
    {html_body}
  </div>
</body>
</html>
"""

    with open(os.path.join(ARTICLES_DIR, filename), "w", encoding="utf-8") as f:
        f.write(article_html)

    articles.append({
        "title": title,
        "filename": filename,
        "date": date_str,
        "category": category
    })
    save_json(ARTICLES_JSON, articles)

    used_topics.append(topic)
    save_json(USED_TOPICS_JSON, used_topics)

    save_json(CATEGORY_INDEX_FILE, {"index": (idx + 1) % len(CATEGORIES)})

    print(f"Created: {filename} [{category}]")


if __name__ == "__main__":
    main()
