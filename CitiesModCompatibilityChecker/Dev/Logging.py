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