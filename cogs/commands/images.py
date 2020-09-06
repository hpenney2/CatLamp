import deeppyer
# noinspection PyPackageRequirements
import PIL
from PIL import Image
import io
import discord
from discord.ext import commands


async def getImage(ctx, user: discord.User = None):
    image = Image.open(io.BytesIO(await ctx.author.avatar_url_as(format="png").read()))
    if len(ctx.message.attachments) > 0 and ctx.message.attachments[0].url[-4:] in ('.png', '.jpg', 'jpeg', '.gif'):
        image = Image.open(io.BytesIO(await ctx.message.attachments[0].read(use_cached=True)))
    elif user:
        image = Image.open(io.BytesIO(await user.avatar_url_as(format="png").read()))
    return image


class Images(commands.Cog, name="Image Manipulation"):
    def __init__(self, bot):
        self.bot = bot
        self.bot.cmds.append(self.deepfry)

    @commands.command(cooldown_after_parsing=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def deepfry(self, ctx, user: discord.User = None):
        """Deepfries the attached image or your/the mentioned user's avatar."""
        async with ctx.channel.typing():
            image = await getImage(ctx, user)
            deepImg = await deeppyer.deepfry(image, flares=False)
            img = io.BytesIO()
            deepImg.save(img, "png")
            img.seek(0)
            await ctx.send(file=discord.File(img, "deepfry.png"))

    @commands.command(cooldown_after_parsing=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def catLamp(self, ctx, user: discord.User = None):
        """catlamp here"""
        async with ctx.channel.typing():
            image = await getImage(ctx, user)
            size = 870, 870  # the resolutions need to match
            image.thumbnail(size)
            template = PIL.Image.open('catlamp-outlineonly.png', mode='r')

            outImg = PIL.Image.alpha_composite(image, template)  # processing here

            img = io.BytesIO()
            outImg.save(img, "png")
            img.seek(0)
            await ctx.send(file=discord.File(img, "catlamp.png"))


def setup(bot):
    bot.add_cog(Images(bot))


# template because I can
#     @commands.command(cooldown_after_parsing=True)
#     @commands.cooldown(1, 5, commands.BucketType.user)
#     async def name(self, ctx, user: discord.User = None):
#         """document here"""
#         async with ctx.channel.typing():
#             image = await getImage(ctx, user)
#
#             outImg = None  # processing here
#
#             img = io.BytesIO()
#             outImg.save(img, "png")
#             img.seek(0)
#             await ctx.send(file=discord.File(img, "image.png"))
