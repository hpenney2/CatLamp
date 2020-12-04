import discord
from discord.ext import commands
from CatLampPY import isGuild, CommandErrorMsg, colors
import asyncio
import youtube_dl
import time


# Suppress noise about console usage from errors
youtube_dl.utils.bug_reports_message = lambda: ''


ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'  # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')
        self.uploader = data.get('uploader')
        self.thumbnail = data.get('thumbnail')
        self.duration = data.get('duration')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(f"ytsearch:{url}", download=not stream))

        if 'entries' in data:
            # take first item from a playlist
            try:
                data = data['entries'][0]
            except IndexError:
                raise ValueError()

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.loopEnabled = []

    async def loop(self, ctx: commands.Context, vClient: discord.VoiceClient):
        guild = ctx.guild
        # if guild.id in self.loopEnabled:


    @commands.command()
    @isGuild()
    async def play(self, ctx, *, url_or_query):
        """Plays audio from the YouTube video provided in your current voice channel."""
        voiceState = ctx.author.voice
        if not voiceState or not voiceState.channel:
            raise CommandErrorMsg("You aren't in a voice channel!")

        selfMember = await ctx.guild.fetch_member(ctx.bot.user.id)
        selfVoiceState = selfMember.voice
        if selfVoiceState and selfVoiceState.channel and selfVoiceState.channel.id != voiceState.channel.id:
            raise CommandErrorMsg("I'm already in a voice channel!")

        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.stop()

        voiceChannel: discord.VoiceChannel = voiceState.channel
        async with ctx.typing():
            if not ctx.voice_client:
                # noinspection PyTypeChecker
                vClient: discord.VoiceClient = await voiceChannel.connect(timeout=30.0)
            else:
                vClient: discord.VoiceClient = ctx.voice_client
            try:
                player = await YTDLSource.from_url(url_or_query, loop=self.bot.loop, stream=True)
            except ValueError:
                raise CommandErrorMsg("No results found!")
            vClient.play(player, after=lambda e: self.bot.loop.create_task(self.loop))
        embed = discord.Embed(title=f'Now playing in {selfVoiceState.channel.name}',
                              color=colors["message"])
        embed.add_field(name="Title", value=player.title, inline=False)
        embed.add_field(name="Uploader", value=player.uploader, inline=False)
        embed.add_field(name="Duration", value=time.strftime('%H:%M:%S', time.gmtime(player.duration)), inline=False)
        embed.set_thumbnail(url=player.thumbnail)
        await ctx.send(embed=embed)

    @commands.command(aliases=["dc", "goAway"])
    async def disconnect(self, ctx):
        """Disconnects the bot from the currently connected voice channel, if any."""
        vClient: discord.VoiceClient = ctx.guild.voice_client
        if vClient:
            await vClient.disconnect()
            vClient.cleanup()
            await ctx.send("Successfully disconnected.")
        else:
            raise CommandErrorMsg("I'm not in a voice channel!")

    # noinspection PyUnusedLocal
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        channel = getattr(before, "channel", None)
        if channel and channel.guild.voice_client and len(channel.members) <= 1:
            vClient = channel.guild.voice_client
            await vClient.disconnect()
            vClient.cleanup()


def setup(bot):
    bot.add_cog(Music(bot))
