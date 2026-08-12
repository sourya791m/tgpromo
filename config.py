import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

# Channels / Group IDs
CHANNEL_1_ID = os.getenv("CHANNEL_1_ID", "-1003260353876")
CHANNEL_2_ID = os.getenv("CHANNEL_2_ID", "-1003971062167")
JOIN_REQUEST_CHANNEL_ID = os.getenv("JOIN_REQUEST_CHANNEL_ID", "-1004360222856")
BACKUP_GC_ID = os.getenv("BACKUP_GC_ID", "-1004331557651")

# Links
CHANNEL_1_LINK = os.getenv("CHANNEL_1_LINK", "https://t.me/TheNextLevelOfficial")
CHANNEL_2_LINK = os.getenv("CHANNEL_2_LINK", "https://t.me/+hYM-A7mpsV4xOTll")
JOIN_REQUEST_CHANNEL_LINK = os.getenv("JOIN_REQUEST_CHANNEL_LINK", "https://t.me/+QucLSiC1M8ZmODc1")
BACKUP_GC_LINK = os.getenv("BACKUP_GC_LINK", "https://t.me/+pPvJbytZmX80NGFl")

REQUIRED_REFERRALS_METHOD_1 = int(os.getenv("REQUIRED_REFERRALS_METHOD_1", "5"))
REQUIRED_REFERRALS_METHOD_2 = int(os.getenv("REQUIRED_REFERRALS_METHOD_2", "10"))
REQUIRED_REFERRALS_ALL = int(os.getenv("REQUIRED_REFERRALS_ALL", "15"))

SUPPORT_LINK = os.getenv("SUPPORT_LINK", "https://t.me/sourya791m_bot")

# Placeholder method texts – replace these later via admin panel
INITIAL_METHOD_TEXTS = {
    1: "🔴 BAN METHOD TEXT – YOUR TEXT HERE",
    2: "🟢 UNBAN METHOD TEXT – YOUR TEXT HERE",
    3: "❄️ UNFREEZE METHOD TEXT – YOUR TEXT HERE",
    4: "♾️ PERMANENT LIMIT REMOVE TEXT – YOUR TEXT HERE",
    5: "⚠️ LIMIT REMOVE TEXT – YOUR TEXT HERE",
    6: "🚨 SCAM REPORT TEXT – YOUR TEXT HERE",
}