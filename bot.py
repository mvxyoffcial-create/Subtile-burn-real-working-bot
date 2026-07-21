import os
import time
import asyncio
import math
from aiohttp import web
from pyrogram import Client, filters
from pyrogram.types import Message

# Credentials
API_ID = 36282056 
API_HASH = "3a948acece533f362b4c90b2b3c14b60"
BOT_TOKEN = "8737705568:AAGSjZlCgT6yrs6h045X88EEq63-iZLCiD4"
PORT = int(os.getenv("PORT", "8000"))

app = Client("hardsub_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
user_data = {}

# --- Health Check Web Server ---
async def health_check(request):
    return web.Response(text="OK", status=200)

async def start_web_server():
    server = web.Application()
    server.router.add_get("/", health_check)
    server.router.add_get("/health", health_check)
    runner = web.AppRunner(server)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    print(f"✅ Web server listening on port {PORT}")

# --- Helper Utilities ---
def human_bytes(size):
    if not size:
        return "0B"
    power = 2 ** 10
    n = 0
    dic_power_n = {0: 'B', 1: 'KB', 2: 'MB', 3: 'GB', 4: 'TB'}
    while size > power:
        size /= power
        n += 1
    return f"{size:.2f} {dic_power_n.get(n, 'GB')}"

def time_formatter(seconds: int) -> str:
    if seconds <= 0 or math.isnan(seconds):
        return "-"
    minutes, seconds = divmod(int(seconds), 60)
    hours, minutes = divmod(minutes, 60)
    if hours > 0:
        return f"{hours}h {minutes}m {seconds}s"
    if minutes > 0:
        return f"{minutes}m {seconds}s"
    return f"{seconds}s"

def generate_progress_text(title: str, current: float, total: float, start_time: float, username: str = "Zerodevss") -> str:
    now = time.time()
    elapsed = max(1, int(now - start_time))
    
    if total > 0:
        percentage = min((current / total) * 100, 100.0)
        speed = current / elapsed
        eta = (total - current) / speed if speed > 0 else 0
        
        filled_length = int(percentage // 10)
        bar = "■" * filled_length + "□" * (10 - filled_length)
        
        processed_str = human_bytes(current)
        total_str = human_bytes(total)
        speed_str = f"{human_bytes(speed)}/s"
        eta_str = time_formatter(eta)
    else:
        percentage = 0
        bar = "□" * 10
        processed_str = human_bytes(current)
        total_str = "Unknown"
        speed_str = "0B/s"
        eta_str = "-"

    text = (
        f"> **Task Running: 1/1**\n\n"
        f"**1. {title}:**\n"
        f"[{bar}] {percentage:.0f}%\n"
        f"**Processed:** {processed_str}\n"
        f"**Size:** {total_str}\n"
        f"**Speed:** {speed_str}\n"
        f"**ETA:** {eta_str}\n"
        f"**Elapsed:** {time_formatter(elapsed)}\n"
        f"**Upload:** Telegram\n"
        f"**Engine:** Pyrogram / FFmpeg\n"
        f"**User:** {username}"
    )
    return text

# --- Progress Callback for Download / Upload ---
def progress_bar(current, total, status_title, message, start_time):
    now = time.time()
    if not hasattr(progress_bar, "last_update"):
        progress_bar.last_update = 0

    if now - progress_bar.last_update > 3:
        progress_bar.last_update = now
        username = message.chat.first_name or "User"
        text = generate_progress_text(status_title, current, total, start_time, username)
        try:
            message.edit_text(text)
        except Exception:
            pass

# --- Helper: Get Duration ---
async def get_video_duration(file_path: str) -> float:
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        file_path
    ]
    process = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL
    )
    stdout, _ = await process.communicate()
    try:
        return float(stdout.decode().strip())
    except ValueError:
        return 0.0

# --- Bot Commands ---
@app.on_message(filters.command("start"))
async def start(client: Client, message: Message):
    await message.reply_text(
        "👋 **Fast Hardsub Bot Ready!**\n\n"
        "1. Send me a **Video File** (up to 2GB).\n"
        "2. Send me a **Subtitle File** (`.srt`, `.ass`, `.vtt`).\n"
        "3. Select `/convert x264` or `/convert x265`."
    )

@app.on_message(filters.video | filters.document)
async def handle_media(client: Client, message: Message):
    user_id = message.from_user.id
    doc = message.document or message.video
    if not doc:
        return

    file_name = doc.file_name or "file.mp4"
    
    # Handle Subtitles
    if file_name.lower().endswith((".srt", ".ass", ".vtt")):
        if user_id not in user_data or "video" not in user_data[user_id]:
            await message.reply_text("❌ Please send the video file first!")
            return
            
        status_msg = await message.reply_text("📥 Downloading subtitle file...")
        sub_ext = os.path.splitext(file_name)[1]
        sub_path = await message.download(file_name=f"sub_{user_id}{sub_ext}")
        user_data[user_id]["sub"] = sub_path
        
        await status_msg.edit_text(
            "⚙️ **Subtitle Received!**\n"
            "Select target codec:\n"
            "• `/convert x264` (Fastest)\n"
            "• `/convert x265` (Smaller size)"
        )
    # Handle Video
    else:
        status_msg = await message.reply_text("📥 Initializing download...")
        start_time = time.time()
        video_path = await message.download(
            file_name=f"vid_{user_id}.mp4",
            progress=progress_bar,
            progress_args=("Download", status_msg, start_time)
        )
        user_data[user_id] = {"video": video_path}
        await status_msg.edit_text("✅ **Video Downloaded!** Now send the subtitle file.")

@app.on_message(filters.command("convert"))
async def process_hardsub(client: Client, message: Message):
    user_id = message.from_user.id
    
    if user_id not in user_data or "video" not in user_data[user_id] or "sub" not in user_data[user_id]:
        await message.reply_text("❌ Missing video or subtitle file.")
        return

    args = message.text.split(" ")
    codec_choice = args[-1].lower() if len(args) > 1 else "x264"
    if codec_choice not in ["x264", "x265"]:
        await message.reply_text("❌ Use `/convert x264` or `/convert x265`")
        return

    video_file = user_data[user_id]["video"]
    sub_file = user_data[user_id]["sub"]
    output_file = f"out_{user_id}.mp4"
    encoder = "libx264" if codec_choice == "x264" else "libx265"

    total_duration = await get_video_duration(video_file)
    file_size = os.path.getsize(video_file) if os.path.exists(video_file) else 0
    escaped_sub_file = sub_file.replace("\\", "/").replace(":", "\\:").replace("'", "\\'")

    # Speed-optimized FFmpeg flags
    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-i", video_file,
        "-vf", f"subtitles={escaped_sub_file}",
        "-c:v", encoder,
        "-preset", "ultrafast",
        "-tune", "fastdecode",
        "-crf", "23",
        "-c:a", "copy",
        "-threads", "0",
        "-movflags", "+faststart",
        "-progress", "pipe:1",
        "-nostats",
        output_file
    ]

    status_msg = await message.reply_text("⚙️ **Starting Hardsub Engine...**")
    start_time = time.time()
    
    process = await asyncio.create_subprocess_exec(
        *ffmpeg_cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.DEVNULL
    )

    last_edit = time.time()
    username = message.chat.first_name or "User"

    while True:
        line = await process.stdout.readline()
        if not line:
            break
        
        line_str = line.decode('utf-8', errors='ignore').strip()
        
        if "out_time_ms=" in line_str and total_duration > 0:
            try:
                time_ms = float(line_str.split("=")[1])
                current_secs = time_ms / 1_000_000
                percent = min(current_secs / total_duration, 1.0)
                current_bytes = percent * file_size
                
                if time.time() - last_edit > 3:
                    last_edit = time.time()
                    text = generate_progress_text(
                        f"Hardsub ({codec_choice})",
                        current_bytes,
                        file_size,
                        start_time,
                        username
                    )
                    await status_msg.edit_text(text)
            except Exception:
                pass

    await process.wait()

    if not os.path.exists(output_file):
        await status_msg.edit_text("❌ Subtitle burn failed.")
        return

    await status_msg.edit_text("📤 Initializing upload...")
    start_time = time.time()
    
    await message.reply_video(
        video=output_file,
        caption=f"✅ **Hardsub Complete!**\nCodec: `{codec_choice}`",
        supports_streaming=True,
        progress=progress_bar,
        progress_args=("Upload", status_msg, start_time)
    )

    # Cleanup temporary local files
    for path in [video_file, sub_file, output_file]:
        if os.path.exists(path):
            os.remove(path)
    del user_data[user_id]

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(start_web_server())
    print("🚀 Web server started! Launching Pyrogram...")
    app.run()
