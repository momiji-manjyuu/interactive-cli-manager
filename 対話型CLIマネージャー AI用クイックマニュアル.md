# 対話型CLIマネージャー AI用クイックマニュアル

目的: AIエージェントが対話型CLIを安全・確実に自動操作するための最小限ガイド。詳細は「対話型CLIマネージャー AI用マニュアル.md」を参照。

## 1) まずはこれ（最短クイックスタート）

- 通常モード（同一環境のAI/スクリプト向け）
  1. `python interactive_cli_manager.py` を起動（常駐）。
  2. 標準入力に「1行=1JSON」で送信、標準出力でJSON応答を受信。

- FSブリッジモード（サンドボックス・隔離環境のAI向け）
  1. ユーザー側で起動: `python interactive_cli_manager.py --fs-bridge`
  2. クライアントの推奨: `fs_send.py`（同梱）でJSONを安全投入
     - 例: `python fs_send.py "{\"action\":\"execute\",\"data\":{\"command\":[\"cmd\",\"/c\",\"echo\",\"HELLO\"],\"wait_for\":\"exited\",\"timeout\":10}}"`
     - `FS_BRIDGE_DIR` 環境変数でfsブリッジの場所を明示可能

ポイント: マネージャ本体はバックグラウンド起動可だが、対話対象のCLIは前景で起動し、API（`wait_status`/`get_output`/`interrupt`/`stop`）で制御する。既定で子プロセス入出力はstderrへエコーされます（無効化は `--no-echo-io`）。

## 2) よく使うアクション（最小セット）

- 実行（配列推奨）
  - `{ "action":"execute", "data": { "command":["cmd","/c","echo","OK"], "wait_for":"exited", "timeout":10 } }`
- 出力取得（差分/待機/パターン）
  - 差分: `{ "action":"get_output" }`
  - パターン待機: `{ "action":"get_output", "data": { "pattern":"ready", "wait":true, "timeout":30 } }`
- 入力送信（対話）
  - `{ "action":"input", "data": { "text":"yes", "wait_for_output":true, "timeout":10 } }`
- 状態
  - `{ "action":"get_status" }`, `{ "action":"wait_status", "data": { "wait_for":"exited", "timeout":60 } }`
- 停止・割り込み
  - 即停止: `{ "action":"stop" }`
  - ポリシー: `{ "action":"interrupt", "data": { "policy":["C","BREAK","graceful","stop"], "timeout":10 } }`
- 出力ダンプ/クリア
  - 全文: `{ "action":"dump_output" }`
  - 末尾Nバイト: `{ "action":"dump_output", "data": { "tail":2048 } }`
  - クリア: `{ "action":"clear_output", "data": { "all":true } }`

## 3) PowerShell利用の最短パターン（引用事故防止）

- 配列で渡す（推奨）
  - `["powershell","-NoProfile","-Command","Write-Output 'HELLO'"]`
- UTF-8統一（必要時）
  - `set_encoding`: `{ "action":"set_encoding", "data": { "encoding":"utf-8" } }`
  - コマンド先頭: `[Console]::OutputEncoding=[Text.Encoding]::UTF8; ...`
- 複雑な処理は `-File` で `.ps1` 実行に切替（JSON中の多重エスケープ回避）

【落とし穴】 `-Command` の文字列はJSON→呼び出しシェル→PowerShellの三重解釈で崩れやすい。`$var` をリテラルにしたい場合は `` `$var `` とする。

## 4) FSブリッジ用クライアント（強く推奨）

- `fs_send.py` の利点
  - リクエストIDの一意化・原子的ファイル投入（.tmp→rename）
  - タイムアウト付き待受・レスポンス自動削除
  - 使い方: `python fs_send.py '<json>' [timeout秒] [bridge_dir]`
- 例
  - 実行: `python fs_send.py "{\"action\":\"execute\",\"data\":{\"command\":[\"cmd\",\"/c\",\"echo\",\"FS_OK\"],\"wait_for\":\"exited\",\"timeout\":10}}" 30`
  - ダンプ: `python fs_send.py "{\"action\":\"dump_output\"}"`

## 5) 実運用の指針（短縮版）

- 状態管理: `get_status`/`wait_status`で遷移を監視（実行中→終了）。
- 出力解析: `pattern`/`regex`/`since`で確実にプロンプト/レディログを検出。
- タイムアウト: `execute.wait_for`/`get_output.wait`/`input.wait_for_output`に十分な余裕を。
- エンコーディング: 可能ならUTF-8へ統一（`set_encoding`＋シェル側設定）。
- セキュリティ: 危険コマンドの抑止、最小権限、機密は環境変数で。

## 6) よくある落とし穴と回避

- PowerShell `-Command` の引用/展開ミス → 配列で渡す／`-File`採用／シングルクォート＋内部''／変数は`` `$ ``でリテラル化。
- 対象CLIをバックグラウンド起動 → 入出力が不安定化。対象は前景、制御はAPIで。
- 無パターン`get_output`の待機 → 新規出力がなければ`timeout`。パターン/`since`の併用を。
- 長時間ジョブのログ肥大 → 定期`dump_output`＋`clear_output(all:true)`でローテーション。

## 7) エラーの読み方（抜粋）

- `ENOENT`: 実行ファイルが見つからない → PATH/コマンドを再確認
- `BAD_REQUEST`: 必須パラメータ不足 → リクエストを修正
- `UNKNOWN_ACTION`: action名の誤り
- `timeout`: 待機系（`wait_status`/`get_output.wait`/`input.wait_for_output`）のタイムアウト
- `INPUT_ERROR`/`BROKEN_PIPE`相当: 終了後に`input`送信など
- `NOT_SUPPORTED`: `tui:true` 指定など未対応

---
このクイック版で足りない場合は、詳細版マニュアル（AI用マニュアル.md）とレシピ集を参照してください。
