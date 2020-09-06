import discord
from discord.ext import commands
import math

from cogs.listeners.pagination import Pagination
from cogs.misc.mdbed import uh

import tables

colors = tables.getColors()


class Info(commands.Cog, name="Bot Info"):
    def __init__(self, bot):
        self.client = bot
        self.pagination = Pagination(self.client)
        self.client.cmds.append(self.documentation)
        self.client.cmds.append(self.invite)
        self.client.cmds.append(self.ping)
        self.client.cmds.append(self.server)
        self.client.cmds.append(self.privacy)

    @commands.command(hidden=True)
    # fuck "Function shadows built-in method help()"
    # all my homies hate "Function shadows built-in method help()"
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
                    self.client.helpEmbeds.append(embed.to_dict())
                    Page += 1
                    embed = discord.Embed(title="Commands", color=colors["message"])
                    embed.set_footer(text=f"Page {Page}/{maxPages}")
                else:
                    # get command from index
                    command = self.client.cmds[i]

                    # generate help field for command
                    if not len(embed.fields) >= 10:
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
            self.client.helpEmbeds.append(embed.to_dict())
        # send the embed lol
        helpMess = await ctx.send(embed=discord.Embed.from_dict(self.client.helpEmbeds[page]))
        await self.pagination.paginate(helpMess, self.client.helpEmbeds, page, 300, True)

    @commands.command()
    async def invite(self, ctx):
        """Sends CatLamp's invite link."""
        msg = await ctx.send("You can add CatLamp to your server using the link below.\nhttps://bit.ly/CatLampBot")
        try:
            await msg.edit(suppress=True)
        except discord.Forbidden:
            pass

    @commands.command()
    async def server(self, ctx):
        """Sends CatLamp's server invite to your DMs."""
        # static server.id is better than getting a server (with the same id, might I add), then using it for comparison
        if ctx.guild.id == 712487389121216584:
            await ctx.send("You're already here! If you need an invite, you can get it from <#712489819334246441>.")
            return
        try:
            # user.send() method is better than getting a dm channel
            await ctx.author.send("You can join the official CatLamp server below.\nhttps://discord.gg/5p8bQcy")
            await ctx.send("Sent CatLamp's server invite to your DMs!")
        except discord.Forbidden:
            await ctx.send("I can't DM you! Make sure to enable your DMs so I can.")

    @commands.command()
    async def privacy(self, ctx):
        """Displays the CatLamp privacy policy."""
        try:
            privacy = self.client.privacy
        except (NameError, AttributeError):
            self.client.privacy = uh()
            privacy = self.client.privacy
        await ctx.send(embed=privacy)

    @commands.command()
    async def ping(self, ctx):
        """Gets the current latency between the bot and Discord."""
        await ctx.send(f"Pong!\nLatency: {round(self.client.latency * 1000)}ms")


def setup(bot):
    bot.add_cog(Info(bot))
