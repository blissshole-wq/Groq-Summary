import asyncio
import os
import sqlite3
from datetime import datetime, timedelta, timezone
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import subprocess

from telethon import TelegramClient
from telethon.sessions import StringSession

DB_PATH = os.environ.get("NEWS_DB_PATH", "news_database.db")
API_ID = int(os.environ.get("API_ID", "0"))
API_HASH = os.environ.get("API_HASH", "")
STRING_SESSION = os.environ.get("STRING_SESSION", "")

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

# --- 1. டேட்டாபேஸ் செட்-அப் ---
def setup_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS news
                        (id INTEGER PRIMARY KEY AUTOINCREMENT,
                         headline TEXT NOT NULL,
                         source TEXT,
                         time_added TIMESTAMP NOT NULL)''')

def save_news(headline, source, saved_at):
    with sqlite3.connect(DB_PATH) as conn:
        existing = conn.execute(
            "SELECT 1 FROM news WHERE headline = ? AND time_added >= ? LIMIT 1",
            (headline, (saved_at - timedelta(hours=12)).isoformat(" ")),
        ).fetchone()
        if not existing:
            conn.execute(
                "INSERT INTO news (headline, source, time_added) VALUES (?, ?, ?)",
                (headline, source, saved_at.isoformat(" ")),
            )

# --- 2. நியூஸ் சேகரிப்பு ---
async def collect_news():
    if API_ID == 0 or not API_HASH or not STRING_SESSION:
        raise RuntimeError("Missing Telethon secrets: API_ID, API_HASH, or STRING_SESSION")

    setup_db()
    tele_client = TelegramClient(StringSession(STRING_SESSION), API_ID, API_HASH)
    time_limit = datetime.now(timezone.utc) - timedelta(hours=12)
    saved = 0

    try:
        await tele_client.start()
        for channel in SOURCE_CHANNELS:
            try:
                messages = await tele_client.get_messages(channel, limit=5)
                for message in messages:
                    if not message.text or not message.date:
                        continue
                    message_date = message.date.astimezone(timezone.utc)
                    if message_date < time_limit:
                        continue

                    headline = " ".join(message.text.split())[:500]
                    source = str(getattr(message.chat, "title", channel))
                    
                    # டேட்டாபேஸ்ல இருக்கிற நியூஸ் எண்ணிக்கையை செக் பண்றோம்
                    with sqlite3.connect(DB_PATH) as conn:
                        before = conn.execute("SELECT count(*) FROM news").fetchone()[0]
                    
                    save_news(headline, source, message_date)
                    
                    with sqlite3.connect(DB_PATH) as conn:
                        after = conn.execute("SELECT count(*) FROM news").fetchone()[0]
                    
                    saved += after - before
            except Exception as exc:
                print(f"Channel {channel} error: {exc}")
    finally:
        await tele_client.disconnect()

    print(f"Saved {saved} recent news items")

# --- 3. Scheduler ஃபங்க்ஷன்கள் ---
def run_summary_script():
    print("⏰ Running AI Summary...")
    if os.path.exists("summary.py"):
        print("✅ summary.py found! Running...")
        subprocess.run(["python", "summary.py"])
    else:
        print("❌ ERROR: summary.py NOT FOUND in Render!")

def run_scanner_script():
    print("⏰ Running Stock Scanner...")
    if os.path.exists("scanner.py"):
        print("✅ scanner.py found! Running...")
        subprocess.run(["python", "scanner.py"])
    else:
        print("❌ ERROR: scanner.py NOT FOUND in Render!")

# --- 4. மெயின் எக்ஸிகியூஷன் (Scheduler செட்-அப்) ---
async def main():
    # முதல்ல நியூஸை சேகரிக்கிறோம்
    await collect_news()

    # Scheduler-ஐ செட் பண்றோம்
    scheduler = AsyncIOScheduler()
    
    # காலை 8:00 AM IST (UTC 2:30) - Summary
    scheduler.add_job(run_summary_script, 'cron', hour=2, minute=30) 
    # மதியம் 2:00 PM IST (UTC 8:30) - Scanner
    scheduler.add_job(run_scanner_script, 'cron', hour=8, minute=30)
    # மாலை 5:00 PM IST (UTC 11:30) - Summary
    scheduler.add_job(run_summary_script, 'cron', hour=11, minute=30)

    scheduler.start()
    print("✅ Scheduler Started Successfully!")

    # ரெண்டர் சர்வர் ஸ்லீப் ஆகாம இருக்க, இந்த லூப் எப்பவும் ரன் ஆகிட்டே இருக்கும்
    while True:
        await asyncio.sleep(3600) # ஒரு மணி நேரத்துக்கு ஒரு முறை வெயிட் பண்ணும்

if __name__ == "__main__":
    asyncio.run(main())