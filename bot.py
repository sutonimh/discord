import discord
from discord.ext import commands
import re
from urllib.parse import urlparse

# List of blacklisted domains. Add any domains you want to censor.
blacklisted_domains = ['x.com', 'twitter.com']

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
                    f"{message.author.mention}, links from `{domain}` are not allowed here."
                )
                # Delete the warning after 5 seconds.
                await warning.delete(delay=5)
            except discord.errors.Forbidden:
                print("Bot lacks permission to delete messages.")
            # Stop processing further URLs after handling one blacklisted link.
            break

    # Process other bot commands if present.
    await bot.process_commands(message)

# Replace 'YOUR_BOT_TOKEN' with your bot's actual token.
bot.run('YOUR_BOT_TOKEN')
