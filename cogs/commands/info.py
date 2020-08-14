import discord
from discord.ext import commands
import math

from CatLampPY import colors


class Info(commands.Cog, name="Bot Info"):
    def __init__(self, bot):
        self.client = bot
        self.client.cmds.append(self.help)
        self.client.cmds.append(self.invite)
        self.client.cmds.append(self.ping)
        self.client.cmds.append(self.server)

    @commands.command(aliases=["cmds", "commands"])
    async def help(self, ctx, page: int = 1):
        """Displays this message."""
        maxPages = round(math.ceil(len(self.client.cmds) / 10))
        if page < 1:
            page = 1
        elif page > maxPages:
            page = maxPages

        embed = discord.Embed(title="Commands", color=colors["message"])
        embed.set_footer(text=f"Page {page}/{maxPages}")
        pageIndex = (page - 1) * 10
        for i in range(len(self.client.cmds)):
            if i + pageIndex >= len(self.client.cmds):
                break
            command = self.client.cmds[i + pageIndex]
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
        await ctx.send(embed=embed)

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
    async def ping(self, ctx):
        """Gets the current latency between the bot and Discord."""
        await ctx.send(f"Pong!\nLatency: {round(self.client.latency * 1000)}ms")


def setup(bot):
    bot.add_cog(Info(bot))
