import os
import asyncio
import shutil
import discord
from discord.ext import commands
from dotenv import load_dotenv


# =========================
# تحميل .env
# =========================

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    raise RuntimeError("❌ DISCORD_TOKEN غير موجود في ملف .env")


# =========================
# البحث عن FFmpeg
# =========================

FFMPEG_PATH = shutil.which("ffmpeg")

if not FFMPEG_PATH:
    possible_paths = [
        r"C:\ffmpeg\bin\ffmpeg.exe",
        r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
        r"C:\Program Files (x86)\ffmpeg\bin\ffmpeg.exe",
    ]

    for path in possible_paths:
        if os.path.isfile(path):
            FFMPEG_PATH = path
            break

if not FFMPEG_PATH:
    raise RuntimeError("❌ FFmpeg غير موجود.")

print(f"✅ FFmpeg: {FFMPEG_PATH}")


# =========================
# Discord
# =========================

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)


# =========================
# ملفات الصوت
# =========================

AUDIO_FILES = {
    f"audio{i}": f"audio{i}.mp3"
    for i in range(1, 11)
}


# =========================
# حالة البوت لكل Server
# =========================

playing = {}
playback_tasks = {}


# =========================
# Anti-Spam لكل شخص
# 3 Commands مسموحين
# الرابعة مرفوضة
# ثم 60 ثانية
# =========================

user_commands = {}

MAX_COMMANDS = 3
COOLDOWN = 60


# =========================
# عند تشغيل البوت
# =========================

@bot.event
async def on_ready():
    print(f"✅ البوت دخل: {bot.user}")
    print("🎵 البوت جاهز!")


# =========================
# Connection Events
# =========================

@bot.event
async def on_disconnect():
    print("⚠️ البوت فقد الاتصال بـ Discord (Network Disconnect).")
    # Reset playing state for all guilds to prevent getting stuck
    playing.clear()
    playback_tasks.clear()

@bot.event
async def on_resumed():
    print("✅ البوت استعاد الاتصال بـ Discord!")

@bot.event
async def on_connect():
    print("🌐 البوت متصل بـ Discord.")


# =========================
# Welcome & Goodbye Events
# =========================

@bot.event
async def on_voice_state_update(member, before, after):
    if member.bot:
        return

    print(f"🎤 Voice state update triggered for {member.name}")

    # User joined a voice channel
    if before.channel is None and after.channel is not None:
        print(f"👋 {member.name} joined {after.channel.name}")
        await play_in_channel(after.channel, r"MAR7BABIK.m4a")

    # User left a voice channel
    elif before.channel is not None and after.channel is None:
        print(f"🏃 {member.name} left {before.channel.name}")
        await play_in_channel(before.channel, r"SIR T9AWED.m4a")

    # User switched channels
    elif before.channel is not None and after.channel is not None and before.channel != after.channel:
        print(f"🏃👋 {member.name} switched from {before.channel.name} to {after.channel.name}")
        await play_in_channel(after.channel, r"MAR7BABIK.m4a")


# =========================
# تشغيل ملف صوتي
# =========================

async def play_file(voice_client, filename):

    if not os.path.isfile(filename):
        print(f"❌ الملف غير موجود: {filename}")
        return

    finished = asyncio.Event()

    source = await asyncio.to_thread(
        discord.FFmpegPCMAudio,
        filename,
        executable=FFMPEG_PATH
    )

    def after_playing(error):

        if error:
            print(f"❌ Audio error: {error}")
        else:
            print(f"✅ سالا: {filename}")

        bot.loop.call_soon_threadsafe(
            finished.set
        )

    voice_client.play(
        source,
        after=after_playing
    )

    await finished.wait()


# =========================
# Play in specific channel
# =========================

import uuid

async def play_in_channel(voice_channel, filename, ctx=None):
    guild_id = voice_channel.guild.id
    task_id = str(uuid.uuid4())

    # Assign this task as the active one
    playback_tasks[guild_id] = task_id

    voice_client = voice_channel.guild.voice_client

    try:
        if voice_client and voice_client.is_connected():
            if voice_client.channel != voice_channel:
                print(f"🔄 Moving to new channel: {voice_channel.name}")
                await voice_client.move_to(voice_channel)
            if voice_client.is_playing():
                print("⏹️ Stopping current audio to play new one.")
                voice_client.stop()
        else:
            if voice_client:
                # Disconnect any ghost sessions
                try:
                    await voice_client.disconnect(force=True)
                except Exception:
                    pass

            print(f"🔊 Connecting to: {voice_channel.name}")
            voice_client = await voice_channel.connect(reconnect=False, timeout=30)
            print("✅ Voice connection established!")

        if ctx:
            await ctx.send(f"🔊 كيشغل: `{filename}`")

        await play_file(voice_client, filename)

        # Only disconnect if this task is still the most recent one
        if playback_tasks.get(guild_id) == task_id:
            if voice_client and voice_client.is_connected():
                voice_client.stop()
                await voice_client.disconnect()
                print("👋 الصوت سالا، والبوت خرج.")

        return True

    except Exception as e:
        print(f"❌ Error: {repr(e)}")
        # Only cleanup connection on error if no other task took over
        if playback_tasks.get(guild_id) == task_id:
            if voice_client:
                try:
                    if voice_client.is_connected():
                        await voice_client.disconnect(force=True)
                except Exception:
                    pass
        return False


# =========================
# Command Audio
# =========================

async def play_audio(ctx, filename):

    user_id = ctx.author.id
    guild_id = ctx.guild.id

    now = asyncio.get_running_loop().time()


    # =========================
    # إنشاء بيانات المستخدم
    # =========================

    if user_id not in user_commands:
        user_commands[user_id] = {
            "timestamps": [],
            "cooldown_until": 0
        }

    data = user_commands[user_id]


    # =========================
    # إذا مازال Cooldown
    # =========================

    if now < data["cooldown_until"]:

        await ctx.send(
            "SIR TA7WA A ZEBI"
        )

        return


    # =========================
    # تأكد المستخدم داخل Voice
    # =========================

    if not ctx.author.voice:

        await ctx.send(
            "❌ خاصك تكون داخل Voice Channel."
        )

        return


    # =========================
    # تأكد الملف موجود
    # =========================

    if not os.path.isfile(filename):

        await ctx.send(
            f"❌ الملف `{filename}` غير موجود."
        )

        return


    # =========================
    # إذا البوت مشغول
    # لا Queue
    # لا Count
    # لا Interrupt
    # =========================

    if playing.get(guild_id, False):

        print(
            f"⏸️ البوت مشغول، تجاهل: {filename}"
        )

        return


    # =========================
    # فحص النافذة الزمنية 60 ثانية
    # =========================

    # إزالة الأوامر القديمة
    data["timestamps"] = [ts for ts in data["timestamps"] if now - ts < COOLDOWN]

    if len(data["timestamps"]) >= MAX_COMMANDS:
        # الرابعة مرفوضة: تعيين الكولداون وتشغيل ملف الوداع
        data["cooldown_until"] = now + COOLDOWN

        await ctx.send(
            "⚠️ انت في فترة Cooldown! 3 أوامر في الدقيقة فقط."
        )

        await play_in_channel(ctx.author.voice.channel, r"SIR T9AWED.m4a", ctx=ctx)

        return


    # =========================
    # Command مقبولة
    # =========================

    data["timestamps"].append(now)

    print(
        f"👤 User {user_id}: "
        f"Command {len(data['timestamps'])}/{MAX_COMMANDS}"
    )


    # =========================
    # تشغيل بالاستعانة بالدالة
    # =========================

    voice_channel = ctx.author.voice.channel
    await play_in_channel(voice_channel, filename, ctx=ctx)


# =========================
# Error Handling
# =========================

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandInvokeError):
        original = error.original
        if isinstance(original, discord.errors.ClientException):
            print(f"⚠️ خطأ أثناء تشغيل الأمر: {original}")
            # Do not send a message to the user for every client exception to avoid spam, just log it.
        elif isinstance(original, (discord.errors.ConnectionClosed, discord.errors.GatewayNotFound)):
             print(f"⚠️ خطأ في الاتصال بالشبكة أثناء تشغيل الأمر: {original}")
        else:
             print(f"❌ خطأ غير متوقع: {original}")
    else:
        print(f"⚠️ Command Error: {error}")

# =========================
# إنشاء !audio1 حتى !audio10
# =========================

def create_audio_command(
    command_name,
    filename
):

    async def audio_command(ctx):

        await play_audio(
            ctx,
            filename
        )

    audio_command.__name__ = command_name

    return commands.command(
        name=command_name
    )(audio_command)


for command_name, filename in AUDIO_FILES.items():

    bot.add_command(
        create_audio_command(
            command_name,
            filename
        )
    )


# =========================
# تشغيل البوت
# =========================

bot.run(TOKEN)
