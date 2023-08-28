class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    REVGREEN = '\033[48;5;10m'
    REVRED = '\033[48;5;196m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
# EXAMPLE USAGE: print(f"{bcolors.FAIL}{bcolors.UNDERLINE}Warning:{bcolors.ENDC}{bcolors.FAIL} No active frommets remain. Continue?{bcolors.ENDC}")
# https://stackabuse.com/how-to-print-colored-text-in-python/