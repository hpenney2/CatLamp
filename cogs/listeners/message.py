from discord.ext import commands


class Message(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, msg):
        if msg.author.id == self.bot.user.id or msg.author.bot:
            return
        if msg.content != "python" and "do not the sex" in msg.content.lower():
            await msg.channel.send("do not the sex")
        elif msg.content != "python" and "do the sex" in msg.content.lower():
            await msg.channel.send("do **not** the sex")
        elif msg.content != "python" and "psps" in msg.content.lower():
            await msg.add_reaction('<:lampstare:747483819388436570>')


def setup(bot):
    bot.add_cog(Message(bot))
