import discord
from discord.ext import commands
import re
from urllib.parse import urlparse
import os
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

# Get required environment variables
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
if not DISCORD_BOT_TOKEN:
    raise Exception("DISCORD_BOT_TOKEN not found in environment variables.")

# Get the warning message or use a default value
WARNING_MESSAGE = os.getenv("WARNING_MESSAGE", "Don't post that trash here:")

# Get the blacklisted domains, expecting a comma-separated string.
blacklisted_domains_env = os.getenv("BLACKLISTED_DOMAINS", "badwebsite.com, malicious.com")
blacklisted_domains = [domain.strip().lower() for domain in blacklisted_domains_env.split(",") if domain.strip()]

# Optionally, get a logging channel ID.
log_channel_id_str = os.getenv("LOG_CHANNEL_ID", "")
if log_channel_id_str:
    try:
        LOG_CHANNEL_ID = int(log_channel_id_str)
    except ValueError:
        LOG_CHANNEL_ID = None
        print("LOG_CHANNEL_ID is not a valid integer; logging will be disabled.")
else:
    LOG_CHANNEL_ID = None

# Setup intents; ensure the message_content intent is enabled.
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Regular expression pattern to match URLs in a message.
url_regex = re.compile(
    r'((https?:\/\/)?((www\.)?([\w\-]+\.[\w\-.]+))(\:\d+)?(\/[\w\-.?%&=]*)?)'
)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')

@bot.event
async def on_message(message):
    # Ignore messages sent by the bot.
    if message.author == bot.user:
        return

    # Search for URLs in the message.
    urls = url_regex.findall(message.content)
    for url_tuple in urls:
        url = url_tuple[0]
        # If the URL doesn't start with a scheme, add http:// for proper parsing.
        if not url.startswith('http'):
            url = 'http://' + url

        parsed_url = urlparse(url)
        domain = parsed_url.netloc.lower()
        # Remove any port number from the domain.
        if ':' in domain:
            domain = domain.split(':')[0]

        # If the domain is blacklisted, delete the message and warn the user.
        if domain in blacklisted_domains:
            try:
                await message.delete()
                warning = await message.channel.send(
                    f"{message.author.mention} {WARNING_MESSAGE}\n{url}"
                )
                await warning.delete(delay=5)
                
                # If logging is enabled, log this action to the designated channel.
                if LOG_CHANNEL_ID:
                    log_channel = bot.get_channel(LOG_CHANNEL_ID)
                    if log_channel:
                        await log_channel.send(
                            f"Deleted message from {message.author} in {message.channel.mention} containing blacklisted domain '{domain}'.\nMessage content: {message.content}"
                        )
                    else:
                        print("Log channel not found.")
            except discord.errors.Forbidden:
                print("Bot lacks permission to delete messages.")
            # Exit after processing the first offending URL.
            break

    # Process other bot commands, if any.
    await bot.process_commands(message)

bot.run(DISCORD_BOT_TOKEN)
