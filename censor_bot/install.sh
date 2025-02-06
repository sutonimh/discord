#!/bin/bash

# Clone the repository
echo "Cloning repository from GitHub..."
git clone https://github.com/sutonimh/discord.git || { echo "Error cloning repository"; exit 1; }

# Navigate into the censor_bot directory
cd discord/censor_bot || { echo "censor_bot directory not found!"; exit 1; }

# Prompt for Discord bot token
read -rp "Enter your Discord Bot Token: " BOT_TOKEN

# Prompt for warning message (with a default suggestion)
read -rp "Enter your warning message (default: \"Don't post that trash here:\"): " USER_WARNING
# If the user leaves it empty, use the default.
WARNING_MESSAGE=${USER_WARNING:-"Don't post that trash here:"}

# Prompt for comma separated blacklisted domains
read -rp "Enter a comma separated list of domains to blacklist (default: badwebsite.com, malicious.com): " DOMAINS
DOMAINS=${DOMAINS:-"badwebsite.com, malicious.com"}

# Create .env file with the provided values
cat <<EOF > .env
DISCORD_BOT_TOKEN=${BOT_TOKEN}
WARNING_MESSAGE=${WARNING_MESSAGE}
BLACKLISTED_DOMAINS=${DOMAINS}
EOF

echo ".env file has been created with your settings."

# Install Python dependencies
if [ -f "requirements.txt" ]; then
    echo "Installing dependencies from requirements.txt..."
    pip install -r requirements.txt
else
    echo "requirements.txt not found. Ensure you have installed discord.py and python-dotenv."
fi

echo "Setup complete. You can now run your bot using: python bot.py"
