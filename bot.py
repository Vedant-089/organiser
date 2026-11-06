from pathlib import Path
import os

import discord
from discord.ext import commands
from dotenv import load_dotenv


load_dotenv(Path(__file__).with_name(".env"))


class OrganiserBot(commands.Bot):
    async def setup_hook(self):
        commands_dir = Path(__file__).parent / "commands"
        for file_path in sorted(commands_dir.glob("*.py")):
            if file_path.name.startswith("_"):
                continue
            await self.load_extension(f"commands.{file_path.stem}")

        try:
            synced = await self.tree.sync()
            print(f"Synced {len(synced)} command(s)")
        except Exception as exc:
            print(f"Failed to sync commands: {exc}")


intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = OrganiserBot(command_prefix=["o!", "O!"], intents=intents)


if __name__ == "__main__":
    TOKEN = os.getenv("DISCORD_BOT_TOKEN")
    if not TOKEN:
        raise RuntimeError(
            "DISCORD_BOT_TOKEN is not set. Add it to the .env file or the environment."
        )
    bot.run(TOKEN)
