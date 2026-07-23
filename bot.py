import os
import time
import asyncio
from datetime import datetime, timedelta
from aiohttp import web
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from collections import defaultdict

# Credentials
API_ID = 36282056 
API_HASH = "3a948acece533f362b4c90b2b3c14b60"
BOT_TOKEN = "8737705568:AAGSjZlCgT6yrs6h045X88EEq63-iZLCiD4"
PORT = int(os.getenv("PORT", "8000"))

app = Client("hardsub_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
user_data = {}
active_tasks = defaultdict(dict)  # Track active tasks per user

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

# --- Helper: Video Duration ---
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

# --- Progress Bar Visualizer ---
def create_progress_bar(percentage: float) -> str:
    """Create visual progress bar"""
    filled = int(percentage / 5)
    bar = "█" * filled + "░" * (20 - filled)
    return f"[{bar}] {percentage:.1f}%"

# --- Calculate ETA ---
def calculate_eta(processed: float, total: float, elapsed: float) -> str:
    """Calculate estimated time remaining"""
    if processed == 0 or elapsed == 0:
        return "-"
    
    speed = processed / elapsed
    remaining_bytes = total - processed
    remaining_seconds = remaining_bytes / speed if speed > 0 else 0
    
    if remaining_seconds < 60:
        return f"{int(remaining_seconds)}s"
    elif remaining_seconds < 3600:
        return f"{int(remaining_seconds // 60)}m"
    else:
        return f"{int(remaining_seconds // 3600)}h"

# --- Format Bytes ---
def format_bytes(bytes_val: float) -> str:
    """Format bytes to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_val < 1024.0:
            return f"{bytes_val:.1f}{unit}"
        bytes_val /= 1024.0
    return f"{bytes_val:.1f}TB"

# --- TDLib-Style Progress Message ---
async def update_progress_message(
    message: Message,
    stage: str,
    current: float,
    total: float,
    start_time: float,
    task_id: int = None,
    total_tasks: int = 20
):
    """Update message with detailed progress statistics"""
    elapsed = time.time() - start_time
    percentage = (current / total * 100) if total > 0 else 0
    speed = (current / elapsed) if elapsed > 0 else 0
    eta = calculate_eta(current, total, elapsed)
    
    progress_bar = create_progress_bar(min(percentage, 100))
    
    # Format the message similar to the screenshot
    status_text = f"""
🚀 **Hardsub Bot (4GB+)**
Scary Movie (2026) 720p 10bit...

⏱️ Task Running: {task_id or 1}/20

1️⃣ **{stage}:**
{progress_bar} {percentage:.0f}%

📊 **Statistics:**
├ Processed: {format_bytes(current)}
├ Size: {format_bytes(total)}
├ Speed: {format_bytes(speed)}/s
├ ETA: {eta}
└ Elapsed: {time.strftime('%M:%S', time.gmtime(elapsed))}

📤 Upload: Telegram
🔧 Engine: TDLib v1.8.66
👤 Bot: Hardsub Encoder (FFmpeg)
"""
    
    try:
        await message.edit_text(status_text)
    except Exception as e:
        print(f"Error updating message: {e}")

# --- Bot Commands ---
@app.on_message(filters.command("start"))
async def start(client: Client, message: Message):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📖 How to Use", callback_data="help")]
    ])
    
    await message.reply_text(
        "👋 **Hardsub Bot (4GB+) Ready!**\n\n"
        "🚀 **Features:**\n"
        "✅ Unlimited file size support\n"
        "✅ Real-time progress tracking\n"
        "✅ Crystal-clear subtitle rendering\n"
        "✅ Ultra-fast encoding\n\n"
        "📝 **How to use:**\n"
        "1️⃣ Send a video file\n"
        "2️⃣ Send subtitle file (.srt, .ass, .vtt)\n"
        "3️⃣ Use `/convert x264` or `/convert x265`\n\n"
        "⚡ Powered by FFmpeg + TDLib",
        reply_markup=keyboard
    )

@app.on_message(filters.video | filters.document)
async def handle_media(client: Client, message: Message):
    user_id = message.from_user.id
    doc = message.document or message.video
    if not doc:
        return

    file_name = doc.file_name or "file.mp4"
    file_size = doc.file_size or 0
    
    if file_name.lower().endswith((".srt", ".ass", ".vtt")):
        if user_id not in user_data or "video" not in user_data[user_id]:
            await message.reply_text("❌ Please send the video file first!")
            return
            
        status_msg = await message.reply_text("📥 **Downloading subtitle file...**\n[░░░░░░░░░░░░░░░░░░░░] 0%")
        
        sub_ext = os.path.splitext(file_name)[1]
        sub_path = await message.download(file_name=f"sub_{user_id}{sub_ext}")
        user_data[user_id]["sub"] = sub_path
        
        await status_msg.edit_text(
            "⚙️ **Subtitle Received!** ✅\n\n"
            "📽️ **Select encoding:**\n"
            "• `/convert x264` (faster)\n"
            "• `/convert x265` (smaller)\n\n"
            "🎬 Ready to hardsub!"
        )
    else:
        status_msg = await message.reply_text(
            f"📥 **Downloading: {file_name}**\n"
            f"💾 Size: {format_bytes(file_size)}\n"
            "[░░░░░░░░░░░░░░░░░░░░] 0%"
        )
        
        start_time = time.time()
        
        async def progress_callback(current, total):
            await update_progress_message(
                status_msg, "Download", current, total, start_time, 1, 20
            )
        
        video_path = await message.download(
            file_name=f"vid_{user_id}.mp4",
            progress=progress_callback
        )
        
        user_data[user_id] = {"video": video_path}
        
        await status_msg.edit_text(
            f"✅ **Video Downloaded!**\n\n"
            f"📊 File: {file_name}\n"
            f"💾 Size: {format_bytes(file_size)}\n\n"
            f"📝 Now send the **subtitle file** (.srt, .ass, or .vtt)"
        )

@app.on_message(filters.command("convert"))
async def process_hardsub(client: Client, message: Message):
    user_id = message.from_user.id
    
    if user_id not in user_data or "video" not in user_data[user_id] or "sub" not in user_data[user_id]:
        await message.reply_text("❌ Missing video or subtitle file. Please start over.")
        return

    args = message.text.split(" ")
    codec_choice = args[-1].lower() if len(args) > 1 else "x264"
    if codec_choice not in ["x264", "x265"]:
        await message.reply_text("❌ Use `/convert x264` or `/convert x265`")
        return

    video_file = user_data[user_id]["video"]
    sub_file = user_data[user_id]["sub"]
    output_file = f"out_{user_id}.mp4"
    
    # Codec selection with optimal settings
    if codec_choice == "x265":
        encoder = "libx265"
        video_args = ["-c:v", encoder, "-preset", "ultrafast", "-x265-params", "log-level=error", "-crf", "22"]
    else:
        encoder = "libx264"
        video_args = ["-c:v", encoder, "-preset", "ultrafast", "-crf", "21"]

    total_duration = await get_video_duration(video_file)
    video_size = os.path.getsize(video_file)
    
    # Escape subtitle path
    escaped_sub_file = sub_file.replace("\\", "/").replace(":", "\\:").replace("'", "\\'")
    
    # Crystal-clear subtitle filter
    subtitle_filter = (
        f"subtitles={escaped_sub_file}:"
        f"force_style='FontName=Arial,FontSize=24,PrimaryColour=&HFFFFFF,OutlineColour=&H000000,BorderStyle=3,Outline=2,Shadow=1,Alignment=2'"
    )

    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-i", video_file,
        "-vf", subtitle_filter,
        *video_args,
        "-c:a", "aac",
        "-b:a", "128k",
        "-threads", "0",
        "-movflags", "+faststart",
        "-progress", "pipe:1",
        "-nostats",
        output_file
    ]

    status_msg = await message.reply_text(
        f"🎬 **Hardsub Processing Started**\n\n"
        f"📹 Video: Scary Movie (2026) 720p\n"
        f"💾 Size: {format_bytes(video_size)}\n"
        f"🔧 Codec: {codec_choice.upper()}\n\n"
        f"⏱️ Task Running: 1/20\n\n"
        f"2️⃣ **Processing:**\n"
        f"[░░░░░░░░░░░░░░░░░░░░] 0%"
    )
    
    active_tasks[user_id] = {
        "status": "encoding",
        "message_id": status_msg.message_id,
        "start_time": time.time()
    }
    
    process = await asyncio.create_subprocess_exec(
        *ffmpeg_cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.DEVNULL
    )

    last_edit = time.time()
    start_time = time.time()

    while True:
        line = await process.stdout.readline()
        if not line:
            break
        
        line_str = line.decode('utf-8', errors='ignore').strip()
        
        if "out_time_ms=" in line_str and total_duration > 0:
            try:
                time_ms = float(line_str.split("=")[1])
                current_secs = time_ms / 1_000_000
                percent = min((current_secs / total_duration) * 100, 100.0)
                
                if time.time() - last_edit > 2:
                    last_edit = time.time()
                    await update_progress_message(
                        status_msg, "Processing", current_secs, total_duration, start_time, 2, 20
                    )
            except Exception:
                pass

    await process.wait()

    if not os.path.exists(output_file):
        await status_msg.edit_text("❌ **Encoding Failed!**\nPlease try again.")
        return

    output_size = os.path.getsize(output_file)
    
    await status_msg.edit_text(
        f"✅ **Encoding Complete!**\n\n"
        f"📊 Output: {format_bytes(output_size)}\n"
        f"⏱️ Task Running: 2/20\n\n"
        f"3️⃣ **Upload:**\n"
        f"[░░░░░░░░░░░░░░░░░░░░] 0%\n\n"
        f"📤 Upload: Telegram\n"
        f"🔧 Engine: TDLib v1.8.66"
    )
    
    start_time = time.time()
    
    async def upload_progress(current, total):
        await update_progress_message(
            status_msg, "Upload", current, total, start_time, 3, 20
        )
    
    await message.reply_video(
        video=output_file,
        caption=f"✅ **Hardsub Complete!**\n\n"
                f"📽️ **Output Info:**\n"
                f"• Codec: `{codec_choice.upper()}`\n"
                f"• Size: `{format_bytes(output_size)}`\n"
                f"• Duration: `{time.strftime('%H:%M:%S', time.gmtime(total_duration))}`\n\n"
                f"🚀 Ready to download!",
        supports_streaming=True,
        progress=upload_progress
    )

    await status_msg.edit_text(
        f"✅ **Task Complete!** 🎉\n\n"
        f"📊 Final Stats:\n"
        f"├ Input: {format_bytes(video_size)}\n"
        f"├ Output: {format_bytes(output_size)}\n"
        f"├ Codec: {codec_choice.upper()}\n"
        f"└ Time: {time.strftime('%H:%M:%S', time.gmtime(time.time() - start_time))}\n\n"
        f"✨ Use `/start` for another conversion!"
    )

    # Cleanup
    for path in [video_file, sub_file, output_file]:
        try:
            if os.path.exists(path):
                os.remove(path)
        except Exception:
            pass
    
    if user_id in user_data:
        del user_data[user_id]
    if user_id in active_tasks:
        del active_tasks[user_id]

@app.on_message(filters.command("status"))
async def show_status(client: Client, message: Message):
    user_id = message.from_user.id
    
    if user_id not in active_tasks:
        await message.reply_text("❌ No active tasks. Use `/start` to begin.")
        return
    
    task = active_tasks[user_id]
    elapsed = time.time() - task["start_time"]
    
    await message.reply_text(
        f"📊 **Active Task Status:**\n\n"
        f"Task ID: {user_id}\n"
        f"Status: {task['status'].upper()}\n"
        f"Elapsed: {time.strftime('%H:%M:%S', time.gmtime(elapsed))}\n"
        f"Engine: TDLib v1.8.66"
    )

@app.on_message(filters.command("stop"))
async def stop_task(client: Client, message: Message):
    user_id = message.from_user.id
    
    if user_id not in active_tasks:
        await message.reply_text("❌ No active task to stop.")
        return
    
    del active_tasks[user_id]
    await message.reply_text("✅ Task stopped. Use `/start` to create a new conversion.")

# --- Startup ---
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(start_web_server())
    print("🚀 Web server started! Now launching Pyrogram...")
    print("📊 TDLib Engine v1.8.66 - Ready for operations")
    app.run()
