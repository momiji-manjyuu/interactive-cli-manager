import json
import os
import sys
import time
import uuid
from pathlib import Path

BASE = Path(__file__).resolve().parents[1] / "fs_bridge"
IN_DIR = BASE / "in"
OUT_DIR = BASE / "out"


def ensure_dirs():
    IN_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)


def send(req: dict, timeout: float = 30.0):
    ensure_dirs()
    rid = f"{int(time.time()*1000)}_{uuid.uuid4().hex}.json"
    in_path = IN_DIR / rid
    out_path = OUT_DIR / rid
    with open(in_path, "w", encoding="utf-8") as f:
        json.dump(req, f, ensure_ascii=False)
    end = time.time() + timeout
    while time.time() < end:
        if out_path.exists():
            try:
                with open(out_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            finally:
                try:
                    out_path.unlink()
                except Exception:
                    pass
        time.sleep(0.05)
    raise TimeoutError("No response file written by manager.")


def main():
    # Example conversation with gemini via cmd
    print("Sending: execute gemini...")
    resp = send({
        "action": "execute",
        "data": {
            "command": ["cmd", "/c", "gemini"],
            "wait_for": "output",
            "timeout": 20,
        },
    }, timeout=35)
    print(resp)

    print("Sending: greeting...")
    resp = send({
        "action": "input",
        "data": {
            "text": "Hi Gemini! Please reply briefly.",
            "wait_for_output": True,
            "timeout": 60,
        },
    }, timeout=65)
    print(resp)

    print("Sending: follow-up...")
    resp = send({
        "action": "input",
        "data": {
            "text": "What's one fun fact about AI agents?",
            "wait_for_output": True,
            "timeout": 60,
        },
    }, timeout=65)
    print(resp)

    print("Dump output...")
    resp = send({"action": "dump_output"})
    print(resp)

    print("Interrupt policy...")
    resp = send({
        "action": "interrupt",
        "data": {
            "policy": ["C", "BREAK", "graceful", "stop"],
            "timeout": 10,
        },
    })
    print(resp)


if __name__ == "__main__":
    main()

