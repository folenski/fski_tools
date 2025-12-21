"""
Wrapper around rclone to sync directories based on a JSON configuration.
Usage: python save.py --action pull|push|check  keys define in config/save.json

Requires `rclone` on PATH. Reads the configuration `config/config.json` 
"""
import json
import argparse
from typing import Optional, List
from configparser import ConfigParser
from pathlib import Path
from rclone_python import rclone # type: ignore

param_file = Path(__file__).parent / "save.ini"


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
    conf_path = Path(file_conf)
    params.append(conf_path)
    return params

def do_action(action: str, key: str, source: str, dest: str, confirm: bool) -> bool:
    print(f"{action}ing ({key}) from {source} to {dest}")
    if confirm:
        resp = input("Continue? [y/N] ").strip().lower()
        if resp not in ("y", "yes"):
            print("Aborted.")
            return False
    rclone.sync(source, dest)
    return True

def main():
    def_action = "check"
    valid_actions = {"pull", "push", "check"}

    if not rclone.is_installed():
        print("Rclone is not installed or not found on PATH.")
        return
    
    parser = argparse.ArgumentParser(description="Sync directories via rclone according to conf/save.json")
    parser.add_argument("keys", nargs='+', help="One or more keys of the rclone remote to use")
    parser.add_argument("-a", "--action", required=False, help="pull | push | check")
    parser.add_argument("--confirm", action="store_true", help="Skip confirmation prompts")
    args = parser.parse_args()

    action = args.action if args.action is not None else def_action
    action = action.lower().strip()
    if action not in valid_actions:
        print(f"Invalid action: {action!r}. Expected one of: {', '.join(sorted(valid_actions))}")
        return
    
    temp = read_ini(param_file)
    t1 = Path(temp[0])

    if not t1.exists():
        print(f"Config file not found: {t1}")
        return
    
    for key in args.keys:
        conf = read_conf_json(t1, key)
        if conf is None:
            print(f"No configuration found for key: {key}")
            continue

        if "description" in conf:
            print(f"Description ({key}): {conf['description']}")

        if action == "push":
            do_action(action, key, conf["source"], conf["dest"], args.confirm)
        elif action == "pull":
            do_action(action, key, conf["dest"], conf["source"], args.confirm)
        else:  # check
            print(f"Checking ({key}) between {conf['source']} and {conf['dest']}")
            ret = rclone.check(conf['source'], conf['dest'])
            if ret[0]:
                print("The source and destination are identical.")
            else:
                print("Differences found:")
                for diff in ret[1]:
                    if diff[0] != "=": print(f"- {diff[1]}")

if __name__ == "__main__":
    main()