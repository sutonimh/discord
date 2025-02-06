#!/bin/bash

# Function to install Git if not found.
install_git() {
    if ! command -v git &>/dev/null; then
        echo "Git is not installed. Attempting to install Git..."
        if [ "$(uname)" == "Darwin" ]; then
            # macOS: Try using Homebrew.
            if command -v brew &>/dev/null; then
                brew install git || { echo "Failed to install Git using brew"; exit 1; }
            else
                echo "Please install Homebrew first (https://brew.sh) or install Git manually."
                exit 1
            fi
        else
            # Assume Linux Debian-based.
            sudo apt update && sudo apt install -y git || { echo "Failed to install Git"; exit 1; }
        fi
    else
        echo "Git is already installed."
    fi
}

# Function to install Python3 and pip if not found.
install_python() {
    if ! command -v python3 &>/dev/null; then
        echo "Python3 is not installed. Attempting to install Python3..."
        if [ "$(uname)" == "Darwin" ]; then
            if command -v brew &>/dev/null; then
                brew install python || { echo "Failed to install Python using brew"; exit 1; }
            else
                echo "Please install Homebrew first (https://brew.sh) or install Python manually."
                exit 1
            fi
        else
            sudo apt update && sudo apt install -y python3 python3-pip || { echo "Failed to install Python3"; exit 1; }
        fi
    else
        echo "Python3 is already installed."
    fi
}

# Install required system dependencies.
install_git
install_python

# Create a directory for the bot.
TARGET_DIR="censor-bot"
if [ -d "$TARGET_DIR" ]; then
    echo "Directory '$TARGET_DIR' already exists. Please remove or rename it and re-run this script."
    exit 1
fi
mkdir "$TARGET_DIR"

# Clone only the censor_bot directory from the repository using sparse-checkout.
echo "Cloning only the censor_bot directory from GitHub repository..."
git clone --filter=blob:none --sparse https://github.com/sutonimh/discord.git "$TARGET_DIR" || { echo "Error cloning repository"; exit 1; }
cd "$TARGET_DIR" || { echo "Failed to enter directory $TARGET_DIR"; exit 1; }
git sparse-checkout init --cone
git sparse-checkout set censor_bot

# Move the contents of censor_bot to the current directory and remove the empty folder.
mv censor_bot/* .
rm -rf censor_bot

# Interactive configuration prompts.
read -rp "Enter your Discord Bot Token: " BOT_TOKEN

read -rp "Enter your warning message (default: \"Don't post that trash here:\"): " USER_WARNING
WARNING_MESSAGE=${USER_WARNING:-"Don't post that trash here:"}

read -rp "Enter a comma separated list of domains to blacklist (default: badwebsite.com, malicious.com): " DOMAINS
DOMAINS=${DOMAINS:-"badwebsite.com, malicious.com"}

read -rp "Enter logging channel ID (optional, leave blank for no logging): " LOG_CHANNEL

# Create the .env file with provided values.
cat <<EOF > .env
DISCORD_BOT_TOKEN=${BOT_TOKEN}
WARNING_MESSAGE=${WARNING_MESSAGE}
BLACKLISTED_DOMAINS=${DOMAINS}
LOG_CHANNEL_ID=${LOG_CHANNEL}
EOF

echo ".env file has been created with your settings."

# Check for requirements.txt; if not found, create it with necessary packages.
if [ ! -f "requirements.txt" ]; then
    echo "requirements.txt not found. Creating requirements.txt with necessary dependencies..."
    cat <<EOL > requirements.txt
discord.py>=2.0.0
python-dotenv
EOL
fi

# Install Python dependencies.
echo "Installing Python dependencies from requirements.txt..."
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt

echo "Setup complete. You can now run your bot using: python3 bot.py"
