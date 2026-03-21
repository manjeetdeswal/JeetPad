# 🎮 JeetPad
**Turn any game controller into a fully customizable mouse and keyboard.**

## ❤️ Support the Creator

If this app helped you land a job, or if you just want to support open-source development, consider buying me a coffee!

<a href="https://www.patreon.com/cw/UnrealComponent">
  <img src="https://c5.patreon.com/external/logo/become_a_patron_button.png" alt="Support on Patreon" height="45">
</a>




JeetPad is a cross-platform desktop utility that allows you to navigate your operating system, browse the web, and control your PC using a standard game controller. It runs silently in the system tray and features a modern, user-friendly interface for remapping buttons on the fly.


## 📸 Screenshots

<p align="center">
  <img src="https://github.com/manjeetdeswal/JeetPad/blob/main/ss/Screenshot%202026-03-21%20215353.png" width="45%" alt="Keyboard" />
  <img src="https://github.com/manjeetdeswal/JeetPad/blob/main/ss/Screenshot%202026-03-21%20215412.png" width="45%" alt="Display Extension" />
</p>
<p align="center">
    <img src="https://github.com/manjeetdeswal/JeetPad/blob/main/ss/Screenshot%202026-03-21%20215430.png" width="85%" alt="Mic Streaming" />
</p



## ✨ Key Features
* **Universal Compatibility:** Works seamlessly on both Windows and Linux.
* **Modern GUI:** Built with CustomTkinter for a sleek, dark-mode ready interface.
* **Full Remapping Engine:** Map any controller button (including the D-Pad) to mouse clicks, keyboard keys, media controls, or the scroll wheel.
* **Smart OS Detection:** Automatically handles Linux `evdev` driver quirks (like fractional scrolling and axis shifting) under the hood so your controller "just works."
* **Multi-Controller Priority:** Plug in multiple controllers and use the built-in Dropdown to choose which one controls the PC.
* **Auto-Scan & Hotplugging:** Automatically detects when a controller is connected or disconnected.
* **Minimize to Tray:** Runs quietly in the background without cluttering your taskbar.
* **Start with OS:** One-click toggle to automatically launch the app when your computer boots.

---

## 🚀 Installation (For Regular Users)

Go to the [Releases](../../releases) page to download the latest version for your operating system.

### Windows
1. Download `JeetPad.exe`.
2. Move it to a permanent folder (like your Documents or Desktop).
3. Double-click to run! (You can check "Start with OS" in the app settings to never worry about it again).

### Linux
1. Download the `JeetPad_Linux.zip` file and extract it.
2. Open your terminal in the extracted folder.
3. Run the installer script:
   bash
   ./install.sh
   
4. The app will now appear in your system's Application Menu! (To remove it later, simply run the included `uninstall.sh`).

---

## 💻 Building from Source (For Developers)

If you want to modify the code or build the executable yourself, follow these steps:

**1. Clone the repository:**
bash
git clone https://github.com/manjeetdeswal/JeetPad.git
cd JeetPad


**2. Install dependencies:**
bash
python -m pip install pygame-ce pynput customtkinter pystray Pillow


**3. Run the app:**
bash
python app.py


**4. Build the Standalone Executable:**
We use PyInstaller to package the app. Make sure your `icon.ico` and `icon.png` are in the root directory.

*For Windows:*
bash
python -m PyInstaller --noconsole --onefile --name "JeetPad" --icon=icon.ico --add-data "icon.ico;." --add-data "icon.png;." --hidden-import pygame --hidden-import pynput --hidden-import customtkinter app.py


*For Linux:*
bash
python3 -m PyInstaller --noconsole --onefile --name "JeetPad" --add-data "icon.png:." --hidden-import pygame --hidden-import pynput --hidden-import customtkinter app.py


---

## 🕹️ How to Use

1. **Activate/Deactivate:** By default, press and hold the **Start** button on your controller for 3 seconds to toggle JeetPad on or off. You will feel a rumble when the state changes.
2. **Change the Toggle Button:** Open the app and use the "Hold to Toggle App" dropdown to change this to any button you prefer.
3. **Remap Buttons:** Click "Open Remap Menu" to bring up the visual keyboard and mouse layout. Click any action to instantly assign it to a controller button.

## 🛠️ Tech Stack
* **Python 3**
* **Pygame-CE:** Hardware polling, D-Pad edge detection, and hotplugging.
* **Pynput:** Low-level OS injection for mouse movement and keystrokes.
* **CustomTkinter:** Modern GUI framework.
* **Pystray:** Cross-platform system tray integration.

## 📄 License
Created by Jeet Studio. Feel free to fork, modify, and improve!
