#!/bin/bash

# Make this script executable just in case
chmod +x "$0"

APP_NAME="JeetPad"
INSTALL_DIR="$HOME/.local/share/$APP_NAME"
DESKTOP_FILE="$HOME/.local/share/applications/$APP_NAME.desktop"
CONFIG_DIR="$HOME/.config/$APP_NAME"
AUTOSTART_FILE="$HOME/.config/autostart/$APP_NAME.desktop"

echo "======================================"
echo " Uninstalling $APP_NAME "
echo "======================================"

echo "🗑️ Removing application files..."
rm -rf "$INSTALL_DIR"

echo "🗑️ Removing application menu shortcut..."
rm -f "$DESKTOP_FILE"

echo "🗑️ Removing autostart shortcut..."
rm -f "$AUTOSTART_FILE"

# Ask the user if they want to delete their saved settings
read -p "Do you want to delete your saved JeetPad settings and mappings? (y/N): " response
if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    echo "🗑️ Removing configuration files..."
    rm -rf "$CONFIG_DIR"
else
    echo "💾 Saved settings kept."
fi

echo ""
echo " $APP_NAME has been completely uninstalled from your system."
