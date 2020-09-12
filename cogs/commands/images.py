import deeppyer
# noinspection PyPackageRequirements
from PIL import Image, ImageOps
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


def hippityHoppityThisColorIsDisappearity(img: Image.Image, color: tuple = (0, 255, 0)):
    """Alias for replaceColor() with a result of transparent white"""
    return replaceColor(img, targetIn=color, colorOut=(255, 255, 255, 0))


# https://stackoverflow.com/questions/765736/using-pil-to-make-all-white-pixels-transparent
def replaceColor(image: Image.Image, targetIn: tuple, colorOut: tuple):
    img = image.convert("RGBA")
    data = img.getdata()

    newData = []
    try:
        for item in data:
            if item[0] == targetIn[0] and item[1] == targetIn[1] and item[2] == targetIn[2] and item[3] == targetIn[3]:
                newData.append(colorOut)
            else:
                newData.append(item)
    except IndexError:
        for item in data:
            if item[0] == targetIn[0] and item[1] == targetIn[1] and item[2] == targetIn[2]:
                newData.append(colorOut)
            else:
                newData.append(item)

    img.putdata(newData)

    return img


def findMonoAlphaTarget(image: Image.Image):
    satisfied = False
    potentialTarget = (0, 255, 0, 255)  # start with green
    blacklist = []
    fuck = 0

    while not satisfied:
        if fuck == 10:
            random.seed()
            fuck = 0

        if potentialTarget not in blacklist:
            if potentialTarget in image.getdata():
                blacklist.append(potentialTarget)
            else:
                satisfied = True
        else:
            fuck += 1

        # randomize target
        potentialTarget = (random.randrange(0, 256), random.randrange(0, 256), random.randrange(0, 256), 255)

    return potentialTarget


def findDualAlphaTarget(image1: Image.Image, image2: Image.Image):
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

    return potentialTarget


async def sendImage(ctx: commands.context, outImg: Image.Image, filename: str):
    img = io.BytesIO()
    outImg.save(img, "png")
    img.seek(0)
    await ctx.send(file=discord.File(img, filename))


class Images(commands.Cog, name="Image Manipulation"):
    def __init__(self, bot):
        self.bot = bot
        self.bot.cmds.append(self.deepfry)
        try:
            self.catLampTemplate = Image.open('images/catlamp-outlineonly.png', mode='r').convert('RGBA')
            self.dioTemplate = Image.open('images/dio.png', mode='r').convert('RGBA')
            self.flushedTemplate = Image.open('images/flushed.png', mode='r').convert('RGBA')
        except FileNotFoundError:
            self.catLampTemplate = Image.open('cogs/commands/images/catlamp-outlineonly.png', mode='r').convert('RGBA')
            self.dioTemplate = Image.open('cogs/commands/images/dio.png', mode='r').convert('RGBA')
            self.flushedTemplate = Image.open('cogs/commands/images/flushed.png', mode='r').convert('RGBA')

    @commands.command(cooldown_after_parsing=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def deepfry(self, ctx, user: discord.User = None):
        """Deepfries the attached image or your/the mentioned user's avatar."""
        async with ctx.channel.typing():
            image = await getImage(ctx, user)
            deepImg = await deeppyer.deepfry(image, flares=False)
            deepImg = deepImg.convert('RGBA')  # i dunno, deepImg is an Image.py, but sendImage() wants Image
            await sendImage(ctx, deepImg, "deepfry.png")

    @commands.command(cooldown_after_parsing=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def catLamp(self, ctx, user: discord.User = None):
        """Generates a Catlamp of the attached image or your/the mentioned user's avatar."""
        async with ctx.channel.typing():
            # set the images
            image = await getImage(ctx, user)
            overlay = self.catLampTemplate.copy()

            # find a color not in either image so we can use it for transparency in the final product
            alpha = findDualAlphaTarget(image, overlay)

            # convert the images to be equal in size and mode for compatibility
            image = forceSquare(image)

            if image.size > overlay.size:
                image.thumbnail(overlay.size)
                # set alpha color outside of the lamp (replace green with the designated alpha color)
                overlay = replaceColor(overlay, (0, 255, 0, 255), alpha)

                # cut hole in template (remove the magenta pixels)
                overlay = hippityHoppityThisColorIsDisappearity(overlay, (255, 0, 255, 255))
            else:
                # cut hole in template (remove the magenta pixels)
                overlay = hippityHoppityThisColorIsDisappearity(overlay, (255, 0, 255, 255))

                overlay.thumbnail(image.size, Image.NEAREST)  # this son of the bitches is the problem

                # replace transparent green with alpha
                overlay = replaceColor(overlay, (0, 255, 0, 255), alpha)

            image = image.convert(mode=overlay.mode)

            # combine catLamp with image
            outImg = Image.alpha_composite(image, overlay)

            # make the outside actually transparent
            outImg = hippityHoppityThisColorIsDisappearity(outImg, alpha)

            # final prep and stuff for sending to the *internet*
            await sendImage(ctx, outImg, "catlamp.png")

    @commands.command(cooldown_after_parsing=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def dio(self, ctx, user: discord.User = None):
        """You expected the attached image or your/the mentioned user's avatar, but it was I, Dio!"""
        async with ctx.channel.typing():
            # set the images
            image = await getImage(ctx, user)
            overlay = self.dioTemplate.copy()

            # convert the images to be equal in size and mode for compatibility
            image = forceSquare(image)

            # cut hole in template (remove the magenta pixels)
            overlay = hippityHoppityThisColorIsDisappearity(overlay, (255, 0, 255, 255))

            if image.size > overlay.size:
                image.thumbnail(overlay.size)
            else:
                overlay.thumbnail(image.size)  # this son of the bitches is the problem

            image = image.convert(mode=overlay.mode)

            # combine dio with image
            outImg = Image.alpha_composite(image, overlay)

            # final prep and stuff for sending to the *internet*
            await sendImage(ctx, outImg, "SPOILER_dio.png")

    @commands.command(cooldown_after_parsing=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def flushed(self, ctx, user: discord.User = None):
        """The attached image or your/the mentioned user's avatar: 😳"""
        async with ctx.channel.typing():
            # set the images
            image = await getImage(ctx, user)
            overlay = self.flushedTemplate.copy()

            # convert the images to be equal in size and mode for compatibility
            image = forceSquare(image)

            # cut hole in template (remove the magenta pixels)
            overlay = hippityHoppityThisColorIsDisappearity(overlay, (255, 0, 255, 255))

            if image.size > overlay.size:
                image.thumbnail(overlay.size)
            else:
                overlay.thumbnail(image.size)  # this son of the bitches is the problem

            image = image.convert(mode=overlay.mode)

            # combine dio with image
            outImg = Image.alpha_composite(image, overlay)

            # final prep and stuff for sending to the *internet*
            await sendImage(ctx, outImg, "flushed.png")

    @commands.command(cooldown_after_parsing=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def invert(self, ctx, user: discord.User = None):
        """Inverts the attached image or your/the mentioned user's avatar."""
        async with ctx.channel.typing():
            image = await getImage(ctx, user)

            if image.mode == "RGBA":
                alpha = findMonoAlphaTarget(image)

                alphaTemp = Image.new('RGB', (1, 1), alpha)
                alphaTemp = ImageOps.invert(alphaTemp)

                alphaInvert = alphaTemp.getdata()[0]  # find inverted alpha color

                image = Image.alpha_composite(Image.new('RGBA', (image.width, image.height), alpha), image)

            image = image.convert('RGB')  # i dunno, ImageOps wants an RGB
            image = ImageOps.invert(image)

            if alphaInvert:
                image = hippityHoppityThisColorIsDisappearity(image, alphaInvert)

            await sendImage(ctx, image, "invert.png")

    @commands.command(cooldown_after_parsing=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def sadden(self, ctx, user: discord.User = None):
        """😔"""
        async with ctx.channel.typing():
            image = await getImage(ctx, user)

            image = image.convert('RGB')  # i dunno, ImageOps wants an RGB
            image = ImageOps.grayscale(image)

            await sendImage(ctx, image, "grayscale.png")




def setup(bot):
    bot.add_cog(Images(bot))

# general template because I can
#     @commands.command(cooldown_after_parsing=True)
#     @commands.cooldown(1, 5, commands.BucketType.user)
#     async def name(self, ctx, user: discord.User = None):
#         """document here"""
#         async with ctx.channel.typing():
#             image = await getImage(ctx, user)
#
#             outImg = None  # processing here
#
#             await sendImage(ctx, outImg, "image.png")

# cookie-cutter ImageOps command template
#     @commands.command(cooldown_after_parsing=True)
#     @commands.cooldown(1, 5, commands.BucketType.user)
#     async def name(self, ctx, user: discord.User = None):
#         """Inverts the attached image or your/the mentioned user's avatar."""
#         async with ctx.channel.typing():
#             image = await getImage(ctx, user)
#
#             if image.mode == "RGBA":
#                 alpha = findMonoAlphaTarget(image)
#
#                 alphaTemp = Image.new('RGB', (1, 1), alpha)
#                 alphaTemp = ImageOps.invert(alphaTemp)
#
#                 alphaInvert = alphaTemp.getdata()[0]  # find inverted alpha color
#
#                 image = Image.alpha_composite(Image.new('RGBA', (image.width, image.height), alpha), image)
#
#                 await sendImage(ctx, image, "debug.png")
#
#             image = image.convert('RGB')  # i dunno, ImageOps wants an RGB
#             image = ImageOps.invert(image)  #  ImageOps function I guess
#
#             if alphaInvert:
#                 image = hippityHoppityThisColorIsDisappearity(image, alphaInvert)
#
#             await sendImage(ctx, image, "invert.png")
