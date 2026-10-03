import discord
from discord.ext import commands
import yt_dlp
import asyncio
from keep_alive import keep_alive

# تشغيل سيرفر الويب الوهمي للحفاظ على نشاط البوت
keep_alive()

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
intents.presences = True

bot = commands.Bot(command_prefix="!", intents=intents)

# إعدادات yt-dlp للبحث التلقائي وجلب الصوتيات
ytdl_format_options = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'default_search': 'ytsearch',
}
ffmpeg_options = {
    'options': '-vn',
}

ytdl = yt_dlp.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, keyword, *, loop=None, stream=True):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(keyword, download=False))
        
        if 'entries' in data:
            data = data['entries'][0]
            
        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

# 1. أمر الدخول
@bot.command(name="come")
async def come(ctx):
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        if ctx.voice_client is not None:
            await ctx.voice_client.move_to(channel)
        else:
            await channel.connect()
        await ctx.send(f"تم الانضمام إلى القناة: {channel.name}")
    else:
        await ctx.send("يجب أن تكون في قناة صوتية أولاً!")

# 2. أمر التشغيل عبر البحث التلقائي
@bot.command(name="ش")
async def play_short(ctx, *, query):
    if not ctx.voice_client:
        if ctx.author.voice:
            await ctx.author.voice.channel.connect()
        else:
            await ctx.send("يجب أن تكون في قناة صوتية أولاً!")
            return

    if ctx.voice_client.is_playing():
        ctx.voice_client.stop()

    async with ctx.typing():
        try:
            player = await YTDLSource.from_url(query, loop=bot.loop, stream=True)
            ctx.voice_client.play(player, after=lambda e: print(f'خطأ في التشغيل: {e}') if e else None)
            await ctx.send(f"🎶 جارٍ الآن تشغيل: **{player.title}**")
        except Exception as e:
            await ctx.send(f"صار خطأ أثناء البحث أو التشغيل: {e}")

# 3. أمر الإيقاف المؤقت
@bot.command(name="وقف")
async def pause_audio(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.pause()
        await ctx.send("⏸️ تم إيقاف الأغنية مؤقتاً.")
    else:
        await ctx.send("مافي شي شغال حالياً عشان أوقفه!")

# 4. أمر الخروج
@bot.command(name="خ")
async def leave_short(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("تم الخروج من القناة الصوتية.")
    else:
        await ctx.send("البوت ليس في أي قناة صوتية.")

bot.run("MTU1NTgzNzY5Mjc3ODkxMzgzMg.GY_r0G.kx9SIZeem7dFvupOCJdI8aZkMACfiROcECNXlM")