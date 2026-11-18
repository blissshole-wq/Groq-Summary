import os
import pytz
from datetime import datetime
import requests
from groq import Groq

# ரகசியங்களை (Secrets) இங்கே படிக்கிறோம்
TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

# Groq AI செட் அப்
client = Groq(api_key=GROQ_API_KEY)

def send_telegram_message(message):
    # டெலிகிராம் மெசேஜ் அளவு வரம்பு 4096 எழுத்துக்கள். அதற்கு மேல் இருந்தால் பிரித்து அனுப்ப வேண்டும்.
    if len(message) > 4000:
        messages = [message[i:i+4000] for i in range(0, len(message), 4000)]
        for msg in messages:
            url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
            payload = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}
            requests.post(url, json=payload)
    else:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
        response = requests.post(url, json=payload)
        print("Status:", response.status_code, response.text)

def get_ai_summary(time_of_day):
    # நீங்கள் கேட்டது போலவே விரிவான, காரணங்களை விளக்கும் Prompt
    if time_of_day == "morning":
        prompt = """
        Act as a Top Wall Street and Dalal Street Financial Analyst.
        Write a comprehensive Morning Market Report in TAMIL. 
        
        Structure it exactly like this:
        1. 🌍 Global Market Overnight Summary (US, Asian markets closing data).
        2. 🇮🇳 Indian Market Pre-Open Scenario (GIFT Nifty, SGX Nifty, FII/DII data).
        3. 📰 Key News & Why it Matters (Explain the impact of 2-3 major world/India news on specific sectors like Tech, Pharma, Auto).
        4. 🎯 Expert View: Mention what top market experts are saying about today's trend.
        5. 💡 Strategy of the Day: Give a short, actionable trading idea.
        
        RULES:
        - Do NOT just list numbers. Explain the STORY: "Why did the market go up or down? How does this number affect the common man or specific stocks?"
        - Use professional Tamil with clear English financial terms in brackets (e.g., வெளிநாட்டு முதலீட்டாளர்கள் (FII)).
        - Use heavy emojis for readability.
        """
    else:
        prompt = """
        Act as a Top Wall Street and Dalal Street Financial Analyst.
        Write a comprehensive Evening Market Wrap-Up Report in TAMIL.
        
        Structure it exactly like this:
        1. 📉 Today's Indian Market Recap (Sensex, Nifty close, Top Gainers & Losers).
        2. 📈 Sectoral Story (Which sector performed well and WHY? e.g., IT sector fell due to US recession fears).
        3. 🌍 Global Cues for Tomorrow (What happened in the US/Europe that will affect India tomorrow).
        4. 📊 FII/DII Activity Explained (Explain the buying/selling data clearly).
        5. 💡 Expert Analysis: How did the market start in the morning vs how it ended in the evening? What is the main takeaway from today?
        
        RULES:
        - Connect the NUMBERS with the NEWS. For example: "Reliance fell by 2% because of X news."
        - Provide a story-like narrative, not just a boring data dump.
        - Use professional Tamil with clear English financial terms.
        - Use heavy emojis for readability.
        """

    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a highly experienced Financial Analyst who writes detailed, story-driven reports in Tamil."},
                {"role": "user", "content": prompt}
            ],
            model="openai/gpt-oss-20b",
            temperature=0.6,
            max_tokens=2500 # விரிவான அறிக்கைக்கு அதிக டோக்கன்கள் தேவை
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        print(f"⚠️ Groq AI Error: {e}")
        return "⚠️ AI மூலம் செய்தியை உருவாக்க முடியவில்லை."

def run_bot():
    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist)
    current_hour = now.hour

    print(f"⏰ தற்போதைய நேரம்: {now.strftime('%I:%M %p')}")

    if current_hour < 12:
        print("☀️ காலை சந்தை அறிக்கை உருவாக்கப்படுகிறது...")
        ai_message = get_ai_summary("morning")
        final_msg = f"☀️ **காலை சந்தை அறிக்கை (Morning Market Report)**\n\n{ai_message}\n\n_நேரம்: {now.strftime('%d-%m-%Y %I:%M %p')}_"
    
    else:
        print("🌙 இரவு சந்தை அறிக்கை உருவாக்கப்படுகிறது...")
        ai_message = get_ai_summary("evening")
        final_msg = f"🌙 **மாலை சந்தை நிலவரம் (Evening Market Wrap)**\n\n{ai_message}\n\n_நேரம்: {now.strftime('%d-%m-%Y %I:%M %p')}_"

    send_telegram_message(final_msg)

if __name__ == "__main__":
    run_bot()