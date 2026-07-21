import os
import time
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message

# Replace these with your credentials from my.telegram.org and @BotFather
API_ID = 36282056 
API_HASH = "3a948acece533f362b4c90b2b3c14b60"
BOT_TOKEN = "8737705568:AAGSjZlCgT6yrs6h045X88EEq63-iZLCiD4"

app = Client("hardsub_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# User state storage for video & subtitle pair
user_data = {}

def progress_bar(current, total, status, message, start_time):
    """Custom progress callback to monitor upload/download speeds."""
    now = time.time()
    diff = now - start_time
    if diff == 0:
        return
    percentage = (current / total) * 100
    speed = current / diff / (1024 * 1024)  # MB/s
    
    # Update progress every 5 seconds to avoid rate-limits
    if not hasattr(progress_bar, "last_update"):
        progress_bar.last_update = 0
        
    if now - progress_bar.last_update > 5:
        progress_bar.last_update = now
        try:
            message.edit_text(
                f"**{status}**\n"
                f"Progress: `{percentage:.1f}%`\n"
                f"Speed: `{speed:.2f} MB/s`"
            )
        except Exception:
            pass

@app.on_message(filters.command("start"))
async def start(client: Client, message: Message):
    await message.reply_text(
        "👋 **Fast Hardsub Bot Ready!**\n\n"
        "1. Send me a **Video File** (up to 2GB).\n"
        "2. Send me a **Subtitle File** (`.srt` or `.ass`).\n"
        "3. Select your desired codec (`x264` or `x265`)."
    )

@app.on_message(filters.video | filters.document)
async def handle_media(client: Client, message: Message):
    user_id = message.from_user.id
    doc = message.document or message.video
    
    if not doc:
        return

    file_name = doc.file_name or "file"
    
    # Handle Subtitle File
    if file_name.endswith((".srt", ".ass")):
        if user_id not in user_data or "video" not in user_data[user_id]:
            await message.reply_text("❌ Please send the video file first!")
            return
            
        status_msg = await message.reply_text("📥 Downloading subtitle file...")
        sub_path = await message.download(file_name=f"sub_{user_id}.ass")
        user_data[user_id]["sub"] = sub_path
        
        await status_msg.edit_text(
            "⚙️ **Select Target Codec:**\n"
            "Reply with `/convert x264` for faster encoding/broad compatibility.\n"
            "Reply with `/convert x265` for smaller file size."
        )

    # Handle Video File
    else:
        status_msg = await message.reply_text("📥 Downloading video file...")
        start_time = time.time()
        video_path = await message.download(
            file_name=f"vid_{user_id}.mp4",
            progress=progress_bar,
            progress_args=("Downloading Video...", status_msg, start_time)
        )
        user_data[user_id] = {"video": video_path}
        await status_msg.edit_text("✅ Video downloaded! Now send the subtitle file (`.srt` or `.ass`).")

@app.on_message(filters.command("convert"))
async def process_hardsub(client: Client, message: Message):
    user_id = message.from_user.id
    
    if user_id not in user_data or "video" not in user_data[user_id] or "sub" not in user_data[user_id]:
        await message.reply_text("❌ Missing video or subtitle file. Please upload both first.")
        return

    codec_choice = message.text.split(" ")[-1].lower()
    if codec_choice not in ["x264", "x265"]:
        await message.reply_text("❌ Invalid choice. Use `/convert x264` or `/convert x265`")
        return

    video_file = user_data[user_id]["video"]
    sub_file = user_data[user_id]["sub"]
    output_file = f"out_{user_id}.mp4"

    # Select FFmpeg Encoder Preset
    encoder = "libx264" if codec_choice == "x264" else "libx265"
    
    # FFmpeg command optimized for fast hardsubbing
    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-i", video_file,
        "-vf", f"subtitles='{sub_file}'",
        "-c:v", encoder,
        "-preset", "ultrafast",  # Max speed encoding
        "-crf", "23",            # High visual quality balance
        "-c:a", "copy",          # Copy audio without re-encoding
        "-threads", "0",         # Utilize all CPU cores
        "-movflags", "+faststart", # Enable streaming preview on Telegram
        output_file
    ]

    status_msg = await message.reply_text("⚙️ **Hardsubbing in progress...** (This may take a few minutes)")
    
    # Run FFmpeg asynchronously
    process = await asyncio.create_subprocess_exec(*ffmpeg_cmd)
    await process.wait()

    if not os.path.exists(output_file):
        await status_msg.edit_text("❌ Encoding failed. Check subtitle file format.")
        return

    # Upload converted video back to Telegram
    await status_msg.edit_text("📤 Uploading hardsubbed video...")
    start_time = time.time()
    
    await message.reply_video(
        video=output_file,
        caption=f"✅ **Hardsub Complete!**\nCodec: `{codec_choice}`",
        supports_streaming=True,
        progress=progress_bar,
        progress_args=("Uploading Video...", status_msg, start_time)
    )

    # Cleanup temporary files
    for path in [video_file, sub_file, output_file]:
        if os.path.exists(path):
            os.remove(path)
    del user_data[user_id]

if __name__ == "__main__":
    app.run()
