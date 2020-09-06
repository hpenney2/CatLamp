import deeppyer
# noinspection PyPackageRequirements
from PIL import Image
import io
import discord
from discord.ext import commands
import random


async def getImage(ctx, user: discord.User = None):
    image = Image.open(io.BytesIO(await ctx.author.avatar_url_as(format="png").read()))
    if len(ctx.message.attachments) > 0 and ctx.message.attachments[0].url[-4:] in ('.png', '.jpg', 'jpeg', '.gif'):
        image = Image.open(io.BytesIO(await ctx.message.attachments[0].read(use_cached=True)))
    elif user:
        image = Image.open(io.BytesIO(await user.avatar_url_as(format="png").read()))
    return image


# stole off the site with best SEO, https://note.nkmk.me/en/python-pillow-square-circle-thumbnail/
def forceSquare(pil_img):
    background_color = (0, 0, 0, 0)
    width, height = pil_img.size
    if width == height:
        return pil_img
    elif width > height:
        result = Image.new(pil_img.mode, (width, width), background_color)
        result.paste(pil_img, (0, (width - height) // 2))
        return result
    else:
        result = Image.new(pil_img.mode, (height, height), background_color)
        result.paste(pil_img, ((height - width) // 2, 0))
        return result


# https://stackoverflow.com/questions/765736/using-pil-to-make-all-white-pixels-transparent
def hippityHoppityThisColorIsDisappearity(img: Image.Image, color: tuple = (0, 255, 0)):
    img = img.convert("RGBA")
    data = img.getdata()

    newData = []
    for item in data:

        if item[0] == color[0] and item[1] == color[1] and item[2] == color[2]:
            newData.append((255, 255, 255, 0))
        else:
            newData.append(item)

    img.putdata(newData)

    return img


def replaceColor(image: Image.Image, targetIn: tuple, colorOut: tuple):
    image = hippityHoppityThisColorIsDisappearity(image, targetIn)
    result = Image.new(mode=image.mode, size=(image.width, image.height), color=colorOut)
    result.paste(image)
    return result


def findAlphaTarget(image1: Image.Image, image2: Image.Image):

    satisfied = False
    potentialTarget = (0, 255, 0, 255)  # start with green
    blacklist = []
    fuck = 0

    while not satisfied:
        if fuck == 10:
            random.seed()
            fuck = 0

        if potentialTarget not in blacklist:
            if potentialTarget in image1.getdata() or potentialTarget in image2.getdata():
                blacklist.append(potentialTarget)
            else:
                satisfied = True
        else:
            fuck += 1

        # randomize target
        potentialTarget = (random.randrange(0, 256), random.randrange(0, 256), random.randrange(0, 256), 255)

    print(potentialTarget)
    return potentialTarget


class Images(commands.Cog, name="Image Manipulation"):
    def __init__(self, bot):
        self.bot = bot
        self.bot.cmds.append(self.deepfry)
        self.catLampTemplate = Image.open('catlamp-outlineonly.png', mode='r').convert('RGBA')

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
            # set the images
            image = await getImage(ctx, user)
            overlay = self.catLampTemplate

            # convert the images to be equal in size and mode for compatibility
            image = forceSquare(image)
            if image.size > overlay.size:
                image.thumbnail(overlay.size)
            else:
                overlay.thumbnail(image.size)
            image = image.convert(mode=overlay.mode)

            # find a color not in either image so we can use it for transparency in the final product
            alpha = findAlphaTarget(image, overlay)

            # set alpha color outside of the lamp
            overlay = replaceColor(overlay, (0, 255, 0, 255), alpha)

            # combine catLamp with image
            outImg = overlay#Image.alpha_composite(image, overlay)

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
