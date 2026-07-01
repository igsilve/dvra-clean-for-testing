import subprocess
import time
from os import listdir
from os.path import isfile, join

from colorama import Fore, Style

BASE_PATH = "app"
INTEGRATION_TESTS_DIR = "tests/integration/"
INTEGRATION_TEST_FILES_PATHS = sorted(
    [
        join(INTEGRATION_TESTS_DIR, f)
        for f in listdir(INTEGRATION_TESTS_DIR)
        if isfile(join(INTEGRATION_TESTS_DIR, f)) and f.endswith(".py")
    ]
)


def run_tests(test_file_path=None):
    try:
        command = [
            "pytest",
            "--disable-warnings",
            "-qq",
        ]
        if test_file_path:
            command.append(test_file_path)

        process = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        animation = "|/-\\"
        idx = 0
        print("  Running tests... Please wait...", end="\r")
        while process.poll() is None:
            print(animation[idx % len(animation)], end="\r")
            idx += 1
            time.sleep(0.1)

        stdout, stderr = process.communicate()

    except subprocess.CalledProcessError as e:
        print(f"Subprocess error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

    class TestsResult:
        def __init__(self, returncode, stdout, stderr):
            self.returncode = returncode
            self.stdout = stdout
            self.stderr = stderr

    return TestsResult(process.returncode, stdout, stderr)


def get_check_passed(test_file_path):
    result = run_tests(test_file_path)
    return result.returncode == 0


def get_unit_tests_suite_result():
    return run_tests()


def get_check_name(test_file_path):
    file_name = test_file_path.split("/")[-1]
    return (
        file_name.replace("test_", "", 1).replace("_", " ").replace(".py", "").title()
    )


def print_welcome_screen():
    print(Fore.GREEN, end="")
    print(
        """
            RESTaurant API - Integration Test Runner

            This tool runs the integration test suite for the
            RESTaurant API and reports the status of each check.
        """,
        end="\n\n",
    )
    print(Style.RESET_ALL, end="")


def print_summary_screen():
    print(Fore.GREEN, end="")
    print(
        """
            All integration checks completed.
        """
    )
    print(Style.RESET_ALL, end="")


def press_key_to_continue(text, color=Fore.YELLOW, end="\n"):
    print(color, end="")
    input(text + end)
    print(Style.RESET_ALL, end="")


def print_color_text(text, color, end="\n"):
    print(color, end="")
    print(text, end=end)
    print(Style.RESET_ALL, end="")


def move_cursor_top(lines=1):
    for line in range(lines):
        print("\033[1A\033[K", end="")


print_welcome_screen()
press_key_to_continue("Click any key to continue...", end="\n\n")

unit_tests_result = get_unit_tests_suite_result()
while unit_tests_result.returncode != 0 and unit_tests_result.stderr:
    unit_tests_result_out = unit_tests_result.stderr.replace("\n", "\n\r")
    print_color_text(
        unit_tests_result_out,
        color=Fore.RED,
        end="\n\r\n\r",
    )
    logs_lines_count = unit_tests_result_out.count("\n\r")
    print_color_text(
        f"It seems, the application is not working correctly. It might be related with wrong formatting, imports or code syntax issues. Check the above logs for more details...",
        color=Fore.RED,
        end="\n\r",
    )
    press_key_to_continue(
        "Fix the issue and press any key to continue... You can use `git restore <affected_file>` to restore the file contents.",
        end="\r\r",
    )
    move_cursor_top(logs_lines_count + 4)
    unit_tests_result = get_unit_tests_suite_result()

for i, integration_test_file in enumerate(INTEGRATION_TEST_FILES_PATHS, start=1):
    check_name = get_check_name(integration_test_file)
    check_passed = get_check_passed(integration_test_file)

    if check_passed:
        print_color_text(
            f'Check passed: "{check_name}"',
            color=Fore.GREEN,
            end="\n\n",
        )
    else:
        print_color_text(
            f'Check failed: "{check_name}"',
            color=Fore.RED,
            end="\n\n",
        )

    if i == len(INTEGRATION_TEST_FILES_PATHS):
        print_summary_screen()
