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

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    try:
        response = requests.post(
            url,
            json={"chat_id": chat_id, "text": message, "parse_mode": "Markdown"},
            timeout=30,
        )
        response.raise_for_status()
    except Exception as e:
        print("Telegram Error:", e)


def get_recent_news():
    setup_db()
    time_limit = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=12)

    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute(
            "SELECT headline, source FROM news WHERE time_added >= ? ORDER BY time_added DESC",
            (time_limit.isoformat(" "),),
        ).fetchall()

    return "\n".join([f"- {row[0]} (Source: {row[1]})" for row in rows])


def summarize_with_ai(news_text):
    if not news_text:
        return "😴 No new updates since last summary."

    groq_api_key = os.environ.get("GROQ_API_KEY")
    if not groq_api_key:
        return "❌ AI Error: GROQ_API_KEY is missing"

    client = Groq(api_key=groq_api_key)

    prompt = f"""
    You are a financial news editor. I have a list of news headlines.
    1. Remove duplicate news (if multiple channels report the same thing, merge it into one).
    2. Categorize each news item into THREE categories with emojis:
       - 🟢 GOOD (Positive news like profits, new orders, expansion)
       - 🟡 MODERATE (Neutral news like management changes, minor updates)
       - 🔴 DANGER (Bad news like losses, legal issues, resignations)
    3. Format the output as a precise, 1-line bullet point for each category.
    4. Keep it extremely brief and in English.

    News List:
    {news_text}
    """

    try:
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama3-8b-8192",
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        return f"❌ AI Error: {e}"


def run_summary():
    print("Fetching news from Database...")
    news_text = get_recent_news()

    print("AI is Summarizing...")
    summary = summarize_with_ai(news_text)

    if summary and "No new updates" not in summary:
        alert_message = f"📰 *NEWS SUMMARY REPORT*\n\n{summary}"
        send_telegram_alert(alert_message)
        print("Summary Sent to Telegram!")
    else:
        print("No news to summarize.")


if __name__ == "__main__":
    run_summary()
