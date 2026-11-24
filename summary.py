import sqlite3
import datetime
import requests
import os
from groq import Groq 

def send_telegram_alert(message):
    bot_token = os.environ.get("BOT_TOKEN") 
    chat_id = os.environ.get("CHAT_ID")
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage?chat_id={chat_id}&text={message}&parse_mode=Markdown"
    try:
        requests.get(url)
    except Exception as e:
        print("Telegram Error:", e)

def get_recent_news():
    conn = sqlite3.connect('news_database.db')
    c = conn.cursor()
    time_limit = datetime.datetime.now() - datetime.timedelta(hours=12)
    c.execute("SELECT headline, source FROM news WHERE time_added > ?", (time_limit,))
    rows = c.fetchall()
    conn.close()
    
    news_text = "\n".join([f"- {row[0]} (Source: {row[1]})" for row in rows])
    return news_text

def summarize_with_ai(news_text):
    if not news_text:
        return "😴 No new updates since last summary."
        
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    
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
