from discord.ext import commands
import re as regex
import datetime

noPrefixBlacklist = [
    264445053596991498,  # Discord Bot List
    336642139381301249,  # discord.py
]


def isOk(msg):
    if msg.guild:
        if msg.guild.id in noPrefixBlacklist:
            return False
    return True


class Message(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.crappyCapsDetector = regex.compile("[P, S][p,s]|[p, s][P, S]")  # i gotta be honest

    @commands.Cog.listener()
    async def on_message(self, msg):
        start = datetime.datetime.now()
        if isOk(msg):
            if msg.author.id == self.bot.user.id or msg.author.bot or msg.content == "python":
                return

            if "do not the sex" in msg.content.lower():
                await msg.channel.send("do not the sex")
            elif "do the sex" in msg.content.lower():
                await msg.channel.send("do **not** the sex")
            if "psps" in msg.content.lower():
                # piss counter
                piss = 0
                for _ in regex.findall("ps", msg.content.lower()):
                    piss += 1

                # full piss counter
                capitals = 0
                for _ in regex.findall("PS", msg.content):
                    capitals += 2
                if capitals / 2 == piss:  # if it's all PS, let it w i d e
                    print('piss')
                    piss = 3

                if piss >= 3:
                    for _ in regex.findall(self.crappyCapsDetector, msg.content):
                        capitals += 1

                    if capitals >= 3:
                        await msg.add_reaction('<:lampstarenear:775818082534424577>')
                        return
                await msg.add_reaction('<:lampstare:747483819388436570>')


def setup(bot):
    bot.add_cog(Message(bot))
