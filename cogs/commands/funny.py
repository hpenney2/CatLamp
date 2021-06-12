import re
from typing import List
from typing import Union

from yippi.Exceptions import UserError

from CatLampPY import CommandErrorMsg
import discord
from discord.ext import commands
from cogs.misc.nsfw import canNSFW
from pygelbooru import Gelbooru
import random
import re as regex
from yippi import AsyncYippiClient


class r34(Gelbooru):
    BASE_URL = "https://rule34.xxx/"


class e926(AsyncYippiClient):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def _call_api(self, method, url, **kwargs):
        query_string = self._generate_query_keys(**kwargs)
        url = re.sub(r'https://e621\.net', 'https://e926.net', url)
        print(url)
        url += "?" + query_string
        r = await self._session.request(method, url, headers=self.headers)
        await self._verify_response(r)
        return await r.json()


def urlParse(url: str, embed: discord.Embed):
    footerNote = ''
    checkImage = False

    # if "?" in url:  # remove get tags for processing and potentially higher quality (no thumbnailing except discord's)
    #     url = url.split("?")[0]

    # do this before we make things NoneType again
    embed.description = f"[(Link)]({url})"

    # check for potential image sharing site
    if regex.findall(r'img|image|g.f|gf', url.lower()):
        checkImage = True

    # coolio image
    if url[-4:] in ('.gif', '.png', '.jpg', 'jpeg') or regex.findall(r'\.png|\.jpg|\.jpeg|\.webp|\.gif', url):
        embed.description = None
        embed.set_image(url=url)

    # not coolio video
    if url.startswith("https://v.redd.it/") or url[-4:] in ('gifv', '.mp4',
                                                            'webm', 'webp'):
        embed.description = f"[(Video)]({url})"  # link to not coolio
        embed.set_image(url=discord.Embed.Empty)  # in case it was a gifv that got picked up by image
        footerNote = 'This is a video, which is not supported in Discord bot embeds.'
        # Currently, it's impossible to add custom videos to embeds, so this is my solution for now.

    if not url.startswith("'https://static1.e926.net/data/" or "https://api-cdn.rule34.xxx/images/"):
        if checkImage:
            badSite = None
            for i in ["https://gfycat.com", "https://redgifs.com", "https://imgur.com"]:
                if i[5:].split('.')[0] in url:
                    badSite = i
            if badSite:
                footerNote = f'This media is on {badSite}, which appears inconsistently in Discord bot embeds.'

    return embed, footerNote


class NSFW(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.gelbooru = r34()
        self.e621 = AsyncYippiClient("Catlamp", "0.1-indev", "joelemonade")
        self.e926 = e926("Catlamp", "0.1-indev", "joelemonade")

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, reactor):
        print(reactor)
        print(reaction)

    @commands.command(aliases=['r34', 'rule_34', 'rule-34'])
    @commands.check(canNSFW)
    async def rule34(self, ctx, *tags):
        """Sends a random rule34 post based on the specified tags. (tags optional)"""
        post = await self.gelbooru.random_post(tags=list(tags))
        if post:
            embed = discord.Embed(title="Sauce")
            embed.url = f"https://rule34.xxx/index.php?page=post&s=view&id={post.id}"
            embed, footerNote = urlParse(url=post.file_url, embed=embed)
            print(post.file_url)
            tags = footerNote + " • Tags: " + (', '.join(post.tags[1:]).rstrip(", "))
            tags = tags.lstrip(" • ")
            if len(tags) > 2048:
                tags = tags[:2045]
                tags = tags.split(", ")
                tags = tags[:-1]
                tags = (', '.join(tags[1:]).rstrip(", ")) + "..."
            embed.set_footer(text=tags)
            await ctx.send(embed=embed)
        else:
            raise CommandErrorMsg("No post could be found with those tags.")
        return

    @commands.command(aliases=['e6', '621', 'monoSodium-glutamate'])
    @commands.check(canNSFW)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def e621(self, ctx, *tags):
        """Sends a random e621 post based on the specified tags. (tags optional)"""
        posts = await self.e621.posts(list(tags))
        if posts:
            post = random.choice(list(posts))
            print(post.file)
            print(post.id)
            print(post.description)
            print(post.tags)
            embed = discord.Embed(title="OwO what's this?~")
            if post.description:
                tags = regex.sub(r'\[[^]]*]', '', post.description)
                if len(tags) > 2048:
                    tags = tags[:2045]
                    tags = tags.split(" ")
                    tags = tags[:-1]
                    embed.description = (' '.join(tags[1:]).rstrip(" ")) + "..."
                else:
                    embed.description = tags
            embed.set_author(name=", ".join(post.tags["artist"]).rstrip(", "))
            embed.url = f"https://e621.net/posts/{post.id}"
            embed, footerNote = urlParse(url=post.file["url"], embed=embed)

            tags = footerNote + " • Tags: " + (
                ', '.join(post.tags["general"] + post.tags["species"] + post.tags["character"]).rstrip(", ")
            )
            tags = tags.lstrip(" • ")

            if len(tags) > 2048:
                tags = tags[:2048]
                tags = tags.split(", ")
                tags = tags[:-1]
                tags = (', '.join(tags[1:]).rstrip(", "))
            embed.set_footer(text=tags)
            await ctx.send(embed=embed)
        else:
            raise CommandErrorMsg("No post could be found with those tags.")

    @commands.command(aliases=['e9', '926', 'chlorine-dioxide'])
    @commands.check(canNSFW)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def e926(self, ctx, *tags):
        """Sends a random e926 post based on the specified tags. (tags optional)"""
        posts = await self.e926.posts(list(tags))
        if posts:
            post = random.choice(list(posts))
            print(post.file)
            print(post.id)
            print(post.description)
            print(post.tags)
            embed = discord.Embed(title="OwO what's this?~")
            if post.description:
                tags = regex.sub(r'\[[^]]*]', '', post.description)
                if len(tags) > 2048:
                    tags = tags[:2045]
                    tags = tags.split(" ")
                    tags = tags[:-1]
                    embed.description = (' '.join(tags[1:]).rstrip(" ")) + "..."
                else:
                    embed.description = tags
            embed.set_author(name=", ".join(post.tags["artist"]).rstrip(", "))
            embed.url = f"https://e926.net/posts/{post.id}"
            embed, footerNote = urlParse(url=post.file["url"], embed=embed)

            tags = footerNote + " • Tags: " + (
                ', '.join(post.tags["general"] + post.tags["species"] + post.tags["character"]).rstrip(", ")
            )
            tags = tags.lstrip(" • ")

            if len(tags) > 2048:
                tags = tags[:2048]
                tags = tags.split(", ")
                tags = tags[:-1]
                tags = (', '.join(tags[1:]).rstrip(", "))
            embed.set_footer(text=tags)
            await ctx.send(embed=embed)
        else:
            raise CommandErrorMsg("No post could be found with those tags.")


def setup(bot):
    bot.add_cog(NSFW(bot))
