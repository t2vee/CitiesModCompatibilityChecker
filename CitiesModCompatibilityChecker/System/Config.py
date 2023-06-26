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
