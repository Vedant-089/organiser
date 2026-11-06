
import discord
from discord.ext import commands


class Sync(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="sync")
    @commands.guild_only()
    @commands.has_permissions(manage_channels=True)
    async def sync(self, ctx):
        """Sync channel permissions with their respective categories."""

        guild = ctx.guild

        # Get all channels that belong to a category
        channels = [
            channel
            for channel in guild.channels
            if channel.category is not None
        ]

        total = len(channels)

        if total == 0:
            await ctx.send("❌ No categorized channels found.")
            return

        # Send ONE progress message
        message = await ctx.send(
            f"🔄 **Syncing permissions...**\n`0/{total}`"
        )

        synced = 0
        failed = 0

        for channel in channels:
            try:
                # Copy the category's permission overwrites
                await channel.edit(
                    overwrites=channel.category.overwrites
                )

                synced += 1

                # Update every 10 channels
                # Also update at the beginning and end
                if synced == 1 or synced % 10 == 0 or synced == total:
                    await message.edit(
                        content=(
                            f"🔄 **Syncing permissions...**\n"
                            f"`{synced}/{total}`"
                        )
                    )

            except discord.HTTPException as e:
                failed += 1

                print(
                    f"Failed to sync {channel.name} "
                    f"({channel.id}): {e}"
                )

        # Final message
        await message.edit(
            content=(
                f"✅ **Permission sync complete!**\n"
                f"Synced: `{synced}/{total}`\n"
                f"Failed: `{failed}`"
            )
        )

    @sync.error
    async def sync_error(self, ctx, error):

        if isinstance(error, commands.MissingPermissions):
            await ctx.send(
                "❌ You need the **Manage Channels** permission "
                "to use this command."
            )

        elif isinstance(error, commands.NoPrivateMessage):
            await ctx.send(
                "❌ This command can only be used in a server."
            )

        else:
            raise error


async def setup(bot):
    await bot.add_cog(Sync(bot))
