import discord
from discord.ext import commands
from discord import app_commands
import re
from urllib.parse import urlparse
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Required environment variable: Bot token
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
if not DISCORD_BOT_TOKEN:
    raise Exception("DISCORD_BOT_TOKEN not found in environment variables.")

# Bot version number
BOT_VERSION = "1.0.0"

# Configuration variables (with defaults)
WARNING_MESSAGE = os.getenv("WARNING_MESSAGE", "Don't post that trash here:")
blacklisted_domains_env = os.getenv("BLACKLISTED_DOMAINS", "x.com, twitter.com")
blacklisted_domains = [domain.strip().lower() for domain in blacklisted_domains_env.split(",") if domain.strip()]

# Optional logging configuration
log_channel_id_str = os.getenv("LOG_CHANNEL_ID", "")
if log_channel_id_str:
    try:
        LOG_CHANNEL_ID = int(log_channel_id_str)
        LOGGING_ENABLED = True
    except ValueError:
        LOG_CHANNEL_ID = None
        LOGGING_ENABLED = False
        print("LOG_CHANNEL_ID is not a valid integer; logging will be disabled.")
else:
    LOG_CHANNEL_ID = None
    LOGGING_ENABLED = False

# Owner ID for restricting slash command access.
# If left blank, no restriction is applied.
owner_id_raw = os.getenv("OWNER_ID", "").strip()
OWNER_ID = None
if owner_id_raw:
    try:
        OWNER_ID = int(owner_id_raw)
    except ValueError:
        print("Invalid OWNER_ID provided; falling back to no owner restriction.")
        OWNER_ID = None

# Setup bot intents and create bot instance
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Global check: Only allow slash commands from the owner (if OWNER_ID is set)
async def check_owner(interaction: discord.Interaction) -> bool:
    if OWNER_ID is None:
        # No owner restriction; allow everyone.
        return True
    elif interaction.user.id == OWNER_ID:
        return True
    else:
        raise app_commands.CheckFailure("You are not authorized to use this command.")

# Add the global check using an alternative method.
if hasattr(bot, "add_application_command_check"):
    bot.add_application_command_check(check_owner)
else:
    print("Global check function 'add_application_command_check' not available; consider decorating each command.")

# Helper function to log command usage.
async def log_command(interaction: discord.Interaction, command_name: str, details: str = ""):
    if LOGGING_ENABLED and LOG_CHANNEL_ID:
        log_channel = bot.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            await log_channel.send(f"User {interaction.user} used command /{command_name}. {details}")
        else:
            print("Log channel not found.")

# Regular expression to match URLs in messages.
url_regex = re.compile(
    r"((https?:\/\/)?((www\.)?([\w\-]+\.[\w\-.]+))(\:\d+)?(\/[\w\-.?%&=]*)?)"
)

@bot.event
async def on_ready():
    # Sync the slash commands (application commands)
    await bot.tree.sync()
    print(f"Logged in as {bot.user.name} (Version: {BOT_VERSION})")

@bot.event
async def on_message(message):
    # Ignore messages sent by the bot.
    if message.author == bot.user:
        return

    # Search for URLs in the message.
    urls = url_regex.findall(message.content)
    for url_tuple in urls:
        url = url_tuple[0]
        # Ensure the URL has a scheme.
        if not url.startswith("http"):
            url = "http://" + url

        parsed_url = urlparse(url)
        domain = parsed_url.netloc.lower()
        if ":" in domain:
            domain = domain.split(":")[0]

        # If the domain is blacklisted, delete the message and warn the user.
        if domain in blacklisted_domains:
            try:
                await message.delete()
                warning = await message.channel.send(
                    f"{message.author.mention} {WARNING_MESSAGE}\n{url}"
                )
                await warning.delete(delay=5)
                if LOGGING_ENABLED and LOG_CHANNEL_ID:
                    log_channel = bot.get_channel(LOG_CHANNEL_ID)
                    if log_channel:
                        await log_channel.send(
                            f"Deleted message from {message.author} in {message.channel.mention} containing blacklisted domain '{domain}'.\nMessage content: {message.content}"
                        )
                    else:
                        print("Log channel not found.")
            except discord.errors.Forbidden:
                print("Bot lacks permission to delete messages.")
            break

    await bot.process_commands(message)

# Slash command to add a domain to the blacklist.
@bot.tree.command(name="adddomain", description="Add a domain to the blacklist.")
async def adddomain(interaction: discord.Interaction, domain: str):
    domain = domain.strip().lower()
    if domain in blacklisted_domains:
        await interaction.response.send_message(f"Domain '{domain}' is already blacklisted.", ephemeral=True)
    else:
        blacklisted_domains.append(domain)
        await interaction.response.send_message(f"Domain '{domain}' added to the blacklist.", ephemeral=True)
    await log_command(interaction, "adddomain", f"Domain: {domain}")

# Slash command to remove a domain from the blacklist.
@bot.tree.command(name="removedomain", description="Remove a domain from the blacklist.")
async def removedomain(interaction: discord.Interaction, domain: str):
    domain = domain.strip().lower()
    if domain in blacklisted_domains:
        blacklisted_domains.remove(domain)
        await interaction.response.send_message(f"Domain '{domain}' removed from the blacklist.", ephemeral=True)
    else:
        await interaction.response.send_message(f"Domain '{domain}' was not found in the blacklist.", ephemeral=True)
    await log_command(interaction, "removedomain", f"Domain: {domain}")

# Slash command to list all blacklisted domains.
@bot.tree.command(name="listdomains", description="List all blacklisted domains.")
async def listdomains(interaction: discord.Interaction):
    domains = ", ".join(blacklisted_domains) if blacklisted_domains else "No domains are blacklisted."
    await interaction.response.send_message(f"Blacklisted domains: {domains}", ephemeral=True)
    await log_command(interaction, "listdomains", f"Domains: {domains}")

# Slash command to update the warning message.
@bot.tree.command(name="setwarning", description="Set a new warning message.")
async def setwarning(interaction: discord.Interaction, message: str):
    global WARNING_MESSAGE
    WARNING_MESSAGE = message
    await interaction.response.send_message(f"Warning message updated to: {WARNING_MESSAGE}", ephemeral=True)
    await log_command(interaction, "setwarning", f"New warning: {WARNING_MESSAGE}")

# Slash command to set the logging channel.
@bot.tree.command(name="setlogchannel", description="Set the logging channel for bot actions.")
async def setlogchannel(interaction: discord.Interaction, channel: discord.TextChannel):
    global LOG_CHANNEL_ID, LOGGING_ENABLED
    LOG_CHANNEL_ID = channel.id
    LOGGING_ENABLED = True
    await interaction.response.send_message(f"Log channel set to {channel.mention}.", ephemeral=True)
    await log_command(interaction, "setlogchannel", f"Log channel set to: {channel.mention}")

# Slash command to toggle logging on/off.
@bot.tree.command(name="togglelogging", description="Toggle logging on or off.")
async def togglelogging(interaction: discord.Interaction):
    global LOGGING_ENABLED
    LOGGING_ENABLED = not LOGGING_ENABLED
    status = "enabled" if LOGGING_ENABLED else "disabled"
    await interaction.response.send_message(f"Logging has been {status}.", ephemeral=True)
    await log_command(interaction, "togglelogging", f"Logging now: {status}")

# Slash command to display the current configuration and status.
@bot.tree.command(name="status", description="Show the current bot configuration and status.")
async def status(interaction: discord.Interaction):
    status_msg = (
        f"Bot Version: {BOT_VERSION}\n"
        f"Blacklisted domains: {', '.join(blacklisted_domains)}\n"
        f"Warning message: {WARNING_MESSAGE}\n"
        f"Logging: {'Enabled' if LOGGING_ENABLED else 'Disabled'}"
    )
    if LOG_CHANNEL_ID:
        status_msg += f" (Log channel ID: {LOG_CHANNEL_ID})"
    await interaction.response.send_message(status_msg, ephemeral=True)
    await log_command(interaction, "status", details=status_msg)

# Slash command to display help information.
@bot.tree.command(name="help", description="Display available slash commands.")
async def help_command(interaction: discord.Interaction):
    help_text = (
        "/adddomain [domain]: Add a new domain to the blacklist.\n"
        "/removedomain [domain]: Remove a domain from the blacklist.\n"
        "/listdomains: List all blacklisted domains.\n"
        "/setwarning [message]: Update the warning message.\n"
        "/setlogchannel [channel]: Set the channel for logging actions.\n"
        "/togglelogging: Toggle logging on or off.\n"
        "/status: Show current configuration and status.\n"
        "/help: Display this help message."
    )
    await interaction.response.send_message(help_text, ephemeral=True)
    await log_command(interaction, "help", "Displayed help information.")

bot.run(DISCORD_BOT_TOKEN)
