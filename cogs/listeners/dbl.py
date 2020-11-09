import dbl
import discord
import asyncio
from aiohttp import web
from discord.ext import commands
# pylint: disable=import-error
from CatLampPY import config, colors
from cogs.commands.economy import getProfile


# noinspection PyAttributeOutsideInit
class DBL(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.dblpy = dbl.DBLClient(self.bot, config["dblToken"], autopost=True)  # pylint: disable=no-member
        self.econ = bot.profiles

    async def webserver(self):
        async def handleDBLVote(request):
            botlogs = self.bot.get_channel(712489826330345534)
            auth = request.headers.get("Authorization")
            if auth != "Imagin3ActuallyHavingGo0dSEcuR1tyF0rCATLAMP":
                print(f"DBL POST request recieved with invalid Authorization header!!!\nAuth header recieved: {auth}")
                botlogs.send(
                    f"**DBL POST request recieved with invalid Authorization header!**\n Auth header recieved: {auth}")
                return web.json_response({"error": "invalid_auth_header"}, status=401)
            else:
                ctype = request.headers.get("Content-Type")
                if ctype != "application/json":
                    print(f"DBL POST request failed due to not having a JSON content type!\n"
                          f"Content-Type header: {ctype}")
                    return web.json_response({"error": "bad_content_type"}, status=400)
                post = await request.json()
                postType = None
                try:
                    postType = post["type"]
                except KeyError:
                    print("'type' key missing from request body!")
                    return web.json_response({"error": "missing_keys"}, status=400)
                if postType == "test":
                    print("Hello, world! Webhook test received from DBL.")
                    await botlogs.send("Hello, world! Webhook test received from DBL.")
                    return web.json_response({"hello": "world"})
                elif postType == "upvote":
                    userId = post.get("user")
                    user = None
                    userName = None
                    try:
                        user = await self.bot.fetch_user(userId)
                        userName = str(user)
                    except discord.NotFound:
                        userName = "Unknown User"

                    profile = await getProfile(self.econ, user)
                    await self.econ.update_one({"_id": str(userId)},
                                               {
                                                   "$inc": {"balance": 15}
                                               })

                    await botlogs.send(f"User `{userName} ({userId})` voted for the bot on DBL and has been credited "
                                       f"15 coins.")
                    if user:
                        try:
                            coins = str(round(profile.get("balance", 0.00) + 15, 2))
                            if coins.endswith(".0"):
                                coins += "0"
                            embed = discord.Embed(title="Vote reward credited",
                                                  description=f"Thank you for voting for us! You have been credited "
                                                              f"15 coins.\n*Your new balance is {coins} coins.*",
                                                  color=colors["success"])
                            await user.send(embed=embed)
                        except discord.Forbidden:
                            pass

                    return web.json_response({"status": "upvote_handled_successfully"})
                else:
                    print(f"Unknown post type! Got '{postType}', expected 'upvote' or 'test'")
                    await botlogs.send(f"Unknown post type! Got '{postType}', expected 'upvote' or 'test'")
                    return web.json_response({"error": "bad_vote_type"}, status=400)
        app = web.Application()
        app.add_routes([web.post("/dblwebhook", handleDBLVote),
                        web.post("/dblwebhook/", handleDBLVote)])
        runner = web.AppRunner(app)
        await runner.setup()
        self.site = web.TCPSite(runner, port=10215)
        await self.bot.wait_until_ready()
        await self.site.start()
        print("DBL webhook started!")

    def __unload(self):
        asyncio.ensure_future(self.site.stop())

    def cog_unload(self):
        asyncio.ensure_future(self.site.stop())


def setup(bot):
    topgg = DBL(bot)
    bot.add_cog(topgg)
    bot.loop.create_task(topgg.webserver())
