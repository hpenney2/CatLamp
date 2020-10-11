import asyncio
import discord
from discord.ext import commands
import prawcore  # because praw exceptions inherit from here
import random
import re as regex
# pylint: disable=import-error
from CatLampPY import reddit
from cogs.misc.isAdmin import isAdmin
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
                footerNote = f'This GIF is on {badSite}, which appears inconsistently in Discord bot embeds.'
        if url.startswith('https://www.reddit.com/gallery/'):
            footerNote = 'This is a Reddit Gallery, which is impossible to format into one ' \
                         'embed.'
        embed.description = f"[(Link)]({url})"
    if embed.description.startswith('https://preview.redd.it/'):
        embed.set_image(url=url)
        embed.description = None

    try:
        if embed.description.startswith('http') and hasImage(embed):
            # this is a link to image, so delete
            embed.description = ''
        elif not (embed.description.startswith('http') or not embed.description) and hasImage(embed):
            # desc is not image link, delete image
            embed.set_image(url=discord.Embed.Empty)
    except AttributeError:  # ok there is no description, so just ignore lol
        pass

    return embed, footerNote


def hasImage(embed: discord.Embed):
    if embed.image:
        return True
    else:
        return False


async def sendData(client, channel: discord.abc.Messageable):
    embed = discord.Embed(title=f"Reddit data for {client.redditStats['Date'].isoformat()}")
    embed.timestamp = datetime.datetime.utcnow()
    if len(client.redditStats) > 1:
        if len(client.redditStats) <= 26:
            for i in client.redditStats:
                if i != 'Date':
                    embed.add_field(name=f'r/{i}', value=client.redditStats[i])
        else:  # stringify it because
            embed = None
            content = ''
            for i in client.redditStats:
                if i != 'Date':
                    content += f'\nr/{i}:\n{client.redditStats[i]}'

        if not embed:
            # noinspection PyUnboundLocalVariable
            payload = f'Reddit data for {client.redditStats["Date"].isoformat()}\n{content}'
            await channel.send(f'There was too much data, so it was uploaded to Hastebin:\n'
                               f'https://hastebin.com/{get_key(payload)}')
    else:
        embed.add_field(name=":(", value="There is no data to send!")
    await channel.send(embed=embed)


class Fun(commands.Cog):
    def __init__(self, bot):
        self.client = bot
        self.client.cmds.append(self.coinFlip)
        self.client.cmds.append(self.guess)
        self.client.cmds.append(self.redditRandom)
        self.degenerates = []
        self.inGame = []

    @commands.command(aliases=["coinToss"])
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
                if subreddit.over18:
                    if not await self.nsfwCheck(ctx, "subreddit"):
                        return
                satisfied = False
                errorMess = ''
                tries = 0
                while not satisfied:
                    if tries >= 15:
                        errorMess = "Failed to get a post."
                        break
                    randPost = subreddit.random()
                    if (not randPost or randPost.distinguished or len(randPost.title) > 256 or
                            len(randPost.selftext) > 2048) or \
                            (randPost.over_18 and not await self.nsfwCheck(ctx, "post")):
                        tries += 1
                        del randPost
                        continue
                    if not (randPost.url or randPost.selftext):  # just because i'm a nervous idiot so i need to check
                        tries += 1
                        del randPost
                        continue
                    satisfied = True
            except prawcore.Forbidden:
                errorMess = "Subreddit is private."
            except(prawcore.BadRequest, prawcore.Redirect, prawcore.NotFound):
                errorMess = "Subreddit not found."

        if errorMess:
            await ctx.send(errorMess)
        elif randPost:
            await sendPost(ctx, randPost)
        else:
            await ctx.send('oy something went wrong big oh no')

    @commands.command(hidden=True)
    @commands.check(isAdmin)
    async def testPost(self, ctx, postID):
        await sendPost(ctx, reddit.submission(id=postID))

    async def nsfwCheck(self, ctx: commands.Context, unit: str):
        note = ''
        if ctx.channel.type == discord.ChannelType.text:  # server/text-channel
            if not ctx.message.channel.is_nsfw():
                note = f"This {unit} is marked as NSFW. Please move to an NSFW channel."
            cool = ctx.message.channel.is_nsfw()
        else:
            if ctx.author.id in self.degenerates:
                cool = True
            else:
                cool = await self.check(ctx, unit)
                if cool:
                    self.degenerates.append(ctx.author.id)

        if unit != 'post':
            if note:
                await ctx.send(note)
        return cool

    async def check(self, ctx: commands.Context, unit: str):
        confirmMess = await ctx.send(f'This {unit} is NSFW. Are you over 18 and *sure* you want to view this content?')
        await confirmMess.add_reaction('✅')
        await confirmMess.add_reaction('❌')

        # wait_for stolen from docs example
        def confirm(react, reactor):
            return reactor == ctx.author and str(react.emoji) in ('✅', '❌') and confirmMess.id == react.message.id

        try:
            reaction, user = await self.client.wait_for('reaction_add', timeout=30, check=confirm)
        except asyncio.TimeoutError:  # timeout cancel
            await confirmMess.edit(text='`+reddit` timed-out.')
        else:
            if reaction.emoji == '✅':
                await confirmMess.delete()
                return True

            else:  # ❌ react cancel
                await confirmMess.remove_reaction('✅', self.client.user)
                await confirmMess.remove_reaction('❌', self.client.user)
            try:
                await confirmMess.remove_reaction('❌', user)
            except (discord.Forbidden, discord.NotFound):
                pass
            await confirmMess.edit(content='`+reddit` was cancelled.')

    @commands.command(hidden=True, aliases=['redditAnal', 'redAnal'])
    @commands.check(isAdmin)
    async def redditAnalytics(self, ctx):
        if ctx.channel.id == 712489826330345534:
            await sendData(self.client, ctx)
        else:
            await ctx.send('This command is locked to <#712489826330345534>.')


def setup(bot):
    bot.add_cog(Fun(bot))
