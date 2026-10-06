"""`hermes pastdotdev setup` and `hermes pastdotdev status`.

Hermes imports this file on its own when `pastdotdev` is the active memory provider, without running the
provider module, so it imports only the standard library and the sibling config.py.
"""

from __future__ import annotations

import getpass
import json
import urllib.error
import urllib.request

from .config import DEFAULT_API_URL, VERSION, load_config, past_home, read_json, write_private


def mask(key: str) -> str:
    return f"...{key[-8:]}" if len(key) > 8 else ("set" if key else "not set")


def check(api_url: str, api_key: str) -> str:
    """One cheap call with the key: its project's usage."""
    request = urllib.request.Request(f"{api_url}/api/v1/usage", headers={
        "Authorization": f"Bearer {api_key}", "User-Agent": f"past-hermes/{VERSION}"})
    try:
        with urllib.request.urlopen(request, timeout=15):
            return "connected"
    except urllib.error.HTTPError as error:
        return "the key was refused" if error.code in (401, 403) else f"past answered {error.code}"
    except Exception as error:
        return f"could not reach {api_url} ({error})"


def enable_provider() -> None:
    """Sets memory.provider to pastdotdev in Hermes' own configuration."""
    try:
        from hermes_cli.config import load_config as load_hermes_config, save_config as save_hermes_config
        config = load_hermes_config()
        if not isinstance(config.get("memory"), dict):
            config["memory"] = {}
        config["memory"]["provider"] = "pastdotdev"
        save_hermes_config(config)
    except Exception as error:
        print(f"  Could not set memory.provider: {error}. Run: hermes config set memory.provider pastdotdev")


def cmd_setup(args=None) -> None:
    path = past_home() / "config.json"
    file = read_json(path, {})
    current = load_config()
    print("\npast memory setup")
    print("─" * 60)
    print("  past gives Hermes persistent cross-session memory.")
    print(f"  Config is shared with past's other plugins at {path}\n")

    print(f"  Current API key: {mask(current['apiKey'])}")
    key = getpass.getpass("  past project key, past_sk_... (leave blank to keep current): ").strip()
    identity = input(f"  Who you are, to recall as you [{current['identity'] or 'an email or id'}]: ").strip()
    api_url = input(f"  past API address [{current['apiUrl'] or DEFAULT_API_URL}]: ").strip()

    if key:
        file["apiKey"] = key
    if identity:
        file["identity"] = identity
    if api_url:
        file["apiUrl"] = api_url.rstrip("/")
    write_private(path, file)
    enable_provider()

    config = load_config()
    if not config["apiKey"]:
        print("\n  No key yet: get one in the past.dev console, then run hermes pastdotdev setup again.\n")
        return
    if config["apiUrl"].startswith("http://") and not config["apiUrl"].startswith(("http://localhost", "http://127.0.0.1")):
        print("  Warning: this address is plain http, so the key travels unencrypted.")
    result = check(config["apiUrl"], config["apiKey"])
    mark = "✓" if result == "connected" else "!"
    print(f"\n  {mark} {result} · identity: {config['identity'] or 'not set (recall is off)'}")
    print("  Memory provider: pastdotdev. Start a new session to use it.\n")


def cmd_status(args=None) -> None:
    config = load_config()
    state = read_json(past_home() / "hermes" / "state.json", {})
    print(f"\npast {VERSION} · {config['apiUrl']} · key {mask(config['apiKey'])} · identity {config['identity'] or 'not set'}")
    print(f"  recall {'on' if config['recall'] and config['identity'] else 'off'} · ingest {'on' if config['ingest'] else 'off'}")
    if config["apiKey"]:
        print(f"  {check(config['apiUrl'], config['apiKey'])}")
    sent = sorted(state.items(), key=lambda item: item[1].get("sentAt", ""), reverse=True)
    print(f"  sessions sent: {sum(1 for _, s in sent if s.get('sentAt'))}")
    for session, entry in sent[:3]:
        line = f"    {session}: sent {entry.get('sentAt', 'never')}"
        print(line + (f" · last error: {entry['lastError']}" if entry.get("lastError") else ""))
    print()


def dispatch(args) -> None:
    {"setup": cmd_setup, "status": cmd_status}.get(getattr(args, "past_command", None) or "status")(args)


def register_cli(subparser) -> None:
    subs = subparser.add_subparsers(dest="past_command")
    subs.add_parser("setup", help="Connect Hermes to past.dev (key, identity, address)")
    subs.add_parser("status", help="Show the connection and the last sessions sent")
    subparser.set_defaults(func=dispatch)
