"""
Wrapper around rclone to sync directories based on a JSON configuration.
Usage: python synchronize.py --action pull|push|check  keys define in config/save.json

Requires `rclone` on PATH. Reads the configuration `config/config.json`

updated 2024-12-22 (fski) update to new config.json format, supporting multiple directories per key
updated 2024-12-24 (fski) update to new config.json format, add remote field
"""
import json
import argparse
import subprocess
from typing import Optional, List
from configparser import ConfigParser
from pathlib import Path
from datetime import datetime
from rclone_python import rclone # type: ignore

param_file = Path(__file__).parent / "save.ini"

def is_need_updated(name: str, remote: str, log: str, tmp: str) -> bool:
    """
    Determine if a file needs to be updated by comparing local and remote log contents.
    Compares the local log file stored in tmp directory with the remote log file
    accessed via rclone. Returns True if the file needs updating (logs differ or
    remote log cannot be accessed), False if they match.
    Args:
        name (str): The name of the file/log to check (without extension).
        remote (str): The base remote path for rclone operations.
        log (str): The relative log directory path on the remote. If empty string,
                   indicates update is needed.
        tmp (str): The local temporary directory path where local logs are stored.
    Returns:
        bool: True if the file needs to be updated, False if local and remote
              logs are identical and update is not needed.
    Raises:
        subprocess.CalledProcessError: If rclone command fails (when check=True).
    """

    if log == "": return True

    log_local = Path(tmp) / f"{name}.txt"
    if log_local.exists():
        local_content = log_local.read_text()
    else:
        local_content = ""

    log_remote = f"{remote}{log}/{name}.txt"

    ret = subprocess.run(["rclone", "cat", log_remote], check=True, capture_output=True, text=True)
    if ret.returncode != 0: return True
    
    remote_content = ret.stdout.strip()
    if local_content == remote_content:
        print(f"No update needed for {name}")
        return False

    return True

def read_conf_json(path: Path, name: str) -> Optional[List[dict]]:
    path = Path(path).resolve()
    dirs = []
    if not path.exists():
        raise FileNotFoundError(f"Config file not found:: {path}")
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    
    if isinstance(data, list):
        dirs = data
    else:
        raise TypeError(f"Config file bad format::{path}")
    
    for entry in dirs:
        if "name" in entry and entry["name"] == name: return entry 
    
    return None

def read_ini(path: Path) -> list :
    params = []
    config = ConfigParser()
    config.read(str(path))
    file_conf = config.get("settings", "config", fallback="./config/config.json")
    tmp = config.get("settings", "tmp", fallback="./log/")
    return file_conf, tmp

def do_action(action: str, key: str, source: str, dest: str, confirm: bool) -> bool:
    print(f"{action}ing ({key}) from {source} to {dest}")
    if confirm:
        resp = input("Continue? [y/N] ").strip().lower()
        if resp not in ("y", "yes"):
            print("Aborted.")
            return False
    subprocess.run(["rclone", "sync", source, dest, "--progress"], check=True)
    return True

def main():
    def_action = "check"
    valid_actions = {"pull", "push", "check"}

    # Test rclone installation
    try:
        subprocess.run(["rclone", "version"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        print(f"Rclone error")
        return
    
    parser = argparse.ArgumentParser(description="Sync directories via rclone according to conf/save.json")
    parser.add_argument("name", help="name defined in config/save.json")
    parser.add_argument("-a", "--action", required=False, help="pull | push | check")
    parser.add_argument("--confirm", action="store_true", help="Skip confirmation prompts")
    args = parser.parse_args()

    action = args.action if args.action is not None else def_action
    action = action.lower().strip()
    if action not in valid_actions:
        print(f"Invalid action: {action!r}. Expected one of: {', '.join(sorted(valid_actions))}")
        return
    
    t1, tmp = read_ini(param_file)
    t1 = Path(t1).resolve()

    if not t1.exists():
        print(f"Config file not found: {t1}")
        return
    
    conf = read_conf_json(t1, args.name)
    if conf is None:
        print(f"No configuration found for key: {args.name}")
        return

    if "description" in conf:
        print(f"Description ({args.name}): {conf['description']}")

    remote = conf.get("remote", "")

    log = conf.get("log", "")
    if log != "":
        log_file = Path(tmp) / f"{args.name}.txt"
        log_file.parent.mkdir(parents=True, exist_ok=True)
        update = is_need_updated(args.name, remote, log, tmp)
        if update:
            if action == "push":
                print(f"Push ({args.name}) not permited as changes detected.")
                return
            else:
                subprocess.run(["rclone", "sync", remote + log, tmp], check=True)
        else:
            if action == "pull":
                print(f"Pull ({args.name}) not permited as no changes detected.")
                return
            else:
                timestamp = datetime.now().isoformat()
                log_file.write_text(timestamp)
                subprocess.run(["rclone", "sync", log_file, remote + log], check=True)

    if "directories" not in conf or not isinstance(conf["directories"], list):
        print(f"No directories defined for key: {args.name}")
        return
    
    for dir in conf["directories"]:
        if action == "push":
            do_action(action, args.name, dir["source"], remote + dir["dest"], args.confirm)
        elif action == "pull":
            do_action(action, args.name, remote + dir["dest"], dir["source"], args.confirm)
        else:
            continue

if __name__ == "__main__":
    main()