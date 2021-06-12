import asyncio
import discord
from discord.ext import commands


async def nsfwCheck(ctx: commands.Context, unit: str = "command"):
    note = ''
    if ctx.channel.type == discord.ChannelType.text:  # server/text-channel
        if not ctx.message.channel.is_nsfw():
            note = f"This {unit} is marked as NSFW. Please move to an NSFW channel."
        cool = ctx.message.channel.is_nsfw()
    else:
        if ctx.author.id in ctx.bot.degenerates:
            cool = True
        else:
            cool = await check(ctx, unit)
            if cool:
                ctx.bot.degenerates.append(ctx.author.id)
    if unit != 'post':
        if note:
            await ctx.send(note)
    print(cool, "and good")
    return cool


async def check(ctx: commands.Context, unit: str = "command"):  # TODO: Replace this after merging game branch
    print("check")
    confirmMess = await ctx.send(f'This {unit} is NSFW. Are you over 18 and *sure* you want to view this content?')
    await confirmMess.add_reaction('✅')
    await confirmMess.add_reaction('❌')
    # wait_for stolen from docs example

    def confirm(react, reactor):
        print(react, reactor)  # only does "❌ Sluglamp (TEST)#9210" pain
        return reactor == ctx.author and str(react.emoji) in ('✅', '❌') and confirmMess.id == react.message.id

    try:
        reaction, user = await ctx.bot.wait_for('reaction_add', timeout=30, check=confirm)
        print("uh what")
    except asyncio.TimeoutError:  # timeout cancel
        print("no")
        await confirmMess.edit(text=f'`+{ctx.command.name}` timed-out.')
    else:
        print("checking emogi " + reaction.emoji)
        if reaction.emoji == '✅':
            await confirmMess.delete()
            return True
        else:  # ❌ react cancel
            await confirmMess.remove_reaction('✅', ctx.bot.user)
            await confirmMess.remove_reaction('❌', ctx.bot.user)
        try:
            await confirmMess.remove_reaction('❌', user)
        except (discord.Forbidden, discord.NotFound):
            pass
        await confirmMess.edit(content=f'`+{ctx.command.name}` was cancelled.')


async def canNSFW(ctx: commands.context):
    return await nsfwCheck(ctx)  # cant directly use nsfwCheck because optional argument is crie
