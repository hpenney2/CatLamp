import asyncio
import datetime
import os
from json import load

import discord
from discord.ext import commands

from CatLampPY import isGuild, CommandErrorMsg  # pylint: disable=import-error
from tables import *

colors = getColors() # pylint: disable=undefined-variable
times = getTimes() # pylint: disable=undefined-variable


class Utility(commands.Cog):
    def __init__(self, bot):
        self.client = bot
        self.client.cmds.append(self.announce)
        self.client.cmds.append(self.cancelReminder)
        self.client.cmds.append(self.remind)
        self.reminders_setup = False

    # @commands.Cog.listener() for a listener event

    # @commands.command() for a command

    @commands.command(aliases=["announcement"])
    @isGuild()
    async def announce(self, ctx, channel: discord.TextChannel, *, message: str):
        """Sends a nicely formatted announcement embed to the specified channel, or if none, the current channel."""
        if channel is None:
            channel = ctx.channel
        if not channel.guild.id or channel.guild.id != ctx.guild.id:
            raise CommandErrorMsg("That channel isn't even in the same server!")
        # The reason I didn't just implement the below with checks is because the channel isn't
        # always the same as ctx.channel
        perms = ctx.author.permissions_in(channel)
        botPerms = ctx.guild.me.permissions_in(channel)
        if not perms.read_messages:
            raise CommandErrorMsg("You don't have the Read Messages permission for that channel!")
        elif not perms.send_messages:
            raise CommandErrorMsg("You don't have the Send Messages permission for that channel!")
        elif not perms.manage_messages:  # adding this one so people aren't just making announcements in general chats
            raise CommandErrorMsg("You don't have the Manage Messages permission for that channel!")
        elif not botPerms.send_messages:
            raise CommandErrorMsg("The bot doesn't have the Send Messages permission for that channel!")
        embed = discord.Embed(title="Announcement", description=message, color=colors["message"])
        embed.set_author(name=ctx.author.name, icon_url=str(ctx.author.avatar_url))
        embed.timestamp = datetime.datetime.utcnow()
        await channel.send(embed=embed)
        try:
            await ctx.message.add_reaction("✅")
        except discord.Forbidden:
            pass

    @commands.command(aliases=["reminder", "timer"])
    async def remind(self, ctx, time: float, unit: str = "minutes", *, reminder_note: str = ""):
        """Sets a reminder, optionally with a note. Valid time units are seconds, minutes, and hours."""
        if ctx.author.id in self.client.reminders:
            await ctx.send("You already have a reminder set! Use `+cancelReminder` to cancel it.")
            return
        if time <= 0:
            time = 1
        # Unit checking
        originalTime = time
        if unit.lower() in times:
            time = times[unit.lower()] * time
        else:
            raise CommandErrorMsg("Invalid time unit!")

        if originalTime == 1 and unit.endswith('s'):
            unit = unit[:-1]
        elif originalTime > 1 and not unit.endswith('s'):
            unit += "s"
        if reminder_note.strip():  # If not empty or whitespace
            reminder_note = f" Note: `{reminder_note}`"

        if str(originalTime).endswith('.0'):  # definitely best wait to remove trailing ".0" in integer floats
            originalTime = str(originalTime)[:-2]

        task = asyncio.ensure_future(self.timer(ctx.channel.id, ctx.author.id, time, originalTime, unit, reminder_note))
        self.client.reminders[ctx.author.id] = {
            "task": task,
            "startTime": datetime.datetime.utcnow().timestamp(),
            "timeSeconds": time,
            "originalTime": originalTime,
            "unit": unit,
            "channelId": ctx.channel.id,
            "userId": ctx.author.id,
            "note": reminder_note
        }
        await ctx.send(f"Reminder set! I'll @ you in {originalTime} {unit}.{reminder_note}")

    async def timer(self, channelId, userId, time, o, unit: str, note: str):
        try:
            await asyncio.sleep(time)
            channel = self.client.get_channel(channelId)
            if channel:
                await channel.send(f"<@{userId}> Your reminder for {o} {unit} is up!{note}")
            self.client.reminders.pop(userId)
        except asyncio.CancelledError:
            pass

    @commands.command(aliases=["cancelRemind", "cancelTimer"])
    async def cancelReminder(self, ctx):
        """Cancels your current reminder if you have one."""
        if ctx.author.id not in self.client.reminders:
            await ctx.send("You don't have a reminder! Use `+remind` to set one.")
            return
        else:
            task = self.client.reminders[ctx.author.id]["task"]
            task.cancel()
            self.client.reminders.pop(ctx.author.id)
            await ctx.send("Reminder cancelled.")


    @commands.command()
    async def timeLeft(self, ctx):
        """Checks how much time is left on your current reminder if you have one."""
        if ctx.author.id not in self.client.reminders:
            await ctx.send("You don't have a reminder! Use `+remind` to set one.")
            return
        else:
            tab = self.client.reminders[ctx.author.id]
            remainingTime = (tab["startTime"] + tab["timeSeconds"]) - datetime.datetime.utcnow().timestamp()
            m, s = divmod(remainingTime, 60)
            h, m = divmod(m, 60)
            d, h = divmod(h, 24)
            valid = [d, h, m, s]
            names = ["days", "hours", "minutes", "seconds"]
            while valid[0] < 1 and len(valid) != 1:
                del valid[0]
                del names[0]
            for time in valid:
                index = valid.index(time)
                unit = names[index]
                if time == 1:
                    unit = unit[:-1]
                valid[valid.index(time)] = f"{round(time)} {unit}"
            remWithUnits = ", ".join(valid)
            await ctx.send(f"Remaining time on current reminder: {remWithUnits}")


    # stuffing this here for the timer reloading
    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Successfully logged in as {self.client.user.name} ({self.client.user.id})")
        await self.client.change_presence(activity=None)
        if not self.reminders_setup:  # this is because on_ready may be called multiple times, sooo debounce
            self.reminders_setup = True
            if os.path.isfile("reminders.json"):
                print("reminders.json exists, loading reminders from file")
                # noinspection PyUnusedLocal
                tempReminders = None
                with open("reminders.json", "r") as file:
                    tempReminders = load(file)
                for tab in tempReminders.values():
                    remainingTime = (tab["startTime"] + tab["timeSeconds"]) - datetime.datetime.utcnow().timestamp()
                    if remainingTime <= 0:
                        self.client.reminders[int(tab["userId"])] = tab
                        asyncio.ensure_future(
                            self.timer(tab["channelId"], tab["userId"], 0, tab["originalTime"], tab["unit"],
                                       tab["note"]))
                    else:
                        self.client.reminders[int(tab["userId"])] = tab
                        task = asyncio.ensure_future(self.timer(tab["channelId"], tab["userId"], remainingTime,
                                                                tab["originalTime"], tab["unit"], tab["note"]))
                        tab["task"] = task
                        self.client.reminders[int(tab["userId"])] = tab
                print("Done!")
                os.remove("reminders.json")


def setup(bot):
    bot.add_cog(Utility(bot))
