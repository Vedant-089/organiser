import discord
from discord.ext import commands


class Test(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="test")
    async def test(self, ctx):
        await ctx.send("m!cl add rare")


async def setup(bot):
    await bot.add_cog(Test(bot))