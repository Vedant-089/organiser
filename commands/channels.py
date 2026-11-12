import discord
from discord.ext import commands


class ChannelCreator(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="channel")
    @commands.has_permissions(manage_channels=True)
    @commands.guild_only()
    async def channel(self, ctx):

        msg = await ctx.send("⏳ Creating categories and 100 channels...")

        try:
            # First category: 101-150
            category1 = await ctx.guild.create_category("101-150")

            # Create channels 101-150
            for i in range(101, 151):
                await ctx.guild.create_text_channel(
                    name=f"channel-{i}",
                    category=category1
                )

            # Second category: 151-200
            category2 = await ctx.guild.create_category("151-200")

            # Create channels 151-200
            for i in range(151, 201):
                await ctx.guild.create_text_channel(
                    name=f"channel-{i}",
                    category=category2
                )

            await msg.edit(
                content="✅ Successfully created both categories and all 100 channels!"
            )

        except discord.Forbidden:
            await msg.edit(
                content="❌ I don't have permission to manage channels."
            )

        except discord.HTTPException as e:
            await msg.edit(
                content=f"❌ Discord API error: {e}"
            )


async def setup(bot):
    await bot.add_cog(ChannelCreator(bot))