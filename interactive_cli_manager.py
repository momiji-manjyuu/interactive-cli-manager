
import subprocess
import json
import sys
import threading
import os
import shlex
import locale
import io
import time
import signal
import argparse

class InteractiveCLIManager:
    def __init__(self):
        self.process = None
        self.output_buffer = []
        self.output_lock = threading.Lock()
        self.output_cv = threading.Condition(self.output_lock)
        self.output_full_buffer = []
        # システムのデフォルトエンコーディングを使用。エラーは置き換えで処理。
        self.encoding = locale.getpreferredencoding(False)
        self._stdout_text = None
        self._env = None
        self._pty_master_fd = None

    def _read_output(self):
        # 改行なしのプロンプト（例: '>>> '）も即時に取得できるよう、
        # テキストラッパで1文字ずつ読み取ってバッファに積む。
        stream = self._stdout_text
        if stream is None:
            return
        while True:
            ch = stream.read(1)
            if ch == '' or ch is None:
                break
            with self.output_lock:
                self.output_buffer.append(ch)
                self.output_full_buffer.append(ch)
                self.output_cv.notify_all()

    def execute_command(self, command, shell=False, env=None, tui=False):
        if self.process:
            self.stop_command()

        try:
            if tui:
                # TUI対応は一旦凍結（将来再実装予定）
                return {"status": "error", "error_code": "NOT_SUPPORTED", "message": "TUI mode is currently disabled."}
            # Windowsでshell=Falseの場合、commandはリスト形式が推奨される
            # shell=Trueの場合、commandは文字列である必要がある
            # ここでは、AIエージェントがリスト形式でコマンドを渡すことを推奨する
            # shell=Trueは、複雑なシェル機能（パイプ、リダイレクトなど）が必要な場合にのみ使用する
            if env is not None:
                # ベースは現在の環境をコピーし、上書きを適用
                proc_env = os.environ.copy()
                for k, v in env.items():
                    if v is None and k in proc_env:
                        proc_env.pop(k)
                    elif v is not None:
                        proc_env[str(k)] = str(v)
            else:
                proc_env = None

            # POSIXではプロセスグループを分離してシグナル送出しやすくする
            preexec = os.setsid if sys.platform != "win32" else None
            self._pty_master_fd = None
            self.process = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                bufsize=-1,
                text=False,
                shell=shell,
                env=proc_env,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0,
                preexec_fn=preexec,
            )
            # stdoutをテキストラップ（改行なし出力も即時に取得するため）
            self._stdout_text = io.TextIOWrapper(
                self.process.stdout, encoding=self.encoding, errors="replace", newline=""
            )
            self.output_buffer = []
            self.output_thread = threading.Thread(target=self._read_output)
            self.output_thread.daemon = True
            self.output_thread.start()
            return {"status": "success", "message": "Command started."}
        except Exception as e:
            code = getattr(e, "errno", None)
            err_code = "EXEC_ERROR"
            if isinstance(e, FileNotFoundError):
                err_code = "ENOENT"
            return {"status": "error", "error_code": err_code, "message": str(e)}

    def send_input(self, input_text):
        if not self.process or not self.process.stdin:
            return {"status": "error", "error_code": "NOT_RUNNING", "message": "No command running or stdin not available."}
        try:
            # システムのデフォルトエンコーディングでエンコード
            self.process.stdin.write((input_text + os.linesep).encode(self.encoding))
            self.process.stdin.flush()
            return {"status": "success", "message": "Input sent."}
        except BrokenPipeError:
            return {"status": "error", "error_code": "BROKEN_PIPE", "message": "BrokenPipeError: The pipe has been closed. The command might have exited."}
        except Exception as e:
            return {"status": "error", "error_code": "INPUT_ERROR", "message": str(e)}

    def get_output(self, peek=False, wait=False, timeout=None, pattern=None, regex=False, since=None, include_index=False):
        with self.output_cv:
            if wait:
                if not self.output_buffer and self.process and self.process.poll() is None:
                    if timeout is None:
                        self.output_cv.wait()
                    else:
                        self.output_cv.wait(timeout=timeout)
            full = "".join(self.output_full_buffer)
            output = "".join(self.output_buffer)
            # パターン待機（出力全体から検索）
            matched = None
            match_index = None
            start = 0
            if since is not None and isinstance(since, int) and since >= 0:
                start = min(since, len(full))
            search_base = full[start:]
            if pattern:
                import re
                if regex:
                    m = re.search(pattern, search_base)
                    matched = m is not None
                    match_index = (start + m.start()) if m else None
                else:
                    idx = search_base.find(pattern)
                    matched = idx != -1
                    match_index = (start + idx) if matched else None
                # waitループ（必要なら）
                if wait and not matched and (self.process and self.process.poll() is None):
                    end = None if timeout is None else (time.time() + float(timeout))
                    while True:
                        remaining = None if end is None else (end - time.time())
                        if remaining is not None and remaining <= 0:
                            break
                        self.output_cv.wait(timeout=0.05 if remaining is None else min(0.05, max(0, remaining)))
                        full = "".join(self.output_full_buffer)
                        search_base = full[start:]
                        if regex:
                            m = re.search(pattern, search_base)
                            matched = m is not None
                            match_index = (start + m.start()) if m else None
                        else:
                            idx = search_base.find(pattern)
                            matched = idx != -1
                            match_index = (start + idx) if matched else None
                        if matched:
                            break
                    if not matched:
                        return {"status": "timeout", "output": output}
            # 通常の取得（since指定時はfullから返す）
            resp_output = output
            if since is not None:
                resp_output = full[start:]
            if not peek and since is None:
                self.output_buffer = []
            resp = {"status": "success", "output": resp_output}
            if include_index:
                resp["index"] = len(full)
                resp["start"] = start
            if pattern:
                resp["matched"] = bool(matched)
                if match_index is not None:
                    resp["match_index"] = match_index
            # タイムアウト判定（パターンなしの単純待機）
            if wait and not pattern and resp_output == "" and self.process and self.process.poll() is None and timeout is not None:
                return {"status": "timeout", "output": resp_output}
            return resp

    def get_status(self):
        if self.process:
            poll = self.process.poll()
            if poll is None:
                return {"status": "running", "pid": self.process.pid}
            else:
                return {"status": "exited", "return_code": poll}
        else:
            return {"status": "not_running"}

    def wait_status(self, wait_for="exited", timeout=None):
        end = None if timeout is None else (time.time() + float(timeout))
        while True:
            st = self.get_status()
            if wait_for == "exited":
                if st.get("status") in ("exited", "not_running"):
                    return st
            elif wait_for == "running":
                if st.get("status") == "running":
                    return st
            else:
                # Unknown wait_for falls back to immediate status
                return st
            if end is not None and time.time() > end:
                return {"status": "timeout"}
            time.sleep(0.05)

    def stop_command(self, scope: str = "process"):
        if self.process:
            try:
                if sys.platform == "win32":
                    # Windowsではtaskkillでプロセスグループを終了
                    subprocess.call(["taskkill", "/F", "/T", "/PID", str(self.process.pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                else:
                    # POSIXシステム: スコープに応じてプロセス/グループを終了
                    if str(scope).lower() == "group":
                        try:
                            pgid = os.getpgid(self.process.pid)
                            os.killpg(pgid, signal.SIGTERM)
                        except Exception:
                            # フォールバック: 個別terminate
                            self.process.terminate()
                    else:
                        self.process.terminate()
                
                # プロセスが終了するまで待機（タイムアウト付き）
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # タイムアウトした場合は強制終了
                if sys.platform != "win32": # Windowsではtaskkillが既に強制終了を試みている
                    try:
                        if str(scope).lower() == "group":
                            pgid = os.getpgid(self.process.pid)
                            os.killpg(pgid, signal.SIGKILL)
                        else:
                            self.process.kill()
                    except Exception:
                        self.process.kill()
            except Exception as e:
                return {"status": "error", "message": f"Error stopping command: {str(e)}"}
            finally:
                try:
                    if self._stdout_text is not None:
                        self._stdout_text.close()
                except Exception:
                    pass
                # PTY master fdを閉じる
                try:
                    if self._pty_master_fd is not None:
                        try:
                            os.close(self._pty_master_fd)
                        except Exception:
                            pass
                except Exception:
                    pass
                self._stdout_text = None
                self._pty_master_fd = None
                self.process = None
                return {"status": "success", "message": "Command stopped."}
        return {"status": "not_running", "message": "No command to stop."}

    def graceful_stop(self, timeout=3, scope: str = "process"):
        if not self.process:
            return {"status": "not_running", "message": "No command to stop."}
        try:
            if sys.platform == "win32":
                try:
                    self.process.send_signal(signal.CTRL_BREAK_EVENT)
                except Exception:
                    # フォールバック: terminate 相当
                    pass
            else:
                # POSIX: スコープに応じてSIGTERMを送出
                try:
                    if str(scope).lower() == "group":
                        pgid = os.getpgid(self.process.pid)
                        os.killpg(pgid, signal.SIGTERM)
                    else:
                        self.process.terminate()
                except Exception:
                    self.process.terminate()
            self.process.wait(timeout=timeout)
            try:
                if self._stdout_text is not None:
                    self._stdout_text.close()
            except Exception:
                pass
            self._stdout_text = None
            self.process = None
            return {"status": "success", "message": "Command gracefully stopped."}
        except subprocess.TimeoutExpired:
            # 強制停止へフォールバック
            return self.stop_command(scope=scope)
        except Exception as e:
            return {"status": "error", "message": f"Error graceful stopping: {str(e)}"}

    def send_ctrl_event(self, event: str):
        if not self.process:
            return {"status": "not_running", "message": "No command running."}
        try:
            if sys.platform == "win32":
                if event.upper() == "C":
                    self.process.send_signal(signal.CTRL_C_EVENT)
                else:
                    self.process.send_signal(signal.CTRL_BREAK_EVENT)
                return {"status": "success", "message": f"Sent CTRL_{event.upper()} event."}
            else:
                # POSIX: Ctrl+C相当はSIGINT、BREAKはSIGTERMにマップ
                pgid = os.getpgid(self.process.pid)
                if event.upper() == "C":
                    os.killpg(pgid, signal.SIGINT)
                else:
                    os.killpg(pgid, signal.SIGTERM)
                return {"status": "success", "message": f"Sent POSIX signal for {event}."}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def set_encoding(self, encoding: str):
        try:
            # 入力エンコーディングの更新
            self.encoding = encoding
            # 出力側はTextIOWrapperを動的に再構成可能
            if self._stdout_text is not None:
                try:
                    self._stdout_text.reconfigure(encoding=encoding, errors="replace", newline="")
                except Exception:
                    # 古いPython等でreconfigure未対応の場合は無視（次回起動に反映）
                    pass
            return {"status": "success", "message": f"Encoding set to {encoding}."}
        except Exception as e:
            return {"status": "error", "message": str(e)}


def main():
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument('--fs-bridge', dest='fs_bridge', nargs='?', const='fs_bridge',
                        help='Use filesystem bridge at given directory (creates in/out). If omitted, defaults to ./fs_bridge.')
    parser.add_argument('--fs-interval', dest='fs_interval', type=float, default=0.05,
                        help='Polling interval (seconds) for FS bridge (default: 0.05).')
    args = parser.parse_args()

    manager = InteractiveCLIManager()

    def handle_request(request: dict):
        action = request.get("action")
        data = request.get("data", {})
        response = {}
        if action == "execute":
            command_to_execute = data.get("command")
            shell_mode = data.get("shell", False)
            env_overrides = data.get("env")
            wait_for = data.get("wait_for") if isinstance(data, dict) else None
            timeout = data.get("timeout") if isinstance(data, dict) else None

            if isinstance(command_to_execute, str) and not shell_mode:
                try:
                    command_to_execute = shlex.split(command_to_execute, posix=False if sys.platform == "win32" else True)
                except ValueError:
                    return {"status": "error", "error_code": "BAD_REQUEST", "message": f"Command parsing error: {command_to_execute}. Provide list or use shell=True."}
            elif isinstance(command_to_execute, list) and shell_mode:
                command_to_execute = subprocess.list2cmdline(command_to_execute)

            tui = bool(data.get("tui", False)) if isinstance(data, dict) else False
            response = manager.execute_command(command_to_execute, shell=shell_mode, env=env_overrides, tui=tui)
            if response.get("status") == "success" and wait_for:
                if wait_for == "output":
                    peek_resp = manager.get_output(peek=True, wait=True, timeout=timeout)
                    out_text = peek_resp.get("output", "")
                    if out_text:
                        response = {"status": "success", "message": "Command started; output available.", "output": out_text}
                    else:
                        extra = 0.5 if timeout is None else min(0.5, float(timeout))
                        deadline = time.time() + extra
                        while time.time() < deadline:
                            peek_resp2 = manager.get_output(peek=True)
                            out_text = peek_resp2.get("output", "")
                            if out_text:
                                response = {"status": "success", "message": "Command started; output available.", "output": out_text}
                                break
                            time.sleep(0.02)
                        else:
                            response = {"status": "timeout", "message": "No output before timeout."}
                elif wait_for == "exited":
                    st = manager.wait_status(wait_for="exited", timeout=timeout)
                    if st.get("status") == "timeout":
                        response = {"status": "timeout", "message": "Command did not exit before timeout."}
                    else:
                        response = {"status": "success", "message": "Command exited.", "final_status": st.get("status"), "return_code": st.get("return_code")}
        elif action == "input":
            response = manager.send_input(data.get("text"))
            wait_output = bool(data.get("wait_for_output", False)) if isinstance(data, dict) else False
            if response.get("status") == "success" and wait_output:
                timeout = data.get("timeout") if isinstance(data, dict) else None
                o = manager.get_output(peek=False, wait=True, timeout=timeout)
                if o.get("status") == "timeout":
                    response = {"status": "timeout", "message": "No output before timeout.", "output": o.get("output", "")}
                else:
                    response = {"status": "success", "message": "Input sent; output received.", "output": o.get("output", "")}
        elif action == "get_output":
            peek = bool(data.get("peek", False)) if isinstance(data, dict) else False
            wait_flag = bool(data.get("wait", False)) if isinstance(data, dict) else False
            timeout = data.get("timeout") if isinstance(data, dict) else None
            pattern = data.get("pattern") if isinstance(data, dict) else None
            regex = bool(data.get("regex", False)) if isinstance(data, dict) else False
            since = data.get("since") if isinstance(data, dict) else None
            include_index = bool(data.get("include_index", False)) if isinstance(data, dict) else False
            response = manager.get_output(peek=peek, wait=wait_flag, timeout=timeout, pattern=pattern, regex=regex, since=since, include_index=include_index)
        elif action == "get_status":
            response = manager.get_status()
        elif action == "wait_status":
            wait_for = data.get("wait_for", "exited") if isinstance(data, dict) else "exited"
            timeout = data.get("timeout") if isinstance(data, dict) else None
            response = manager.wait_status(wait_for=wait_for, timeout=timeout)
        elif action == "stop":
            scope = data.get("scope", "process") if isinstance(data, dict) else "process"
            response = manager.stop_command(scope=scope)
        elif action == "graceful_stop":
            timeout = data.get("timeout", 3) if isinstance(data, dict) else 3
            scope = data.get("scope", "process") if isinstance(data, dict) else "process"
            response = manager.graceful_stop(timeout=timeout, scope=scope)
        elif action == "send_ctrl_event":
            ev = data.get("event", "BREAK") if isinstance(data, dict) else "BREAK"
            response = manager.send_ctrl_event(ev)
        elif action == "interrupt":
            policy = []
            timeout = None
            graceful_timeout = 3
            if isinstance(data, dict):
                policy = data.get("policy", []) or []
                timeout = data.get("timeout")
                graceful_timeout = data.get("graceful_timeout", 3)
            if not policy:
                policy = ["BREAK", "graceful", "stop"]
            start_time = time.time()
            def remaining():
                if timeout is None:
                    return None
                return max(0.0, float(timeout) - (time.time() - start_time))
            last_resp = {"status": "error", "message": "No policy steps executed."}
            for step in policy:
                step = str(step).lower()
                parts = step.split(":", 1)
                name = parts[0]
                step_scope = parts[1] if len(parts) > 1 else "process"
                if name in ("c", "break"):
                    last_resp = manager.send_ctrl_event("C" if name == "c" else "BREAK")
                elif name == "graceful":
                    t = graceful_timeout
                    if timeout is not None:
                        rem = remaining()
                        t = min(t, rem) if rem is not None else t
                    last_resp = manager.graceful_stop(timeout=t, scope=step_scope)
                elif name == "stop":
                    last_resp = manager.stop_command(scope=step_scope)
                st = manager.get_status()
                if st.get("status") in ("exited", "not_running"):
                    response = {"status": "success", "message": "Interrupted per policy.", "final_status": st.get("status"), "return_code": st.get("return_code")}
                    break
                if timeout is not None and remaining() == 0:
                    response = {"status": "timeout", "message": "Interrupt policy timed out."}
                    break
            else:
                response = last_resp
        elif action == "set_encoding":
            enc = data.get("encoding") if isinstance(data, dict) else None
            if not enc:
                response = {"status": "error", "error_code": "BAD_REQUEST", "message": "encoding is required"}
            else:
                response = manager.set_encoding(enc)
        elif action == "dump_output":
            since = None
            tail = None
            include_index = True
            if isinstance(data, dict):
                since = data.get("since")
                tail = data.get("tail")
                include_index = data.get("include_index", True)
            with manager.output_lock:
                full = "".join(manager.output_full_buffer)
                total_len = len(full)
                start = 0
                if isinstance(since, int) and since >= 0:
                    start = min(since, total_len)
                elif isinstance(tail, int) and tail >= 0:
                    start = max(0, total_len - tail)
                out = full[start:]
                response = {"status": "success", "output": out}
                if include_index:
                    response["index"] = total_len
                    response["start"] = start
        elif action == "clear_output":
            clear_all = bool(data.get("all", False)) if isinstance(data, dict) else False
            with manager.output_lock:
                manager.output_buffer = []
                if clear_all:
                    manager.output_full_buffer = []
            response = {"status": "success", "message": "Output cleared."}
        elif action == "close_stdin":
            if manager.process and manager.process.stdin:
                try:
                    manager.process.stdin.close()
                    response = {"status": "success", "message": "stdin closed."}
                except Exception as e:
                    response = {"status": "error", "message": str(e)}
            else:
                response = {"status": "not_running", "message": "No command running or stdin unavailable."}
        else:
            response = {"status": "error", "error_code": "UNKNOWN_ACTION", "message": "Unknown action."}
        return response

    if args.fs_bridge:
        base = args.fs_bridge
        in_dir = os.path.join(base, 'in')
        out_dir = os.path.join(base, 'out')
        os.makedirs(in_dir, exist_ok=True)
        os.makedirs(out_dir, exist_ok=True)
        # Polling loop
        while True:
            try:
                files = [f for f in os.listdir(in_dir) if f.endswith('.json')]
                files.sort()
                if not files:
                    time.sleep(max(0.0, float(args.fs_interval)))
                    continue
                for fname in files:
                    in_path = os.path.join(in_dir, fname)
                    try:
                        with open(in_path, 'r', encoding='utf-8') as rf:
                            content = rf.read()
                        try:
                            request = json.loads(content)
                        except json.JSONDecodeError as e:
                            response = {"status": "error", "error_code": "JSON_DECODE", "message": f"Invalid JSON input: {e}"}
                        else:
                            response = handle_request(request)
                        out_path = os.path.join(out_dir, fname)
                        with open(out_path, 'w', encoding='utf-8') as wf:
                            wf.write(json.dumps(response, ensure_ascii=False))
                    finally:
                        try:
                            os.remove(in_path)
                        except Exception:
                            pass
            except KeyboardInterrupt:
                break
            except Exception:
                # Avoid tight crash loop
                time.sleep(0.1)
    else:
        while True:
            try:
                line = sys.stdin.readline()
                if not line:
                    break
                try:
                    request = json.loads(line)
                except json.JSONDecodeError as e:
                    response = {"status": "error", "error_code": "JSON_DECODE", "message": f"Invalid JSON input: {e}"}
                    sys.stdout.write(json.dumps(response, ensure_ascii=False) + os.linesep)
                    sys.stdout.flush()
                    continue
                response = handle_request(request)
                sys.stdout.write(json.dumps(response, ensure_ascii=False) + os.linesep)
                sys.stdout.flush()
            except Exception as e:
                sys.stdout.write(json.dumps({"status": "error", "error_code": "INTERNAL", "message": str(e)}, ensure_ascii=False) + os.linesep)
                sys.stdout.flush()

if __name__ == "__main__":
    main()
