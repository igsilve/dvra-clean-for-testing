"""T4450: prove the deployment scripts refuse an unauthenticated caller.

Run inside the Python suite rather than as a standalone shell script, so the
guard is exercised by the same command CI already runs and cannot be left
out of the pipeline by omission.

The authorised case runs with a stub `docker` first on PATH, so the tests
prove the guard lets an operator through without actually starting anything.
"""

import os
import pathlib
import stat
import subprocess

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
GUARDED_SCRIPTS = ("start_app.sh", "stop_app.sh", "start_game.sh")


@pytest.fixture
def fake_docker(tmp_path):
    """A no-op `docker` that records nothing and succeeds."""
    stub = tmp_path / "docker"
    stub.write_text("#!/bin/bash\nexit 0\n")
    stub.chmod(stub.stat().st_mode | stat.S_IEXEC)
    return tmp_path


def _run(script, env_extra=None, path_prefix=None):
    env = dict(os.environ)
    env.pop("SDE_DEPLOY_ROLE", None)
    if env_extra:
        env.update(env_extra)
    if path_prefix:
        env["PATH"] = f"{path_prefix}:{env['PATH']}"

    return subprocess.run(
        ["bash", str(REPO_ROOT / script)],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )


@pytest.mark.security
@pytest.mark.parametrize("script", GUARDED_SCRIPTS)
def test_script_refuses_an_unauthenticated_invocation(script):
    result = _run(script)

    assert result.returncode != 0, f"{script} ran without an operator identity"
    assert "operator" in result.stderr.lower()


@pytest.mark.security
@pytest.mark.parametrize("script", GUARDED_SCRIPTS)
def test_script_refuses_a_wrong_operator_value(script):
    """Any value other than the expected one is refused, not just an empty one."""
    result = _run(script, env_extra={"SDE_DEPLOY_ROLE": "developer"})

    assert result.returncode != 0
    assert "operator" in result.stderr.lower()


@pytest.mark.security
def test_the_guard_does_not_block_an_authorised_operator():
    """A control nobody can pass gets deleted; prove the allow path works.

    Asserted on the refusal rather than on the exit status. The scripts now
    set an absolute PATH before running anything, which is the point of
    T4441, and that means a stub `docker` placed first on the caller's PATH is
    no longer reachable -- the control this test used to rely on to observe
    the allow path is the control being tested. So the evidence is that the
    guard did not speak: an operator gets past it and the script goes on to
    whatever the container runtime does or does not do on this host.
    """
    result = _run("stop_app.sh", env_extra={"SDE_DEPLOY_ROLE": "operator"})

    assert "refusing to run" not in result.stderr, result.stderr


@pytest.mark.security
@pytest.mark.parametrize("script", GUARDED_SCRIPTS)
def test_scripts_abort_on_error(script):
    """Without `set -e` a failed guard would be printed and then ignored."""
    text = (REPO_ROOT / script).read_text()

    assert "set -euo pipefail" in text, f"{script} does not fail closed"
    assert "require_operator" in text, f"{script} does not check the operator"


@pytest.mark.security
def test_no_privileged_script_skips_the_guard():
    """Catches a future script that runs docker without the check."""
    offenders = []
    for path in REPO_ROOT.glob("*.sh"):
        if path.name == "ops_guard.sh":
            continue
        text = path.read_text()
        if "docker" in text and "require_operator" not in text:
            offenders.append(path.name)

    assert offenders == [], f"scripts invoking docker without the guard: {offenders}"


@pytest.mark.security
def test_database_volume_is_not_world_readable():
    """Tightened from 0750 to 0700 under T4436: the database files need no
    group reader, and the group on a shared host is usually larger than
    whoever set it expected."""
    text = (REPO_ROOT / "start_app.sh").read_text()

    assert 'mkdir -m 0700 -p "$DATA_DIR"' in text


@pytest.mark.security
def test_arguments_are_passed_without_word_splitting():
    """`$1` unquoted splits on whitespace and glob-expands."""
    text = (REPO_ROOT / "start_app.sh").read_text()

    assert '"$DOCKER" compose up "$@"' in text
    assert "docker compose up $1" not in text


# --- T4440 / T4451: the privileged action must not run after a refusal ---


@pytest.mark.security
@pytest.mark.parametrize("script", GUARDED_SCRIPTS)
def test_the_privileged_command_never_runs_after_a_failed_check(script):
    """Exiting non-zero is not enough if the action already happened.

    A script can refuse loudly and still have run the compose command,
    either because the guard came too late or because execution continued
    past a failing check. Checked by position in the source rather than by
    intercepting a stub on PATH: the scripts now fix PATH to absolute system
    directories, so an injected `docker` is unreachable, and a test that
    watched for one would pass whether or not the guard ran at all.
    """
    text = (REPO_ROOT / script).read_text()

    guard_at = text.index("require_operator")
    docker_at = min(
        (text.index(call) for call in ("docker compose", "$SCRIPT_DIR/start_app.sh") if call in text),
        default=len(text),
    )

    assert guard_at < docker_at, f"{script} runs the privileged action before the check"


# --- T4441 / T4452: the script's own environment, not the caller's ---


@pytest.mark.security
@pytest.mark.parametrize("script", GUARDED_SCRIPTS)
def test_path_is_absolute_and_set_before_any_command(script):
    """An inherited PATH lets the caller pick which `docker` runs as root."""
    lines = [line.strip() for line in (REPO_ROOT / script).read_text().splitlines()]
    body = [
        line
        for line in lines
        if line and not line.startswith("#") and not line.startswith("#!")
    ]

    path_lines = [i for i, line in enumerate(body) if line.startswith("export PATH=")]
    assert path_lines, f"{script} does not set PATH"

    exported = body[path_lines[0]]
    assert "$PATH" not in exported, f"{script} extends the caller's PATH instead of replacing it"
    for directory in exported.split("=", 1)[1].strip('"').split(":"):
        assert directory.startswith("/"), f"{script} has a relative PATH entry: {directory}"

    # Nothing external may run before it. `set`, `IFS`, `umask` and `cd` are
    # builtins and do not resolve through PATH.
    for line in body[: path_lines[0]]:
        assert line.startswith(("set ", "IFS=", "umask", "cd ", "export IFS")), (
            f"{script} runs `{line}` before fixing PATH"
        )


@pytest.mark.security
@pytest.mark.parametrize("script", GUARDED_SCRIPTS)
def test_ifs_is_set_explicitly(script):
    """IFS is inherited, so the caller otherwise chooses how words are split."""
    text = (REPO_ROOT / script).read_text()

    assert "IFS=$'\\n\\t'" in text, f"{script} accepts the caller's IFS"


@pytest.mark.security
def test_the_sibling_script_is_invoked_through_a_resolved_path():
    """`./start_app.sh` runs whatever is in the caller's directory."""
    text = (REPO_ROOT / "start_game.sh").read_text()
    code = "\n".join(
        line for line in text.splitlines() if not line.strip().startswith("#")
    )

    assert "./start_app.sh" not in code, "start_game.sh resolves a sibling from the cwd"
    assert 'SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"' in text
    assert '"$SCRIPT_DIR/start_app.sh"' in text


@pytest.mark.security
def test_the_runtime_is_invoked_with_a_cleared_environment():
    """The caller's variables are not handed to the container runtime."""
    text = (REPO_ROOT / "start_app.sh").read_text()

    assert '"$ENV_BIN" -i' in text, "start_app.sh passes its whole environment through"


# --- T4442 / T4453: the spawned process is supervised ---


@pytest.mark.security
def test_teardown_takes_a_lock_before_acting():
    """Two concurrent `compose down` runs interleave container removal."""
    text = (REPO_ROOT / "stop_app.sh").read_text()

    assert "mkdir \"$LOCK\"" in text, "stop_app.sh does not take a lock"
    assert text.index("$LOCK") < text.index('"$DOCKER" compose down')


@pytest.mark.security
def test_the_lock_is_taken_atomically_rather_than_tested_for():
    """A check followed by a create has a race between the two steps."""
    text = (REPO_ROOT / "stop_app.sh").read_text()

    assert "[ -e \"$LOCK\" ]" not in text
    assert "[ -d \"$LOCK\" ]" not in text
    # A dead holder must not block every later run.
    assert "kill -0" in text, "a crashed run would leave the lock held forever"


@pytest.mark.security
@pytest.mark.parametrize(
    "script,command",
    [("stop_app.sh", '"$DOCKER" compose down'), ("start_game.sh", '"$DOCKER" compose exec')],
)
def test_the_privileged_command_runs_under_a_timeout(script, command):
    """Without it, a container ignoring SIGTERM blocks the script forever."""
    text = (REPO_ROOT / script).read_text()

    for line in text.splitlines():
        if command in line and not line.strip().startswith("#"):
            assert "run_bounded " in line, f"{script}: `{command}` has no timeout"
            break
    else:
        raise AssertionError(f"{script} no longer runs `{command}`")


@pytest.mark.security
def test_the_bounded_wait_does_not_depend_on_a_command_that_may_be_absent():
    """`timeout` is GNU coreutils and a stock macOS has neither it nor
    `gtimeout`. Calling it unconditionally turned a hang into `timeout:
    command not found` followed by the script drawing a conclusion from a
    command that never ran -- worse than the hang it was preventing."""
    text = (REPO_ROOT / "ops_guard.sh").read_text()

    assert "command -v timeout" in text
    assert "command -v gtimeout" in text
    assert "run_bounded()" in text


@pytest.mark.security
def test_the_bounded_wait_still_runs_the_command_when_no_timeout_exists():
    """The fallback runs the command unbounded rather than skipping it: an
    operator at a terminal can interrupt a hang, but a silently skipped
    command produces a false result."""
    script = (
        f'source "{REPO_ROOT / "ops_guard.sh"}"\n'
        "timeout() { return 127; }\n"
        "gtimeout() { return 127; }\n"
        "run_bounded() { shift; \"$@\"; }\n"
        'run_bounded 5 echo ran-the-command\n'
    )

    result = subprocess.run(
        ["bash", "-c", script], capture_output=True, text=True, timeout=30
    )

    assert result.returncode == 0
    assert "ran-the-command" in result.stdout


@pytest.mark.security
@pytest.mark.parametrize("script", ("stop_app.sh", "start_game.sh"))
def test_a_trap_cleans_up_on_every_exit_path(script):
    """`set -e` exits without running the cleanup unless a trap is installed."""
    text = (REPO_ROOT / script).read_text()

    assert "trap " in text, f"{script} leaves its state behind on an error exit"


@pytest.mark.security
def test_the_spawned_process_gets_no_tty_and_its_status_is_propagated():
    """-T keeps the child off this terminal; the exit status is the result."""
    text = (REPO_ROOT / "start_game.sh").read_text()

    assert '"$DOCKER" compose exec -T' in text, "the child is given a TTY"
    assert "docker compose exec web" not in text
    assert 'exit "$status"' in text, "the child's outcome is discarded"
    assert 'trap \'"$DOCKER" compose kill web' in text, "an interrupt leaves the child running"


@pytest.mark.security
@pytest.mark.parametrize("script", GUARDED_SCRIPTS)
def test_the_refusal_does_not_disclose_how_to_pass(script):
    """The message must not read as instructions for an attacker."""
    result = _run(script)

    assert "SDE_DEPLOY_ROLE=operator" in result.stderr
    # It says where the value must come from, not merely how to set it.
    assert "authenticated" in result.stderr.lower()


# --- T4436 / T4447: the directory the script creates -------------------


@pytest.mark.security
def test_the_data_directory_is_created_owner_only():
    """0700, not 0750. The database files need no group reader, and the group
    on a shared host is usually larger than whoever set it expected."""
    text = (REPO_ROOT / "start_app.sh").read_text()

    assert 'mkdir -m 0700 -p "$DATA_DIR"' in text
    assert "mkdir -m 0750" not in text
    assert "mkdir -p postgres_data" not in text


@pytest.mark.security
def test_the_data_directory_path_is_absolute():
    """A relative path resolves against wherever the caller was standing."""
    text = (REPO_ROOT / "start_app.sh").read_text()

    assert 'DATA_DIR="$(pwd -P)/postgres_data"' in text


@pytest.mark.security
def test_an_existing_data_directory_is_checked_rather_than_trusted():
    """mkdir leaves an existing directory's mode and owner alone, so creating
    it correctly says nothing about the one that is actually there."""
    text = (REPO_ROOT / "start_app.sh").read_text()

    assert '[ -L "$DATA_DIR" ]' in text, "a symlink would be written through"
    assert "id -u" in text, "ownership is not verified"


# --- T4437 / T4448 / T4449: files the script hands to something else ---


@pytest.mark.security
def test_the_sibling_script_is_checked_before_it_is_executed():
    text = (REPO_ROOT / "start_game.sh").read_text()

    assert '[ -L "$SCRIPT_DIR/start_app.sh" ]' in text, "a symlink substitution passes"
    assert '[ ! -f "$SCRIPT_DIR/start_app.sh" ]' in text
    assert '[ ! -x "$SCRIPT_DIR/start_app.sh" ]' in text


@pytest.mark.security
def test_the_file_run_inside_the_container_is_checked_first():
    """Otherwise a missing game.py is a python3 error that reads as an
    application failure rather than a deployment one."""
    text = (REPO_ROOT / "start_game.sh").read_text()

    assert '"$DOCKER" compose exec -T web test -f "$GAME"' in text
    assert 'python3 "$GAME"' in text


@pytest.mark.security
def test_a_missing_dependency_stops_the_script(tmp_path):
    """Behavioural: remove the required input and confirm a non-zero exit.

    Run against a copy so the repository is not modified, and with an
    operator identity so the refusal being observed is the file check rather
    than the guard.
    """
    import shutil

    for name in ("start_game.sh", "ops_guard.sh"):
        shutil.copy(REPO_ROOT / name, tmp_path / name)
        (tmp_path / name).chmod(0o755)
    # start_app.sh is deliberately absent.

    result = subprocess.run(
        ["bash", str(tmp_path / "start_game.sh")],
        cwd=tmp_path,
        env={**os.environ, "SDE_DEPLOY_ROLE": "operator"},
        capture_output=True,
        text=True,
        timeout=60,
    )

    assert result.returncode != 0
    assert "start_app.sh is missing" in result.stderr


@pytest.mark.security
def test_a_symlinked_dependency_stops_the_script(tmp_path):
    """A file with the right name that points somewhere else is the attack
    the existence check alone would pass."""
    import shutil

    for name in ("start_game.sh", "ops_guard.sh"):
        shutil.copy(REPO_ROOT / name, tmp_path / name)
        (tmp_path / name).chmod(0o755)

    planted = tmp_path / "elsewhere.sh"
    planted.write_text("#!/bin/bash\nexit 0\n")
    planted.chmod(0o755)
    (tmp_path / "start_app.sh").symlink_to(planted)

    result = subprocess.run(
        ["bash", str(tmp_path / "start_game.sh")],
        cwd=tmp_path,
        env={**os.environ, "SDE_DEPLOY_ROLE": "operator"},
        capture_output=True,
        text=True,
        timeout=60,
    )

    assert result.returncode != 0
    # The full message, not the word: pytest names the temporary directory
    # after the test, so bash echoing the script's own path puts "symlink"
    # in stderr whatever the script does.
    assert "start_app.sh is a symlink" in result.stderr


# --- T4434 / T4445: nothing in these scripts builds a command string ---


@pytest.mark.security
@pytest.mark.parametrize(
    "script", ("start_app.sh", "stop_app.sh", "start_game.sh", "ops_guard.sh")
)
def test_no_script_evaluates_a_constructed_string(script):
    """`eval`, backticks and `bash -c` on assembled text are how an argument
    stops being an argument and becomes a command."""
    text = (REPO_ROOT / script).read_text()
    code = [
        line for line in text.splitlines() if not line.strip().startswith("#")
    ]

    for construct in ("eval ", "eval(", "`", "bash -c", "sh -c"):
        offenders = [line for line in code if construct in line]
        assert offenders == [], f"{script}: {construct} in {offenders}"


def _has_unquoted_expansion(line: str) -> bool:
    """Whether `line` expands a variable outside of double quotes.

    Quote state is tracked rather than inferred from the characters next to
    the `$`, because an expansion in the middle of a quoted message has a
    space on either side. Command substitutions are recursed into instead of
    being read straight through: bash starts a fresh quoting context inside
    `$( ... )`, so the inner quotes do not close the outer ones and a
    single left-to-right pass reports `"$(cat "$LOCK/pid")"` as unquoted.
    """
    import re as _re

    def scan(text: str) -> bool:
        in_double = in_single = False
        index = 0
        while index < len(text):
            char = text[index]
            if char == "'" and not in_double:
                in_single = not in_single
            elif char == '"' and not in_single:
                in_double = not in_double
            elif char == "$" and not in_single and text[index : index + 2] == "$(":
                depth, end = 1, index + 2
                while end < len(text) and depth:
                    if text[end] == "(":
                        depth += 1
                    elif text[end] == ")":
                        depth -= 1
                    end += 1
                if scan(text[index + 2 : end - 1]):
                    return True
                index = end
                continue
            elif (
                char == "$"
                and not in_double
                and not in_single
                and _re.match(r"\$\{?[A-Za-z_0-9@*]", text[index:])
            ):
                return True
            index += 1
        return False

    return scan(line)


@pytest.mark.security
@pytest.mark.parametrize(
    "script", ("start_app.sh", "stop_app.sh", "start_game.sh")
)
def test_every_expansion_in_a_command_is_quoted(script):
    """An unquoted expansion is re-split and glob-expanded by the shell, so
    a value with a space in it silently becomes two arguments."""
    import re

    text = (REPO_ROOT / script).read_text()
    offenders = []

    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#") or not stripped:
            continue
        # Assignments do not word-split; command lines do.
        if re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", stripped):
            continue

        if _has_unquoted_expansion(stripped):
            offenders.append(stripped)

    assert offenders == [], f"{script}: unquoted expansion in {offenders}"


# --- T4438 / T4449: the scripts accept no file from anyone ------------


@pytest.mark.security
@pytest.mark.parametrize(
    "script", ("start_app.sh", "stop_app.sh", "start_game.sh")
)
def test_no_script_reads_a_path_from_its_arguments(script):
    """These scripts take no filename, which is the reason there is no
    upload-validation helper in them: there is nothing to validate. This
    fails if one starts reading a caller-supplied path, at which point the
    validator the recipe describes becomes necessary."""
    text = (REPO_ROOT / script).read_text()
    code = [
        line for line in text.splitlines() if not line.strip().startswith("#")
    ]

    for reader in ("< $", '< "$1', "cat $", 'cat "$1', "source $", ". $"):
        offenders = [line for line in code if reader in line]
        assert offenders == [], f"{script}: reads a caller path: {offenders}"


@pytest.mark.security
@pytest.mark.parametrize(
    "line,unquoted",
    [
        ('docker compose up $1', True),
        ('"$DOCKER" compose up "$@"', False),
        ('echo "a $GAME b"', False),
        ('echo \'a $GAME b\'', False),
        ('if [ "$(cat "$LOCK/pid")" != "$(id -u)" ]; then', False),
        ('if [ "$(cat $LOCK/pid)" != "x" ]; then', True),
        ('rm -rf $LOCK', True),
    ],
)
def test_the_quoting_check_recognises_both_cases(line, unquoted):
    """The check above is only worth its result if it can tell the two
    apart, and nested command substitution is where a naive left-to-right
    pass gets it wrong in the safe direction's favour."""
    assert _has_unquoted_expansion(line) is unquoted


# --- T4433 / T4444: PATH and command resolution -----------------------


@pytest.mark.security
@pytest.mark.parametrize(
    "script", ("start_app.sh", "stop_app.sh", "start_game.sh")
)
def test_path_is_readonly_after_it_is_set(script):
    """Setting PATH is not enough on its own: anything sourced or called
    later can put a writable directory back at the front of it, and these
    scripts source a sibling file."""
    text = (REPO_ROOT / script).read_text()
    # Comment lines are excluded: "# readonly PATH" contains the substring
    # and would otherwise satisfy the assertion while doing nothing.
    code = "\n".join(
        line for line in text.splitlines() if not line.strip().startswith("#")
    )

    assert "readonly PATH" in code
    assert code.index("export PATH=") < code.index("readonly PATH")


@pytest.mark.security
@pytest.mark.parametrize(
    "script", ("start_app.sh", "stop_app.sh", "start_game.sh")
)
def test_external_commands_are_invoked_through_a_resolved_path(script):
    """`docker compose` by bare name resolves through PATH at the moment of
    execution. Resolving once, up front, and invoking the result is what
    makes the fixed PATH above actually decide which binary runs."""
    text = (REPO_ROOT / script).read_text()
    code = [
        line for line in text.splitlines() if not line.strip().startswith("#")
    ]

    assert 'resolve_binary docker' in text
    bare = [
        line
        for line in code
        if "docker compose" in line and '"$DOCKER" compose' not in line
    ]
    assert bare == [], f"{script}: docker invoked by bare name: {bare}"


@pytest.mark.security
def test_the_resolver_refuses_a_name_that_is_not_on_the_fixed_path():
    """A name that does not resolve must be a refusal, not an empty string
    that later expands to nothing and silently runs `compose down`."""
    script = (
        'export PATH=/usr/local/bin:/usr/bin:/bin\n'
        f'source "{REPO_ROOT / "ops_guard.sh"}"\n'
        'resolve_binary definitely-not-a-real-binary\n'
    )

    result = subprocess.run(
        ["bash", "-c", script], capture_output=True, text=True, timeout=30
    )

    assert result.returncode != 0
    assert "did not resolve to an absolute path" in result.stderr
    assert result.stdout.strip() == ""


@pytest.mark.security
def test_the_resolver_returns_an_absolute_path_for_a_real_binary():
    script = (
        'export PATH=/usr/local/bin:/usr/bin:/bin\n'
        f'source "{REPO_ROOT / "ops_guard.sh"}"\n'
        'resolve_binary env\n'
    )

    result = subprocess.run(
        ["bash", "-c", script], capture_output=True, text=True, timeout=30
    )

    assert result.returncode == 0
    assert result.stdout.strip().startswith("/")
    assert os.access(result.stdout.strip(), os.X_OK)


@pytest.mark.security
def test_the_resolver_refuses_a_binary_in_a_world_writable_directory(tmp_path):
    """Resolution is only worth doing if the resolved location cannot be
    rewritten between resolving and executing."""
    writable = tmp_path / "bin"
    writable.mkdir()
    planted = writable / "plausible-tool"
    planted.write_text("#!/bin/bash\nexit 0\n")
    planted.chmod(0o755)
    writable.chmod(0o777)

    script = (
        # The writable directory first, with the system ones still behind
        # it: that is the shape of the attack, and it also means `stat`
        # resolves, so the mode is read rather than falling back to a
        # conservative default.
        f'export PATH="{writable}:/usr/bin:/bin"\n'
        f'source "{REPO_ROOT / "ops_guard.sh"}"\n'
        'resolve_binary plausible-tool\n'
    )

    result = subprocess.run(
        ["bash", "-c", script], capture_output=True, text=True, timeout=30
    )

    assert result.returncode != 0
    assert "writable by others" in result.stderr
