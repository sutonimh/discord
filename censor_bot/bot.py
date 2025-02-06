import discord
from discord.ext import commands
import re
from urllib.parse import urlparse
import os
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

# Get environment variables (with defaults if not set)
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
if not DISCORD_BOT_TOKEN:
    raise Exception("DISCORD_BOT_TOKEN not found in environment variables.")

# Default warning message if not provided via .env
WARNING_MESSAGE = os.getenv("WARNING_MESSAGE", "Don't post that trash here:")

# Get the blacklisted domains from env, defaulting to a sample list if not provided.
# Expected format: "badwebsite.com, malicious.com"
blacklisted_domains_env = os.getenv("BLACKLISTED_DOMAINS", "badwebsite.com,malicious.com")
# Create a list by splitting and stripping whitespace
blacklisted_domains = [domain.strip().lower() for domain in blacklisted_domains_env.split(",") if domain.strip()]

# Setup intents; ensure the message_content intent is enabled.
intents = discord.Intents.default()
intents.message_content = True

# Create bot instance with a chosen command prefix.
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
    # Ignore messages from the bot itself.
    if message.author == bot.user:
        return

    # Search for URLs in the message.
    urls = url_regex.findall(message.content)
    for url_tuple in urls:
        # Extract the full URL string from the regex match.
        url = url_tuple[0]
        # If URL doesn't start with a scheme, add http:// for proper parsing.
        if not url.startswith('http'):
            url = 'http://' + url

        parsed_url = urlparse(url)
        domain = parsed_url.netloc.lower()
        # Remove any port numbers from the domain.
        if ':' in domain:
            domain = domain.split(':')[0]

        # If the domain is blacklisted, delete the message and notify the user.
        if domain in blacklisted_domains:
            try:
                await message.delete()
                warning = await message.channel.send(
                    f"{message.author.mention} {WARNING_MESSAGE}\n{url}"
                )
                # Delete the warning after 5 seconds.
                await warning.delete(delay=5)
            except discord.errors.Forbidden:
                print("Bot lacks permission to delete messages.")
            # Stop processing further URLs after handling one blacklisted link.
            break

    # Process other bot commands if present.
    await bot.process_commands(message)

bot.run(DISCORD_BOT_TOKEN)
