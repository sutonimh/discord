#!/bin/bash

# Function to install Git if not found.
install_git() {
    if ! command -v git &>/dev/null; then
        echo "Git is not installed. Attempting to install Git..."
        if [ "$(uname)" == "Darwin" ]; then
            if command -v brew &>/dev/null; then
                brew install git || { echo "Failed to install Git using brew"; exit 1; }
            else
                echo "Please install Homebrew (https://brew.sh) or Git manually."
                exit 1
            fi
        else
            sudo apt update && sudo apt install -y git || { echo "Failed to install Git"; exit 1; }
        fi
    else
        echo "Git is already installed."
    fi
}

# Function to install Python3 if not found.
install_python() {
    if ! command -v python3 &>/dev/null; then
        echo "Python3 is not installed. Attempting to install Python3..."
        if [ "$(uname)" == "Darwin" ]; then
            if command -v brew &>/dev/null; then
                brew install python || { echo "Failed to install Python using brew"; exit 1; }
            else
                echo "Please install Homebrew (https://brew.sh) or Python manually."
                exit 1
            fi
        else
            sudo apt update && sudo apt install -y python3 || { echo "Failed to install Python3"; exit 1; }
        fi
    else
        echo "Python3 is already installed."
    fi
}

# Function to ensure that python3-venv is installed.
install_venv() {
    python3 -m venv --help &>/dev/null
    if [ $? -ne 0 ]; then
        echo "python3-venv does not appear to be installed."
        if [ "$(uname)" != "Darwin" ]; then
            echo "Attempting to install python3-venv using apt..."
            sudo apt update && sudo apt install -y python3-venv || { echo "Failed to install python3-venv. Please install it manually."; exit 1; }
            # Verify that venv is now available.
            python3 -m venv --help &>/dev/null
            if [ $? -ne 0 ]; then
                echo "python3-venv is still not available after installation. Exiting."
                exit 1
            fi
        else
            echo "On macOS, please ensure that Python is installed properly (via Homebrew, for example)."
            exit 1
        fi
    else
        echo "Python3 venv module is available."
    fi
}

# Function to ensure either curl or wget is installed.
install_downloader() {
    if ! command -v curl &>/dev/null && ! command -v wget &>/dev/null; then
        echo "Neither curl nor wget is installed. Attempting to install curl..."
        if [ "$(uname)" == "Darwin" ]; then
            if command -v brew &>/dev/null; then
                brew install curl || { echo "Failed to install curl using brew"; exit 1; }
            else
                echo "Please install curl manually on macOS."
                exit 1
            fi
        else
            sudo apt update && sudo apt install -y curl || { echo "Failed to install curl"; exit 1; }
        fi
    fi
}

# Install required system dependencies.
install_git
install_python
install_venv
install_downloader

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

# Default blacklist domains updated to x.com, twitter.com
read -rp "Enter a comma separated list of domains to blacklist (default: x.com, twitter.com): " DOMAINS
DOMAINS=${DOMAINS:-"x.com, twitter.com"}

read -rp "Enter logging channel ID (optional, leave blank for no logging): " LOG_CHANNEL

# Create the .env file with provided values.
cat <<EOF > .env
DISCORD_BOT_TOKEN=${BOT_TOKEN}
WARNING_MESSAGE=${WARNING_MESSAGE}
BLACKLISTED_DOMAINS=${DOMAINS}
LOG_CHANNEL_ID=${LOG_CHANNEL}
EOF

echo ".env file has been created with your settings."

# Create requirements.txt if it does not exist.
if [ ! -f "requirements.txt" ]; then
    echo "requirements.txt not found. Creating requirements.txt with necessary dependencies..."
    cat <<EOL > requirements.txt
discord.py>=2.0.0
python-dotenv
EOL
fi

# Create a virtual environment using --upgrade-deps and --break-system-packages.
echo "Creating Python virtual environment..."
python3 -m venv --upgrade-deps --break-system-packages venv || { echo "Failed to create virtual environment"; exit 1; }

# Activate the virtual environment.
source venv/bin/activate

# Upgrade pip and install Python dependencies.
echo "Upgrading pip and installing Python dependencies from requirements.txt..."
pip install --upgrade pip
pip install -r requirements.txt || { echo "Failed to install dependencies"; exit 1; }

echo "Setup complete."
echo "To run your bot, activate the virtual environment with 'source venv/bin/activate' and then run 'python bot.py'."
