from tkinter import messagebox
from datetime import datetime
from tkinter import ttk
import tkinter as tk
import pandas as pd
import configparser
import webbrowser
import winreg
import shutil
import gdown
import time
import sys
import csv
import vdf
import os

VERSION = "v010-DEBUGBuild?"
config = configparser.RawConfigParser()
now = datetime.now()
dt = now.strftime("%d/%m/%Y %H:%M:%S")
config_path = f"{os.environ['APPDATA']}/CitiesModCompatibilityChecker"
config_file_path = os.path.join(f"{os.environ['APPDATA']}/CitiesModCompatibilityChecker", "ClientConfig.ini")


def add_line(text, args):
    time.sleep(0.1)
    tk.Label(args[0], text=text, wraplength=280).pack()
    args[0].update_idletasks()
    args[1].configure(scrollregion=args[1].bbox("all"))
    args[1].yview_moveto(1)


def get_steam_library_folders(args):
    try:
        add_line("Finding Steam Install Location...", args)
        steam_registry_path = r"SOFTWARE\WOW6432Node\Valve\Steam"
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, steam_registry_path) as key:
            steam_path = winreg.QueryValueEx(key, "InstallPath")[0]

        add_line("Finding Steam Library Folders...", args)
        vdf_path = os.path.join(steam_path, "steamapps", "libraryfolders.vdf")
        with open(vdf_path, "r") as file:
            content = file.read()
            parsed_data = vdf.loads(content)
            library_folders = parsed_data.get('libraryfolders', {})
            paths = []
            for folder in library_folders.values():
                path = folder.get('path')
                if path:
                    paths.append(path)
            for folder in paths:
                add_line(f"Found: {folder}", args)
        return paths
    except Exception as e:
        print("Error: ", e)


def grab_mods_list(cities_dir):
    mods_list = []
    for root, dirs, files in os.walk(cities_dir + '/steamapps/workshop/content/255710'):
        for subdir in dirs:
            path_parts = subdir.split('\\')
            mod_id_part = path_parts[-1]
            mods_list.append(mod_id_part)
    return mods_list


def run_mod_checker(args):
    library_folders = get_steam_library_folders(args)
    add_line(f"Checking for Cities Skylines...", args)
    cities_skylines_dir = None
    for folder in library_folders:
        sanitised_folder = folder.replace("\\", "/") + '/steamapps/common/Cities_Skylines'
        if os.path.isdir(sanitised_folder):
            add_line(f"{sanitised_folder}. Found! Setting to Default", args)
            cities_skylines_dir = folder.replace("\\", "/")
            break
        add_line(f"{sanitised_folder}. Not Found. Skipping...", args)

    add_line("Grabbing Mods List..", args)
    mods_list = grab_mods_list(cities_skylines_dir)
    txt_path = os.path.join(config_path, "LocalCitiesModList.txt")
    if os.path.exists(txt_path):
        os.remove(txt_path)
    with open(txt_path, 'w') as f:
        for mod_id in mods_list:
            f.write(f"{mod_id}\n")
    add_line(f"Mods List Completed: {mods_list}", args)
    config.read(config_file_path)
    config.set('LastUpdated', 'sys_list_last_updated', str(dt))
    config.set('ProgramFiles', 'modlist_path', "./LocalCitiesModList.txt")
    with open(config_file_path, 'w') as f:
        config.write(f)
    args[3][1].set(config.get('LastUpdated', 'sys_list_last_updated'))
    load_config(args)
    add_line("System Check Completed", args)


def run_mod_list_downloader(args):
    add_line("Starting Mod List Spreadsheet Update...", args)
    xlsx_path = os.path.join(config_path, "CitiesModCompatibilityList.xlsx")
    if os.path.exists(xlsx_path):
        add_line("Old Version Found. Deleting...", args)
        os.remove(xlsx_path)
    try:
        add_line("Beginning xlsx Download...", args)
        gdown.download(id="1mVFkj_7ij4FLzKs2QJaONNmb9Z-SRqUeG6xFGqEX1ew", output=xlsx_path, quiet=True)
        add_line("Download was Successful.", args)
        pass
    except:
        add_line("Download Failed. Please place the csv in the config directory and edit ClientConfig.ini", args)
        add_line("You can download an updated csv at https://pdxint.at/BrokenModCS", args)
        args[3][0].set("Failed to Download.")
        return None
    add_line("Converting xlsx File to csv Files...", args)
    try:
        xlf = pd.ExcelFile(xlsx_path)
        for page in xlf.sheet_names:
            if os.path.exists(xlsx_path.replace("xlsx", f"{page}.csv")):
                add_line("Old Version Found. Deleting...", args)
                os.remove(xlsx_path.replace("xlsx", f"{page}.csv"))
            df = xlf.parse(page)
            df.to_csv(xlsx_path.replace("xlsx", f"{page.replace(' ', '_')}.csv"), index=False)
        xlf.close()
        if os.path.exists(xlsx_path):
            time.sleep(1)
            add_line("Deleting Old xlsx File...", args)
            os.remove(xlsx_path)
        add_line("Converted xlsx File to csv.", args)
        config.read(config_file_path)
        config.set('LastUpdated', 'mod_list_last_updated', str(dt))
        config.set('ProgramFiles', 'cities_mod_csv', './CitiesModCompatibilityList.csv')
        with open(config_file_path, 'w') as f:
            config.write(f)
        args[3][0].set(config.get('LastUpdated', 'mod_list_last_updated'))
        load_config(args)
        add_line("Mod List Spreadsheet Updated Successfully.", args)
    except Exception as e:
        print(e)
        add_line("Failed to Convert xlsx File to csv. Try Again?", args)
        args[3][0].set("Failed to Download.")


def compare_mods(args, progressbar):
    add_line("Generating Compatibility Report. Hang Tight...", args)
    progressbar.step(10)
    progressbar.update()
    config.read(config_file_path)
    add_line("Grabbing Local Mod List...", args)
    progressbar.step(10)
    progressbar.update()
    with open(str(config.get('ProgramFiles', 'modlist_path').replace("./", f"{config_path}/")), 'r') as txt_file:
        txt_ids = [line.strip() for line in txt_file]
    progressbar.step(10)
    progressbar.update()
    add_line("Gathering csv Mod Lists...", args)
    path_str = str(config.get('ProgramFiles', 'cities_mod_csv').replace("./", f"{config_path}/"))
    mod_list_csv_names = [path_str.replace(".csv", ".Incompatible_Mods.csv"), path_str.replace(".csv", ".Broken.csv"),
                          path_str.replace(".csv", ".Dependency_Mods_For_Saves.csv"),
                          path_str.replace(".csv", ".Game_Breaking_Assets_.csv")]
    print(mod_list_csv_names)
    for fn in os.listdir(config_path):
        if 'patch' in fn.lower():
            print(fn)
            add_line("Found Patch Specific Mod List. Adding...", args)
            mod_list_csv_names.append(os.path.join(config_path, fn))
    print(mod_list_csv_names)

    final_compat_check_list = []
    for mod_list in mod_list_csv_names:
        print(mod_list)
        csv_ids = []
        add_line("Grabbing csv File...", args)
        with open(mod_list, 'r', encoding='utf-8') as csv_file:
            reader = csv.reader(csv_file)
            for row in reader:
                progressbar.step(5)
                progressbar.update()
                csv_ids.append(row[3])
        add_line("Comparing...", args)
        compat_array = list(set(txt_ids) & set(csv_ids))
        compat_array.insert(0, mod_list)
        progressbar.step(10)
        progressbar.update()
        add_line("Check Completed. Adding...", args)
        final_compat_check_list.append(compat_array)
    add_line("Mod Compatibility Checks Completed.", args)
    add_line("Generating Report Now...", args)




def report_generation_window(args):
    rg_window = tk.Toplevel()
    rg_window.title("Confirmation")
    rg_window.geometry("400x150")
    tk.Label(rg_window, text="Generating a Mod Compatibility Report... Hang Tight... ").pack()
    progressbar = ttk.Progressbar(rg_window, style='TProgressbar')
    progressbar['orient'] = 'horizontal'
    progressbar['length'] = 300
    progressbar['mode'] = 'determinate'
    progressbar.pack()
    progressbar["value"] = 0
    compare_mods(args, progressbar)


def cancel_mod_checker():
    sys.exit('Cancelling...')


def create_config(args):
    add_line("Generating Program Configuration...", args)
    config.read(config_file_path)
    config.add_section('LastUpdated')
    config.set('LastUpdated', 'mod_list_last_updated', "Not Run Yet")
    config.set('LastUpdated', 'sys_list_last_updated', "Not Run Yet")
    config.add_section('ProgramFiles')
    config.set('ProgramFiles', 'modlist_path', "Not Generated Yet")
    config.set('ProgramFiles', 'cities_mod_csv', "Not Generated Yet")
    config.set('ProgramFiles', 'debug_log_path', "./debug.log")

    with open(config_file_path, 'w') as f:
        config.write(f)
    with open(config_file_path, 'r') as original:
        data = original.read()
    with open(config_file_path, 'w') as modified:
        modified.write("; CitiesModCompatibilityChecker by t2v @ 2023 - ClientConfig.ini\n" + data)

    add_line("Configuration Generated.", args)
    load_config(args)
    try:
        pass
    except:
        add_line("Failed to Create Config. Permissions?", args)


def load_config(args):
    tk.Label(args[0], text="Loading Configuration...", wraplength=280).pack()
    config_dir = f"{os.environ['APPDATA']}/CitiesModCompatibilityChecker"
    if os.path.isdir(config_dir):
        add_line("Config Directory Found. Attempting to Load ClientConfig.ini...", args)
        if os.path.exists(config_file_path):
            try:
                with open(config_file_path, 'r') as f:
                    config.read_file(f)
                    args[3][0].set(config.get('LastUpdated', 'mod_list_last_updated'))
                    args[3][1].set(config.get('LastUpdated', 'sys_list_last_updated'))
                    f.close()
                add_line("ClientConfig.ini Loaded.", args)
                gen_compare_mods_button(args)
            except configparser.NoSectionError:
                add_line("Config File is wrong or Corrupt. Attempting Fix...", args)
                create_config(args)
            except Exception:
                add_line("Failed to open config file. Permissions?", args)
                pass
        else:
            add_line("ClientConfig.ini Not Found.", args)
            create_config(args)
    else:
        add_line("Previous Configuration Not Found.", args)
        os.makedirs(config_dir)
        create_config(args)


def gen_compare_mods_button(args):
    config.read(config_file_path)
    if config.get('ProgramFiles', 'cities_mod_csv') and config.get('ProgramFiles',
                                                                   'modlist_path') != "Not Generated Yet":
        try:
            eb = args[4].nametowidget("compare_mods_button")
            if eb:
                eb.destroy()
        except KeyError:
            pass
        ttk.Button(args[4], text="Generate Report", command=lambda: report_generation_window(args),
                   name="compare_mods_button").pack(anchor="w")
        try:
            eb = args[4].nametowidget("generating_loader")
            if eb:
                eb.destroy()
        except KeyError:
            pass
        tk.Label(args[4], textvariable=args[3][2], name="generating_loader").pack(anchor="w")


def show_help():
    messagebox.showinfo("Help", 'How to use CitiesModCompatibilityChecker.\n1. Run '
                                '"Download Latest Mod List" and wait for it to '
                                'complete.\n2. Run "Check System" and wait for it to '
                                'complete.\n 3. CMC should automatically refresh the '
                                'configuration but in the case it doesnt, '
                                'press "Refresh Config".\n4. You should now see a '
                                '"Generate Report" button, click that to compare your '
                                'mods.\n5. You can check the Mods Compatibilty Report '
                                'by hitting the "view report" link.')


def open_link(link):
    webbrowser.open(link, new=1)


def delete_confirmation_window():
    confirmation_window = tk.Toplevel()
    confirmation_window.title("Confirmation")
    tk.Label(confirmation_window, text="This will delete all files generated by CMCC.").pack()
    tk.Label(confirmation_window, text="You will need to rerun everything.").pack()
    tk.Label(confirmation_window, text="The program will exit after deletion.").pack()
    tk.Button(confirmation_window, text="Confirm", command=confirm_action).pack(side="left")
    tk.Button(confirmation_window, text="Cancel", command=lambda: confirmation_window.destroy()).pack(side="left")


def confirm_action():
    shutil.rmtree(config_path)
    messagebox.showinfo("Information", "Data Deleted. The Program will now exit.")
    sys.exit("Exiting...")


def create_window():
    window = tk.Tk()
    window.title("CitiesModChecker - t2v.city @ 2023")
    window.geometry("450x300")
    window.resizable(False, False)

    button_frame = tk.Frame(window)
    button_frame.pack(side="left", fill="y")

    mod_list_update = tk.StringVar()
    sys_list_update = tk.StringVar()
    generating_loader = tk.StringVar()
    config_label_vars = [mod_list_update, sys_list_update, generating_loader]

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
    # site = tk.Label(window, text="t2v @ 2023", cursor="hand2")
    # site.pack(side="bottom", anchor="w")
    # site.bind("<Button-1>", lambda: open_link("https://t2v.city"))
    help = tk.Label(window, text="Need Help?", cursor="hand2")
    help.pack(side="bottom", anchor="w")
    help.bind("<Button-1>", lambda event: show_help())

    canvas = tk.Canvas(window)
    canvas.pack(side="right", fill="both", expand=True)
    scrollbar = ttk.Scrollbar(window, orient="vertical", command=canvas.yview)
    scrollbar.pack(side="right", fill="y")
    canvas.configure(yscrollcommand=scrollbar.set)
    frame = tk.Frame(canvas)
    canvas.create_window((0, 0), window=frame, anchor="nw")

    tk.Label(frame, text="Starting Cities Skylines Mod Compatibility Checker...", wraplength=280).pack()
    canvas.bind_all("<MouseWheel>", lambda event: canvas.yview_scroll(int(-1 * (event.delta / 120)), "units"))

    tkinter_info = [frame, canvas, window, config_label_vars, button_frame]

    window.update()
    load_config(tkinter_info)
    window.mainloop()


if __name__ == "__main__":
    create_window()
