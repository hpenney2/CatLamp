# pylint: disable=import-error
from discord.ext import commands
import discord

import tables
colors = tables.getColors()


class EmbedHelpCommand(commands.HelpCommand):
    """This is an example of a HelpCommand that utilizes embeds.
    It's pretty basic but it lacks some nuances that people might expect.
    1. It breaks if you have more than 25 cogs or more than 25 subcommands. (Most people don't reach this)
    2. It doesn't DM users. To do this, you have to override `get_destination`. It's simple.
    Other than those two things this is a basic skeleton to get you started. It should
    be simple to modify if you desire some other behaviour.

    To use this, pass it to the bot constructor e.g.:

    bot = commands.Bot(help_command=EmbedHelpCommand())
    """
    # Set the embed colour here
    COLOUR = colors['message']

    # Set the things to manually remove
    placeholders = ['=minutes', '=No reason specified.', '=0']

    def get_ending_note(self):
        return 'Use {0}{1} [command] for more info on a command.'.format(self.clean_prefix, self.invoked_with)

    def get_command_signature(self, command):
        syntax = command.signature.replace("_", " ")

        for i in self.placeholders:  # remove placeholder things (please don't crucify me for not knowing the term)
            if i in syntax:
                syntax = syntax.replace(i, '')

        return f'+{command.qualified_name} {syntax}'

    async def send_bot_help(self, mapping):
        embed = discord.Embed(title='Bot Commands', colour=self.COLOUR)
        description = "`[option]` = Optional argument\n`<option>` = Required argument"
        if description:
            embed.description = description

        for cog, Commands in mapping.items():
            name = 'No Category' if cog is None else cog.qualified_name
            filtered = await self.filter_commands(Commands, sort=True)

            # override processing
            new = []
            for c in Commands:
                if not c.hidden:
                    new.append(c.name)
            new.sort()
            Commands = new
            del new

            value = ''  # start of field value creation
            if filtered:
                if name == "Bot Info":
                    value = 'help, '
                for c in Commands:
                    if c != "help":
                        value += f'{c}, '
                value = value.rstrip(", ")

            if cog and cog.description:  # add cog desc to field value
                value = '{0}\n{1}'.format(cog.description, value)

            if value:
                embed.add_field(name=name, value=value, inline=False)

        embed.set_footer(text=self.get_ending_note())
        await self.get_destination().send(embed=embed)

    async def send_cog_help(self, cog):
        embed = discord.Embed(title='{0.qualified_name} Commands'.format(cog), colour=self.COLOUR)
        if cog.description:
            embed.description = cog.description

        filtered = await self.filter_commands(cog.get_commands(), sort=True)
        for command in filtered:
            embed.add_field(name=self.get_command_signature(command), value=command.short_doc or '...', inline=False)

        embed.set_footer(text=self.get_ending_note())
        await self.get_destination().send(embed=embed)

    async def send_group_help(self, group):
        embed = discord.Embed(title=group.qualified_name, colour=self.COLOUR)
        if group.help:
            embed.description = group.help

        if isinstance(group, commands.Group):
            filtered = await self.filter_commands(group.commands, sort=True)
            for command in filtered:
                embed.add_field(name=self.get_command_signature(command), value=command.short_doc or '...',
                                inline=False)

        embed.set_footer(text=self.get_ending_note())
        await self.get_destination().send(embed=embed)

    async def send_command_help(self, Command):
        embed = discord.Embed(title=self.get_command_signature(Command), colour=self.COLOUR)

        if Command.qualified_name == 'help':
            embed.description = "Displays the documentation for Catlamp."
        elif Command.help:
            embed.description = Command.help
        if Command.aliases:
            value = ''
            for a in Command.aliases:
                if a != "help":
                    value += f'`{a}`, '
            value = value.rstrip(", ")
            embed.add_field(name='Aliases', value=value)

        embed.set_footer(text=self.get_ending_note())
        await self.get_destination().send(embed=embed)
