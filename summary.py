import sqlite3
import datetime
import requests
import os
from groq import Groq

DB_PATH = os.environ.get("NEWS_DB_PATH", "news_database.db")


def setup_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS news
                        (id INTEGER PRIMARY KEY AUTOINCREMENT,
                         headline TEXT NOT NULL,
                         source TEXT,
                         time_added TIMESTAMP NOT NULL)''')


def send_telegram_alert(message):
    bot_token = os.environ.get("BOT_TOKEN")
    chat_id = os.environ.get("CHAT_ID")
    if not bot_token or not chat_id:
        print("Telegram Error: BOT_TOKEN or CHAT_ID is missing")
        return

    try:
        response = requests.post(
            f"https://api.telegram.org/bot{bot_token}/sendMessage",
            json={"chat_id": chat_id, "text": message, "parse_mode": "Markdown"},
            timeout=30,
        )
        response.raise_for_status()
    except Exception as exc:
        print("Telegram Error:", exc)


def get_recent_news():
    setup_db()
    time_limit = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=12)

    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute(
            "SELECT headline, source FROM news WHERE time_added >= ? ORDER BY time_added DESC",
            (time_limit.isoformat(" "),),
        ).fetchall()

    return "\n".join(f"- {row[0]} (Source: {row[1]})" for row in rows)


def summarize_with_ai(news_text):
    if not news_text:
        return "😴 No new updates since last summary."

    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return "❌ AI Error: GROQ_API_KEY is missing"

    client = Groq(api_key=api_key)
    prompt = f"""
You are a financial news editor. Use only the supplied headlines.
1. Remove duplicate news.
2. Categorize items into:
   - 🟢 GOOD
   - 🟡 MODERATE
   - 🔴 DANGER
3. Give one concise bullet per category.

News List:
{news_text}
"""

    try:
        result = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama3-8b-8192",
        )
        return result.choices[0].message.content
    except Exception as exc:
        return f"❌ AI Error: {exc}"


def run_summary():
    print("Fetching news from Database...")
    news_text = get_recent_news()

    print("AI is Summarizing...")
    summary = summarize_with_ai(news_text)

    if news_text and summary and "No new updates" not in summary:
        send_telegram_alert(f"📰 *NEWS SUMMARY REPORT*\n\n{summary}")
        print("Summary Sent to Telegram!")
    else:
        print("No news to summarize.")


if __name__ == "__main__":
    run_summary()
