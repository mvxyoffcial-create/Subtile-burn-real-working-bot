import os
import time
import asyncio
from aiohttp import web
from pyrogram import Client, filters
from pyrogram.types import Message

# Credentials
API_ID = 36282056
API_HASH = "3a948acece533f362b4c90b2b3c14b60"
BOT_TOKEN = "8737705568:AAGSjZlCgT6yrs6h045X88EEq63-iZLCiD4"
PORT = int(os.getenv("PORT", "8000"))

# max_concurrent_transmissions splits big files into parallel chunks for
# download/upload. This is the single biggest speed lever pyrogram exposes.
app = Client(
    "hardsub_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    max_concurrent_transmissions=8,
    sleep_threshold=60,
)

user_data = {}
_encoder_cache = {}

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

# --- Helper: Detect hardware encoder once, cache the result ---
async def get_encoder(codec_choice: str) -> tuple[str, list[str]]:
    """Returns (encoder_name, extra_args) — prefers NVENC GPU encoding,
    falls back to fast software encoding if no GPU is available."""
    if codec_choice in _encoder_cache:
        return _encoder_cache[codec_choice]

    process = await asyncio.create_subprocess_exec(
        "ffmpeg", "-hide_banner", "-encoders",
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL
    )
    stdout, _ = await process.communicate()
    available = stdout.decode(errors="ignore")

    if codec_choice == "x264":
        if "h264_nvenc" in available:
            result = ("h264_nvenc", ["-preset", "p1", "-tune", "ll", "-cq", "23", "-b:v", "0"])
        else:
            result = ("libx264", ["-preset", "ultrafast", "-crf", "23"])
    else:  # x265
        if "hevc_nvenc" in available:
            result = ("hevc_nvenc", ["-preset", "p1", "-tune", "ll", "-cq", "26", "-b:v", "0"])
        else:
            result = ("libx265", ["-preset", "ultrafast", "-crf", "26"])

    _encoder_cache[codec_choice] = result
    return result

# --- Progress Callback (async, actually awaits the edit) ---
_last_update = {}

async def progress_bar(current, total, status, message: Message, start_time):
    now = time.time()
    diff = now - start_time
    if diff == 0:
        return
    key = message.id
    if now - _last_update.get(key, 0) < 4:
        return
    _last_update[key] = now

    percentage = (current / total) * 100
    speed = current / diff / (1024 * 1024)
    try:
        await message.edit_text(
            f"**{status}**\n"
            f"Progress: `{percentage:.1f}%`\n"
            f"Speed: `{speed:.2f} MB/s`"
        )
    except Exception:
        pass

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
            "• `/convert x264`\n"
            "• `/convert x265`"
        )
    else:
        status_msg = await message.reply_text("📥 Downloading video file...")
        start_time = time.time()
        video_path = await message.download(
            file_name=f"vid_{user_id}.mp4",
            progress=progress_bar,
            progress_args=("Downloading Video...", status_msg, start_time)
        )
        user_data[user_id] = {"video": video_path}
        await status_msg.edit_text("✅ Video downloaded! Now send the subtitle file.")

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

    encoder, encoder_args = await get_encoder(codec_choice)

    total_duration = await get_video_duration(video_file)
    escaped_sub_file = sub_file.replace("\\", "/").replace(":", "\\:").replace("'", "\\'")

    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-i", video_file,
        "-vf", f"subtitles={escaped_sub_file}",
        "-c:v", encoder,
        *encoder_args,
        "-c:a", "copy",
        "-threads", "0",
        "-movflags", "+faststart",
        "-progress", "pipe:1",
        "-nostats",
        output_file
    ]

    status_msg = await message.reply_text(
        f"⚙️ **Starting Hardsub Process...**\nEncoder: `{encoder}`"
    )

    process = await asyncio.create_subprocess_exec(
        *ffmpeg_cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.DEVNULL
    )

    last_edit = time.time()

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

                if time.time() - last_edit > 4:
                    last_edit = time.time()
                    await status_msg.edit_text(
                        f"🔥 **Hardsubbing Video...**\n"
                        f"Progress: `{percent:.1f}%`\n"
                        f"Codec: `{codec_choice}` (`{encoder}`)"
                    )
            except Exception:
                pass

    await process.wait()

    if process.returncode != 0 or not os.path.exists(output_file):
        # Retry once with software encoder if hardware encoder failed
        if encoder.endswith("_nvenc"):
            await status_msg.edit_text("⚠️ GPU encode failed, retrying with software encoder...")
            sw_encoder = "libx264" if codec_choice == "x264" else "libx265"
            sw_args = ["-preset", "ultrafast", "-crf", "23" if codec_choice == "x264" else "26"]
            ffmpeg_cmd = [
                "ffmpeg", "-y", "-i", video_file,
                "-vf", f"subtitles={escaped_sub_file}",
                "-c:v", sw_encoder, *sw_args,
                "-c:a", "copy", "-threads", "0",
                "-movflags", "+faststart", output_file
            ]
            process = await asyncio.create_subprocess_exec(
                *ffmpeg_cmd,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL
            )
            await process.wait()
            _encoder_cache.pop(codec_choice, None)  # don't reuse the broken hw encoder

        if not os.path.exists(output_file):
            await status_msg.edit_text("❌ Subtitle burn failed.")
            return

    await status_msg.edit_text("📤 Uploading hardsubbed video...")
    start_time = time.time()

    await message.reply_video(
        video=output_file,
        caption=f"✅ **Hardsub Complete!**\nCodec: `{codec_choice}`",
        supports_streaming=True,
        progress=progress_bar,
        progress_args=("Uploading Video...", status_msg, start_time)
    )

    for path in [video_file, sub_file, output_file]:
        if os.path.exists(path):
            os.remove(path)
    del user_data[user_id]

# --- Correct Startup Procedure ---
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(start_web_server())
    print("🚀 Web server started! Now launching Pyrogram...")
    app.run()
