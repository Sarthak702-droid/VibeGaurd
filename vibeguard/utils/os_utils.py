import platform

def get_os_name() -> str:
    sys_name = platform.system()
    if sys_name == "Windows":
        return "windows"
    elif sys_name == "Darwin":
        return "macos"
    elif sys_name == "Linux":
        return "linux"
    return "unknown"
