from pathlib import Path

import psutil


def get_disk_usage(parameters: str):
    target_path = parameters.strip() if parameters and parameters.strip() else "/"
    path_obj = Path(target_path).resolve()

    if not path_obj.exists():
        raise Exception("Path not found")

    try:
        usage = psutil.disk_usage(str(path_obj))
    except Exception:
        raise Exception("An unexpected error was observed")

    return (
        f"Filesystem: {path_obj}\n"
        f"Total: {usage.total}\n"
        f"Used: {usage.used}\n"
        f"Free: {usage.free}\n"
        f"Percent: {usage.percent}%"
    )
