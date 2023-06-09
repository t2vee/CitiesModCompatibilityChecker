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


class FastAPISettings:
    def __init__(self):
        self.api_version = "v1"
        self.api_name = "my_api"
        self.db = "some db"
        self.logger = "configured logger"
        self.DEBUG = True


class FastAPIWebReportViewer:
    def __init__(self, settings):
        self.settings = settings
        self._fastapi = FastAPI(
            version=self.settings.api_version,
        )
        self._fastapi.add_api_route(
            path="/keepalive",
            endpoint=self.keepalive,
            methods=["GET"]
        )
        self._fastapi.add_api_route(
            path="/WebReportViewer",
            endpoint=self.web_viewer,
            methods=["GET"]
        )

        thread = threading.Thread(target=self.run, args=())
        thread.daemon = True
        thread.start()

    async def keepalive(self, request: Request):
        return {"message": "server is running!",
                "referer": f"{request.client.host}:{request.client.port}" if request.client.port else request.client.host}

    async def web_viewer(self):
        with open(str(config.get('ProgramFiles', 'json_report').replace("./", f"{config_path}/")), 'r') as f:
            json_data = f.read()
            return

    def __getattr__(self, attr):
        if hasattr(self._fastapi, attr):
            return getattr(self._fastapi, attr)
        else:
            raise AttributeError(f"{attr} not exist")

    async def __call__(self, *args, **kwargs):
        return await self._fastapi(*args, **kwargs)

    def run(self):
        while True:
            uvicorn.run(self._fastapi, host="127.0.0.1", port=8000)


class bcolors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


def clog(text, variable):
    if ENABLE_CONSOLE_GARBAGE:
        print(f"========== START PRINT-DEBUG FOR {variable} ==========\n"
        )
        print(
            "LOG_LEVEL: [DEBUG] LOG_TYPE: [DEVELOPMENT] "
            + f"{bcolors.BOLD}{text}{bcolors.ENDC}\n"
        )
        print(f"========== END PRINT-DEBUG FOR {variable} ==========\n"
        )
    pass


def add_line(text, args):
    # time.sleep(0.1)
    tk.Label(args[0], text=text, wraplength=280).pack()
    print(f"DEBUG: {text}")
    args[0].update_idletasks()
    args[1].configure(scrollregion=args[1].bbox("all"))
    args[1].yview_moveto(1)


def get_steam_library_folders(args):
    try:
        add_line("Finding Steam Install Location...", args)
        steam_registry_path = r"SOFTWARE\WOW6432Node\Valve\Steam"
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, steam_registry_path) as key:
            steam_path = winreg.QueryValueEx(key, "InstallPath") [0]

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
    mod_list_csv_names = [path_str.replace(".csv", ".Broken.csv"),
                          path_str.replace(".csv", ".Dependency_Mods_For_Saves.csv"),
                          path_str.replace(".csv", ".Game_Breaking_Assets_.csv")]
    for fn in os.listdir(config_path):
        if 'patch' in fn.lower():
            add_line("Found Patch Specific Mod List. Adding...", args)
            mod_list_csv_names.append(os.path.join(config_path, fn))
    final_compat_check_list = []
    for mod_list in mod_list_csv_names:
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
    mod_links = {}
    for item in final_compat_check_list:
        file_name = item[0]
        mod_ids = item[1:]
        add_line("Filtering Results...", args)
        if mod_ids:
            with open(file_name, 'r') as csv_file:
                add_line("Opening CSV for Mod Info...", args)
                reader = csv.reader(csv_file)
                next(reader)
                section_name = file_name.split('/')[-1].split('.')[-2]
                add_line("Sectioning Data...", args)
                section_data = {}
                add_line("Gathering Mod Information...", args)
                for row in reader:
                    mod_id = row[3]
                    link = row[5]
                    mod_name = row[1]
                    reason = row[7]
                    progressbar.step(5)
                    progressbar.update()
                    if mod_id in mod_ids:
                        section_data[mod_id] = {'link': link, 'mod_name': mod_name, 'reason': reason}
                mod_links[section_name] = section_data
        progressbar.step(30)
        progressbar.update()
    add_line("Starting Incompatible Mods Check...", args)
    with open(path_str.replace(".csv", ".Incompatible_Mods.csv"), 'r') as file:
        reader = csv.reader(file)
        headers = next(reader)
        rows = list(reader)
        progressbar.step(10)
        progressbar.update()
    pairs = []
    add_line("Sectioning Data...", args)
    for row in rows:
        row_pair = [str(row[3]), str(row[7]), str(row[1]), str(row[5]), [str(row[9])]]
        pairs.append(row_pair)
    matching_pairs = []
    progressbar.step(10)
    progressbar.update()
    add_line("Comparing Pairs...", args)
    for pair in pairs:
        if pair[1] in txt_ids and pair[0] in txt_ids:
            matching_pairs.append(pair)
    progressbar.step(10)
    progressbar.update()
    output_pairs = []
    for pair in matching_pairs:
        add_line("Formatting Data...", args)
        output_pair = {
            "Mod 1": pair[2],
            "Mod 1 Steam ID": pair[0],
            "Mod 2": pair[3],
            "Mod 2 Steam ID": pair[1],
            "Issue": pair[4]
        }
        output_pairs.append(output_pair)
    progressbar.step(10)
    progressbar.update()
    add_line("Packing into JSON...", args)
    ijd = json.dumps(output_pairs, indent=4)
    add_line("Completed. Packing All Data Into JSON...", args)
    jd = json.dumps(mod_links, indent=4)
    progressbar.step(10)
    progressbar.update()
    json_path = os.path.join(config_path, f"CitiesModCompatibilityReport.json")
    add_line("Saving to CitiesModCompatibilityReport.json", args)
    if os.path.exists(json_path):
        os.remove(json_path)
    with open(json_path, 'w') as f:
        f.write("// INCOMPATIBLE MODS LIST DATA\n")
        f.write(ijd + "\n")
        f.write("// ETC MODS LIST DATA\n")
        f.write(jd)
    progressbar["value"] = 100
    progressbar.update()
    add_line("Report Generation Complete.", args)


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
    messagebox.showinfo("Information", "Report Generation is Now Complete. You can view it from either the 'view "
                                       "report' button or by opening the report json file on at "
                                       "https://cities-report.t2v.city")
    rg_window.destroy()
    config.read(config_file_path)
    config.set('ProgramFiles', 'json_report', './CitiesModCompatibilityReport.json')
    with open(config_file_path, 'w') as f:
        config.write(f)
    load_config(args)


def cancel_mod_checker():
    sys.exit('Cancelling...')


def view_report_window(args):
    add_line("Loading Report Window...", args)
    report_window = tk.Toplevel()
    report_window.title(f"Compatibility Report - {dt}")
    report_window.geometry("1000x600")
    add_line("Generating Data First Tree...", args)
    tree = ttk.Treeview(report_window)
    tree.pack(fill="both", expand=True)
    tree["columns"] = ("link", "mod_name", "reason")
    tree.column("#0", width=100, minwidth=100)
    tree.column("link", width=200, minwidth=200)
    tree.column("mod_name", width=200, minwidth=200)
    tree.column("reason", width=300, minwidth=300)
    tree.heading("#0", text="Mod ID")
    tree.heading("link", text="Link")
    tree.heading("mod_name", text="Mod Name")
    tree.heading("reason", text="Reason")
    add_line("Opening JSON Report...", args)
    with open(str(config.get('ProgramFiles', 'json_report').replace("./", f"{config_path}/")), 'r') as f:
        json_data = f.read()
        json_lines = json_data.splitlines()
    add_line("Formatting Loaded Data...", args)
    incompatible_start = json_lines.index("// INCOMPATIBLE MODS LIST DATA")
    etc_start = json_lines.index("// ETC MODS LIST DATA")
    incompatible_json_data = "\n".join(json_lines[incompatible_start + 1:etc_start])
    etc_json_data = "\n".join(json_lines[etc_start + 1:])
    add_line("Loading Formatted JSON Data...", args)
    incompatible_data = json5.loads(incompatible_json_data)
    etc_data = json5.loads(etc_json_data)
    tree_incompat = ttk.Treeview(report_window)
    tree_incompat.pack(fill="both", expand=True)
    tree_incompat["columns"] = ("mod_1", "mod_2_id", "mod_2", "issue")
    tree_incompat.column("#0", width=100, minwidth=100)
    tree_incompat.column("mod_2_id", width=100, minwidth=100)
    tree_incompat.column("mod_1", width=200, minwidth=200)
    tree_incompat.column("mod_2", width=200, minwidth=200)
    tree_incompat.column("issue", width=300, minwidth=300)
    tree_incompat.heading("mod_1", text="Mod 1")
    tree_incompat.heading("#0", text="Mod 1 Steam ID")
    tree_incompat.heading("mod_2", text="Mod 2")
    tree_incompat.heading("mod_2_id", text="Mod 2 Steam ID")
    tree_incompat.heading("issue", text="Issue")
    tree_incompat.insert("", "end", "Incompatible_Mods", text="Incompatible Mods")
    for mod_data in incompatible_data:
        mod1 = mod_data["Mod 1"]
        mod1_id = mod_data["Mod 1 Steam ID"]
        mod2 = mod_data["Mod 2"]
        mod2_id = mod_data["Mod 2 Steam ID"]
        issue = mod_data["Issue"][0]
        tree_incompat.insert("Incompatible_Mods", "end", text=mod1_id, values=(mod1, mod2_id, mod2, issue))
    for category, mods in etc_data.items():
        category_id = category.replace(" ", "_").replace("(", "").replace(")", "")
        tree.insert("", "end", category_id, text=category)
        for mod_id, mod_info in mods.items():
            link = mod_info["link"]
            mod_name = mod_info["mod_name"]
            reason = mod_info["reason"]
            tree.insert(category_id, "end", text=mod_id, values=(link, mod_name, reason))

    def callback(event):
        tree = event.widget
        region = tree.identify_region(event.x, event.y)
        col = tree.identify_column(event.x)
        iid = tree.identify('item', event.x, event.y)
        if region == 'cell' and col == '#1':
            link = tree.item(iid)['values'][0]
            webbrowser.open_new_tab(link)

    tree.bind("<Button-1>", callback)


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
    config.set('ProgramFiles', 'json_report', "Not Generated Yet")
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
                gen_view_report_link(args)
            except configparser.NoSectionError:
                add_line("Config File is wrong or Corrupt. Attempting Fix...", args)
                create_config(args)
            except Exception:
                add_line("Failed to load config file. Try clearing data.", args)
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


def gen_view_report_link(args):
    config.read(config_file_path)
    if config.get('ProgramFiles', 'json_report') != "Not Generated Yet":
        try:
            eb = args[4].nametowidget("view_report_link")
            if eb:
                eb.destroy()
        except KeyError:
            pass
        ttk.Button(args[1], text="view report", command=lambda: view_report_window(args),
                   name="view_report_link").pack(anchor="w")


def show_help():
    messagebox.showinfo("Help", 'How to use CitiesModCompatibilityChecker.\n1. Run '
                                '"Download Latest Mod List" and wait for it to '
                                'complete.\n2. Run "Check System" and wait for it to '
                                'complete.\n 3. CMC should automatically refresh the '
                                'configuration but in the case it doesnt, '
                                'press "Refresh Config".\n4. You should now see a '
                                '"Generate Report" button, click that to compare your '
                                'mods.\n5. You can check the Mods Compatibility Report '
                                'by hitting the "view report" link.')


def open_link(link):
    webbrowser.open(link, new=1)


def delete_confirmation_window():
    confirmation_window = tk.Toplevel()
    confirmation_window.title("Confirmation")
    tk.Label(confirmation_window, text="This will delete all files generated by CitiesModCompatibilityChecker.").pack()
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
    window.iconbitmap("favicon.ico")
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
    settings = FastAPISettings()
    app = FastAPIWebReportViewer(settings)
    load_config(tkinter_info)
    window.mainloop()


if __name__ == "__main__":
    create_window()
