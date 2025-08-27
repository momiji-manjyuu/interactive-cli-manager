import json
import os
import sys
import time
import uuid
from pathlib import Path


def _resolve_base(arg_path: str | None) -> Path:
    # 明示引数 > 環境変数 FS_BRIDGE_DIR > CWD/fs_bridge
    if arg_path:
        return Path(arg_path).expanduser().resolve()
    env = os.environ.get("FS_BRIDGE_DIR")
    if env:
        return Path(env).expanduser().resolve()
    return (Path.cwd() / "fs_bridge").resolve()

def send(req: dict, timeout: float = 60.0, bridge_dir: str | None = None):
    base = _resolve_base(bridge_dir)
    in_dir = base / "in"
    out_dir = base / "out"
    in_dir.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)
    rid = f"{int(time.time()*1000)}_{uuid.uuid4().hex}.json"
    in_path = in_dir / rid
    out_path = out_dir / rid
    tmp_path = in_path.with_suffix(in_path.suffix + ".tmp")
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(req, f, ensure_ascii=False)
    tmp_path.replace(in_path)
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
    raise TimeoutError("No response.")

def main():
    # Usage: fs_send.py '<json_request>' [timeout] [bridge_dir]
    if len(sys.argv) < 2:
        print("Usage: fs_send.py '<json_request>' [timeout] [bridge_dir]", file=sys.stderr)
        sys.exit(1)
    req = json.loads(sys.argv[1])
    to = float(sys.argv[2]) if len(sys.argv) > 2 else 60.0
    bridge = sys.argv[3] if len(sys.argv) > 3 else None
    resp = send(req, timeout=to, bridge_dir=bridge)
    print(json.dumps(resp, ensure_ascii=False))

if __name__ == "__main__":
    main()

