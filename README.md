# Reddit Sentiment Analytics — r/India

A data pipeline and dashboard project analyzing sentiment, engagement, and discussion patterns from the r/India subreddit, using **MongoDB Atlas** for storage and **Power BI** for visualization.

## Overview

This project ingests Reddit post and comment data, restructures it into a document-oriented schema in MongoDB, applies sentiment analysis to comments, and visualizes the results in an interactive Power BI dashboard covering activity trends, sentiment patterns, and top content.

## Why MongoDB

Reddit threads are naturally nested (posts → comments → replies → replies), and post metadata varies (some posts have flair, some don't; some are text posts, some are links). Rather than forcing this into a rigid relational schema, each thread is stored as a single MongoDB document with its comments embedded as an array — including a computed `depth` field for each comment (0 = top-level, increasing with reply depth). This lets a full thread and its discussion be read in one query, with no joins.

## Tech Stack

- **MongoDB Atlas** — document storage
- **Python** (`pymongo`, `pandas`) — data loading and ETL
- **VADER Sentiment** (`vaderSentiment`) — sentiment scoring, tuned for informal/social text
- **Power BI Desktop** — dashboard and visualization
- **python-dotenv** — environment/credential management

## Dataset

Source: [r/India Subreddit Threads and Comments](https://www.kaggle.com/datasets/bwandowando/reddit-rindia-subreddit-threads-and-comments) (Kaggle, published by bwandowando).

The raw dataset is not included in this repo (file size). To reproduce:
1. Download the dataset from the link above.
2. Place `india_subreddit_threads.csv` and `india_subreddit_comments.csv` into a local `data/` folder.

This project works with a filtered subset: the **top 2,000 threads by comment count**, and their associated comments (~417,000 comments), to keep the dataset within MongoDB Atlas's free-tier storage limit.

## Pipeline

```
data/*.csv
   │
   ▼
load_to_mongo.py        → loads threads + comments into MongoDB as nested documents,
                           computes comment depth via parent-chain traversal
   │
   ▼
sentiment_scoring.py    → scores thread titles and comment bodies with VADER,
                           writes sentiment scores back into MongoDB
   │
   ▼
export_for_powerbi.py   → flattens nested documents into two tabular CSVs
                           (threads_flat.csv, comments_flat.csv) for Power BI
   │
   ▼
power_reddit_analytics.pbix   → dashboard
```

### Setup

```bash
pip install pymongo python-dotenv pandas vaderSentiment
```

Create a `.env` file in the project root:
```
MONGO_URI=mongodb+srv://<username>:<password>@<cluster-url>/?appName=<app-name>
```

Run the pipeline in order:
```bash
python load_to_mongo.py
python sentiment_scoring.py
python export_for_powerbi.py
```

Then open `power_reddit_analytics.pbix` in Power BI Desktop.

## Data Model

Each MongoDB document in the `threads` collection:

```json
{
  "thread_id": "...",
  "author": "...",
  "title": "...",
  "flair": "...",
  "score": 1234,
  "num_comments": 87,
  "upvote_ratio": 0.91,
  "created_utc": "...",
  "title_sentiment": 0.42,
  "comments": [
    {
      "comment_id": "...",
      "parent_id": "...",
      "author": "...",
      "body": "...",
      "score": 45,
      "depth": 0,
      "sentiment": 0.31,
      "created_utc": "..."
    }
  ]
}
```

## Dashboard

Two pages:

**Overview & Trends** — total threads/comments, average sentiment and score, post volume by category, activity over time, and discussion volume by category (treemap).

**Sentiment & Top Content** — sentiment distribution, comment depth vs. sentiment, sentiment vs. score correlation (scatter), top threads, most extreme-sentiment threads, and most active commenters.

## Key Findings

- Comment sentiment across the dataset skews slightly positive on average, though the distribution includes a substantial share of negative and very negative comments.
- Sentiment does not show a strong, consistent relationship with post score — highly upvoted threads span the full range of sentiment, suggesting engagement is not simply a function of "positivity."
- Comment sentiment tends to shift at deeper reply levels, consistent with the general pattern that extended back-and-forth threads skew more contentious than top-level comments.

*(These are based on this specific 2,000-thread sample and should be read as directional observations, not definitive claims about the subreddit as a whole.)*

## Known Limitations

- **Sample size**: analysis is limited to the top 2,000 threads by comment count, not the full subreddit history — this biases the dataset toward already-popular/active discussions.
- **Deleted content**: some threads in the source data have been removed from Reddit (title shows as removed) but retain their original score/comment metadata, which can skew "top" rankings.
- **Sparse high-depth comments**: very few comments exist at extreme reply depths, so sentiment averages at those depths are based on small samples and should be interpreted cautiously.
- **Bot/moderator accounts**: "most active commenter" metrics may include automated accounts (e.g., AutoModerator) rather than only human activity.
- **Sensitive content**: as a general-discussion subreddit, the dataset includes posts on serious topics (crime, personal hardship); sentiment scores on these should not be read the same way as sentiment on light/entertainment content.

## Project Structure

```
reddit_analytics/
├── data/                        # raw CSVs (not included, see Dataset section)
├── exports/                     # flattened CSVs for Power BI (not included)
├── load_to_mongo.py
├── sentiment_scoring.py
├── export_for_powerbi.py
├── inspect_data.py
├── test_connection.py
├── power_reddit_analytics.pbix
└── README.md
```
