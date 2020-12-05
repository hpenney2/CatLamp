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
        self.id = data.get('display_id')
        self.uploader = data.get('uploader')
        self.thumbnail = data.get('thumbnail')
        self.duration = data.get('duration')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            # take first item from a playlist
            try:
                data = data['entries'][0]
            except IndexError:
                raise ValueError()

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options,
                                          before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 30"),
                   data=data)


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # self.queues = {}
        self.manuallyStopped = []
        self.loopEnabled = []

    async def afterPlayback(self, ctx: commands.Context,
                            vClient: discord.VoiceClient, query: str, error: Exception):
        if error:
            print("Error after finished playing:", error)
            raise error
        elif not error:
            guild = ctx.guild.id
            stopped = guild in self.manuallyStopped
            if vClient.is_connected() and guild in self.loopEnabled and not stopped:
                await self.playAudio(ctx, vClient.channel, query, True)
            elif not vClient.is_connected() and ctx.guild.id in self.loopEnabled:
                self.loopEnabled.remove(ctx.guild.id)

            if stopped:
                self.manuallyStopped.remove(guild)

    # noinspection PyTypeChecker
    async def playAudio(self, ctx: commands.Context, connectTo: discord.VoiceChannel, query: str,
                        sendMessage: bool = True):
        if not ctx.voice_client:
            vClient: discord.VoiceClient = await connectTo.connect(timeout=30.0)
        elif ctx.voice_client.channel.id != connectTo.id:
            await ctx.voice_client.disconnect()
            ctx.voice_client.cleanup()
            vClient: discord.VoiceClient = await connectTo.connect(timeout=30.0)
        else:
            vClient: discord.VoiceClient = ctx.voice_client
            vClient.stop()

        async with ctx.typing():
            try:
                source = await YTDLSource.from_url(query, loop=self.bot.loop, stream=True)
            except ValueError:
                raise CommandErrorMsg("No results found!")

        vClient.play(source,
                     after=lambda error: self.bot.loop.create_task(self.afterPlayback(ctx, vClient, query, error)))

        if sendMessage:
            embed = discord.Embed(title=f'Now playing in {connectTo.name}',
                                  color=colors["message"])
            embed.add_field(name="Title",
                            value=f"{source.title}", inline=False)
            embed.add_field(name="Uploader",
                            value=f"{source.uploader}", inline=False)
            embed.add_field(name="Duration",
                            value=time.strftime('%H:%M:%S', time.gmtime(source.duration)), inline=False)
            if source.thumbnail:
                embed.set_thumbnail(url=source.thumbnail)
            await ctx.send(embed=embed)

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
            raise CommandErrorMsg("I'm already in a different voice channel!")

        if ctx.voice_client and ctx.voice_client.is_playing():
            self.manuallyStopped.append(ctx.guild.id)
            ctx.voice_client.stop()

        voiceChannel: discord.VoiceChannel = voiceState.channel
        await self.playAudio(ctx, voiceChannel, url_or_query, True)

    @commands.command()
    @isGuild()
    async def stop(self, ctx):
        if not ctx.voice_client:
            raise CommandErrorMsg("I'm not connected to a voice channel!")
        elif not ctx.voice_client.is_playing():
            raise CommandErrorMsg("I'm not playing anything!")
        else:
            self.manuallyStopped.append(ctx.guild.id)
            ctx.voice_client.stop()
            await ctx.send("Stopped the current song.")

    @commands.command()
    @isGuild()
    async def loop(self, ctx):
        """Toggles looping the song that is currently playing."""
        if not ctx.voice_client:
            raise CommandErrorMsg("I'm not connected to a voice channel!")
        if ctx.guild.id in self.loopEnabled:
            self.loopEnabled.remove(ctx.guild.id)
            await ctx.send("Disabled song looping.")
        else:
            self.loopEnabled.append(ctx.guild.id)
            await ctx.send("Enabled song looping.")

    @commands.command(aliases=["dc", "goAway"])
    @isGuild()
    async def disconnect(self, ctx):
        """Disconnects the bot from the currently connected voice channel, if any."""
        vClient: discord.VoiceClient = ctx.voice_client
        if vClient:
            await vClient.disconnect()
            vClient.cleanup()
            if ctx.guild.id in self.loopEnabled:
                self.loopEnabled.remove(ctx.guild.id)
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
            if member.guild.id in self.loopEnabled:
                self.loopEnabled.remove(member.guild.id)


def setup(bot):
    bot.add_cog(Music(bot))
