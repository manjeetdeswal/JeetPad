#!/bin/bash

# Make this script executable for future runs just in case it was launched via 'bash install.sh'
chmod +x "$0"

# --- CONFIGURATION ---
APP_NAME="JeetPad"
EXECUTABLE="JeetPad"
ICON="icon.png"

# Define destination paths (User-level install avoids needing sudo permissions)
INSTALL_DIR="$HOME/.local/share/$APP_NAME"
DESKTOP_DIR="$HOME/.local/share/applications"

echo "======================================"
echo " Starting installation for $APP_NAME "
echo "======================================"

# 1. Check if the required files are actually in the folder
if [ ! -f "$EXECUTABLE" ] || [ ! -f "$ICON" ]; then
    echo "❌ Error: Could not find '$EXECUTABLE' or '$ICON' in the current directory."
    echo "Please make sure you extracted the entire zip file before running this script."
    exit 1
fi

# 2. Create the installation directories if they don't exist
echo "📂 Creating directories..."
mkdir -p "$INSTALL_DIR"
mkdir -p "$DESKTOP_DIR"

# 3. Copy the executable and icon to the safe local folder
echo "🚚 Copying files..."
cp "$EXECUTABLE" "$INSTALL_DIR/"
cp "$ICON" "$INSTALL_DIR/"

# 4. Guarantee the app has permission to run
chmod +x "$INSTALL_DIR/$EXECUTABLE"

# 5. Create the .desktop file for the Linux Application Menu
echo "🔗 Creating application menu shortcut..."
DESKTOP_FILE="$DESKTOP_DIR/$APP_NAME.desktop"

# Write the configuration into the .desktop file
cat > "$DESKTOP_FILE" << EOL
[Desktop Entry]
Name=$APP_NAME
Comment=Use your controller as a mouse and keyboard
Exec="$INSTALL_DIR/$EXECUTABLE"
Icon=$INSTALL_DIR/$ICON
Terminal=false
Type=Application
Categories=Utility;HardwareSettings;
EOL

# 6. Make the shortcut trusted/executable
chmod +x "$DESKTOP_FILE"

echo ""
echo " $APP_NAME has been successfully installed!"
echo "You can now safely delete this downloaded folder."
echo "Press the Super (Windows) key and search for '$APP_NAME' to launch it!"
