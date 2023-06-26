from fastapi.templating import Jinja2Templates
from fastapi import FastAPI, Request
from tkinter import messagebox
from datetime import datetime
from tkinter import ttk
import tkinter as tk
import pandas as pd
import configparser
import webbrowser
import threading
import uvicorn
import winreg
import shutil
import gdown
import json5
import json
import time
import sys
import csv
import vdf
import os

VERSION = "v022-DEBUGBuild"
ENABLE_CONSOLE_GARBAGE = True
config = configparser.RawConfigParser()
now = datetime.now()
dt = now.strftime("%d/%m/%Y %H:%M:%S")
config_path = f"{os.environ['APPDATA']}/CitiesModCompatibilityChecker"
config_file_path = os.path.join(f"{os.environ['APPDATA']}/CitiesModCompatibilityChecker", "ClientConfig.ini")
templates = Jinja2Templates(directory="templates")


class CitiesModCompatibilityChecker:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("CitiesModChecker - t2v.city @ 2023")
        self.window.geometry("450x300")
        self.window.resizable(False, False)
        self.window.iconbitmap("favicon.ico")

        self.button_frame = tk.Frame(self.window)
        self.button_frame.pack(side="left", fill="y")

        canvas = tk.Canvas(window)
        canvas.pack(side="right", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(window, orient="vertical", command=canvas.yview)
        scrollbar.pack(side="right", fill="y")

        canvas.configure(yscrollcommand=scrollbar.set)

        frame = tk.Frame(canvas)
        canvas.create_window((0, 0), window=frame, anchor="nw")

        mod_list_update = tk.StringVar()
        sys_list_update = tk.StringVar()
        generating_loader = tk.StringVar()
        self.config_label_vars = [mod_list_update, sys_list_update, generating_loader]


    def __call__(self, *args, **kwargs):
        ttk.Button(button_frame, text="Download Latest Mods List",
                   command=lambda: run_mod_list_downloader(tkinter_info)).pack(anchor="w")
        ttk.Button(button_frame, text="Check System",
                   command=lambda: run_mod_checker(tkinter_info)).pack(anchor="w")

        tk.Label(button_frame, text="Last Mods List Update: ").pack(anchor="w")
        tk.Label(button_frame, textvariable=mod_list_update).pack(anchor="w")
        tk.Label(button_frame, text="Last System Check Update: ").pack(anchor="w")
        tk.Label(button_frame, textvariable=sys_list_update).pack(anchor="w")

        ttk.Button(button_frame, text="Refresh Config",
                   command=lambda: load_config(tkinter_info)).pack(anchor="w")
        ttk.Button(button_frame, text="Delete Data",
                   command=lambda: delete_confirmation_window()).pack(anchor="w")

        ttk.Button(button_frame, text="Close", command=cancel_mod_checker).pack(side="bottom", anchor="w")
        tk.Label(button_frame, text="Version: " + VERSION).pack(side="bottom", anchor="w")

        help = tk.Label(window, text="Need Help?", cursor="hand2")
        help.pack(side="bottom", anchor="w")
        help.bind("<Button-1>", lambda event: show_help())

        tk.Label(frame, text="Starting Cities Skylines Mod Compatibility Checker...", wraplength=280).pack()
        canvas.bind_all("<MouseWheel>", lambda event: canvas.yview_scroll(int(-1 * (event.delta / 120)), "units"))


        window.update()
        settings = FastAPISettings()
        app = FastAPIWebReportViewer(settings)
        load_config(tkinter_info)
        window.mainloop()