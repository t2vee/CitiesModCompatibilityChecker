from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.encoders import jsonable_encoder
from fastapi import FastAPI, Request
from flaskwebgui import FlaskUI
from datetime import datetime
from time import sleep
import threading
import uvicorn
import winreg
import json
import sys
import vdf
import os

app = FastAPI()
now = datetime.now()
dt = now.strftime("%d/%m/%Y %H:%M:%S")
templates = Jinja2Templates(directory="templates")
VERSION = "v001"


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


class DebugLogger:
    def __init__(self):
        pass

    @staticmethod
    def testing(message):
        print(
            f"{dt}: [MSS] LOG_TYPE: "
            + f"[{bcolors.OKCYAN}TEST{bcolors.ENDC}] "
            + f"{bcolors.OKCYAN}{message}{bcolors.ENDC}"
        )

    @staticmethod
    def critical(message):
        print(
            f"{dt}: [MSS] LOG_TYPE: "
            + f"[{bcolors.FAIL}CRITICAL{bcolors.ENDC}] "
            + f"{bcolors.FAIL}{message}{bcolors.ENDC}"
        )

    @staticmethod
    def warning(message):
        print(
            f"{dt}: [MSS] LOG_TYPE: "
            + f"[{bcolors.WARNING}WARNING{bcolors.ENDC}] "
            + f"{bcolors.WARNING}{message}{bcolors.ENDC}"
        )

    @staticmethod
    def info(message):
        print(
            f"{dt}: [MSS] LOG_TYPE: "
            + f"[{bcolors.OKGREEN}INFO{bcolors.ENDC}] "
            + f"{bcolors.OKGREEN}{message}{bcolors.ENDC}"
        )

    @staticmethod
    def success(message):
        print(
            f"{dt}: [MSS] LOG_TYPE: "
            + f"[{bcolors.BOLD}{bcolors.UNDERLINE}{bcolors.OKGREEN}SUCCESS{bcolors.ENDC}] "
            + f"{bcolors.BOLD}{bcolors.UNDERLINE}{bcolors.OKGREEN}{message}{bcolors.ENDC}"
        )

    @staticmethod
    def fail(message):
        print(
            f"{dt}: [MSS] LOG_TYPE: "
            + f"[{bcolors.BOLD}{bcolors.UNDERLINE}{bcolors.FAIL}FAIL{bcolors.ENDC}] "
            + f"{bcolors.BOLD}{bcolors.UNDERLINE}{bcolors.FAIL}{message}{bcolors.ENDC}"
        )

    @staticmethod
    def warn(message):
        print(
            f"{dt}: [MSS] LOG_TYPE: "
            + f"[{bcolors.BOLD}{bcolors.UNDERLINE}{bcolors.WARNING}WARN{bcolors.ENDC}] "
            + f"{bcolors.BOLD}{bcolors.UNDERLINE}{bcolors.WARNING}{message}{bcolors.ENDC}"
        )

    @staticmethod
    def instruction(message):
        print(
            "LOG_LEVEL: [MM_LOG] LOG_TYPE: [INSTRUCTION] "
            + f"{bcolors.UNDERLINE}{message}{bcolors.ENDC}"
        )

    @staticmethod
    def dev(message):
        print(
            "LOG_LEVEL: [MM_LOG] LOG_TYPE: [DEVELOPMENT] "
            + f"{bcolors.BOLD}{message}{bcolors.ENDC}"
        )


log = DebugLogger()


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get('/keepalive', response_class=JSONResponse)
def root(request: Request):
    return JSONResponse(content=jsonable_encoder({"message": "client up and running!",
                                                  "referer": f"{request.client.host}{':' + str(request.client.port) if request.client.port else ''}"}))


os.system("title " + "CitiesModChecker - t2v @ 2023")


def get_steam_library_folders():
    try:
        log.testing("Finding Steam Install Location...")
        steam_registry_path = r"SOFTWARE\WOW6432Node\Valve\Steam"
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, steam_registry_path) as key:
            steam_path = winreg.QueryValueEx(key, "InstallPath")[0]
        log.success(f"Found {steam_path}")

        log.testing("Finding Steam Library Folders...")
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
                log.success(f"Found: {folder}")
        return paths
    except Exception as e:
        log.critical("Error: " + str(e))


def grab_mods_list(cities_dir):
    log.testing("Grabbing Mods List...")
    mods_list = []
    for root, dirs, files in os.walk(cities_dir + '/steamapps/workshop/content/255710'):
        for subdir in dirs:
            path_parts = subdir.split('\\')
            mod_id_part = path_parts[-1]
            mods_list.append(mod_id_part)
    # for mod_id in mods_list:
    #    add_line(f"Mod Found. ID: {mod_id}")
    log.info(f"Mods List: {mods_list}")
    return mods_list


def grab_game_version(cities_dir):
    log.testing("Grabbing Game version...")
    with open(cities_dir + '/steamapps/appmanifest_255710.acf', 'r') as manifest_file:
        manifest_data = manifest_file.read()
        version_start = manifest_data.find('"buildid"') + len('"buildid"') + 2
        version_end = manifest_data.find('\n', version_start) - 1
        version = manifest_data[version_start:version_end]
        log.info(f"Cities Skylines Version: {version}")
        return version


def grab_dlc_info(cities_dir):
    log.testing("Checking for DLC Unlockers...")
    creamapi_files = ['CreamAPI.dll', 'cream_api.ini']
    smokeapi_files = ['SmokeAPI64.dll', 'SmokeAPI.json']
    dlc_unlocker = []
    base_dir = cities_dir + "/steamapps/common/Cities_Skylines/"
    for op in creamapi_files:
        if os.path.exists(base_dir + op):
            dlc_unlocker.append(True)
            break
        pass
    for op in smokeapi_files:
        if os.path.exists(base_dir + op):
            dlc_unlocker.append(True)
            break
        pass
    dlc_unlocker_list = []
    if dlc_unlocker[0]:
        log.success("CreamAPI Found...")
        dlc_unlocker_list.append("CreamAPI")
    else:
        log.warn("CreamAPI Not Found...")
        dlc_unlocker_list.append(None)
    if dlc_unlocker[1]:
        log.success("SmokeAPI Found...")
        dlc_unlocker_list.append("SmokeAPI")
    else:
        log.warn("SmokeAPI Not Found...")
        dlc_unlocker_list.append(None)
    return dlc_unlocker_list


@app.get('/API/RequestSystemCheck')
def run_checker_thread():
    log.info("Starting Cities Skylines Mod Compatibility Checker...")
    try:
        library_folders = get_steam_library_folders()
        log.testing(f"Checking for Cities Skylines...")
        cities_skylines_dir = None
        for folder in library_folders:
            sanitised_folder = folder.replace("\\", "/") + '/steamapps/common/Cities_Skylines'
            if os.path.isdir(sanitised_folder):
                log.success(f"{sanitised_folder}. Found! Setting to Default")
                cities_skylines_dir = folder.replace("\\", "/")
                break
            log.warn(f"{sanitised_folder}. Not Found. Skipping...")
        log.info('Creating Information Payload...')
        log.success('Checker Finished Successfully.')
        cities_payload = {
            "CitiesSkylinesModCompatibilityChecker": {
                "Version": VERSION,
                "PayLoad": {
                    "ModList": json.dumps(grab_mods_list(cities_skylines_dir)),
                    "GameVersion": grab_game_version(cities_skylines_dir).replace('"', ''),
                    "DlcInfo": json.dumps(grab_dlc_info(cities_skylines_dir))
                }
            }
        }
        return JSONResponse(content=jsonable_encoder(cities_payload))

    except KeyboardInterrupt:
        log.warn("Shutting down...")
        sys.exit("Process Closed")


if __name__ == "__main__":
    FlaskUI(app=app, server="fastapi", width=400, height=300).run()
    # try:
    #    log.info('Starting Local Server on 127.0.0.1:64839')
    #    uvicorn.run(app, host="127.0.0.1", port=64839)
    # except KeyboardInterrupt:
    #    log.warn("Shutting down...")
    #    sys.exit("Process Closed")
    # except:
    #    log.fail('Port in use! trying again...')
    #    log.info('Starting Local Server on 127.0.0.1:64457')
    #    uvicorn.run(app, host="127.0.0.1", port=64457)
