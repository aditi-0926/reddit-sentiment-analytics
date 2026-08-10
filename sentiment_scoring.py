from pymongo import MongoClient
from dotenv import load_dotenv
import os
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

load_dotenv()
client = MongoClient(os.getenv("MONGO_URI"))
db = client["reddit_india"]
threads_col = db["threads"]

analyzer = SentimentIntensityAnalyzer()

def score_text(text):
    if not text or not isinstance(text, str) or text.strip() == "":
        return None
    return analyzer.polarity_scores(text)["compound"]  # -1 (negative) to +1 (positive)

print("Fetching threads...")
threads = list(threads_col.find({}))
print(f"Scoring {len(threads)} threads...")

updated_count = 0
for i, thread in enumerate(threads):
    # Score the thread itself
    title_sentiment = score_text(thread.get("title"))
    selftext_sentiment = score_text(thread.get("selftext"))

    # Score each comment
    comments = thread.get("comments", [])
    for c in comments:
        c["sentiment"] = score_text(c.get("body"))

    # Write back
    threads_col.update_one(
        {"_id": thread["_id"]},
        {"$set": {
            "title_sentiment": title_sentiment,
            "selftext_sentiment": selftext_sentiment,
            "comments": comments
        }}
    )
    updated_count += 1

    if (i + 1) % 200 == 0:
        print(f"  Processed {i + 1}/{len(threads)} threads")

print(f"✅ Done! Updated {updated_count} threads with sentiment scores.")