python3 -m PyInstaller --noconsole --onefile --name "JeetPad" --add-data "icon.png:." --hidden-import pygame --hidden-import pynput --hidden-import customtkinter app.py
