import pandas as pd
from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()
client = MongoClient(os.getenv("MONGO_URI"))
db = client["reddit_india"]
threads_col = db["threads"]
comments_col = db["threads"]  # comments will be embedded, not separate

# Clear existing data (safe to re-run)
threads_col.delete_many({})

# --- Step 1: Load threads, pick top N by num_comments ---
print("Loading threads.csv...")
threads_df = pd.read_csv("data/india_subreddit_threads.csv")
threads_df["created_utc"] = pd.to_datetime(threads_df["created_utc"], errors="coerce")

TOP_N_THREADS = 2000
top_threads = threads_df.sort_values("num_comments", ascending=False).head(TOP_N_THREADS)
selected_thread_ids = set(top_threads["thread_id"])
print(f"Selected {len(selected_thread_ids)} threads")

# --- Step 2: Stream comments.csv in chunks, keep only comments for selected threads ---
print("Loading comments.csv (this is a 321MB file, may take a few minutes)...")
CHUNK_SIZE = 100_000
comments_by_thread = {tid: [] for tid in selected_thread_ids}

chunks_processed = 0
for chunk in pd.read_csv("data/india_subreddit_comments.csv", chunksize=CHUNK_SIZE):
    filtered = chunk[chunk["thread_id"].isin(selected_thread_ids)]
    for _, row in filtered.iterrows():
        comments_by_thread[row["thread_id"]].append({
            "comment_id": row["comment_id"],
            "parent_id": row["parent_id"],
            "author": row["author"],
            "body": row["body"],
            "score": row["score"],
            "created_utc": row["created_utc"],
        })
    chunks_processed += 1
    print(f"  Processed chunk {chunks_processed} ({chunks_processed * CHUNK_SIZE:,} rows scanned)")

# --- Step 3: Compute comment depth via parent chain ---
def compute_depths(comments, thread_id):
    id_to_parent = {c["comment_id"]: c["parent_id"] for c in comments}
    depth_cache = {}

    def get_depth(comment_id, visited=None):
        if visited is None:
            visited = set()
        if comment_id in depth_cache:
            return depth_cache[comment_id]
        if comment_id in visited:  # cycle guard
            return 0
        visited.add(comment_id)
        parent = id_to_parent.get(comment_id)
        if parent is None or parent == thread_id or parent not in id_to_parent:
            depth = 0
        else:
            depth = 1 + get_depth(parent, visited)
        depth_cache[comment_id] = depth
        return depth

    for c in comments:
        c["depth"] = get_depth(c["comment_id"])
    return comments

# --- Step 4: Build final documents and insert ---
print("Building documents...")
documents = []
for _, thread in top_threads.iterrows():
    tid = thread["thread_id"]
    comments = compute_depths(comments_by_thread.get(tid, []), tid)
    doc = {
        "thread_id": tid,
        "author": thread["author"],
        "title": thread["title"],
        "selftext": thread.get("selftext"),
        "flair": thread.get("link_flair_text"),
        "score": thread["score"],
        "num_comments": thread["num_comments"],
        "upvote_ratio": thread.get("upvote_ratio"),
        "over_18": thread.get("over_18"),
        "created_utc": thread["created_utc"],
        "comments": comments,
        "comment_count_loaded": len(comments),
    }
    documents.append(doc)

print(f"Inserting {len(documents)} thread documents into MongoDB...")
if documents:
    threads_col.insert_many(documents)

print("✅ Done!")
print(f"Total threads: {len(documents)}")
print(f"Total comments embedded: {sum(d['comment_count_loaded'] for d in documents)}")