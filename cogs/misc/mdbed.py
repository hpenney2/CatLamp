def uh():
    """Shitty converter for Privacy.md embeds"""
    import discord

    a = open('PRIVACY.md', 'r')

    a = a.read()
    a = a.splitlines()
    print(a)
    embed = discord.Embed(title='Sample')
    temp = []
    for i in a:
        print(i)
        if i == '':
            continue
        elif i.startswith('# '):
            embed = discord.Embed(title=i[2:])
        elif i.startswith('## '):
            temp.append(i[3:])
        elif i.startswith('### '):
            try:
                e = temp[0]
                r = embed.fields[:1][0]
                embed.add_field(name=r.name, value=r.value + f'\n**⠀**', inline=False)
                embed.remove_field(len(embed.fields) - 1)
                embed.add_field(name=temp[0], value="⠀", inline=False)
                temp = [i[4:]]
            except IndexError:
                temp.append(i[4:])
        else:
            print('\nfield \n' + str(embed.fields[:1]))
            try:
                print(temp)
                e = temp[0]
                temp.append(i)
            except IndexError:
                print('fucking')
                r = embed.fields[:1][0]
                embed.add_field(name=r.name, value=r.value + f'\n {i}', inline=False)
                embed.remove_field(len(embed.fields) - 1)
        if len(temp) == 2:
            embed.add_field(name=temp[0], value=temp[1], inline=False)
            print(embed.fields[:1][0])
            print(temp)
            temp = []

    print('footer?')
    embed.remove_field(len(embed.fields) - 1)
    embed.set_footer(text=f"{a[-3:][0][2:]}: {a[-2:][:1][0]}")  # fuck it this mainly supports the Note: line in CatLamp

    print(f'\n{embed.to_dict()}')
    return embed
