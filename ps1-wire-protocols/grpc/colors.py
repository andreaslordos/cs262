class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def strBlue(str) -> str:
    return bcolors.OKBLUE + str + bcolors.ENDC

def strGreen(str) -> str:
    return bcolors.OKGREEN + str + bcolors.ENDC

def strWarning(str) -> str:
    return bcolors.WARNING + str + bcolors.ENDC

def strFail(str) -> str:
    return bcolors.FAIL + str + bcolors.ENDC

def strBold(str) -> str:
    return bcolors.BOLD + str + bcolors.ENDC

def strUnderline(str) -> str:
    return bcolors.UNDERLINE + str + bcolors.ENDC

def strCyan(str) -> str:
    return bcolors.OKCYAN + str + bcolors.ENDC

def strHeader(str) -> str:
    return bcolors.HEADER + str + bcolors.ENDC