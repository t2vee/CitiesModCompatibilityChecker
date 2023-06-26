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