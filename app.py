from flask import Flask, render_template, request, redirect, url_for, jsonify
import requests, time, math

app = Flask(__name__)

# --------------- Fibonacci Heap ----------------
class Node:
    def __init__(self, key, value, article_id=None):
        self.key = key
        self.value = value
        self.article_id = article_id
        self.parent = None
        self.child = None
        self.left = self
        self.right = self
        self.degree = 0
        self.mark = False

class FibonacciHeap:
    def __init__(self):
        self.max_node = None
        self.total_nodes = 0

    def _iterate(self, start):
        if not start:
            return
        node = start
        while True:
            yield node
            node = node.right
            if node == start:
                break

    def _add_to_root_list(self, node):
        if not self.max_node:
            node.left = node.right = node
            self.max_node = node
        else:
            node.left = self.max_node.left
            node.right = self.max_node
            self.max_node.left.right = node
            self.max_node.left = node
            if node.key > self.max_node.key:
                self.max_node = node

    def insert(self, key, value, article_id=None):
        node = Node(key, value, article_id)
        self._add_to_root_list(node)
        self.total_nodes += 1
        return node

    def extract_max(self):
        z = self.max_node
        if not z:
            return None
        if z.child:
            for child in [x for x in self._iterate(z.child)]:
                child.parent = None
                self._add_to_root_list(child)
        if z.right == z:
            self.max_node = None
        else:
            z.left.right = z.right
            z.right.left = z.left
            self.max_node = z.right
        self.total_nodes -= 1
        return z

# ----------- News Feed Engine (Personalized) ----------
def compute_score(article, profile):
    now = time.time()
    age_days = (now - article.get("ts", now)) / 86400
    cat_score = profile["category_scores"].get(article["category"], 0.0)
    recency = math.exp(-age_days / 1.5)
    popularity = math.log(1 + article["views"])
    # You can tune weights for recency/popularity/category below:
    return cat_score + 0.5 * recency + 0.8 * popularity

class NewsFeedEngine:
    def __init__(self):
        self.heaps = {}

    def _ensure_user(self, uid):
        if uid not in self.heaps:
            self.heaps[uid] = FibonacciHeap()

    def ingest_articles(self, uid, articles, profile):
        self._ensure_user(uid)
        heap = self.heaps[uid]
        for art in articles:
            score = compute_score(art, profile)
            heap.insert(score, art, art["id"])

    def clear_user(self, uid):
        self.heaps[uid] = FibonacciHeap()

    def get_top_n(self, uid, n=6):
        if uid not in self.heaps or self.heaps[uid].total_nodes == 0:
            return []
        heap = self.heaps[uid]
        temp = []
        for _ in range(min(n, heap.total_nodes)):
            node = heap.extract_max()
            if not node:
                break
            temp.append((node.key, node.value))
        for k, art in temp:
            heap.insert(k, art, art["id"])
        # Only send necessary info
        return [
            {
                "title": a["title"],
                "source": a["source"],
                "category": a["category"],
                "desc": a["desc"],
                "url": a["url"],
                "score": round(k, 2)
            }
            for k, a in temp
        ]

feed_engine = NewsFeedEngine()

# ----------- GNews Fetch Function ----------
def fetch_latest_news():
    try:
        url = (
            "https://api.currentsapi.services/v1/latest-news?"
            "language=en&"
            "apiKey=ijZlDX7ehOWix7TuVLx9gq8VRVOYEHIWGUJJnkG-IYeeMYoi"
        )
        res = requests.get(url)
        print("API status:", res.status_code)
        data = res.json()

        if res.status_code != 200 or data.get("status") == "401":
            print("⚠️ API Error:", data)
            # Fallback data
            return [
                {
                    "id": "sample_1",
                    "title": "AI Revolution: How ChatGPT is Changing Everything",
                    "desc": "OpenAI's new models are transforming industries.",
                    "source": "CodesWorld",
                    "category": "Tech",
                    "url": "#",
                    "views": 1200,
                    "ts": time.time()
                },
                {
                    "id": "sample_2",
                    "title": "Stock Market Sees Unusual Growth Amid Global Shifts",
                    "desc": "Investors remain optimistic about the tech sector.",
                    "source": "Finance Daily",
                    "category": "Finance",
                    "url": "#",
                    "views": 950,
                    "ts": time.time()
                }
            ]

        fetched = []
        for i, art in enumerate(data.get("news", [])):
            title = art.get("title", "")
            category = "Tech" if "tech" in title.lower() else (
                "Finance" if "market" in title.lower() or "finance" in title.lower() else (
                    "Sports" if "sport" in title.lower() else "General"
                )
            )
            fetched.append({
                "id": f"currents_{i}",
                "title": title,
                "desc": art.get("description", ""),
                "source": art.get("author", "Unknown"),
                "category": category,
                "url": art.get("url", "#"),
                "views": 1000 - i * 77,
                "ts": time.time() - i * 2000
            })
        return fetched

    except Exception as e:
        print("API Error:", e)
        return []


# def fetch_latest_news():
#     try:
#         url = (
#             "https://gnews.io/api/v4/top-headlines?"
#             # "country=in&lang=en&max=15&token=e4e6c8ff16524e07979770c101207266"
#             "country=in&lang=en&max=15&token=ijZlDX7ehOWix7TuVLx9gq8VRVOYEHIWGUJJnkG-IYeeMYoi"
#         )
#         # url = (
#         #     "https://gnews.io/api/v4/top-headlines?"
#         #     "country=in&lang=en&max=15&token=25d26fb12fed5c97725277b8871b7119"
#         # )
#         res = requests.get(url)
#         print("API status:", res.status_code)
#         data = res.json()
#         fetched = []
#         for i, art in enumerate(data.get("articles", [])):
#             title = art.get("title", "")
#             category = "Tech" if "tech" in title.lower() else (
#                 "Finance" if "market" in title.lower() or "finance" in title.lower() else (
#                     "Sports" if "sport" in title.lower() else "General"
#                 )
#             )
#             fetched.append({
#                 "id": f"gnews_{i}",
#                 "title": art.get("title", "No Title"),
#                 "desc": art.get("description", ""),
#                 "source": art.get("source", "Unknown"),
#                 "category": category,
#                 "url": art.get("url", "#"),
#                 "views": 1000 - i * 77,
#                 "ts": time.time() - i * 2000
#             })
#         return fetched
#     except Exception as e:
#         print("API Error:", e)
#         return []

# ----------- ROUTES ----------

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/set_preferences", methods=["POST"])
def set_preferences():
    tech = float(request.form.get("tech", 0.5))
    finance = float(request.form.get("finance", 0.5))
    sports = float(request.form.get("sports", 0.5))
    general = float(request.form.get("general", 0.5))

    profile = {
        "category_scores": {
            "Tech": tech,
            "Finance": finance,
            "Sports": sports,
            "General": general
        }
    }
    global last_profile
    last_profile = profile

    articles = fetch_latest_news()
    feed_engine.clear_user("user_1")      # Clear heap before new ingest!
    feed_engine.ingest_articles("user_1", articles, profile)
    return redirect(url_for("feed"))

@app.route("/feed")
def feed():
    return render_template("feed.html")

@app.route("/get_feed")
def get_feed():
    uid = "user_1"
    profile = globals().get("last_profile", {"category_scores": {
        "Tech": 0.5, "Finance": 0.5, "Sports": 0.5, "General": 0.5
    }})
    articles = fetch_latest_news()
    feed_engine.clear_user(uid)   # Clear heap to respect current profile
    feed_engine.ingest_articles(uid, articles, profile)
    top_articles = feed_engine.get_top_n(uid, n=6)
    return jsonify(top_articles)

if __name__ == "__main__":
    app.run(debug=True)
