import discord
def getColors():
    """Returns table of colors for use with embeds."""
    return {
        "error": discord.Color.from_rgb(255, 68, 78),
        "success": discord.Color.from_rgb(60, 255, 100),
        "message": discord.Color.from_rgb(42, 141, 222)
    }
