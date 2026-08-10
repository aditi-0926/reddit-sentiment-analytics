from pymongo import MongoClient
from dotenv import load_dotenv
import os
import pandas as pd

load_dotenv()
client = MongoClient(os.getenv("MONGO_URI"))
db = client["reddit_india"]
threads_col = db["threads"]

print("Fetching all threads...")
threads = list(threads_col.find({}))
print(f"Fetched {len(threads)} threads")

# --- Build threads_flat ---
thread_rows = []
comment_rows = []

for t in threads:
    thread_rows.append({
        "thread_id": t.get("thread_id"),
        "author": t.get("author"),
        "title": t.get("title"),
        "flair": t.get("flair"),
        "score": t.get("score"),
        "num_comments": t.get("num_comments"),
        "upvote_ratio": t.get("upvote_ratio"),
        "over_18": t.get("over_18"),
        "created_utc": t.get("created_utc"),
        "title_sentiment": t.get("title_sentiment"),
        "selftext_sentiment": t.get("selftext_sentiment"),
        "comment_count_loaded": t.get("comment_count_loaded"),
    })

    for c in t.get("comments", []):
        comment_rows.append({
            "comment_id": c.get("comment_id"),
            "thread_id": t.get("thread_id"),
            "thread_title": t.get("title"),
            "thread_flair": t.get("flair"),
            "parent_id": c.get("parent_id"),
            "author": c.get("author"),
            "body": c.get("body"),
            "score": c.get("score"),
            "depth": c.get("depth"),
            "sentiment": c.get("sentiment"),
            "created_utc": c.get("created_utc"),
        })

print(f"Building DataFrames: {len(thread_rows)} threads, {len(comment_rows)} comments")

threads_df = pd.DataFrame(thread_rows)
comments_df = pd.DataFrame(comment_rows)

# Add useful derived columns for Power BI
threads_df["created_utc"] = pd.to_datetime(threads_df["created_utc"], errors="coerce")
comments_df["created_utc"] = pd.to_datetime(comments_df["created_utc"], errors="coerce")

threads_df["created_date"] = threads_df["created_utc"].dt.date
comments_df["created_date"] = comments_df["created_utc"].dt.date

os.makedirs("exports", exist_ok=True)
threads_df.to_csv("exports/threads_flat.csv", index=False)
comments_df.to_csv("exports/comments_flat.csv", index=False)

print("✅ Exported:")
print(f"  exports/threads_flat.csv ({len(threads_df)} rows)")
print(f"  exports/comments_flat.csv ({len(comments_df)} rows)")