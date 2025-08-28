 # 対話型CLIマネージャー AI用ガイド（AGENTS.md）

 このガイドは、AIエージェントが`interactive_cli_manager.py`を正しく利用するための最小かつ実用的な説明です。標準入力/出力モードとファイルシステム（FS）ブリッジの両方に対応し、1行1JSONで指示・応答します。

 ## 概要
 - 目的: 任意のCLIプロセスを安全に起動・制御し、入出力を管理するゲートウェイ。
 - 対象スクリプト: `interactive_cli_manager.py`
 - 通信方式: 1行1JSON（UTF-8推奨）。
 - モード:
   - 標準（STDIN/STDOUT）: その場で1行JSONを送信→1行JSONで応答。
   - FSブリッジ: `in/*.json`に投入→処理→`out/*.json`に応答を書き出し。

 ## 起動方法
 - 標準モード: `python interactive_cli_manager.py`
 - FSブリッジ: `python interactive_cli_manager.py --fs-bridge [dir] --fs-interval 0.05`
   - `--fs-bridge`省略時は`./fs_bridge`を使用。
   - `--fs-interval`はポーリング間隔（秒）。
 - I/Oエコー: 既定で子プロセスの入出力を`stderr`にエコー。無効化は`--no-echo-io`。
 - TUI: 現在は未対応（エラーを返却）。

 ## リクエストの基本形
 - 送信: 1行のJSON（UTF-8、改行で区切る）。
 - 応答: 1行のJSON（必ず`status`を含む）。
 - 例（標準モードの実行開始）:
 ```json
 { "action": "execute", "data": { "command": "python --version" } }
 ```

 ## アクション一覧（要点と例）

 - execute: コマンド開始
   - 引数: `command`(str|list), `shell`(bool), `env`(obj), `tui`(bool/未対応), `wait_for`("output"|"exited"), `timeout`(秒)
   - 注意: パイプ/リダイレクト使用時は`shell:true`。文字列+`shell:false`は自動分割（Windowsはposix=False）。
   - 例:
 ```json
 { "action": "execute", "data": { "command": "ping 127.0.0.1 -n 2", "shell": true, "wait_for": "output", "timeout": 2 } }
 ```

 - input: 実行中プロセスへ文字列を送信
   - 引数: `text`(str), `wait_for_output`(bool), `timeout`(秒)
   - 例:
 ```json
 { "action": "input", "data": { "text": "help\n", "wait_for_output": true, "timeout": 1 } }
 ```

 - get_output: 出力取得（インクリメンタル/全文）
   - 引数: `peek`(bool), `wait`(bool), `timeout`(秒), `pattern`(str), `regex`(bool), `since`(int), `include_index`(bool)
   - ヒント: `since`は全体バッファのオフセット。`include_index`で次回の`since`に使う終端位置を受け取る。
   - 例（新規出力が来るまで待つ）:
 ```json
 { "action": "get_output", "data": { "wait": true, "timeout": 1 } }
 ```

 - get_status / wait_status: 状態取得/待機
   - `wait_status`引数: `wait_for`("running"|"exited"), `timeout`
   - 例:
 ```json
 { "action": "get_status" }
 { "action": "wait_status", "data": { "wait_for": "exited", "timeout": 5 } }
 ```

 - stop / graceful_stop: 強制/穏当終了
   - 引数: `scope`("process"|"group"), `timeout`(graceful_stopのみ)
   - 備考: Windowsは`taskkill /T /F`、POSIXは`SIGTERM`→必要に応じ`SIGKILL`。

 - send_ctrl_event: CTRLイベント送信
   - 引数: `event`("C"|"BREAK")
   - 備考: Windowsは`CTRL_C_EVENT`/`CTRL_BREAK_EVENT`、POSIXは`SIGINT`/`SIGTERM`相当。

 - interrupt: 中断ポリシー実行
   - 引数: `policy`(例: `["BREAK", "graceful", "stop"]`), `timeout`, `graceful_timeout`
   - 例:
 ```json
 { "action": "interrupt", "data": { "policy": ["BREAK", "graceful:group", "stop:group"], "timeout": 10 } }
 ```

 - set_encoding: 出力のデコードエンコーディング変更
   - 引数: `encoding`(str)
   - 例:
 ```json
 { "action": "set_encoding", "data": { "encoding": "utf-8" } }
 ```

 - set_output_limit: 全体バッファの上限
   - 引数: `max_chars`(int, 0=無制限)

 - clear_output: バッファクリア
   - 引数: `all`(bool) — trueで全文バッファも消去

 - close_stdin: 子プロセスの標準入力を閉じる

 ## FSブリッジの使い方（疎結合運用）
 1. 起動: `python interactive_cli_manager.py --fs-bridge fs_bridge`
 2. リクエスト: `fs_bridge/in/0001.json` などに1行JSON（ファイル本文はJSONの1本）
 3. 応答: 同名で `fs_bridge/out/0001.json` が生成される
 4. 例（実行要求のファイル本文）:
 ```json
 { "action": "execute", "data": { "command": "python --version" } }
 ```
 - 付属ツール: `fs_send.py`（1要求→1応答を簡易送受信）

 ## ベストプラクティス / 注意
 - シェル構文: パイプ/リダイレクト/ワイルドカードは`shell:true`。
 - 文字コード: UTF-8推奨。Windowsで文字化けする場合は`set_encoding`を使用。
 - 出力監視: 長時間待機は`wait:true`+`timeout`や`pattern`/`regex`併用で効率化。
 - 増分取得: `include_index:true`で返る`index`を次回`since`に指定すると差分取得が容易。
 - エコー制御: ログが冗長な場合は`--no-echo-io`でstderrエコーを無効化。
 - TUI: 現在未対応（`tui:true`はエラー応答）。

 ## よくある応答/エラー
 - `status: success|error|timeout`
 - 代表エラーコード: `JSON_DECODE`, `BAD_REQUEST`, `NOT_SUPPORTED`, `BROKEN_PIPE`, `INTERNAL`

 ## クイックレシピ
 - PowerShellでワンショット実行:
 ```powershell
 "{ \"action\": \"execute\", \"data\": { \"command\": \"python --version\" } }" |
 python interactive_cli_manager.py
 ```
 - 連続制御（例）:
   1) execute → 2) wait_status(exited) → 3) get_output(since/index活用)

 ---
 このAGENTS.mdはクイックマニュアルの要点を凝縮し、実装の挙動に合わせて加筆しています。詳細は`対話型CLIマネージャー AI用マニュアル.md`を参照してください。
