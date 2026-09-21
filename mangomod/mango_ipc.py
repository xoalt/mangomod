"""Wrappers around Mango IPC operations (Unix domain socket & mmsg CLI)."""

from __future__ import annotations

import glob
import json
import os
import shutil
import socket
import subprocess
from typing import Any, Callable


def get_socket_path() -> str | None:
    """Find the path to the running Mango IPC Unix domain socket."""
    env_sock = os.environ.get("MANGO_INSTANCE_SIGNATURE")
    if env_sock and os.path.exists(env_sock):
        return env_sock

    uid = os.getuid()
    candidates = glob.glob(f"/run/user/{uid}/mango-*.sock")
    if not candidates:
        candidates = glob.glob("/tmp/mango-*.sock")

    if candidates:
        # Return newest socket
        candidates.sort(key=lambda p: os.path.getmtime(p), reverse=True)
        return candidates[0]

    return None


def _socket_request(command: str, timeout: float = 2.0) -> str:
    """Send a command string directly to the Mango Unix domain socket and read response."""
    sock_path = get_socket_path()
    if not sock_path:
        raise ConnectionError("No Mango IPC socket found")

    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.settimeout(timeout)
    try:
        s.connect(sock_path)
        cmd_bytes = (command.strip() + "\n").encode("utf-8")
        s.sendall(cmd_bytes)

        chunks = []
        while True:
            try:
                data = s.recv(4096)
                if not data:
                    break
                chunks.append(data)
            except socket.timeout:
                break
        return b"".join(chunks).decode("utf-8", errors="replace")
    finally:
        s.close()


def _run_mmsg(args: list[str], timeout: float = 3.0) -> tuple[str, str, int]:
    """Fallback: run mmsg executable synchronously."""
    mmsg_bin = shutil.which("mmsg")
    if not mmsg_bin:
        return "", "mmsg command not found", 1

    try:
        r = subprocess.run(
            [mmsg_bin, *args],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return r.stdout, r.stderr, r.returncode
    except FileNotFoundError:
        return "", "mmsg not found", 1
    except subprocess.TimeoutExpired:
        return "", "mmsg timed out", 1


def is_mango_running() -> bool:
    """Return True if Mango compositor is active and reachable via IPC."""
    sock_path = get_socket_path()
    if not sock_path:
        return False
    try:
        resp = _socket_request("get version", timeout=0.5)
        return bool(resp.strip())
    except Exception:
        stdout, _, rc = _run_mmsg(["get", "version"], timeout=0.5)
        return rc == 0 and bool(stdout.strip())


def get_version() -> str:
    """Get Mango version string."""
    try:
        resp = _socket_request("get version")
        data = json.loads(resp.strip())
        if isinstance(data, dict) and "version" in data:
            return data["version"]
        return resp.strip()
    except Exception:
        stdout, _, rc = _run_mmsg(["get", "version"])
        if rc == 0 and stdout.strip():
            try:
                data = json.loads(stdout.strip())
                return data.get("version", stdout.strip())
            except Exception:
                return stdout.strip()
    return "Not running"


def query_json(cmd: str) -> Any:
    """Send a query to Mango IPC and return parsed JSON result, or None on failure."""
    try:
        raw = _socket_request(cmd)
        lines = [line for line in raw.strip().splitlines() if line.strip()]
        if lines:
            return json.loads(lines[0])
    except Exception:
        # Fallback to mmsg
        parts = cmd.strip().split()
        stdout, _, rc = _run_mmsg(parts)
        if rc == 0 and stdout.strip():
            try:
                return json.loads(stdout.strip())
            except Exception:
                pass
    return None


def get_all_monitors() -> list[dict]:
    """Fetch all active monitors from Mango."""
    data = query_json("get all-monitors")
    if isinstance(data, dict) and "monitors" in data:
        return data["monitors"]
    if isinstance(data, list):
        return data
    return []


def get_all_tags() -> list[dict]:
    """Fetch status of all tags across monitors."""
    data = query_json("get all-tags")
    if isinstance(data, dict) and "all_tags" in data:
        return data["all_tags"]
    if isinstance(data, list):
        return data
    return []


def get_all_clients() -> list[dict]:
    """Fetch all active window clients."""
    data = query_json("get all-clients")
    if isinstance(data, dict) and "clients" in data:
        return data["clients"]
    if isinstance(data, list):
        return data
    return []


def get_all_devices() -> list[dict]:
    """Fetch all physical input devices."""
    data = query_json("get all-devices")
    if isinstance(data, dict) and "devices" in data:
        return data["devices"]
    if isinstance(data, list):
        return data
    return []


def get_layouts() -> list[str]:
    """Fetch available layout names."""
    data = query_json("get layouts")
    if isinstance(data, dict) and "layouts" in data:
        raw = data["layouts"]
        if isinstance(raw, list):
            names = []
            for item in raw:
                if isinstance(item, dict) and "name" in item:
                    names.append(item["name"])
                elif isinstance(item, str):
                    names.append(item)
            if names:
                return names
    if isinstance(data, list):
        names = []
        for item in data:
            if isinstance(item, dict) and "name" in item:
                names.append(item["name"])
            elif isinstance(item, str):
                names.append(item)
        if names:
            return names
    return [
        "tile",
        "scroller",
        "grid",
        "deck",
        "monocle",
        "center_tile",
        "vertical_tile",
        "vertical_scroller",
        "dwindle",
    ]


def dispatch(command_str: str) -> tuple[bool, str]:
    """Dispatch an action to Mango compositor (e.g. 'reload_config', 'togglefloating')."""
    cmd = f"dispatch {command_str}"
    try:
        resp = _socket_request(cmd, timeout=1.5)
        return True, resp.strip()
    except Exception as exc:
        stdout, stderr, rc = _run_mmsg(["dispatch", *command_str.split(",")])
        if rc == 0:
            return True, stdout.strip()
        return False, str(exc) or stderr.strip()


def reload_config() -> tuple[bool, str]:
    """Trigger hot-reload in Mango compositor."""
    return dispatch("reload_config")


def _strip_ansi(text: str) -> str:
    """Mango prints color codes even when piped — strip them so messages
    are readable in toasts and dialogs instead of raw escape garbage."""
    import re

    return re.sub(r"\x1b\[[0-9;]*[A-Za-z]", "", text)


def validate_config(config_path: str) -> tuple[bool, str]:
    """Validate a mango configuration file using `mango -c <path> -p`."""
    mango_bin = shutil.which("mango")
    if not mango_bin:
        # If mango binary not installed, skip validation
        return True, "mango binary not found; skipped external validation"

    try:
        r = subprocess.run(
            [mango_bin, "-c", config_path, "-p"],
            capture_output=True,
            text=True,
            timeout=5.0,
        )
        if r.returncode == 0:
            return True, _strip_ansi(r.stdout.strip() or "Config syntax OK")
        err_msg = r.stderr.strip() or r.stdout.strip() or f"Validation failed with code {r.returncode}"
        return False, _strip_ansi(err_msg)
    except subprocess.TimeoutExpired:
        return False, "Validation process timed out"
    except Exception as exc:
        return False, str(exc)


_touchpad_cache: bool | None = None


def has_touchpad() -> bool:
    """Check whether a physical touchpad is available."""
    global _touchpad_cache
    if _touchpad_cache is not None:
        return _touchpad_cache

    try:
        devices = get_all_devices()
        for dev in devices:
            types = dev.get("types", [])
            name = dev.get("name", "").lower()
            if "touchpad" in types or "touchpad" in name or "trackpad" in name:
                _touchpad_cache = True
                return True
    except Exception:
        pass

    # Fallback: check /sys/class/input
    try:
        for p in glob.glob("/sys/class/input/event*/device/name"):
            with open(p, "r", errors="ignore") as f:
                content = f.read().lower()
                if "touchpad" in content or "trackpad" in content or "synaptics" in content:
                    _touchpad_cache = True
                    return True
    except Exception:
        pass

    _touchpad_cache = False
    return False
