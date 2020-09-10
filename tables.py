import discord


def getColors():
    """Returns table of colors for use with embeds."""
    return {
        "error": discord.Color.from_rgb(255, 68, 78),
        "success": discord.Color.from_rgb(60, 255, 100),
        "warning": discord.Color.from_rgb(255, 230, 0),
        "message": discord.Color.from_rgb(42, 141, 222)
    }


def getTimes():
    """Returns table of time units for use with reminders."""
    return {
        "second": 1,
        "seconds": 1,
        "minute": 60,
        "minutes": 60,
        "hour": 3600,
        "hours": 3600,
        "day": 3600 * 24,  # i cant math
        "days": 3600 * 24
    }
