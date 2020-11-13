import asyncio
import discord


async def confirm(ctx, targetUser: discord.User, confirmMess: discord.Message, timeout: int = 30, delete: bool = False):
    """
    A general confirm prompt function that can be attached to any message.

    Return Types:
    True: User confirmed.
    False: User declined.
    asyncio.TimeoutError: The timeout time was reached before a response was given.
    """
    await confirmMess.add_reaction('✅')
    await confirmMess.add_reaction('❌')

    # wait_for stolen from docs example
    def check(react, reactor):
        return reactor == targetUser and str(react.emoji) in ('✅', '❌') and confirmMess.id == react.message.id

    try:
        reaction, user = await ctx.bot.wait_for('reaction_add', timeout=timeout, check=check)
    except asyncio.TimeoutError as e:  # timeout cancel
        return e
    else:
        if reaction.emoji == '✅':
            if delete:
                await confirmMess.delete()
            else:
                try:
                    await confirmMess.clear_reactions()
                except discord.Forbidden:
                    await confirmMess.remove_reaction('✅', user)
                    await confirmMess.remove_reaction('✅', ctx.bot.user)
                    await confirmMess.remove_reaction('❌', ctx.bot.user)
                except discord.NotFound:
                    pass
            return True

        else:  # ❌ react cancel
            try:
                await confirmMess.clear_reactions()
            except discord.Forbidden:
                await confirmMess.remove_reaction('❌', user)
                await confirmMess.remove_reaction('✅', ctx.bot.user)
                await confirmMess.remove_reaction('❌', ctx.bot.user)
            except discord.NotFound:
                pass
            return False
