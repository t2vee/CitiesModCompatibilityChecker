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