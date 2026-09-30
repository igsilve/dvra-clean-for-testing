"""The container image and its runtime constraints.

These assertions run in the ordinary test suite rather than as a separate
image-scanning stage, because a check that lives in a pipeline nobody has
built yet is a check that does not exist. They read the Dockerfile and the
compose file as text and as parsed YAML, so they hold without a Docker
daemon and cannot be skipped by an environment that lacks one.

What they cannot do is inspect a built image, so they assert the
instructions that produce it. Image scanning against the built artifact
remains an infrastructure activity.
"""

import os
import pathlib
import re

import pytest
import yaml

pytestmark = pytest.mark.security

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
DOCKERFILE = REPO_ROOT / "Dockerfile"
COMPOSE = REPO_ROOT / "docker-compose.yml"


@pytest.fixture(scope="module")
def dockerfile() -> str:
    return DOCKERFILE.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def compose() -> dict:
    return yaml.safe_load(COMPOSE.read_text(encoding="utf-8"))


def _runtime_stage(text: str) -> str:
    """Only the runtime stage ships; the builder is discarded."""
    stages = re.split(r"^FROM ", text, flags=re.MULTILINE)
    runtime = [s for s in stages if "AS runtime" in s.splitlines()[0]]
    assert runtime, "no runtime stage found in the Dockerfile"
    return runtime[0]


# --- T4751 / T1917: attack surface of the image --------------------------


@pytest.mark.parametrize("package", ["gcc", "vim", "sudo", "libpq-dev"])
def test_the_runtime_image_does_not_install_build_or_shell_tooling(
    dockerfile, package
):
    """A compiler turns a file-write bug into arbitrary code execution."""
    runtime = _runtime_stage(dockerfile)

    installs = re.findall(r"apt-get install[^\n]*(?:\\\n[^\n]*)*", runtime)
    for line in installs:
        assert not re.search(rf"\b{re.escape(package)}\b", line), (
            f"{package} is installed into the runtime image"
        )


def test_no_passwordless_sudo_rule_is_created(dockerfile):
    """`sudo find -exec` is a one-command path from the app user to root."""
    assert "NOPASSWD" not in dockerfile
    assert "sudoers" not in dockerfile


def test_apt_lists_are_removed_in_the_same_layer(dockerfile):
    runtime = _runtime_stage(dockerfile)

    assert "--no-install-recommends" in runtime

    apt_run = re.search(r"RUN apt-get update(?:[^\n]*\\\n)*[^\n]*", runtime)
    assert apt_run, "no apt-get layer found"
    assert "rm -rf /var/lib/apt/lists/*" in apt_run.group(0), (
        "the apt lists are removed in a later layer, so they still ship "
        "inside the image"
    )


# --- T4746: image provenance ---------------------------------------------


def test_every_base_image_is_pinned_by_digest(dockerfile):
    from_lines = re.findall(r"^FROM (\S+)", dockerfile, re.MULTILINE)

    assert from_lines, "no FROM instructions found"
    for reference in from_lines:
        assert "@sha256:" in reference, (
            f"{reference} is pinned by tag; a tag is a moving pointer, so "
            "a rebuild can pull a base nobody reviewed"
        )


def test_the_pinned_digests_are_recorded_with_their_tags(dockerfile):
    """A bare digest says nothing about how old it is or what it was."""
    lock = REPO_ROOT / "deploy" / "base-images.lock"
    assert lock.exists()

    recorded = lock.read_text(encoding="utf-8")
    for digest in re.findall(r"@(sha256:[0-9a-f]{64})", dockerfile):
        assert digest in recorded, f"{digest} is not recorded in {lock.name}"


# --- T1174 / T1175: the container does not run as root -------------------


def test_the_image_drops_to_a_non_root_user(dockerfile):
    runtime = _runtime_stage(dockerfile)

    user_lines = re.findall(r"^USER (.+)$", runtime, re.MULTILINE)
    assert user_lines, "the runtime stage never leaves root"

    final = user_lines[-1].strip()
    assert final not in ("root", "0", "0:0")

    uid = final.split(":")[0]
    assert uid.isdigit() and int(uid) >= 1000, (
        f"USER {final} is not a fixed non-system uid, so the effective "
        "account depends on what exists in the image"
    )


def test_compose_pins_the_same_non_root_user(compose):
    declared = compose["services"]["web"].get("user")

    assert declared == "10001:10001", (
        "compose does not pin the runtime user, so the image's USER is "
        "the only thing preventing root and an override would be silent"
    )


# --- T4747: capabilities and privilege escalation ------------------------


def test_no_service_runs_privileged(compose):
    for name, service in compose["services"].items():
        assert not service.get("privileged"), f"{name} runs privileged"


def test_every_service_drops_all_capabilities_first(compose):
    for name, service in compose["services"].items():
        assert service.get("cap_drop") == ["ALL"], (
            f"{name} does not drop ALL capabilities, so it keeps the "
            "default set whether or not it needs them"
        )


def test_added_capabilities_are_individually_justified(compose):
    """Adding back is allowed; adding back SYS_ADMIN is not."""
    forbidden = {"SYS_ADMIN", "ALL", "NET_ADMIN", "SYS_PTRACE", "SYS_MODULE"}

    for name, service in compose["services"].items():
        for capability in service.get("cap_add", []):
            assert capability not in forbidden, (
                f"{name} adds {capability} back, which returns most of "
                "what dropping ALL removed"
            )


def test_privilege_escalation_is_blocked(compose):
    for name, service in compose["services"].items():
        assert "no-new-privileges:true" in service.get("security_opt", []), (
            f"{name} allows setuid escalation"
        )


# --- T4750: network segmentation -----------------------------------------


def test_no_service_uses_the_default_bridge(compose):
    for name, service in compose["services"].items():
        assert service.get("networks"), (
            f"{name} declares no network, so it lands on the default "
            "bridge alongside everything else"
        )


def test_the_database_is_not_reachable_from_the_edge(compose):
    services = compose["services"]

    db_networks = set(services["db"]["networks"])
    proxy_networks = set(services["proxy"]["networks"])

    assert not db_networks & proxy_networks, (
        "the database shares a network with the internet-facing proxy"
    )
    assert db_networks == {"backend"}


def test_the_backend_network_is_internal(compose):
    backend = compose["networks"]["backend"]

    assert backend and backend.get("internal") is True, (
        "the backend network is not internal, so a later edit that "
        "publishes a port on the database would succeed"
    )


def test_only_the_proxy_publishes_ports(compose):
    for name, service in compose["services"].items():
        if name == "proxy":
            continue
        assert not service.get("ports"), (
            f"{name} publishes ports directly, bypassing the proxy and "
            "the TLS termination in front of it"
        )


# --- T1917: the assessment that runs on every build ----------------------
#
# A vulnerability scan against the built image needs a build and a scanner,
# neither of which exists for this project yet; that part is recorded as
# pipeline work. What can run today is the lint, and it runs here so it is
# executed by the same command as every other test rather than waiting for
# a pipeline to be created.


def test_no_image_is_referenced_by_a_floating_tag(compose, dockerfile):
    """`latest`, or any bare tag, means the build is not reproducible."""
    for name, service in compose["services"].items():
        image = service.get("image")
        if not image:
            continue
        assert not image.endswith(":latest") and image != image.split(":")[0], (
            f"{name} uses a floating or absent tag: {image}"
        )


def test_the_dockerfile_does_not_fetch_remote_content_at_build_time(dockerfile):
    """ADD from a URL pulls unverified content into the image."""
    for line in dockerfile.splitlines():
        stripped = line.strip()
        if stripped.startswith("ADD "):
            assert "://" not in stripped, f"remote ADD: {stripped}"
        if stripped.startswith("RUN ") and (
            "curl " in stripped or "wget " in stripped
        ):
            assert "sha256" in stripped.lower(), (
                f"build-time download with no integrity check: {stripped}"
            )


def test_no_secret_is_baked_into_the_image(dockerfile):
    """ENV and ARG values survive in the image history, readable by anyone."""
    declarations = re.findall(r"^(?:ENV|ARG)\s+(.+)$", dockerfile, re.MULTILINE)

    for declaration in declarations:
        for assignment in re.findall(r"([A-Z0-9_]+)=(\S*)", declaration):
            name, value = assignment
            if any(
                marker in name
                for marker in ("PASSWORD", "SECRET", "TOKEN", "KEY")
            ):
                assert not value, (
                    f"{name} is given a value in the image, where it is "
                    "visible in the layer history forever"
                )


def test_the_image_declares_a_healthcheck(dockerfile):
    """Without one the orchestrator cannot tell hung from healthy."""
    assert "HEALTHCHECK" in dockerfile


def test_pip_leaves_no_cache_in_the_image(dockerfile):
    for line in re.findall(r"^RUN pip install.+$", dockerfile, re.MULTILINE):
        if "requirements.txt" in line:
            assert "--no-cache-dir" in line, (
                f"pip cache is left in the image layer: {line}"
            )


# --- T1192, T1193: no host resource reaches into a container -------------

SENSITIVE_HOST_PATHS = (
    "/var/run/docker.sock",
    "/var/lib/docker",
    "/etc",
    "/proc",
    "/sys",
    "/dev",
    "/root",
    "/boot",
    "/",
)


def _mount_sources(service: dict) -> list:
    """Compose accepts both `host:container` and the long mapping form."""
    sources = []
    for volume in service.get("volumes") or []:
        if isinstance(volume, str):
            sources.append(volume.split(":")[0])
        else:
            sources.append(volume.get("source", ""))
    return sources


def test_the_application_container_mounts_no_host_path(compose):
    """The image already contains the code; a mount would let a write
    primitive in the application modify what it is about to run."""
    assert _mount_sources(compose["services"]["web"]) == []


@pytest.mark.parametrize(
    "name", ["web", "proxy", "db"]
)
def test_no_service_mounts_a_sensitive_host_path(compose, name):
    for source in _mount_sources(compose["services"][name]):
        if source.startswith("./") or source.startswith("${"):
            continue
        # A named volume has no leading slash.
        if not source.startswith("/"):
            continue
        resolved = os.path.normpath(source)
        assert resolved not in SENSITIVE_HOST_PATHS, (
            f"{name} mounts the host path {source}"
        )


def test_every_host_mount_is_read_only(compose):
    """The proxy genuinely needs its config and certificate from the host;
    baking a certificate into an image is worse. Read-only is the line."""
    for name, service in compose["services"].items():
        for volume in service.get("volumes") or []:
            if isinstance(volume, str):
                parts = volume.split(":")
                if not (parts[0].startswith("./") or parts[0].startswith("${")):
                    continue
                assert parts[-1] == "ro", f"{name} mounts {parts[0]} writable"


@pytest.mark.parametrize("field", ["devices", "device_cgroup_rules"])
def test_no_service_passes_a_host_device_through(compose, field):
    for name, service in compose["services"].items():
        assert not service.get(field), f"{name} sets {field}"


@pytest.mark.parametrize("namespace", ["pid", "ipc", "uts", "userns_mode"])
def test_no_service_shares_a_host_namespace(compose, namespace):
    for name, service in compose["services"].items():
        assert service.get(namespace) != "host", (
            f"{name} shares the host {namespace} namespace"
        )


def test_every_writable_path_is_a_sized_tmpfs(compose):
    """An unsized tmpfs can consume host memory up to its total."""
    for name, service in compose["services"].items():
        if not service.get("read_only"):
            continue
        for mount in service.get("tmpfs") or []:
            assert "size=" in mount, f"{name} has an unsized tmpfs: {mount}"


# --- T1194, T1195: no SSH anywhere near a container ---------------------


def test_the_image_installs_no_ssh_server(dockerfile):
    for marker in ("openssh", "sshd", "ssh-server"):
        assert marker not in dockerfile.lower(), f"image references {marker}"


def test_no_container_exposes_or_publishes_the_ssh_port(compose, dockerfile):
    assert not re.search(r"^\s*EXPOSE\s+22\b", dockerfile, re.MULTILINE)

    for name, service in compose["services"].items():
        for port in service.get("ports") or []:
            assert not str(port).endswith(":22"), f"{name} publishes ssh"
        for port in service.get("expose") or []:
            assert str(port) != "22", f"{name} exposes ssh"


# --- T1196, T1197: only the ports the application listens on ------------

APPROVED_PORTS = {"8091", "8443", "5432"}


def test_only_approved_ports_are_declared(compose, dockerfile):
    declared = set(re.findall(r"^\s*EXPOSE\s+(.+)$", dockerfile, re.MULTILINE))
    for name, service in compose["services"].items():
        for port in service.get("expose") or []:
            declared.add(str(port))

    for entry in declared:
        for port in entry.split():
            number = port.split("/")[0]
            assert number in APPROVED_PORTS, f"unapproved port declared: {port}"


def test_no_port_is_published_on_every_interface(compose):
    """`8443:8443` binds 0.0.0.0, which is rarely what anyone intended."""
    for name, service in compose["services"].items():
        for port in service.get("ports") or []:
            mapping = str(port)
            assert mapping.count(":") >= 2, (
                f"{name} publishes {mapping} on all interfaces; give a bind "
                "address"
            )
            assert mapping.startswith(("127.0.0.1:", "localhost:")), (
                f"{name} publishes {mapping} beyond the loopback interface"
            )


def test_exactly_one_service_publishes_a_port(compose):
    publishers = [
        name
        for name, service in compose["services"].items()
        if service.get("ports")
    ]
    assert publishers == ["proxy"], (
        f"expected only the proxy to publish; got {publishers}"
    )


# --- T1188, T1189: the LSM profile is stated, not inherited -------------


@pytest.mark.parametrize("name", ["web", "proxy", "db"])
def test_every_service_names_a_confinement_profile(compose, name):
    options = compose["services"][name].get("security_opt") or []
    profiles = [o for o in options if o.startswith("apparmor")]

    assert profiles, f"{name} names no AppArmor profile"
    for profile in profiles:
        assert profile != "apparmor=unconfined", f"{name} runs unconfined"
        assert profile.split("=", 1)[1].strip(), f"{name} has an empty profile"


def test_nothing_in_the_repository_recommends_running_unconfined(dockerfile):
    """Guidance outlives the config it describes."""
    for path in ("docker-compose.yml", "Dockerfile", "start_app.sh"):
        candidate = REPO_ROOT / path
        if candidate.exists():
            text = candidate.read_text(encoding="utf-8")
            assert "apparmor=unconfined" not in text, path
            assert "seccomp=unconfined" not in text, path


# --- T1200: a container cannot starve its neighbours --------------------


@pytest.mark.parametrize("name", ["web", "proxy", "db"])
def test_every_service_limits_cpu_memory_and_processes(compose, name):
    service = compose["services"][name]

    assert service.get("cpus"), f"{name} has no cpu limit"
    assert service.get("mem_limit"), f"{name} has no memory limit"
    # Without this a fork bomb exhausts the host's pid space while staying
    # inside its cpu and memory allowance.
    assert service.get("pids_limit"), f"{name} has no pids_limit"


# --- T1201, T1202, T1203: every exhaustion route is bounded ------------

SERVICES = ["web", "proxy", "db"]


@pytest.mark.parametrize("name", SERVICES)
def test_memory_cannot_overflow_into_swap(compose, name):
    """A memory limit without an equal swap limit lets the container use
    roughly twice what the limit says."""
    service = compose["services"][name]

    assert service.get("mem_limit"), f"{name} has no mem_limit"
    assert service.get("memswap_limit") == service["mem_limit"], (
        f"{name} allows swap beyond its memory limit"
    )


@pytest.mark.parametrize("name", SERVICES)
def test_file_descriptors_are_bounded(compose, name):
    nofile = (compose["services"][name].get("ulimits") or {}).get("nofile")

    assert nofile, f"{name} has no nofile ulimit"
    assert 0 < nofile["soft"] <= nofile["hard"], f"{name} nofile is incoherent"


@pytest.mark.parametrize("name", SERVICES)
def test_cpu_is_both_capped_and_weighted(compose, name):
    """`cpus` is the cap; `cpu_shares` only decides who wins under
    contention. Neither substitutes for the other."""
    service = compose["services"][name]

    for field in ("cpus", "cpu_shares"):
        value = service.get(field)
        assert value is not None, f"{name} has no {field}"
        assert float(value) > 0, f"{name} has a non-positive {field}"


# --- T1204, T1205: nothing writes to the image ------------------------


@pytest.mark.parametrize("name", SERVICES)
def test_every_root_filesystem_is_read_only(compose, name):
    assert compose["services"][name].get("read_only") is True, (
        f"{name} can write to its own image"
    )


def test_no_writable_path_is_broader_than_it_needs_to_be(compose):
    """A writable /app or / defeats the point of the read-only root."""
    for name, service in compose["services"].items():
        for mount in service.get("tmpfs") or []:
            target = mount.split(":")[0]
            assert target not in ("/", "/app", "/usr", "/etc"), (
                f"{name} makes {target} writable"
            )


# --- T1206, T1207: restarts are bounded ------------------------------


@pytest.mark.parametrize("name", SERVICES)
def test_the_restart_policy_is_bounded(compose, name):
    """`always` hides a service that fails on every start: it keeps
    restarting and the aggregate looks alive."""
    assert compose["services"][name].get("restart") == "on-failure:5", (
        f"{name} does not use on-failure:5"
    )


# --- T1210, T1211, T1214, T1215: privilege cannot be regained --------


@pytest.mark.parametrize("name", SERVICES)
def test_a_seccomp_profile_is_named_explicitly(compose, name):
    options = compose["services"][name].get("security_opt") or []
    profiles = [o for o in options if o.startswith("seccomp")]

    assert profiles, f"{name} relies on whatever seccomp the daemon defaults to"
    for profile in profiles:
        value = profile.split("=", 1)[1]
        assert value != "unconfined", f"{name} disables seccomp"
        assert (REPO_ROOT / value.lstrip("./")).exists(), (
            f"{name} references a seccomp profile that is not committed: {value}"
        )


def test_the_committed_seccomp_profile_denies_by_default():
    """A profile whose default action is ALLOW blocks only what it lists,
    which is the opposite of the intent."""
    import json

    profile = json.loads((REPO_ROOT / "deploy/seccomp.json").read_text())

    assert profile["defaultAction"] == "SCMP_ACT_ERRNO"
    assert profile["syscalls"], "the profile allows nothing back"


@pytest.mark.parametrize("name", SERVICES)
def test_no_service_can_acquire_new_privileges(compose, name):
    service = compose["services"][name]
    options = service.get("security_opt") or []

    assert "no-new-privileges:true" in options, f"{name} may escalate"
    assert not service.get("privileged"), f"{name} is privileged"
    assert "ALL" not in [c.upper() for c in (service.get("cap_add") or [])]


# --- T1150, T1151, T1176, T1177: where images come from ----------------

APPROVED_IMAGE_SOURCES = (
    # Docker Hub official images live in the implicit `library` namespace,
    # so an approved reference here is a bare name with no slash in it.
    "python",
    "nginx",
    "postgres",
)


def _image_references(compose: dict, dockerfile: str) -> list:
    references = [
        service["image"]
        for service in compose["services"].values()
        if service.get("image")
    ]
    references += re.findall(r"^FROM\s+(\S+)", dockerfile, re.MULTILINE)
    return references


def test_every_image_comes_from_an_approved_source(compose, dockerfile):
    """An image reference is untrusted input like any other. Keeping the
    approved set in one place means an unreviewed registry cannot arrive
    quietly in a diff that otherwise looks like a version bump."""
    for reference in _image_references(compose, dockerfile):
        repository = reference.split("@")[0].split(":")[0]

        assert "/" not in repository, (
            f"{reference} is not a Docker Hub official image; add its "
            "registry to the approved set deliberately"
        )
        assert repository in APPROVED_IMAGE_SOURCES, (
            f"{repository} is not an approved image source"
        )


def test_the_application_port_is_bound_but_never_published(compose):
    """The application binds 0.0.0.0 because the proxy reaches it across a
    container boundary, which is only safe because the port is not
    published and the proxy is the single ingress."""
    web = compose["services"]["web"]

    assert "--host 0.0.0.0" in web["command"]
    assert not web.get("ports"), "the application port is published directly"
    assert 8091 in [int(p) for p in web["expose"]]


def test_the_database_is_unreachable_from_the_ingress_network(compose):
    """Docker's inter-container communication default lets anything on a
    network talk to anything else on it, so separation has to come from
    the network layout rather than from a daemon flag."""
    db_networks = set(compose["services"]["db"]["networks"])
    proxy_networks = set(compose["services"]["proxy"]["networks"])

    assert db_networks.isdisjoint(proxy_networks)
    assert compose["networks"]["backend"]["internal"] is True


# --- T1208, T1209: mount propagation is stated ------------------------


def test_every_bind_mount_declares_private_propagation(compose):
    """The short `host:container:ro` form leaves propagation at the
    default. Stating it means a later change to shared, which would let a
    mount made inside the container appear on the host, is a visible edit
    rather than an omission."""
    for name, service in compose["services"].items():
        for volume in service.get("volumes") or []:
            assert not isinstance(volume, str), (
                f"{name} declares a mount in short form, so its propagation "
                f"is unstated: {volume}"
            )
            if volume.get("type") != "bind":
                continue
            propagation = (volume.get("bind") or {}).get("propagation")
            assert propagation in ("private", "rprivate", "slave", "rslave"), (
                f"{name} mounts {volume['source']} with propagation "
                f"{propagation!r}"
            )


# --- T1212, T1213: the cgroup the limits are enforced by --------------


@pytest.mark.parametrize("name", SERVICES)
def test_every_service_names_its_cgroup_parent(compose, name):
    """Without this the limits land in whatever slice the daemon chooses,
    which the host cannot then apply an aggregate ceiling to."""
    assert compose["services"][name].get("cgroup_parent"), (
        f"{name} has no cgroup_parent"
    )


def test_all_services_share_one_cgroup_parent(compose):
    parents = {
        service["cgroup_parent"] for service in compose["services"].values()
    }

    assert len(parents) == 1, f"services are split across cgroups: {parents}"


@pytest.mark.parametrize("name", SERVICES)
def test_no_service_can_reconfigure_cgroups(compose, name):
    """SYS_ADMIN is what would let a container rewrite its own limits, so
    the limits above are only meaningful while it is absent."""
    granted = [c.upper() for c in (compose["services"][name].get("cap_add") or [])]

    assert "SYS_ADMIN" not in granted
    assert not compose["services"][name].get("privileged")


# --- T21: the database connection is encrypted ------------------------


def test_the_application_requires_tls_to_the_database(compose):
    environment = compose["services"]["web"]["environment"]
    sslmode = [e for e in environment if e.startswith("POSTGRES_SSLMODE=")]

    assert sslmode, "the database connection mode is unset"
    # `prefer` and below encrypt when they can and fall back silently when
    # they cannot, which is indistinguishable from working.
    assert "prefer" not in sslmode[0] and "disable" not in sslmode[0]


# --- T7415: the container running a subprocess is not the privileged one --


@pytest.mark.security
@pytest.mark.parametrize("name", SERVICES)
def test_no_service_is_granted_the_capability_to_administer_the_host(compose, name):
    """SYS_ADMIN is most of root.

    The application answers a request by starting a process; that is the
    functionality this countermeasure asks to be isolated, and SYS_ADMIN on
    the container running it means the isolation is nominal -- it permits
    mount, and mount is a path out.
    """
    service = compose["services"][name]
    granted = {capability.upper() for capability in service.get("cap_add", [])}

    for dangerous in ("SYS_ADMIN", "SYS_PTRACE", "SYS_MODULE", "DAC_READ_SEARCH", "ALL"):
        assert dangerous not in granted, f"{name} is granted CAP_{dangerous}"


@pytest.mark.security
def test_the_service_that_spawns_processes_is_unprivileged(compose):
    """Three properties together, because each is bypassable alone.

    A non-root user, a read-only root filesystem, and no-new-privileges: a
    spawned process that finds a setuid binary escalates without the third,
    and writes a payload to disk to persist without the second.
    """
    web = compose["services"]["web"]

    assert web["user"] == "10001:10001"
    assert web["read_only"] is True
    assert "no-new-privileges:true" in web["security_opt"]
