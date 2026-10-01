import os
import sqlite3
import disnake
from disnake.ext import commands
from dotenv import load_dotenv
from config_loader import config

# Load environment variables
load_dotenv()

# Initialize bot with config
try:
    bot = commands.Bot(
        command_prefix=config.prefix,
        help_command=None,
        intents=disnake.Intents.all(),
        test_guilds=[config.guild_id]
    )
except ValueError as e:
    print(f"\n❌ Configuration Error: {e}")
    print("\nPlease run the setup wizard first: python setup_wizard.py")
    exit(1)

# Database connection
db = sqlite3.connect("database.db")
cursor = db.cursor()

# Load banned words from config
banned_words = config.banned_words


@commands.Cog.listener()
async def on_ready(self):
    # When the bot connects to the server, search for and initialize the channel
    self.channel = self.bot.get_channel(self.channel_id)

@bot.command()
@commands.is_owner()
async def load(ctx, extension):
    bot.load_extension(f"cogs.{extension}")

@bot.command()
@commands.is_owner()
async def unload(ctx, extension):
    bot.unload_extension(f"cogs.{extension}")

@bot.command()
@commands.is_owner()
async def reload(ctx, extension):
    bot.reload_extension(f"cogs.{extension}")

for filename in os.listdir("cogs"):
    if filename.endswith(".db"):
        pass

for filename in os.listdir("cogs"):
    if filename.endswith(".py"):
        bot.load_extension(f"cogs.{filename[:-3]}")

"""
@bot.event
async def on_message(message):
    await bot.process_commands(message)
    for content in message.content.split():
        for censored_word in banned_words:
            if content.lower() == censored_word.lower():
                await message.delete()
                auto_mod = AutoMod(bot)
                await auto_mod.amod(await bot.get_context(message), user=message.author)
"""

@bot.event
async def on_ready():
    print(f"✅ Bot {bot.user} is ready!")
    print(f"📊 Connected to {len(bot.guilds)} guild(s)")
    print(f"🔧 Prefix: {config.prefix}")

# Load bot token from environment
try:
    bot.run(config.bot_token)
except ValueError as e:
    print(f"\n❌ Error: {e}")
    exit(1)
