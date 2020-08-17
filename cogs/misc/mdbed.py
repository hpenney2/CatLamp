def uh():
    """Shitty converter for Privacy.md embeds"""
    import discord

    a = open('PRIVACY.md', 'r')

    a = a.read()
    a = a.splitlines()
    b = {}
    for i in a:
        # Sort this mess into something with numbered levels
        if i in ("", " "):
            continue
        elif i.startswith("# "):
            b[i[2:]] = 1
        elif i.startswith("## "):
            b[i[3:]] = 2
        elif i.startswith("### "):
            b[i[4:]] = 3
        elif i.startswith("#### "):
            b[i[5:]] = 4
        elif i.startswith("##### "):
            b[i[6:]] = 5
        else:
            b[i] = 0

    embed = discord.Embed(title='Sample')
    field_title = None
    values = []
    for i in b:
        # Made this so things are "readable" and i don't have to do the string slicing anymore
        compare = b[i]
        if compare == 1:
            embed = discord.Embed(title=i)
        elif compare == 2:
            if field_title:
                embed.add_field(name=field_title, value=valueProcess(values), inline=False)
                values = []
            field_title = i
        elif compare == 3:
            values.append(f"\n**- {i}**\n")
        elif compare == 0:
            values.append(i + '\n')
        elif compare == 4:
            values.append(f"\n*{i}*\n")
        # use different format for the footer because fuck you
        # elif compare == 5:
        #     embed.set_footer(text=i)
        else:
            print('fiddlesticks')
    embed.set_footer(text=f"{field_title}: {valueProcess(values)}")

    return embed


def valueProcess(values):
    value = ''
    for i in values:
        value += i
    return value


if __name__ == "__main__":
    uh()
