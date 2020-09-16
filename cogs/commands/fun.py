import asyncio
import discord
from discord.ext import commands, tasks
import prawcore  # because praw exceptions inherit from here
import random
import re as regex
from CatLampPY import reddit, isAdmin
import datetime

from hastebin import get_key


async def sendPost(ctx, post):
    randPost = post

    embed = discord.Embed(title=randPost.title, description=randPost.selftext,
                          url=f"https://www.reddit.com{randPost.permalink}")

    # remove problematic &#x200B; that fuck with link detection
    if randPost.selftext.startswith("&#x200B;\n"):
        embed.description = randPost.selftext.replace("&#x200B;\n", "").strip('\n')
        fuckYouX200B = True
    else:
        fuckYouX200B = False

    footerNote = None

    if randPost.url and not randPost.is_self:
        embed, footerNote = urlParse(randPost.url, embed)
    elif fuckYouX200B:
        embed, footerNote = urlParse(embed.description, embed)
    try:
        embed.set_author(name=f"Posted by /u/{randPost.author.name}")
    except AttributeError:
        embed.set_author(name=f"Posted by /u/[deleted]")
    footer = f"{str(round(randPost.upvote_ratio * 100))}% upvoted"
    if footerNote:
        footer += f" || {footerNote}"
    embed.set_footer(text=footer)
    embed.timestamp = datetime.datetime.fromtimestamp(randPost.created_utc)

    await ctx.send(embed=embed)
    return True


def urlParse(url: str, embed: discord.Embed):
    footerNote = ''
    checkImage = False
    expressions = []
    for i in ['img', 'image', 'gif', 'g.f', 'gf']:
        for ex in regex.findall(i, url):
            expressions.append(ex)
    if len(expressions) > 0:
        checkImage = True
    if url[-4:] in ('.gif', '.png', '.jpg', 'jpeg'):
        embed.set_image(url=url)
    if url.startswith("https://v.redd.it/") or url[-4:] in ('gifv', '.mp4',
                                                            'webm', 'webp'):
        embed.description = f"[(Video)]({url})"
        footerNote = 'This is a video, which is not supported in Discord bot embeds.'
        # Currently, it's impossible to add custom videos to embeds, so this is my solution for now.
    elif url.startswith("/r/"):
        embed.description = f"[(Crosspost)](https://www.reddit.com{url})"
    if not url.startswith("https://i.redd.it/"):
        if checkImage:
            badSite = None
            for i in ["https://gfycat.com", "https://redgifs.com", "https://imgur.com"]:
                if url.startswith(i):
                    badSite = i
            if badSite:
                embed.description = f"[(GIF)]({url})"
                footerNote = f'This GIF is on {badSite},' \
                             f' which is too complex for Discord bot embeds.'
        if url.startswith('https://www.reddit.com/gallery/'):
            footerNote = 'This is a Reddit Gallery, which is impossible to format into one ' \
                         'embed.'
        embed.description = f"[(Link)]({url})"
    if embed.description.startswith('https://preview.redd.it/'):
        embed.set_image(url=url)
        embed.description = None

    # try:
    #     if embed.description.startswith('http') and embed.image != discord.Embed.Empty:
    #         print('link to image, delete desc')
    #         embed.description = ''
    #     elif not embed.description.startswith('http') and embed.image != discord.embeds.EmbedProxy:
    # except AttributeError:  # ok there is no description, so just ignore lol
    #     pass

    return embed, footerNote


class Fun(commands.Cog):
    def __init__(self, bot):
        self.client = bot
        self.client.cmds.append(self.coinFlip)
        self.client.cmds.append(self.guess)
        self.client.cmds.append(self.redditRandom)
        self.inGame = []

        self.statReset.start()

    @commands.command(aliases=["flip"])
    async def coinFlip(self, ctx):
        """Flips a coin."""
        rand = random.randint(0, 1)
        side = random.randint(1, 20)
        if side == 20:
            await ctx.send("The coin landed on... its side?")
        elif rand == 0:
            await ctx.send("The coin landed on heads.")
        elif rand == 1:
            await ctx.send("The coin landed on tails.")

    @commands.command()
    async def guess(self, ctx):
        """Plays a number guessing game. Guess a random number between 1 and 10."""
        if ctx.author.id in self.inGame:
            return
        self.inGame.append(ctx.author.id)

        def check(m):
            b = m.author == ctx.message.author and m.channel == ctx.channel and m.content.isdigit()
            if b:
                b = 1 <= int(m.content) <= 10
            return b

        num = random.randint(1, 10)
        guesses = 3
        await ctx.send(f"{ctx.author.mention} Guess a number between 1 and 10. You have {guesses} guesses left.",
                       allowed_mentions=discord.AllowedMentions(users=False))
        while guesses > 0:
            try:
                Guess = await self.client.wait_for("message", check=check, timeout=15.0)
            except asyncio.TimeoutError:
                await ctx.send(f"You took too long, the correct number was {num}.")
                self.inGame.remove(ctx.author.id)
                return

            if int(Guess.content) == num:
                await ctx.send(f"Correct! The number was {num}.")
                self.inGame.remove(ctx.author.id)
                return
            else:
                guesses += -1
                msg = "Incorrect!"
                if guesses > 0:
                    msg += f"\n{ctx.author.mention} Guess a number between 1 and 10. You have {guesses} guesses left."
                else:
                    msg += f"\nYou're out of guesses! The correct number was {num}."
                    self.inGame.remove(ctx.author.id)
                await ctx.send(msg, allowed_mentions=discord.AllowedMentions(users=False))

    @commands.command(name='reddit', aliases=['randomReddit', 'redditRandom', 'randomPost'])
    async def redditRandom(self, ctx, subreddit_name: str):
        """Sends a random post from the specified subreddit."""
        # in case someone types it with r/ or /r/ at the start
        if subreddit_name.startswith('r/'):
            subreddit_name = subreddit_name[2:]
        elif subreddit_name.startswith('/r/'):
            subreddit_name = subreddit_name[3:]
        async with ctx.channel.typing():
            try:
                subreddit = reddit.subreddit(subreddit_name)
                try:
                    self.client.redditStats[subreddit.display_name.lower()] += 1
                except KeyError:
                    self.client.redditStats[subreddit.display_name.lower()] = 1
                if not ctx.message.channel.is_nsfw() and subreddit.over18:
                    await ctx.send("This subreddit is marked as NSFW. Please move to an NSFW channel.")
                    return
                satisfied = False
                tries = 0
                while not satisfied:
                    if tries >= 15:
                        await ctx.send("Failed to get a post.")
                        return
                    randPost = subreddit.random()
                    if (not randPost or randPost.distinguished or len(randPost.title) > 256 or
                            len(randPost.selftext) > 2048) or (randPost.over_18 and not ctx.message.channel.is_nsfw()):
                        tries += 1
                        continue
                    if not randPost.url or not randPost.selftext:  # just because i'm a nervous idiot so i need to check
                        pass
                    if await sendPost(ctx, randPost):
                        satisfied = True
            except prawcore.Forbidden:
                await ctx.send("Subreddit is private.")
            except(prawcore.BadRequest, prawcore.Redirect, prawcore.NotFound):
                await ctx.send("Subreddit not found.")

    @commands.command(hidden=True)
    async def testPost(self, ctx, postID):
        if isAdmin(ctx.author):
            await sendPost(ctx, reddit.submission(id=postID))

    async def sendData(self, channel: discord.abc.Messageable):
        if len(self.client.redditStats) > 1:
            embed = None
            titleMaybe = ''
            content = ''
            if len(self.client.redditStats) <= 26:
                embed = discord.Embed(title=f"Reddit data for {self.client.redditStats['Date'].isoformat()}")
                for i in self.client.redditStats:
                    if i != 'Date':
                        embed.add_field(name=f'r/{i}', value=self.client.redditStats[i])
                embed.timestamp = datetime.datetime.now()
            else:  # stringify it because
                titleMaybe = f"Reddit data for {self.client.redditStats['Date'].isoformat()}"
                for i in self.client.redditStats:
                    if i != 'Date':
                        content += f'\nr/{i}:\n{self.client.redditStats[i]}'

            if embed:
                await channel.send(embed=embed)
            else:
                payload = f'{titleMaybe}\n{content}'
                await channel.send(f'There was too much data, so it was uploaded to Hastebin:\n'
                                   f'https://hastebin.com/{get_key(payload)}')
        else:
            await channel.send('There is no data to send!')

    @commands.command(hidden=True, aliases=['redditAnal', 'redAnal'])
    async def redditAnalytics(self, ctx):
        if isAdmin(ctx.author):
            await self.sendData(ctx)

    def cog_unload(self):
        if len(self.client.redditStats) > 1:
            print(f"Reddit data for {self.client.redditStats['Date'].isoformat()}")
            content = ''
            for i in self.client.redditStats:
                if i != 'Date':
                    content += f'\nr/{i}:\n{self.client.redditStats[i]}'
            print(content)

    @tasks.loop(hours=24)
    async def statReset(self):
        self.client.redditStats = {'Date': datetime.date.today()}  # reset stats

    @statReset.after_loop
    async def on_daily_cancel(self):
        if self.statReset.is_being_cancelled():
            print(f"Reddit data for {self.client.redditStats['Date'].isoformat()}")
            content = ''
            for i in self.client.redditStats:
                if i != 'Date':
                    content += f'\nr/{i}:\n{self.client.redditStats[i]}'
            print(content)

    @statReset.before_loop
    async def before_daily(self):
        await self.client.wait_until_ready()


def setup(bot):
    bot.add_cog(Fun(bot))
