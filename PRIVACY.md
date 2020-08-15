# Eggbot Privacy Policy

## Why we collect data
Eggbot collects certain information visible to the bot for bot functionality and administration.

## Deletion Policy
For the official instance of Eggbot, a user or server administrator may request that their data be deleted. However, we do not prevent the bot from recollecting the data from a future source.

If you are considered an Involved User, you may request that your attribution is removed in the code or from the official configuration. 

We recommend that hosts abide by these policies for their own instances, but we cannot guarantee that these standards will be followed.

## What we always collect

### User IDs
We collect these for reference in reminders. (+remind)

### Server IDs
We collect server identification, member count, and owner names for our auditing logs.

### User-Submitted Content
We save the message IDs, emoji names, and role IDs provided in the setup of an automatic Role Giver.
The names and prices of Goals set for a server are also saved.

### Involved Users' IDs
If you are involved in the development of Eggbot or are listed as an Administrator for the Eggbot instance, your identification number is saved for reference in bot functions (attribution and permission checks are the common uses).

### All Discord Network Traffic to the Bot
For debugging purposes, we save a `discord.log` which saves all incoming information.

This log is seldom looked at, and is overwritten with every reboot of the bot.

## What we log in terminal (depending on configuration)

### All Messages
Mainly for debugging purposes, this setting will log the message author and content (text and attachments).

### Direct Messages to an active instance of the bot
The bot can log direct messages to itself in order to allow for manual managing and viewing of the private messages sent to the bot.
### Locked Command Usage
If a command locked to Eggbot Administrators is used, the terminal will log the username and identifier of the invoker.

### Deleted Messages
The bot can log deleted message IDs, the ID of the channel the message originated from, and, if cached, the message content (text and attachments).
This is intended to be used in personal server administration, in order to preserve information that would be inaccessible otherwise.

#### Using the e!settings command, you can check the state of these settings.

### Emoji Names
If an Eggbot Administrator uses the "print_emoji" command, the raw emoji text will be printed to the terminal.

##Note:
We reserve the right to revise this privacy policy without notice, as needed.
 