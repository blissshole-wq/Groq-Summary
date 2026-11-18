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

# உங்கள் Source சேனல்களின் ID-கள்
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
            messages = await tele_client.get_messages(channel, limit=15) # 15 மெசேஜ்கள் வரை எடுக்கலாம்
            for msg in messages:
                if msg.date.astimezone(ist) > time_limit and msg.text:
                    all_news.append(msg.text)
        except Exception as e:
            print(f"❌ {channel} படிக்க முடியவில்லை: {e}")
            
    await tele_client.disconnect()
    return "\n---\n".join(all_news)

def generate_report(news_text, time_of_day):
    if not news_text:
        return "⚠️ கடந்த 12 மணி நேரத்தில் புதிய செய்திகள் எதுவும் இல்லை."

    # நீங்கள் கேட்ட அந்த விரிவான, ஆழமான பகுப்பாய்வு Prompt இதோ 👇
    if time_of_day == "morning":
        prompt = f"""
        Act as a Top Wall Street and Dalal Street Financial Analyst.
        Analyze the following raw news collected from various channels in the last 12 hours:
        {news_text}
        
        Write a comprehensive Morning Market Report in TAMIL based ONLY on these news items.
        
        Structure it exactly like this:
        1. 🌍 Global Market Overnight Narrative (US/Asian market trends & major news).
        2. 🇮🇳 Indian Market Pre-Open Sentiment (Overall mood, FII/DII general activity without specific numbers).
        3. 📰 Key News & Why it Matters (Explain the impact of 2-3 major world/India news on specific sectors like Tech, Pharma, Auto).
        4. 🎯 Expert View: What is the general market consensus?
        5. 💡 Strategy of the Day: Actionable advice based on the news.
        
        CRITICAL RULES:
        - DO NOT INVENT OR IMAGINE ANY SPECIFIC NUMBERS. Focus entirely on the NARRATIVE.
        - Explain the STORY: "Why did this happen? How does this news affect specific stocks?"
        - Use professional Tamil with clear English financial terms in brackets.
        - Use heavy emojis for readability.
        """
    else:
        prompt = f"""
        Act as a Top Wall Street and Dalal Street Financial Analyst.
        Analyze the following raw news collected from various channels in the last 12 hours:
        {news_text}
        
        Write a comprehensive Evening Market Wrap-Up Report in TAMIL based ONLY on these news items.
        
        Structure it exactly like this:
        1. 📉 Today's Indian Market Story (Overall market sentiment: Was it a bullish or bearish day based on the news?).
        2. 📈 Sectoral Performance Narrative (Which sectors outperformed and WHY?).
        3. 🌍 Global Cues for Tomorrow (What happened globally that will affect India tomorrow).
        4. 📊 Market Dynamics (General FII/DII buying/selling trends without specific numbers).
        5. 💡 Expert Analysis: What is the main takeaway from today?
        
        CRITICAL RULES:
        - DO NOT INVENT OR IMAGINE ANY SPECIFIC NUMBERS.
        - Connect the NEWS with the sector performance. Provide a story-like narrative.
        - Use professional Tamil with clear English financial terms.
        - Use heavy emojis for readability.
        """

    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a highly experienced Financial Analyst who writes detailed, story-driven reports in Tamil. You never hallucinate numbers."},
                {"role": "user", "content": prompt}
            ],
            model="openai/gpt-oss-20b",
            temperature=0.6,
            max_tokens=2500 
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
        print("☀️ காலை அறிக்கை உருவாக்கப்படுகிறது...")
        report = generate_report(news_text, "morning")
        final_msg = f"☀️ **காலை சந்தை அறிக்கை (Morning Report)**\n\n{report}\n\n_நேரம்: {now.strftime('%d-%m-%Y %I:%M %p')}_"
    else:
        print("🌙 இரவு அறிக்கை உருவாக்கப்படுகிறது...")
        report = generate_report(news_text, "evening")
        final_msg = f"🌙 **மாலை சந்தை அறிக்கை (Evening Wrap)**\n\n{report}\n\n_நேரம்: {now.strftime('%d-%m-%Y %I:%M %p')}_"

    send_telegram_message(final_msg)

if __name__ == "__main__":
    import asyncio
    asyncio.run(run_bot())