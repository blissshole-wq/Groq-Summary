import os
import pytz
from datetime import datetime, timedelta
import requests
from groq import Groq
from telethon import TelegramClient
from telethon.sessions import StringSession

# ரகசியங்கள்
TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")
STRING_SESSION = os.environ.get("STRING_SESSION", "")

# உங்கள் Source சேனல்களின் ID-கள் (இங்கே உங்கள் 14 சேனல்களின் ID-களைப் போடுங்கள்)
SOURCE_CHANNELS = [
-1001096581370, 
-1002897476578,
-1001330148120,
-1001498073945,
-1001823497790,
-1001291324441,
-1003808911367,
-1001450185719,
-1001490398856,
-1001345563500, 
-1001274268284,
-1001421618043,
-1001299805329,
-1001247488093,
 
]

client = Groq(api_key=GROQ_API_KEY)
tele_client = TelegramClient(StringSession(STRING_SESSION), API_ID, API_HASH)

def send_telegram_message(message):
    if len(message) > 4000:
        messages = [message[i:i+4000] for i in range(0, len(message), 4000)]
        for msg in messages:
            url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
            payload = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}
            requests.post(url, json=payload)
    else:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
        requests.post(url, json=payload)

async def fetch_recent_news():
    await tele_client.start()
    all_news = []
    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist)
    time_limit = now - timedelta(hours=12) 
    
    print("📥 செய்திகள் சேகரிக்கப்படுகின்றன...")
    for channel in SOURCE_CHANNELS:
        try:
            # ஒவ்வொரு சேனலில் இருந்தும் கடைசி 1 மெசேஜ் மட்டும் எடுக்கிறோம்
            messages = await tele_client.get_messages(channel, limit=1) 
            for msg in messages:
                if msg.date.astimezone(ist) > time_limit and msg.text:
                    # ஒவ்வொரு மெசேஜின் அளவையும் 200 எழுத்துக்களுக்குள் வெட்டுகிறோம்
                    short_text = msg.text[:200] 
                    all_news.append(short_text)
        except Exception as e:
            print(f"❌ {channel} படிக்க முடியவில்லை: {e}")
            
    await tele_client.disconnect()
    
    # மொத்த டெக்ஸ்ட்டும் 2500 எழுத்துக்களுக்கு மேல் போகாமல் வெட்டுகிறோம்
    final_news = "\n---\n".join(all_news)
    return final_news[:2500] 

def generate_report(news_text, time_of_day):
    if not news_text:
        return "⚠️ கடந்த 12 மணி நேரத்தில் புதிய செய்திகள் எதுவும் இல்லை."

    # மிகச் சிறிய, குறுகிய Prompt (டோக்கன் குறைக்க)
    if time_of_day == "morning":
        prompt = f"""
        Analyze these news items and write a short Morning Market Report in TAMIL:
        {news_text}
        
        Rules:
        1. Do NOT invent numbers. Use "XX" if unsure.
        2. Explain the story: Global trend, Indian sentiment, and sector impacts.
        3. Use emojis. Keep it concise.
        """
    else:
        prompt = f"""
        Analyze these news items and write a short Evening Market Wrap in TAMIL:
        {news_text}
        
        Rules:
        1. Do NOT invent numbers. Use "XX" if unsure.
        2. Explain the story: Market mood, sector performance, and tomorrow's outlook.
        3. Use emojis. Keep it concise.
        """

    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a Financial Analyst writing in Tamil."},
                {"role": "user", "content": prompt}
            ],
            model="openai/gpt-oss-20b",
            temperature=0.5,
            max_tokens=1500 # அவுட்புட் அளவையும் குறைத்துள்ளோம்
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        return f"⚠️ AI எரர்: {e}"

async def run_bot():
    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist)
    current_hour = now.hour

    news_text = await fetch_recent_news()
    
    if current_hour < 12:
        report = generate_report(news_text, "morning")
        final_msg = f"☀️ **காலை சந்தை அறிக்கை**\n\n{report}\n\n_நேரம்: {now.strftime('%d-%m-%Y %I:%M %p')}_"
    else:
        report = generate_report(news_text, "evening")
        final_msg = f"🌙 **மாலை சந்தை அறிக்கை**\n\n{report}\n\n_நேரம்: {now.strftime('%d-%m-%Y %I:%M %p')}_"

    send_telegram_message(final_msg)

if __name__ == "__main__":
    import asyncio
    asyncio.run(run_bot())