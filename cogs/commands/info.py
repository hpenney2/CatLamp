import discord
from discord.ext import commands
import math

# pylint: disable=import-error
from cogs.misc.isAdmin import isAdmin
from cogs.listeners.pagination import Pagination
from cogs.misc.mdbed import uh

import tables

colors = tables.getColors()


class Info(commands.Cog, name="Bot Info"):
    def __init__(self, bot):
        self.client = bot
        self.client.privacy = uh()
        self.pagination = Pagination(self.client)
        self.client.cmds.append(self.documentation)
        self.client.cmds.append(self.invite)
        self.client.cmds.append(self.ping)
        self.client.cmds.append(self.server)
        self.client.cmds.append(self.privacy)

    @commands.command(hidden=True)
    @commands.check(isAdmin)
    async def documentation(self, ctx, page: int = 1):
        """Displays the old version of this message."""
        # 10 per page, can't just have half a page of commands go bye-bye
        maxPages = round(math.ceil(len(self.client.cmds) / 10))
        page -= 1
        # underflow bad
        if page < 0:
            page = 0
        # overflow bad
        elif page > maxPages - 1:
            page = maxPages - 1

        # set the things to find
        # pageIndex = (page - 1) * 10
        if len(self.client.helpEmbeds) == 0:
            Page = 1
            # set initial title and footer based on page no.
            embed = discord.Embed(title="Commands", color=colors["message"])
            embed.set_footer(text=f"Page 1/{maxPages}")

            for i in range(len(self.client.cmds)):
                # don't overflow, dumb
                if i >= (Page * 10):
                    self.client.helpEmbeds.append(embed)
                    Page += 1
                    embed = discord.Embed(title="Commands", color=colors["message"])
                    embed.set_footer(text=f"Page {Page}/{maxPages}")
                elif len(embed.fields) < 10:
                    # get command from index
                    command = self.client.cmds[i]

                    name = "+" + command.name
                    Params = command.clean_params
                    for param in Params:
                        param = param.replace('_', ' ')
                        name += f" <{param}>"
                    desc = command.short_doc or "No description."
                    if command.aliases:
                        desc += "\nAliases: "
                        desc += ", ".join(command.aliases)
                    embed.add_field(name=name, value=desc, inline=False)
            self.client.helpEmbeds.append(embed)
        # send the embed lol
        helpMess = await ctx.send(embed=self.client.helpEmbeds[page])
        await self.pagination.paginate(message=helpMess, embeds=self.client.helpEmbeds, indexNumber=page, endTime=300,
                                       userId=ctx.author.id)

    @commands.command(aliases=["about"])
    async def info(self, ctx):
        """Sends information about CatLamp and its developers."""
        embed = discord.Embed(title="About CatLamp", color=colors["message"])
        embed.add_field(name="Information",
                        value="CatLamp is designed as an \"all-in-one\" bot, trying to provide as many good features "
                              "as possible in a single bot. CatLamp is built in Python using the discord.py library.",
                        inline=False)
        embed.add_field(name="Origin",
                        value="CatLamp was originally created in May of 2020 using the C# language and the "
                              "Discord.Net library. It wasn't great and never became public, soon to be forgotten. "
                              "However, the project was revived in August of 2020 with a new Python rewrite as well as "
                              "TheEgghead27 joining the development team. Ever since, the project has been only "
                              "growing.\nThe name and logo of CatLamp is based off a real cat lamp that hpenney2 owns.",
                        inline=False)
        embed.add_field(name="Developers",
                        value="**hp(enney2)** - Developer, creator\n"
                              "**TheEgghead27** - Developer\n"
                              "*If you need to contact a developer, please join our support server (+server).*",
                        inline=False)
        embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/775506680926306306/775506867044089887"
                                "/catlamp_avatar-small.png")
        await ctx.send(embed=embed)

    @commands.command()
    async def invite(self, ctx):
        """Sends CatLamp's invite link. If you wanted to join the CatLamp support server, use `+server` instad."""
        await ctx.send("You can add CatLamp to your server using the link below.\n"
                       "https://top.gg/bot/712394747548794950")

    @commands.command()
    async def vote(self, ctx):
        """Sends CatLamp's top.gg voting link."""
        await ctx.send("Want to support CatLamp? Vote for us on Discord Bot List below!\n"
                       "https://top.gg/bot/712394747548794950/vote")

    @commands.command()
    async def server(self, ctx):
        """Sends CatLamp's server invite to your DMs. Join to get support with CatLamp, report bugs, and get notified about updates!"""
        # static server.id is better than getting a server (with the same id, might I add), then using it for comparison
        try:
            if ctx.guild.id == 712487389121216584:
                await ctx.send("You're already here! If you need an invite, you can get it from <#712489819334246441>.")
                return
        except AttributeError:
            pass
        try:
            # user.send() method is better than getting a dm channel
            await ctx.author.send("You can join the official CatLamp server below.\nhttps://discord.gg/5p8bQcy")
            if ctx.channel.type == discord.ChannelType.text:
                await ctx.send("Sent CatLamp's server invite to your DMs!")
        except discord.Forbidden:
            await ctx.send("I can't DM you! Make sure to enable your DMs so I can.")

    @commands.command()
    async def privacy(self, ctx):
        """Displays the CatLamp privacy policy."""
        await ctx.send(embed=self.client.privacy)

    @commands.command()
    async def ping(self, ctx):
        """Gets the current latency between the bot and Discord."""
        message = await ctx.send("Measuring ping...")
        ping = round((message.created_at.timestamp() - ctx.message.created_at.timestamp()) * 1000)
        embed = discord.Embed(title="Pong!")
        embed.add_field(name="API Latency", value=f"{round(self.client.latency * 1000)}ms")
        embed.add_field(name="Measured Ping", value=f"{ping}ms")
        await message.edit(content=None, embed=embed)


def setup(bot):
    bot.add_cog(Info(bot))
