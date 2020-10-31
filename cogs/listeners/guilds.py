from CatLampPY import colors # pylint: disable=import-error
import datetime
import discord
from discord.ext import commands


class Guilds(commands.Cog):
    def __init__(self, bot):
        self.client = bot

    # @commands.Cog.listener() for a listener event

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        embed = discord.Embed(title="Joined guild", description=f"{guild.name} ({guild.id})", color=colors["success"])
        embed.timestamp = datetime.datetime.utcnow()
        embed.set_footer(text=f"Now in {len(self.client.guilds)} guilds.")
        if bool(guild.icon_url):
            embed.set_thumbnail(url=str(guild.icon_url))
        if not guild.chunked:
            await guild.chunk()
        # Owner and members fields disabled because Discord
        # doesn't like the member intent being used like that
        # embed.add_field(name="Owner", value=f"`{guild.owner}`")  # str()ing a User returns the thing properly formatted
        # embed.add_field(name="Members", value=guild.member_count)
        embed.add_field(name="Shard ID", value=guild.shard_id)
        channel = self.client.get_channel(712489826330345534)
        if channel:
            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        embed = discord.Embed(title="Left guild", description=f"{guild.name} ({guild.id})", color=colors["error"])
        embed.timestamp = datetime.datetime.utcnow()
        embed.set_footer(text=f"Now in {len(self.client.guilds)} guilds.")
        if bool(guild.icon_url):
            embed.set_thumbnail(url=str(guild.icon_url))
        channel = self.client.get_channel(712489826330345534)
        if channel:
            await channel.send(embed=embed)


    async def chunkGuildsAsync(self):
        await self.client.wait_until_ready()
        print("Beginning guild chunking...")
        for guild in self.client.guilds:
            if not guild.chunked:
                await guild.chunk()
        print(f"Done chunking {len(self.client.guilds)} guilds!")


def setup(bot):
    g = Guilds(bot)
    bot.add_cog(g)
    # bot.loop.create_task(g.chunkGuildsAsync())
