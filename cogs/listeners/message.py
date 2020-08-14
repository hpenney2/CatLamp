from discord.ext import commands


class Message(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, msg):
        if msg.author.id == self.bot.user.id or msg.author.bot:
            return
        if msg.content != "python" and msg.content.lower().startswith("do not the sex"):
            await msg.channel.send("do not the sex")
        await self.bot.process_commands(msg)


def setup(bot):
    bot.add_cog(Message(bot))
