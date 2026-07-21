import os

# --- Telegram API & Bot Setup ---
API_ID = int(os.environ.get("API_ID", "1234567"))
API_HASH = os.environ.get("API_HASH", "your_api_hash_here")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "your_bot_token_here")

# Pyrogram User Session String (Required for downloading/uploading up to 4GB files)
STRING_SESSION = os.environ.get("STRING_SESSION", "")

# --- Database Setup ---
DB_URL = os.environ.get(
    "DB_URL",
    "mongodb+srv://cloudnestoffcail_db_user:Venura8907@cluster0.hjqkg75.mongodb.net/?appName=Cluster0"
)
DB_NAME = os.environ.get("DB_NAME", "Cluster0")

# --- Admins & Support ---
ADMINS = [int(x) for x in os.environ.get("ADMINS", "123456789").split()]
PREMIUM_LOGS = int(os.environ.get("PREMIUM_LOGS", "-1001234567890"))
SUPPORT_CHAT = os.environ.get("SUPPORT_CHAT", "https://t.me/spideyoffcail")

# --- Force Subscribe Channels ---
AUTH_CHANNELS = [
    "spideyoffcail",
    "mvxyoffcail"
]

# --- UI Assets & Texts ---
WELCOME_STICKER = "CAACAgIAAxkBAAEQZtFpgEdROhGouBVFD3e0K-YjmVHwsgACtCMAAphLKUjeub7NKlvk2TgE"
PICS_URL = [
    "https://api.aniwallpaper.workers.dev/random?type=girl"
]

SUBSCRIPTION_IMG = "https://i.ibb.co/gMrpRQWP/photo-2025-07-09-05-21-32-7524948058832896004.jpg"
PLAN_IMG = "https://graph.org/file/86da2027469565b5873d6.jpg"

# Telegram Stars Payment Packages (Stars : Duration)
STAR_PREMIUM_PLANS = {
    100: "1 month",
    500: "6 months",
    900: "1 year"
}

START_TXT = """<b>ʜᴇʏ, {}! 👋</b>

ɪ'ᴍ ᴀɴ <b>ʜᴀʀᴅsᴜʙ ᴍᴇʀɢᴇ ʙᴏᴛ</b> 🎬
ɪ ᴄᴀɴ ᴍᴇʀɢᴇ ʜᴀʀᴅ sᴜʙᴛɪᴛʟᴇs ɪɴᴛᴏ ᴠɪᴅᴇᴏs ᴏғ ᴀɴʏ ʟᴀɴɢᴜᴀɢᴇ 🌍

📤 Sᴇɴᴅ ᴍᴇ ᴀ ᴠɪᴅᴇᴏ + sᴜʙᴛɪᴛʟᴇ ғɪʟᴇ
⚡ I'ʟʟ ᴍᴇʀɢᴇ ᴛʜᴇᴍ ᴘᴇʀғᴇᴄᴛʟʏ!
🚀 Uᴘ ᴛᴏ 4GB ғᴏʀ ᴘʀᴇᴍɪᴜᴍ ᴜsᴇʀs

👨‍💻 Dᴇᴠᴇʟᴏᴘᴇʀ: @Venuboyy"""

HELP_TXT = """<b>✨ Hᴏᴡ Tᴏ Usᴇ HᴀʀᴅSᴜʙ Mᴇʀɢᴇ Bᴏᴛ ✨</b>

1️⃣ <b>Sᴇɴᴅ Vɪᴅᴇᴏ:</b>
   Sᴇɴᴅ ᴛʜᴇ ᴠɪᴅᴇᴏ ғɪʟᴇ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ᴍᴇʀɢᴇ 🎬

2️⃣ <b>Sᴇɴᴅ Sᴜʙᴛɪᴛʟᴇ:</b>
   Sᴇɴᴅ ᴛʜᴇ sᴜʙᴛɪᴛʟᴇ ғɪʟᴇ (.sʀᴛ, .ᴀss, ᴇᴛᴄ.) 📝

3️⃣ <b>Mᴇʀɢᴇ:</b>
   Bᴏᴛ ᴡɪʟʟ ᴀᴜᴛᴏᴍᴀᴛɪᴄᴀʟʟʏ ᴍᴇʀɢᴇ ᴛʜᴇᴍ ⚡

4️⃣ <b>Dᴏᴡɴʟᴏᴀᴅ:</b>
   Gᴇᴛ ʏᴏᴜʀ ᴍᴇʀɢᴇᴅ ᴠɪᴅᴇᴏ ᴡɪᴛʜ ʜᴀʀᴅ sᴜʙᴛɪᴛʟᴇs 📥

📌 <b>Fᴇᴀᴛᴜʀᴇs:</b>
➤ Sᴜᴘᴘᴏʀᴛs ᴀʟʟ ʟᴀɴɢᴜᴀɢᴇs 🌐
➤ Fʀᴇᴇ: ᴜᴘ ᴛᴏ 2GB | Pʀᴇᴍɪᴜᴍ: ᴜᴘ ᴛᴏ 4GB 💎
➤ Fᴀsᴛ ᴘʀᴏᴄᴇssɪɴɢ ⚡
➤ 100% sᴇᴄᴜʀᴇ & ᴘʀɪᴠᴀᴛᴇ 🔒

<b>🚀 Sᴛᴀʀᴛ ᴍᴇʀɢɪɴɢ ɴᴏᴡ!</b>"""

ABOUT_TXT = """<b>╭────[ Mʏ Dᴇᴛᴀɪʟs ]────⍟
├⍟ Nᴀᴍᴇ : HᴀʀᴅSᴜʙ Mᴇʀɢᴇ Bᴏᴛ
├⍟ Dᴇᴠᴇʟᴏᴘᴇʀ : <a href='https://t.me/Venuboyy'>Vᴇɴᴜʙᴏʏʏ</a> 👨‍💻
├⍟ Lɪʙʀᴀʀʏ : <a href='https://github.com/pyrogram/pyrogram'>Pʏʀᴏɢʀᴀᴍ</a> 📚
├⍟ Lᴀɴɢᴜᴀɢᴇ : <a href='https://www.python.org/'>Pʏᴛʜᴏɴ 𝟹</a> 🐍
├⍟ Dᴀᴛᴀʙᴀsᴇ : <a href='https://www.mongodb.com/'>MᴏɴɢᴏDB</a> 🍃
├⍟ Fᴇᴀᴛᴜʀᴇ : Hᴀʀᴅ Sᴜʙᴛɪᴛʟᴇ Mᴇʀɢᴇ 🔤
├⍟ Mᴀx Sɪᴢᴇ : 4GB (Pʀᴇᴍɪᴜᴍ) 💎
├⍟ Lᴀɴɢᴜᴀɢᴇs : Aʟʟ Lᴀɴɢᴜᴀɢᴇs 🌍
╰───────────────⍟</b>"""

PREMIUM_END_TEXT = "👋 Hey {}, your Premium subscription has expired."
BPREMIUM_TXT = "<b>💎 Upgrade to Premium to enjoy 4GB uploads, unlimited daily merges, and priority processing!</b>"
