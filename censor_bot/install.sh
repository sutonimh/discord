#!/bin/bash

# Clone the repository
echo "Cloning repository from GitHub..."
git clone https://github.com/sutonimh/discord.git || { echo "Error cloning repository"; exit 1; }

# Navigate into the censor_bot directory
cd discord/censor_bot || { echo "censor_bot directory not found!"; exit 1; }

# Prompt for Discord Bot Token
read -rp "Enter your Discord Bot Token: " BOT_TOKEN

# Prompt for warning message (with a default suggestion)
read -rp "Enter your warning message (default: \"Don't post that trash here:\"): " USER_WARNING
WARNING_MESSAGE=${USER_WARNING:-"Don't post that trash here:"}

# Prompt for comma separated blacklisted domains
read -rp "Enter a comma separated list of domains to blacklist (default: badwebsite.com, malicious.com): " DOMAINS
DOMAINS=${DOMAINS:-"badwebsite.com, malicious.com"}

# Prompt for an optional logging channel ID
read -rp "Enter logging channel ID (optional, leave blank for no logging): " LOG_CHANNEL

# Create .env file with the provided values
cat <<EOF > .env
DISCORD_BOT_TOKEN=${BOT_TOKEN}
WARNING_MESSAGE=${WARNING_MESSAGE}
BLACKLISTED_DOMAINS=${DOMAINS}
LOG_CHANNEL_ID=${LOG_CHANNEL}
EOF

echo ".env file has been created with your settings."

# Install Python dependencies if requirements.txt exists
if [ -f "requirements.txt" ]; then
    echo "Installing dependencies from requirements.txt..."
    pip install -r requirements.txt
else
    echo "requirements.txt not found. Ensure you have installed discord.py and python-dotenv."
fi

echo "Setup complete. You can now run your bot using: python bot.py"
