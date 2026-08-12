import aiosqlite
from datetime import datetime
import json
from config import (
    CHANNEL_1_ID, CHANNEL_2_ID, JOIN_REQUEST_CHANNEL_ID, BACKUP_GC_ID,
    CHANNEL_1_LINK, CHANNEL_2_LINK, JOIN_REQUEST_CHANNEL_LINK, BACKUP_GC_LINK,
    REQUIRED_REFERRALS_METHOD_1, REQUIRED_REFERRALS_METHOD_2, REQUIRED_REFERRALS_ALL,
    SUPPORT_LINK
)

DB_PATH = "bot_data.db"

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                referrer_id INTEGER,
                referral_count INTEGER DEFAULT 0,
                unlocked_methods TEXT DEFAULT '[]',
                is_blocked INTEGER DEFAULT 0,
                registered_date TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS referrals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                referrer_id INTEGER,
                referred_user_id INTEGER,
                timestamp TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS method_texts (
                method_id INTEGER PRIMARY KEY,
                text TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS account_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                username TEXT,
                first_name TEXT,
                referral_count INTEGER,
                request_date TEXT,
                status TEXT DEFAULT 'pending',
                admin_message_id INTEGER
            )
        """)
        # Insert initial method texts if empty
        cursor = await db.execute("SELECT COUNT(*) FROM method_texts")
        count = (await cursor.fetchone())[0]
        if count == 0:
            from config import INITIAL_METHOD_TEXTS
            for mid, text in INITIAL_METHOD_TEXTS.items():
                await db.execute("INSERT OR IGNORE INTO method_texts (method_id, text) VALUES (?, ?)", (mid, text))
        # Insert default settings
        defaults = {
            "channel_1_id": CHANNEL_1_ID,
            "channel_2_id": CHANNEL_2_ID,
            "join_request_channel_id": JOIN_REQUEST_CHANNEL_ID,
            "backup_gc_id": BACKUP_GC_ID,
            "channel_1_link": CHANNEL_1_LINK,
            "channel_2_link": CHANNEL_2_LINK,
            "join_request_channel_link": JOIN_REQUEST_CHANNEL_LINK,
            "backup_gc_link": BACKUP_GC_LINK,
            "required_refs_method_1": str(REQUIRED_REFERRALS_METHOD_1),
            "required_refs_method_2": str(REQUIRED_REFERRALS_METHOD_2),
            "required_refs_all": str(REQUIRED_REFERRALS_ALL),
            "support_link": SUPPORT_LINK,
        }
        for key, val in defaults.items():
            await db.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (key, val))
        await db.commit()

# --- User functions ---
async def get_user(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        user = await cursor.fetchone()
        if user is None:
            now = datetime.utcnow().isoformat()
            await db.execute("INSERT INTO users (user_id, registered_date) VALUES (?, ?)", (user_id, now))
            await db.commit()
            cursor = await db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            user = await cursor.fetchone()
        return dict(user)

async def set_username_first_name(user_id: int, username: str, first_name: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET username = ?, first_name = ? WHERE user_id = ?", (username, first_name, user_id))
        await db.commit()

async def set_referrer(user_id: int, referrer_id: int) -> bool:
    if user_id == referrer_id:
        return False
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT referrer_id FROM users WHERE user_id = ?", (user_id,))
        row = await cursor.fetchone()
        if row and row[0] is not None:
            return False
        await db.execute("UPDATE users SET referrer_id = ? WHERE user_id = ?", (referrer_id, user_id))
        await db.execute("INSERT INTO referrals (referrer_id, referred_user_id, timestamp) VALUES (?, ?, ?)",
                         (referrer_id, user_id, datetime.utcnow().isoformat()))
        await db.execute("UPDATE users SET referral_count = referral_count + 1 WHERE user_id = ?", (referrer_id,))
        await db.commit()
        return True

async def get_referral_count(user_id: int) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT referral_count FROM users WHERE user_id = ?", (user_id,))
        row = await cursor.fetchone()
        return row[0] if row else 0

async def get_unlocked_methods(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT unlocked_methods FROM users WHERE user_id = ?", (user_id,))
        row = await cursor.fetchone()
        if row:
            return json.loads(row[0])
        return []

async def save_unlocked_methods(user_id: int, methods: list):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET unlocked_methods = ? WHERE user_id = ?", (json.dumps(methods), user_id))
        await db.commit()

async def unlock_method(user_id: int, method_index: int):
    methods = await get_unlocked_methods(user_id)
    if method_index not in methods:
        methods.append(method_index)
        await save_unlocked_methods(user_id, methods)

async def is_method_unlocked(user_id: int, method_index: int) -> bool:
    methods = await get_unlocked_methods(user_id)
    return method_index in methods

# --- Method texts ---
async def get_method_text(method_id: int) -> str:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT text FROM method_texts WHERE method_id = ?", (method_id,))
        row = await cursor.fetchone()
        return row[0] if row else "Method text not available."

async def set_method_text(method_id: int, text: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE method_texts SET text = ? WHERE method_id = ?", (text, method_id))
        await db.commit()

# --- Settings ---
async def get_setting(key: str) -> str:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = await cursor.fetchone()
        return row[0] if row else None

async def set_setting(key: str, value: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
        await db.commit()

# --- Account requests ---
async def add_account_request(user_id: int, username: str, first_name: str, referral_count: int) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO account_requests (user_id, username, first_name, referral_count, request_date, status) VALUES (?, ?, ?, ?, ?, 'pending')",
            (user_id, username, first_name, referral_count, datetime.utcnow().isoformat())
        )
        await db.commit()
        return cursor.lastrowid

async def update_request_status(request_id: int, status: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE account_requests SET status = ? WHERE id = ?", (status, request_id))
        await db.commit()

async def get_request_by_id(request_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM account_requests WHERE id = ?", (request_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None

async def get_pending_requests():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM account_requests WHERE status = 'pending'")
        return [dict(row) for row in await cursor.fetchall()]

# --- Admin helpers ---
async def get_all_users():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM users")
        return [dict(row) for row in await cursor.fetchall()]

async def block_user(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET is_blocked = 1 WHERE user_id = ?", (user_id,))
        await db.commit()

async def unblock_user(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET is_blocked = 0 WHERE user_id = ?", (user_id,))
        await db.commit()

async def is_blocked(user_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT is_blocked FROM users WHERE user_id = ?", (user_id,))
        row = await cursor.fetchone()
        return bool(row[0]) if row else False

async def get_statistics():
    async with aiosqlite.connect(DB_PATH) as db:
        total_users = (await (await db.execute("SELECT COUNT(*) FROM users")).fetchone())[0]
        total_refs = (await (await db.execute("SELECT COUNT(*) FROM referrals")).fetchone())[0]
        total_requests = (await (await db.execute("SELECT COUNT(*) FROM account_requests")).fetchone())[0]
        pending_requests = (await (await db.execute("SELECT COUNT(*) FROM account_requests WHERE status='pending'")).fetchone())[0]
        return {
            "total_users": total_users,
            "total_referrals": total_refs,
            "total_requests": total_requests,
            "pending_requests": pending_requests,
        }