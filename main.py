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
            "count": 0,
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
    # إذا سالات الدقيقة
    # =========================

    if data["cooldown_until"] > 0:

        data["cooldown_until"] = 0
        data["count"] = 0


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
    # الرابعة مرفوضة
    # =========================

    if data["count"] >= MAX_COMMANDS:

        data["cooldown_until"] = now + COOLDOWN

        await ctx.send(
            "SIR TA7WA A ZEBI"
        )

        return


    # =========================
    # Command مقبولة
    # =========================

    data["count"] += 1

    print(
        f"👤 User {user_id}: "
        f"Command {data['count']}/{MAX_COMMANDS}"
    )


    # =========================
    # البوت أصبح مشغول
    # =========================

    playing[guild_id] = True

    voice_client = None

    try:

        voice_channel = ctx.author.voice.channel


        # =========================
        # تأكد ما كاينش Voice Client قديم
        # =========================

        existing_voice = ctx.guild.voice_client

        if existing_voice:

            if existing_voice.is_connected():

                print(
                    "⚠️ البوت مازال داخل Voice، تجاهل command."
                )

                playing[guild_id] = False
                return

            else:

                try:
                    await existing_voice.disconnect(
                        force=True
                    )
                except Exception:
                    pass


        # =========================
        # يدخل للروم
        # =========================

        print(
            f"🔊 Connecting to: {voice_channel.name}"
        )

        voice_client = await voice_channel.connect(
            reconnect=False,
            timeout=30
        )

        print(
            "✅ Voice connection established!"
        )


        # =========================
        # تشغيل الصوت
        # =========================

        await ctx.send(
            f"🔊 كيشغل: `{filename}`"
        )

        await play_file(
            voice_client,
            filename
        )


        # =========================
        # يخرج من Voice
        # =========================

        if voice_client.is_connected():

            voice_client.stop()
            await voice_client.disconnect()

            print(
                "👋 الصوت سالا، والبوت خرج."
            )


    except Exception as e:

        print(
            f"❌ Error: {repr(e)}"
        )

        if voice_client:

            try:

                if voice_client.is_connected():

                    await voice_client.disconnect(
                        force=True
                    )

            except Exception:
                pass


    finally:

        # =========================
        # البوت ولى فاضي
        # =========================

        playing[guild_id] = False

        print(
            "🟢 البوت فاضي، command جديدة ممكنة."
        )


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
