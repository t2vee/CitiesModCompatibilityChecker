def _get_steam_library_folders(args):
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


def _grab_mods_list(cities_dir):
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