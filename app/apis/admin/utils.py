import subprocess


def get_disk_usage():
    try:
        result = subprocess.run(
            ["df", "-h"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
        )
        usage = result.stdout.strip().decode()
    except Exception:
        raise Exception("An unexpected error was observed")

    return usage
