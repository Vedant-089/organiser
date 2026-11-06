import asyncio
import os
import random
import re
from urllib.parse import urlparse

import aiohttp
import discord
from discord.ext import commands


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOWNLOADS_DIR = os.path.join(BASE_DIR, "downloads")
TARGET_AUTHOR_ID = 716390085896962058


def sanitize_folder_name(folder_name):
    cleaned_name = folder_name.strip()
    for invalid_character in '<>:"/\\|?*':
        cleaned_name = cleaned_name.replace(invalid_character, "_")
    cleaned_name = " ".join(cleaned_name.split())
    return cleaned_name or "unknown"


def guess_extension(image_url, content_type):
    url_path = urlparse(image_url).path
    _, extension = os.path.splitext(url_path)
    extension = extension.lower()

    if extension:
        return extension

    content_type = (content_type or "").split(";")[0].strip().lower()
    return {
        "image/jpeg": ".jpg",
        "image/jpg": ".jpg",
        "image/png": ".png",
        "image/gif": ".gif",
        "image/webp": ".webp",
    }.get(content_type, ".png")


def random_six_digit_name(target_directory, extension):
    while True:
        file_name = f"{random.randint(100000, 999999)}{extension}"
        file_path = os.path.join(target_directory, file_name)
        if not os.path.exists(file_path):
            return file_name, file_path


class DownloadCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def fetch_replied_message(self, ctx):
        reference = ctx.message.reference
        if reference is None or reference.message_id is None:
            return None

        if isinstance(reference.resolved, discord.Message):
            return reference.resolved

        try:
            return await ctx.channel.fetch_message(reference.message_id)
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            return None

    def pick_embed_image_url(self, message):
        for embed in message.embeds:
            if embed.image and embed.image.url:
                return embed.image.url
        return None

    def infer_pokemon_name(self, ctx, source_message):
        message_content = ctx.message.content.split(maxsplit=2)
        if len(message_content) >= 3:
            return message_content[2]

        if source_message.embeds:
            first_embed = source_message.embeds[0]
            if first_embed.title:
                return first_embed.title

            if first_embed.description:
                return first_embed.description

        return None

    def is_fled_spawn_title(self, title, pokemon_name):
        if not title:
            return False

        normalized_title = re.sub(r"\s+", " ", title.strip()).casefold()
        normalized_name = re.sub(r"\s+", " ", pokemon_name.strip()).casefold()

        return (
            normalized_title.startswith(f"wild {normalized_name} fled")
            and "a new wild pok" in normalized_title
            and normalized_title.endswith("appeared!")
            and ". a new wild pok" in normalized_title
        )

    async def save_embed_image(self, image_url, folder_name):
        if not image_url:
            return None

        timeout = aiohttp.ClientTimeout(total=30)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            try:
                async with session.get(image_url) as response:
                    if response.status != 200:
                        return None

                    content_type = response.headers.get("Content-Type", "")
                    extension = guess_extension(image_url, content_type)
                    file_name, file_path = random_six_digit_name(os.path.join(DOWNLOADS_DIR, folder_name), extension)
                    image_bytes = await response.read()
            except (aiohttp.ClientError, asyncio.TimeoutError):
                return None

        with open(file_path, "wb") as file_handle:
            file_handle.write(image_bytes)

        return file_name

    async def find_recent_spawn_images(self, pokemon_name, target_count):
        matched_images = []
        seen_urls = set()
        history_limit = max(40, min(200, target_count * 25))

        for guild in self.bot.guilds:
            for channel in guild.text_channels:
                if not channel.name.lower().startswith("incense-"):
                    continue

                try:
                    last_message = None
                    async for message in channel.history(limit=history_limit, oldest_first=True):
                        if last_message is not None and message.embeds:
                            for embed in message.embeds:
                                if not self.is_fled_spawn_title(embed.title, pokemon_name):
                                    continue

                                image_url = self.pick_embed_image_url(last_message)
                                if not image_url or image_url in seen_urls:
                                    break

                                seen_urls.add(image_url)
                                matched_images.append({
                                    "channel": channel,
                                    "image_url": image_url,
                                    "message_id": last_message.id,
                                })

                                if len(matched_images) >= target_count:
                                    return matched_images
                                break

                        last_message = message
                except (discord.Forbidden, discord.HTTPException):
                    continue

        return matched_images

    @commands.command(name="download", aliases=["d"])
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def download(self, ctx, *, pokemon_name=None):
        source_message = await self.fetch_replied_message(ctx)
        if source_message is None:
            await ctx.send("❌ Reply to the target bot message when using this command.")
            return

        if source_message.author.id != TARGET_AUTHOR_ID:
            await ctx.send("❌ The replied message must be from the tracked bot.")
            return

        image_url = self.pick_embed_image_url(source_message)
        if not image_url:
            await ctx.send("❌ That message does not contain an embed image to download.")
            return

        if not pokemon_name:
            pokemon_name = self.infer_pokemon_name(ctx, source_message)

        if not pokemon_name:
            await ctx.send("❌ Provide a pokemon name after the command, or make sure the replied embed has a title.")
            return

        folder_name = sanitize_folder_name(pokemon_name)
        target_directory = os.path.join(DOWNLOADS_DIR, folder_name)
        os.makedirs(target_directory, exist_ok=True)

        timeout = aiohttp.ClientTimeout(total=30)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            try:
                async with session.get(image_url) as response:
                    if response.status != 200:
                        await ctx.send(f"❌ Failed to download the image. HTTP status: {response.status}.")
                        return

                    content_type = response.headers.get("Content-Type", "")
                    extension = guess_extension(image_url, content_type)
                    file_name, file_path = random_six_digit_name(target_directory, extension)
                    image_bytes = await response.read()
            except (aiohttp.ClientError, asyncio.TimeoutError):
                await ctx.send("❌ Failed to download the image from the embed URL.")
                return

        with open(file_path, "wb") as file_handle:
            file_handle.write(image_bytes)

        await ctx.send(f"✅ Saved image as `{file_name}` in `{folder_name}`.")

    @commands.command(name="rundownload")
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def rundownload(self, ctx, *args):
        if len(args) < 2:
            await ctx.send("❌ Usage: `o!rundownload <name> <number>`")
            return

        try:
            download_count = int(args[-1])
        except ValueError:
            await ctx.send("❌ The last value must be the number of images to download.")
            return

        if download_count <= 0:
            await ctx.send("❌ Number of images must be greater than 0.")
            return

        pokemon_name = " ".join(args[:-1]).strip()
        if not pokemon_name:
            await ctx.send("❌ Please provide a pokemon name before the number.")
            return

        matches = await self.find_recent_spawn_images(pokemon_name, download_count)
        if not matches:
            await ctx.send(f"❌ No recent spawn images found for `{pokemon_name}` in incense channels.")
            return

        folder_name = sanitize_folder_name(pokemon_name)
        os.makedirs(os.path.join(DOWNLOADS_DIR, folder_name), exist_ok=True)

        saved_files = []
        for match in matches:
            file_name = await self.save_embed_image(match["image_url"], folder_name)
            if file_name:
                saved_files.append(file_name)

        if not saved_files:
            await ctx.send(f"❌ Found matching spawn messages for `{pokemon_name}`, but all downloads failed.")
            return

        await ctx.send(f"✅ Downloaded {len(saved_files)} image(s) for `{pokemon_name}` into `{folder_name}`.")


async def setup(bot):
    await bot.add_cog(DownloadCog(bot))