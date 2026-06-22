# -------------------------------
# IMPORT REQUIRED LIBRARIES
# -------------------------------

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import requests
from collections import Counter
from textblob import TextBlob
from dotenv import load_dotenv
import os

load_dotenv()
# -------------------------------
# CREATE FASTAPI APP
# -------------------------------

app = FastAPI()

# -------------------------------
# API KEYS (ADD YOUR OWN)
# -------------------------------
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")


# -------------------------------
# TRUSTED NEWS SOURCES
# -------------------------------

TRUSTED_SOURCES = [
    "BBC News",
    "Reuters",
    "Al Jazeera English",
    "CNN",
    "The Guardian"
]

# -------------------------------
# ENABLE CORS
# -------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------
# ROOT ROUTE
# -------------------------------

@app.get("/")
def home():
    return {"message": "OSINT API is running 🚀"}

# -------------------------------
# 🚨 RISK SCORE (NEW)
# -------------------------------

def calculate_risk_score(articles, trend):

    """
    Calculates a risk score based on:
    - Negative sentiment
    - News volume
    - Trend spikes
    """

    score = 0

    # 1. Sentiment impact
    negative_count = sum(1 for a in articles if a.get("sentiment") == "Negative")
    total = len(articles) if articles else 1

    sentiment_ratio = negative_count / total
    score += sentiment_ratio * 40  # weight = 40

    # 2. Volume impact
    volume = len(articles)
    if volume > 20:
        score += 30
    elif volume > 10:
        score += 20
    else:
        score += 10

    # 3. Trend spike impact
    if trend:
        values = list(trend.values())
        avg = sum(values) / len(values)

        if max(values) > avg * 1.5:
            score += 30

    # normalize to 100
    return min(int(score), 100)

def get_risk_label(score):
    if score > 70:
        return "High 🚨"
    elif score > 40:
        return "Medium ⚠️"
    return "Low ✅"

# -------------------------------
# 🧠 RISK EXPLANATION (NEW)
# -------------------------------

def generate_risk_explanation(articles, trend):

    total = len(articles) if articles else 1
    negative = sum(1 for a in articles if a.get("sentiment") == "Negative")

    neg_percent = int((negative / total) * 100)

    explanation = []

    # 1. Sentiment explanation
    if neg_percent > 50:
        explanation.append(f"High negative sentiment ({neg_percent}%)")
    elif neg_percent > 20:
        explanation.append(f"Moderate negative sentiment ({neg_percent}%)")
    else:
        explanation.append(f"Low negative sentiment ({neg_percent}%)")

    # 2. Trend explanation
    if trend:
        values = list(trend.values())
        avg = sum(values) / len(values)

        if max(values) > avg * 1.5:
            explanation.append("Sudden spike in activity detected")
        else:
            explanation.append("No significant activity spike")

    # 3. Volume explanation
    if total > 20:
        explanation.append("High news volume")
    elif total > 10:
        explanation.append("Moderate news volume")
    else:
        explanation.append("Low news volume")

    return explanation

# -------------------------------
# 🖼️ IMAGE ANALYSIS (STEP 1)
# -------------------------------

@app.get("/analyze-image")
def analyze_image(image_url: str):

    """
    Takes an image URL and returns AI-based analysis
    """

    prompt = f"""
    Analyze this image from an OSINT perspective.

    Image URL: {image_url}

    Provide:
    1. What is visible in the image
    2. Whether it relates to military / conflict / normal activity
    3. Any potential intelligence value
    """

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "openai/gpt-4o-mini",
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            }
        )

        result = response.json()

        if "choices" in result:
            return {
                "analysis": result["choices"][0]["message"]["content"]
            }

    except Exception as e:
        print("IMAGE ANALYSIS ERROR:", e)

    return {"analysis": "Could not analyze image"}


# -------------------------------
# 📍 LOCATION NORMALIZATION (NEW)
# -------------------------------

def normalize_location(loc):
    loc = loc.lower()

    if "hormuz" in loc:
        return "Strait of Hormuz"

    if "bab" in loc:
        return "Bab el-Mandeb"

    if "suez" in loc:
        return "Suez Canal"

    if "red sea" in loc:
        return "Red Sea"

    return loc.title()


# -------------------------------
# 📍 LOCATION EXTRACTION (UPGRADED)
# -------------------------------

def extract_location(text):
    text = text.lower()

    locations = [
        "iran","usa","united states","china","india",
        "russia","israel","ukraine","gaza","yemen",
        "iraq","syria","qatar","bahrain","kuwait",
        "saudi arabia",

        # 🔥 strategic keywords
        "hormuz",
        "bab el mandeb",
        "bab-el-mandeb",
        "suez",
        "red sea",

        # 🔥 base detection keywords
        "air base",
        "naval base",
        "military base"
    ]

    for loc in locations:
        if loc in text:
            return normalize_location(loc)

    return "Unknown"


# -------------------------------
# 📊 TREND ANALYSIS
# -------------------------------

def generate_trend_data(data):
    times = []

    for article in data.get("articles", []):
        if article.get("publishedAt"):
            times.append(article["publishedAt"][:13])

    return dict(Counter(times))


# -------------------------------
# 💬 REDDIT DATA
# -------------------------------

def fetch_reddit(query):
    try:
        url = f"https://www.reddit.com/search.json?q={query}&limit=5"
        headers = {"User-Agent": "osint-app"}

        data = requests.get(url, headers=headers).json()

        posts = []

        for p in data["data"]["children"]:
            posts.append({
                "title": p["data"]["title"],
                "description": p["data"].get("selftext", ""),
                "source": "Reddit (Social)",
                "url": "https://reddit.com" + p["data"]["permalink"],
                "location": extract_location(p["data"]["title"])
            })

        return posts
    except:
        return []


# -------------------------------
# 💬 HACKER NEWS DATA
# -------------------------------

def fetch_hn(query):
    try:
        url = f"https://hn.algolia.com/api/v1/search?query={query}"
        data = requests.get(url).json()

        posts = []

        for hit in data.get("hits", [])[:5]:
            posts.append({
                "title": hit.get("title", ""),
                "description": hit.get("story_text", "") or "",
                "source": "HackerNews (Social)",
                "url": hit.get("url", ""),
                "location": extract_location(hit.get("title", ""))
            })

        return posts
    except:
        return []


# -------------------------------
# 🧹 REMOVE DUPLICATES
# -------------------------------

def remove_duplicates(items):
    seen = set()
    unique = []

    for item in items:
        key = item["title"].lower()

        if key not in seen:
            seen.add(key)
            unique.append(item)

    return unique


# -------------------------------
# 💬 SENTIMENT
# -------------------------------

def get_sentiment(text):
    polarity = TextBlob(text).sentiment.polarity

    if polarity > 0.1:
        return "Positive"
    elif polarity < -0.1:
        return "Negative"
    return "Neutral"


# -------------------------------
# 🔑 KEYWORDS
# -------------------------------

def extract_keywords(text):
    words = text.lower().split()
    return list(set([w for w in words if len(w) > 5]))[:5]


# -------------------------------
# 🧠 CREDIBILITY
# -------------------------------

def credibility(source, title=""):

    source_lower = source.lower()
    title_lower = title.lower()

    # Trusted sources
    if source in TRUSTED_SOURCES:
        return "High"

    # Social media = low
    if "reddit" in source_lower or "social" in source_lower:
        return "Low"

    # Suspicious keywords
    suspicious_keywords = ["rumor", "unverified", "viral", "breaking"]

    if any(k in title_lower for k in suspicious_keywords):
        return "Low"

    return "Medium"

# -------------------------------
# 🚨 SPIKE DETECTION
# -------------------------------

def detect_spike(trend):
    if not trend:
        return "No data"

    vals = list(trend.values())

    if max(vals) > (sum(vals)/len(vals))*1.5:
        return "High Activity Spike 🚨"

    return "Normal Activity"


# -------------------------------
# 🧠 AI SUMMARY
# -------------------------------

def summarize_articles_openrouter(articles, query):
    if not articles:
        return "No relevant articles found."

    combined_text = ""

    for a in articles[:5]:
        combined_text += a["title"] + ". "
        if a["description"]:
            combined_text += a["description"] + " "

    prompt = f"""
    Analyze the following data related to: {query}

    Provide:
    1. Key developments
    2. Important observations
    3. Overall trend

    Data:
    {combined_text}
    """

    try:
        res = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "openai/gpt-4o-mini",
                "messages": [{"role": "user", "content": prompt}]
            }
        )

        result = res.json()

        if "choices" in result:
            return result["choices"][0]["message"]["content"]

    except Exception as e:
        print("SUMMARY ERROR:", e)

    return "Summary not available"


# -------------------------------
# 🧠 AI CLASSIFICATION
# -------------------------------

def classify_intelligence(text):
    prompt = f"""
    Classify into ONE:

    Military Activity
    Strategic Location
    General News

    Text: {text}
    """

    try:
        res = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "openai/gpt-4o-mini",
                "messages": [{"role": "user", "content": prompt}]
            }
        )

        result = res.json()

        if "choices" in result:
            return result["choices"][0]["message"]["content"].strip()

    except:
        pass

    return "General News"


# -------------------------------
# ⚠️ AI IMPORTANCE
# -------------------------------

def explain_importance(text):
    prompt = f"""
    Explain in one short sentence why this is geopolitically important:

    {text}
    """

    try:
        res = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "openai/gpt-4o-mini",
                "messages": [{"role": "user", "content": prompt}]
            }
        )

        result = res.json()

        if "choices" in result:
            return result["choices"][0]["message"]["content"].strip()

    except:
        pass

    return "No additional context available."


# -------------------------------
# 🌍 MAIN API
# -------------------------------

@app.get("/news")
def get_news(query: str = "Iran US war"):

    url = "https://newsapi.org/v2/everything"

    params = {
        "q": query,
        "language": "en",
        "sortBy": "publishedAt",
        "apiKey": NEWS_API_KEY
    }

    data = requests.get(url, params=params).json()

    articles = []

    for a in data.get("articles", []):
        raw_text = (a["title"] or "") + " " + (a["description"] or "")

        articles.append({
            "title": a["title"] or "",
            "description": a["description"] or "",
            "source": a["source"]["name"],
            "url": a["url"],
            "date": a["publishedAt"][:10] if a.get("publishedAt") else "",
            "location": extract_location(raw_text)
        })

    # social
    reddit = fetch_reddit(query)
    hn = fetch_hn(query)

    articles.extend(reddit)
    articles.extend(hn)

    articles = remove_duplicates(articles)

    filtered = articles

    # -------------------------------
    # ADD ANALYSIS
    # -------------------------------

    for i, art in enumerate(filtered):

        art["sentiment"] = get_sentiment(art["title"])
        art["keywords"] = extract_keywords(art["title"])
        art["credibility"] = credibility(art["source"] , art["title"])

        # 🚨 Possible misinformation
        if art["credibility"] == "Low" and art["sentiment"] == "Negative":
            art["misinformation"] = "⚠️ Potential misinformation"
        else:
            art["misinformation"] = None

        if i < 5:
            text = art["title"] + " " + art["description"]

            art["type"] = classify_intelligence(text)
            art["importance"] = explain_importance(art["title"])
        else:
            art["type"] = "General News"
            art["importance"] = ""

    trend = generate_trend_data(data)
    spike = detect_spike(trend)

    # 🔥 NEW: risk calculation
    risk_score = calculate_risk_score(filtered, trend)
    risk_label = get_risk_label(risk_score)
    # 🧠 Explanation layer
    risk_explanation = generate_risk_explanation(filtered, trend)

    # 🚨 ALERT SYSTEM (ADD HERE)

    alert_message = None

    if risk_score > 70:
        alert_message = "🚨 High threat detected! Immediate attention required."
    elif risk_score > 40:
        alert_message = "⚠️ Moderate risk detected. Monitor closely."
    # 🔍 DEBUG (ADD HERE)

    print("Total articles:", len(filtered))
    print("Negative:", sum(1 for a in filtered if a.get("sentiment") == "Negative"))
    print("Trend:", trend)
    print("Risk score:", risk_score)

    summary = summarize_articles_openrouter(filtered, query)
    social_summary = summarize_articles_openrouter(reddit + hn, query)

    return {
        "summary": summary,
        "social_summary": social_summary,
        "articles": filtered,
        "trend": trend,
        "spike": spike,
        "risk_score": risk_score,
        "risk_label": risk_label,
        "alert": alert_message,
        "risk_explanation": risk_explanation
    }