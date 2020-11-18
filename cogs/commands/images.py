import math

import deeppyer
# noinspection PyPackageRequirements
from PIL import Image, ImageOps, ImageEnhance
import io
import discord
from discord.ext import commands
import random
from typing import Union
import re as regex
import aiohttp
# pylint: disable=import-error
from CatLampPY import CommandErrorMsg


async def getImage(ctx, user: Union[discord.Member, str, None] = None):
    try:
        image = Image.open(io.BytesIO(await ctx.author.avatar_url_as(format="png").read()))
    except discord.NotFound:
        try:
            image = Image.open(io.BytesIO((await ctx.bot.fetch_user(ctx.author.id)).avatar_url_as(format="png").read()))
        except discord.NotFound:
            image = CommandErrorMsg("Your profile picture could not be fetched at this time. "
                                    "Try attaching an image instead.")

    if len(ctx.message.attachments) > 0 and ctx.message.attachments[0].url[-4:] in ('.png', '.jpg', 'jpeg', '.gif'):
        image = Image.open(io.BytesIO(await ctx.message.attachments[0].read(use_cached=True)))
    elif user and isinstance(user, discord.Member):
        try:
            image = Image.open(io.BytesIO(await user.avatar_url_as(format="png").read()))
        except discord.NotFound:
            try:
                image = Image.open(io.BytesIO((await ctx.bot.fetch_user(user.id)).avatar_url_as(format="png").read()))
            except discord.NotFound:
                image = CommandErrorMsg(f"{user}'s profile picture could not be fetched at this time. "
                                        "Try attaching an image instead.")

    elif user and isinstance(user, str):
        if "?" in user:  # remove get tags for processing and potentially higher quality (no resolution get tags)
            user = user.split("?")[0]

        matcher = regex.compile(
            r'^(?:http|ftp)s?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
            # r'localhost|' #localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', regex.IGNORECASE)
        if regex.match(matcher, user) and user[-4:] in ('.png', '.jpg', 'jpeg', '.gif'):
            async with aiohttp.request('get', user) as res:
                if res.status == 200:
                    image = Image.open(io.BytesIO(await res.read()))
                else:
                    raise CommandErrorMsg(f'There was an issue getting the URL "{user}"!')
        else:
            raise CommandErrorMsg(f'"{user}" is not a valid user or image URL!')
    if isinstance(image, CommandErrorMsg):
        raise image
    return image


# stole off the site with best SEO, https://note.nkmk.me/en/python-pillow-square-circle-thumbnail/
def centerSquare(pil_img: Image.Image):
    """Adds padding on both sides to make an image square. (Centered)"""
    pil_img = pil_img.convert('RGBA')  # ensure transparency
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


def simpSquare(pil_img: Image.Image):
    """Adds padding to the bottom or right of an image to make it square."""
    background_color = (0, 0, 0, 0)
    width, height = pil_img.size
    if width == height:
        return pil_img
    elif width > height:
        result = Image.new(pil_img.mode, (width, width), background_color)
        result.paste(pil_img, (0, 0))
        return result, 'Y'
    else:
        result = Image.new(pil_img.mode, (height, height), background_color)
        result.paste(pil_img, (0, 0))
        return result, 'X'


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
            self.joyTemplate = Image.open('images/joy.png', mode='r').convert('RGBA')
        except FileNotFoundError:
            self.catLampTemplate = Image.open('cogs/commands/images/catlamp-outlineonly.png', mode='r').convert('RGBA')
            self.dioTemplate = Image.open('cogs/commands/images/dio.png', mode='r').convert('RGBA')
            self.flushedTemplate = Image.open('cogs/commands/images/flushed.png', mode='r').convert('RGBA')
            self.joyTemplate = Image.open('cogs/commands/images/joy.png', mode='r').convert('RGBA')

    @commands.command(cooldown_after_parsing=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def deepfry(self, ctx, *, user_or_url: Union[discord.Member, str, None] = None):
        """Deepfries the attached image or your/the mentioned user's avatar."""
        async with ctx.channel.typing():
            image = await getImage(ctx, user_or_url)
            deepImg = await deeppyer.deepfry(image, flares=False)
            deepImg = deepImg.convert('RGBA')  # i dunno, deepImg is an Image.py, but sendImage() wants Image
            await sendImage(ctx, deepImg, "deepfry.png")

    @commands.command(cooldown_after_parsing=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def catLamp(self, ctx, *, user_or_url: Union[discord.Member, str, None] = None):
        """Generates a Catlamp of the attached image or your/the mentioned user's avatar."""
        async with ctx.channel.typing():
            # set the images
            image = await getImage(ctx, user_or_url)
            overlay = self.catLampTemplate.copy()

            # find a color not in either image so we can use it for transparency in the final product
            alpha = findDualAlphaTarget(image, overlay)

            # convert the images to be equal in size and mode for compatibility
            image = centerSquare(image)

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
    async def dio(self, ctx, *, user_or_url: Union[discord.Member, str, None] = None):
        """You expected the attached image or your/the mentioned user's avatar, but it was I, Dio!"""
        async with ctx.channel.typing():
            # set the images
            image = await getImage(ctx, user_or_url)
            overlay = self.dioTemplate.copy()

            # convert the images to be equal in size and mode for compatibility
            image = centerSquare(image)

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
    async def flushed(self, ctx, *, user_or_url: Union[discord.Member, str, None] = None):
        """The attached image or your/the mentioned user's avatar: 😳"""
        async with ctx.channel.typing():
            # set the images
            image = await getImage(ctx, user_or_url)
            overlay = self.flushedTemplate.copy()

            # convert the images to be equal in size and mode for compatibility
            image = centerSquare(image)

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
    async def joy(self, ctx, *, user_or_url: Union[discord.Member, str, None] = None):
        """😂😂😂 This command makes the attached image or your/the mentioned user's avatar a joke. 😂😂😂"""
        async with ctx.channel.typing():
            # set the images
            image = await getImage(ctx, user_or_url)
            overlay = self.joyTemplate.copy()

            # convert the images to be equal in size and mode for compatibility
            image = centerSquare(image)

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
            await sendImage(ctx, outImg, "joy.png")

    @commands.command(cooldown_after_parsing=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def invert(self, ctx, *, user_or_url: Union[discord.Member, str, None] = None):
        """Inverts the attached image or your/the mentioned user's avatar."""
        async with ctx.channel.typing():
            image = await getImage(ctx, user_or_url)

            if image.mode == "RGBA":
                alpha = findMonoAlphaTarget(image)

                alphaTemp = Image.new('RGB', (1, 1), alpha)
                alphaTemp = ImageOps.invert(alphaTemp)

                alphaInvert = alphaTemp.getdata()[0]  # find inverted alpha color

                image = Image.alpha_composite(Image.new('RGBA', (image.width, image.height), alpha), image)
            else:
                alphaInvert = None

            image = image.convert('RGB')  # i dunno, ImageOps wants an RGB
            image = ImageOps.invert(image)

            if alphaInvert:
                image = hippityHoppityThisColorIsDisappearity(image, alphaInvert)

            await sendImage(ctx, image, "invert.png")

    @commands.command(cooldown_after_parsing=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def sadden(self, ctx, *, user_or_url: Union[discord.Member, str, None] = None):
        """😔"""
        async with ctx.channel.typing():
            image = await getImage(ctx, user_or_url)

            image = image.convert('RGB')  # i dunno, ImageOps wants an RGB
            image = ImageOps.grayscale(image)

            await sendImage(ctx, image, "grayscale.png")

    @commands.command(cooldown_after_parsing=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def saturate(self, ctx, *, user_or_url: Union[discord.Member, str, None] = None):
        """Saturates the attached image or your/the mentioned user's avatar."""
        async with ctx.channel.typing():
            image = await getImage(ctx, user_or_url)

            image = image.convert('RGB')  # i dunno, ImageEnhance might want an RGB
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(2)
            enhancer = ImageEnhance.Color(image)
            image = enhancer.enhance(3)

            await sendImage(ctx, image, "saturate.png")

    @commands.command(cooldown_after_parsing=True, aliases=["xFlip", "sideFlip"])
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def mirror(self, ctx, *, user_or_url: Union[discord.Member, str, None] = None):
        """Creates a mirrored image of the attached image or your/the mentioned user's avatar."""
        async with ctx.channel.typing():
            image = await getImage(ctx, user_or_url)

            outImg = image.transpose(method=Image.FLIP_LEFT_RIGHT)  # processing here

            await sendImage(ctx, outImg, "mirror.png")

    @commands.command(cooldown_after_parsing=True, aliases=["yFlip", "topFlip", "bottomFlip"])
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def flip(self, ctx, *, user_or_url: Union[discord.Member, str, None] = None):
        """Creates an upside-down copy of the attached image or your/the mentioned user's avatar."""
        async with ctx.channel.typing():
            image = await getImage(ctx, user_or_url)

            outImg = image.transpose(method=Image.FLIP_TOP_BOTTOM)  # processing here
            outImg = outImg.transpose(method=Image.FLIP_LEFT_RIGHT)  # top bottom makes it also flip on the x

            await sendImage(ctx, outImg, "upside_down.png")

    @commands.command(cooldown_after_parsing=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def rotate(self, ctx, degrees: float, *, user_or_url: Union[discord.Member, str, None] = None):
        """Rotates the attached image or your/the mentioned user's avatar clockwise by the specified number of degrees.
        (Algorithms contributed by Blue#1287 (494615059474153483))"""
        async with ctx.channel.typing():
            image = await getImage(ctx, user_or_url)

            image = image.convert('RGBA')  # make it so transparency generates instead of black

            angleOffset = degrees % 90  # this is what we'll use instead of input
            if angleOffset == 0:
                if degrees % 180 == 90:  # plot twist, the angle was also 90
                    angleOffset = 90

            diagonal = math.sqrt(image.width ** 2 + image.height ** 2)  # finding the length of the rectangle's diagonal
            
            # this very well might return radians instead of degrees so we gotta convert
            b = math.degrees(math.atan(image.width / image.height))

            # finding angle of the diagonal of the rectangle to the uhhhh global 90 degree line uhhhhh
            a = 90 - (angleOffset + b)

            rotatedWidth = diagonal * math.cos(math.radians(a))  # this requires radians and not degrees
            
            b = math.degrees(math.atan(image.height / image.width))
            
            # finding angle of the diagonal of the rectangle to the uhhhh global 90 degree line uhhhhh
            a = 90 - (angleOffset + b)

            rotatedHeight = diagonal * math.cos(math.radians(a))  # this requires radians and not degrees

            if rotatedWidth > rotatedHeight:
                biggest = math.floor(rotatedWidth)
            else:
                biggest = math.floor(rotatedHeight)
            result = Image.new(image.mode, (biggest, biggest), (0, 0, 0, 0))  # big image to prevent cutting off stuff
            # paste the image on in a centered position
            result.paste(image, ((result.width // 2) - (image.width // 2), (result.height // 2) - image.height // 2))

            outImg = result.rotate(angle=-degrees)  # for some cursed reason, rotate() defaults to counterclockwise

            # do some centering math stuff to find the coordinates of the actual content
            outImg = outImg.crop((round(outImg.width / 2 - rotatedWidth / 2),
                                  round(outImg.height / 2 - rotatedHeight / 2),
                                  round(outImg.width / 2 + rotatedWidth / 2),
                                  round(outImg.height / 2 + rotatedHeight / 2)))

            await sendImage(ctx, outImg, "rotate.png")


def setup(bot):
    bot.add_cog(Images(bot))

# general template because I can
#     @commands.command(cooldown_after_parsing=True)
#     @commands.cooldown(1, 5, commands.BucketType.user)
#     async def name(self, ctx, *, user_or_url: Union[discord.Member, str, None] = None):
#         """document here"""
#         async with ctx.channel.typing():
#             image = await getImage(ctx, user_or_url)
#
#             outImg = None  # processing here
#
#             await sendImage(ctx, outImg, "image.png")

# cookie-cutter ImageOps command template
#     @commands.command(cooldown_after_parsing=True)
#     @commands.cooldown(1, 5, commands.BucketType.user)
#     async def name(self, ctx, *, user_or_url: Union[discord.Member, str, None] = None):
#         """Inverts the attached image or your/the mentioned user's avatar."""
#         async with ctx.channel.typing():
#             image = await getImage(ctx, user_or_url)
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
