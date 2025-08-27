# 対話型CLIマネージャー AI用マニュアル

## はじめに

このマニュアルは、LangChainやReActフレームワークなどのAIエージェントフレームワークを使用するAIエージェントが、対話型コマンドラインインターフェース（CLI）ツールを効果的に操作するためのアプリケーション「対話型CLIマネージャー」の利用方法を説明します。従来のCLIツールは、その対話的な性質からAIエージェントによる自動化が困難な場合がありましたが、本アプリケーションは、AIエージェントがCLIツールの実行、入力の送信、出力の取得、および状態の監視をプログラム的に行えるようにすることで、この課題を解決します。

本アプリケーションは、Pythonで実装されており、標準入出力（stdin/stdout）を介してJSON形式のデータを受け渡しすることで、AIエージェントとの連携を可能にします。これにより、AIエージェントは、まるで人間がCLIツールを操作するかのように、対話的なプロセスを自動化し、より複雑なタスクを実行できるようになります。

このマニュアルでは、アプリケーションのセットアップから基本的な使い方、対話型CLIツールの操作、エラーハンドリング、そして高度な利用方法までを網羅的に解説します。AIエージェントが本アプリケーションを最大限に活用し、その能力を拡張するための手助けとなることを目的としています。

## モード選択（重要）
- ローカルLLM/同一マシンのスクリプト: 基本は「通常モード（STDIN/STDOUT直結）」を使用してください。必要な場合のみFSブリッジを起動します。
- サンドボックス/隔離環境のAI: 「FSブリッジモード」のみ利用可能です。ユーザーにFSブリッジの起動を依頼してください（`interactive_cli_manager.py --fs-bridge`）。
- FSブリッジの検出方法: クライアント（AI）は `fs_bridge/in` に疎通用のリクエスト（例: `{ "action":"get_status" }`）を書き込み、同名のレスポンスが `fs_bridge/out` に現れるかを待機（タイムアウト付き）することで起動確認ができます。ユーザーから「起動OK」の連絡をもらう運用でも構いません。

## セットアップ

「対話型CLIマネージャー」アプリケーションはPythonで記述されており、特別なライブラリのインストールは必要ありません。Python 3.10以降のバージョンがインストールされている環境であれば、すぐに利用を開始できます。

### 動作環境

本アプリケーションは、Windows環境での動作を想定して開発されています。LinuxやmacOS環境でも動作する可能性はありますが、一部の機能（特にプロセスの終了処理）はWindowsに特化した実装となっているため、予期せぬ動作が発生する可能性があります。

**エンコーディングについて:**

本アプリケーションは、CLIツールとの入出力において、システムのデフォルトエンコーディング（Windowsでは通称Shift-JIS（実体はcp932）、LinuxではUTF-8など）を使用します。これにより、日本語などのマルチバイト文字を含むCLIツールの出力も正しく処理されます。AIエージェントが本アプリケーションに送信する入力、および本アプリケーションから受け取る出力は、このシステムデフォルトエンコーディングで処理されることを前提とします。

### インストール

本アプリケーションは単一のPythonスクリプトファイル `interactive_cli_manager.py` として提供されます。以下の手順でセットアップを完了してください。

1.  `interactive_cli_manager.py` ファイルを任意のディレクトリに配置します。

    例：`C:\Users\YourUser\Documents\cli_manager\interactive_cli_manager.py`

2.  配置したディレクトリに移動します。

    ```bash
    cd C:\Users\YourUser\Documents\cli_manager
    ```

### 起動方法

アプリケーションは、Pythonインタープリタを使用して直接起動します。AIエージェントは、このプロセスに対して標準入出力を介してコマンドを送信し、応答を受け取ります。

```bash
python interactive_cli_manager.py
```

アプリケーションが起動すると、標準入力からのJSON形式のコマンドを待ち受け状態になります。AIエージェントは、このプロセスに対してJSON形式の文字列を送信することで、CLIツールの操作を開始できます。

**注意点:**

*   アプリケーションはバックグラウンドで実行され続けるため、AIエージェントが操作を終了する際には、明示的に `stop` アクションを送信するか、プロセスを終了させる必要があります。
*   複数のCLIツールを同時に操作したい場合は、本アプリケーションのインスタンスを複数起動する必要があります。各インスタンスは独立して動作します。

## 基本的な使い方：CLIツールの実行と出力の取得

本アプリケーションは、AIエージェントからのJSON形式のリクエストを受け取り、それに応じてCLIツールの実行、入力の送信、出力の取得、および状態の確認を行います。以下に、基本的な操作とそれに対応するJSONリクエストの形式を説明します。

### コマンドの実行 (`execute` アクション)

任意のCLIコマンドを実行するには、`execute` アクションを使用します。このアクションは、新しいCLIプロセスを開始し、その出力を監視します。既に別のコマンドが実行中の場合、そのコマンドは自動的に停止されます。

**リクエスト形式:**

```json
{
    "action": "execute",
    "data": {
        "command": ["<実行したいCLIコマンドのパスまたはコマンド名>", "<引数1>", "<引数2>", ...],
        "shell": false,               // オプション: シェル経由で実行するかどうか (デフォルト: false)
        "env": {"KEY": "VALUE"},     // オプション: 環境変数の上書き/追加（値nullで削除）
        "wait_for": "output|exited",  // オプション: 起動直後に待つ対象（最初の出力 or 終了）
        "timeout": 30                  // オプション: 上記待機のタイムアウト秒
    }
}
```

*   `command`: 実行したいCLIコマンドを文字列のリストで指定します。最初の要素はコマンドのパスまたはコマンド名、それ以降の要素は引数です。例えば、`["dir"]` や `["python", "--version"]` のように指定できます。スペースを含むパスや引数も、リストの要素として渡すことで正しく処理されます。
*   `shell`: `true` に設定すると、コマンドはシステムのシェル（Windowsでは`cmd.exe`、Linuxでは`bash`など）を介して実行されます。これにより、パイプ（`|`）やリダイレクト（`>`）などのシェル機能を利用できます。ただし、セキュリティリスクが増加するため、必要な場合にのみ使用し、`command` は文字列で指定してください。デフォルトは `false` です。
*   `env`: 実行時の環境変数を上書きできます。値を省略/`null`にすると該当キーを削除します。
*   `wait_for`/`timeout`: 起動直後に「最初の出力」または「終了」まで待機できます。長時間の処理に対しては適切な`timeout`を設定してください。

**`shell: true` を使用する場合のリクエスト形式（必要時のみ）:**

```json
{
    "action": "execute",
    "data": {
        "command": "<シェルで実行したいCLIコマンドを文字列で指定>",
        "shell": true
    }
}
```

この形式は、コマンドや引数にスペースが含まれる場合に、正しく解析されない可能性があります。可能な限りリスト形式を使用し、`shell: false` で実行することを推奨します。
ただし、Windowsのパイプ/リダイレクト（`|`, `>`, `>>` など）やPowerShellパイプラインを使う際は、`shell: true`で文字列コマンドとして渡してください。

**応答形式:**

コマンドが正常に開始された場合、以下のJSON応答が返されます。

```json
{
    "status": "success",
    "message": "Command started."
}
```

コマンドの開始に失敗した場合や、コマンドの解析に失敗した場合は、`status` が `error` となり、`message` にエラーの詳細が含まれます。

`wait_for:"exited"` 指定時は、終了を待ってから以下のように返します。

```json
{
  "status": "success",
  "message": "Command exited.",
  "final_status": "exited",
  "return_code": 0
}
```

【使いどころ】
- 最初の出力を待ってから次の操作に移る必要がある場合は`wait_for:"output"`を指定（対話プロンプトの安定検出に有効）。
- バッチ処理など完了を待つ場合は`wait_for:"exited"`＋`timeout`。
- 環境依存のCLIは`env`でPATHや設定を一時上書き。

### 出力の取得 (`get_output` アクション)

現在の標準出力/標準エラーを取得します。既定では取得時にバッファを消費しますが、`peek: true`で非消費読み取りが可能です。`wait: true`と`timeout`を指定すると、指定時間まで新しい出力を待機できます（タイムアウト時は`status: "timeout"`）。

```json
{"action":"get_output","data":{"peek":false,"wait":false,"timeout":10,"pattern":">>> ","regex":false,"since":0,"include_index":true}}
```

【使いどころ】
- 逐次ポーリングで取りこぼしたくない場合は`peek:true`で覗き見。
- プロンプト待ちなど「新規出力を待つ」用途には`wait:true`＋適切な`timeout`。
- 特定のプロンプトやキーワードが出るまで待つ場合は`pattern`/`regex`を活用（`since`と併用で差分領域だけ検索）。

【返却仕様の補足】
- `include_index:true`を指定すると、累積出力に対するオフセット情報を返します。
  - `index`: 取得時点の累積出力末尾位置（文字数）
  - `start`: 今回の`output`の開始オフセット（`since`未指定時は0）
- `since`を指定すると、`output`は未読バッファではなく累積出力の該当範囲（`start`以降）になります。
- `wait:true`で待機し、`timeout`に達して新規出力が到達しなかった場合は`status:"timeout"`かつ通常は`output:""`を返します（同時到達があれば到達分のみ返る場合があります）。

### 出力ダンプ/クリア (`dump_output`, `clear_output`)

プロセス開始以降の累積出力を取得/クリアします。`dump_output`は`since`または`tail`指定で部分取得が可能で、`index`（累積末尾位置）と`start`（今回の開始位置）を返します。`clear_output`は`all: true`で累積履歴も消去します。

```json
{"action":"dump_output"}
{"action":"dump_output","data":{"since": 12345}}
{"action":"dump_output","data":{"tail": 2048}}
{"action":"clear_output","data":{"all": true}}
```

【使いどころ】
- ログの継続取得には、初回`dump_output`の`index`を保存→以後`since`で差分だけ取得。
- エラー時の全文収集は`dump_output`（サイズ制限なし）。
- セッション切替や解析リセット時は`clear_output(all:true)`。

### エンコーディングの変更 (`set_encoding`)

入出力のテキストエンコーディング（デフォルトはOS既定）を動的に変更します。

```json
{"action":"set_encoding","data":{"encoding":"utf-8"}}
```

注記: `set_encoding` の変更は以降の入出力にのみ適用され、既存の累積出力は再解釈しません。

【運用の指針】
- まずは現状のコードページ/想定を確認（Windowsなら`chcp`、PowerShellなら`[Console]::OutputEncoding`）。
- 可能ならコンソール/シェル側をUTF-8に統一（例: `chcp 65001`、PowerShell先頭で`[Console]::OutputEncoding=[Text.Encoding]::UTF8;`）。
- 本マネージャー側も`set_encoding`でUTF-8へ統一（上記例）。
- それでも化ける場合は、ツール個別の出力エンコーディング（環境変数や設定）を再確認。

【使いどころ】
- CLI側の出力がUTF-8/Shift-JIS/UTF-16LEなどOS既定と異なる場合に切替。

### 状態待機 (`wait_status`)

`exited`または`running`まで待機します。タイムアウト時は`status: "timeout"`を返します。

```json
{"action":"wait_status","data":{"wait_for":"exited","timeout":120}}
{"action":"wait_status","data":{"wait_for":"running","timeout":10}}
```

【使いどころ】
- バッチ完了を待ってから次の`execute`へ進めたいときに。

## 対話型CLIツールの操作：プロンプトへの応答方法

多くのCLIツールは、ユーザーからの入力を必要とする対話型です。本アプリケーションは、このような対話型CLIツールに対して、AIエージェントがプログラム的に入力を送信できるように設計されています。

### 入力の送信 (`input` アクション)

実行中のCLIツールに対して入力を送信するには、`input` アクションを使用します。このアクションは、CLIツールがプロンプトを表示して入力を待っている場合や、特定の処理のためにユーザーからの情報が必要な場合に利用します。

**リクエスト形式:**

```json
{
    "action": "input",
    "data": {
        "text": "<送信したい入力テキスト>",
        "wait_for_output": false,
        "timeout": 30
    }
}
```

*   `text`: CLIツールに送信したいテキストを指定します。このテキストは、自動的に改行コード（Windowsの場合はCRLF、Linuxの場合はLF）が付加されて送信されます。

**応答形式:**

入力が正常に送信された場合、以下のJSON応答が返されます。

```json
{
    "status": "success",
    "message": "Input sent."
}
```

【動作の補足】
- `wait_for_output:true`を指定した場合、送信後に新規出力の到達を待機します。最初の到達（最小1文字）時点で解除し、到達分のみを`output`として返します（未読累積全体ではなく差分）。
- 既に未読バッファが存在する場合は、その差分が即時に返ります。
- `timeout`に達して新規出力が到達しなかった場合は、`status:"timeout"`に`output:""`（または到達分のみ）を返します。
- 改行付加: 送信文字列末尾にOS既定の改行（Windows: CRLF, POSIX: LF）を自動付加します。現状、この付加抑止や改行コードの明示指定はできません。

入力の送信に失敗した場合は、`status` が `error` となり、`message` にエラーの詳細が含まれます。

### 状態の確認 (`get_status` アクション)

実行中のCLIツールの現在の状態を確認するには、`get_status` アクションを使用します。これにより、CLIツールがまだ実行中であるか、または終了しているかを確認できます。

**リクエスト形式:**

```json
{
    "action": "get_status"
}
```

**応答形式:**

CLIツールの状態に応じて、以下のいずれかのJSON応答が返されます。

*   **実行中の場合:**

    ```json
    {
        "status": "running",
        "pid": <プロセスのPID>
    }
    ```

*   **終了している場合:**

    ```json
    {
        "status": "exited",
        "return_code": <終了コード>
    }
    ```

*   **コマンドが実行されていない場合:**

    ```json
    {
        "status": "not_running"
    }
    ```

### コマンドの停止 (`stop` アクション)

実行中のCLIツールを明示的に停止するには、`stop` アクションを使用します。これは、CLIツールが応答しなくなった場合や、AIエージェントがタスクを完了してプロセスを終了させたい場合に有用です。

**リクエスト形式:**

```json
{
    "action": "stop",
    "data": {"scope": "process|group"}
}
```

【使いどころ】
- 通常は`process`で個別停止。パイプや子をまとめて落としたい場合は`group`（POSIX）。Windowsは`taskkill /T`のため常にツリーを停止します。

**応答形式:**

コマンドが正常に停止された場合、以下のJSON応答が返されます。

```json
{
    "status": "success",
    "message": "Command stopped."
}
```

停止するコマンドがない場合は、`status` が `not_running` となります。

### 穏やかな停止と割り込み (`graceful_stop`, `send_ctrl_event`)

対話やビルドなど長い処理に対し、中断/安全終了を試みるアクションです。

- `graceful_stop`: Windowsでは`CTRL_BREAK_EVENT`を送出し、一定時間待機後も終了しない場合は強制停止します。POSIXでは`SIGTERM`→未終了時は`SIGKILL`相当。
- `send_ctrl_event`: 割り込みイベントを送出します。Windowsでは`event: "C"`でCtrl+C（`CTRL_C_EVENT`）、`"BREAK"`でCtrl+Break（`CTRL_BREAK_EVENT`）。POSIXでは`"C"`を`SIGINT`、`"BREAK"`を`SIGTERM`にマップします。

**リクエスト例:**

```json
{"action":"graceful_stop","data":{"timeout":5, "scope": "process|group"}}
{"action":"send_ctrl_event","data":{"event":"C"}}
{"action":"send_ctrl_event","data":{"event":"BREAK"}}
```

**注意（Windowsの制約）:**

- Ctrl+C/Breakは「コンソール制御イベント」です。同一コンソールに接続しているプロセス（グループ）にのみ送信できます。本アプリはWindowsで子プロセスを新しいプロセスグループとして起動しており、原則として送信可能です。
- 一部のツールはCtrl+Cを独自処理/無視する場合があり、期待通りに中断しないことがあります。その場合は`graceful_stop`や`stop`を併用してください。

### バックグラウンド起動に関する注意

`start /b`（Windows）や `&`（POSIXのシェル）で“対話対象のCLIツール”をバックグラウンド起動すると、標準入出力の結び付きが環境依存で変化し、以降の`input`/`get_output`が期待通りに機能しない場合があります。特にWindowsの`start /b`は新しいコンソールセッション扱いになる場合があるため、ツールは前景で起動し、制御は本マネージャーのAPI（`wait_for`/`wait_status`/`interrupt`/`stop`）で行ってください（“バックグラウンド推奨”はマネージャー本体の起動に限る）。

### ポリシー駆動の割り込み (`interrupt`)

割り込み手段の「順序」をポリシーで指定し、順次試行して停止させます。柔軟に現場のガイドラインを反映できます。

```json
{
  "action": "interrupt",
  "data": {
    "policy": [
      "C",
      "BREAK",
      "graceful",
      "graceful:group",
      "stop:group",
      "stop"
    ],
    "timeout": 10,
    "graceful_timeout": 3
  }
}
```

【使いどころ】
- Ctrl+Cをまず試し、効かない実行体にはCtrl+Break→穏やか停止→最終的に強制停止といった自組織の標準運用を明示化。
- パイプラインや子プロセスも含め確実に落としたい場合は`:group`を併用（POSIX）。

**使用例：対話型Pythonインタープリタの操作**

対話型Pythonインタープリタを操作する例を以下に示します。AIエージェントは、`get_output` を定期的に呼び出してプロンプトを監視し、必要に応じて `input` で応答を送信します。

1.  **Pythonインタープリタの起動:**

    ```json
    {
        "action": "execute",
        "data": {
            "command": ["python"]
        }
    }
    ```

2.  **プロンプトの確認と入力の送信:**

    AIエージェントは `get_output` を呼び出して、Pythonインタープリタのプロンプト（`>>>`）を確認します。プロンプトが表示されたら、コードを送信します。

    ```json
    {
        "action": "input",
        "data": {
            "text": "print(\'Hello from AI!\')"
        }
    }
    ```

3.  **出力の取得:**

    ```json
    {
        "action": "get_output"
    }
    ```

    （応答例）
    ```json
    {
        "status": "success",
        "output": ">>> print(\'Hello from AI!\')\nHello from AI!\n>>> "
    }
    ```

4.  **インタープリタの終了:**

    ```json
    {
        "action": "input",
        "data": {
            "text": "exit()"
        }
    }
    ```

5.  **最終出力の取得と状態確認:**

    ```json
    {
        "action": "get_output"
    }
    ```

    ```json
    {
        "action": "get_status"
    }
    ```
    （応答例）
    ```json
    {
        "status": "exited",
        "return_code": 0
    }
    ```

## エラーハンドリング

本アプリケーションは、CLIツールの実行中に発生する可能性のある様々なエラーや、AIエージェントからの不正なリクエストに対して、適切なエラー応答を返します。AIエージェントは、これらのエラー応答を解析し、適切な対応を取ることで、堅牢な自動化プロセスを構築できます。

### アプリケーション内部エラー

`interactive_cli_manager.py` 内部で予期せぬエラーが発生した場合、`status` が `error` となり、`message` フィールドにエラーの詳細が記述されたJSON応答が返されます。例えば、存在しないコマンドを実行しようとした場合や、プロセスの起動に失敗した場合などです。また、AIエージェントから送信されたJSONリクエストが不正な形式である場合も、JSON形式のエラー応答が返されるようになりました。

**応答例:**

```json
{
    "status": "error",
    "message": "[WinError 2] 指定されたファイルが見つかりません。"
}
```

**不正なJSON入力の応答例:**

```json
{
    "status": "error",
    "message": "Invalid JSON input: Expecting value: line 1 column 1 (char 0)"
}
```

AIエージェントは、`status` が `error` である応答を受け取った場合、`message` の内容を解析してエラーの原因を特定し、コマンドの再試行、代替コマンドの実行、またはユーザーへの通知などの適切なリカバリー処理を検討する必要があります。

### CLIツールからのエラー出力

実行中のCLIツールが標準エラー出力にメッセージを書き込んだ場合、それらのメッセージは `get_output` アクションで取得される出力に含まれます。本アプリケーションは、標準出力と標準エラー出力を区別せずに結合して返します。

AIエージェントは、取得した出力内容を解析し、エラーメッセージや警告が含まれていないかを確認する必要があります。例えば、特定のキーワード（"Error", "Failed", "Warning"など）を検索することで、CLIツール内部で発生した問題を検出できます。

**例：存在しないファイルへのアクセス**

```json
{
    "action": "execute",
    "data": {
        "command": ["type", "non_existent_file.txt"]
    }
}
```

`get_output` で取得される出力には、以下のようなエラーメッセージが含まれる可能性があります。

```json
{
    "status": "success",
    "output": "指定されたファイルが見つかりません。\n"
}
```

このように、CLIツール自体のエラーは `output` フィールドに含まれるため、AIエージェントは出力内容のセマンティックな解析を行う必要があります。

## 高度な使い方：複数のコマンドのシーケンス実行

本アプリケーションは、一度に一つのCLIツールとの対話を管理しますが、AIエージェントはこれらの基本的なアクションを組み合わせることで、より複雑なワークフローや複数のCLIコマンドのシーケンス実行を実現できます。

### 逐次実行

最も基本的なシーケンス実行は、一つのコマンドが完了した後に次のコマンドを実行する逐次実行です。これは、`execute` アクションでコマンドを開始し、`get_status` アクションでそのコマンドの終了を待機し、その後次の `execute` アクションを発行するというパターンで実現できます。

**例：複数のディレクトリを作成し、それぞれにファイルを作成する**

1.  **ディレクトリAの作成:**

    ```json
    {
        "action": "execute",
        "data": {
            "command": ["mkdir", "dir_A"]
        }
    }
    ```

2.  **`dir_A` の終了を待機:**

    AIエージェントは `get_status` を繰り返し呼び出し、`status` が `exited` になるのを待ちます。

    ```json
    {
        "action": "get_status"
    }
    ```

3.  **ディレクトリBの作成:**

    ```json
    {
        "action": "execute",
        "data": {
            "command": ["mkdir", "dir_B"]
        }
    }
    ```

4.  **`dir_B` の終了を待機:**

    同様に `get_status` で終了を待ちます。

5.  **`dir_A` にファイルを作成:**（シェルリダイレクトは`shell:true`で文字列として渡す）

    ```json
    {"action":"execute","data":{"command":"cmd /c echo Hello > dir_A\\file_A.txt","shell":true,"wait_for":"exited","timeout":10}}
    ```

このパターンでは、各ステップの完了を確実に待つことで、依存関係のあるコマンドを正確に実行できます。

### 対話型シーケンスの自動化

対話型CLIツールを自動化する場合、AIエージェントは `get_output` でプロンプトを検出し、`input` で応答を送信するというループを実装する必要があります。これにより、人間が手動で操作するのと同じように、CLIツールとの対話を自動化できます。

**例：対話型インストーラーの自動化**

多くのインストーラーは、インストールパスの確認、ライセンス同意、機能選択などのプロンプトを表示します。AIエージェントは、これらのプロンプトを `get_output` で読み取り、適切な応答（例: `y`, `Enter`, パス名など）を `input` で送信することで、インストールのプロセスを自動化できます。

1.  **インストーラーの起動:**

    ```json
    {
        "action": "execute",
        "data": {
            "command": ["setup.exe"]
        }
    }
    ```

2.  **対話ループ:**

    AIエージェントは、以下のようなループを実装します。

    *   `get_output` を呼び出し、CLIツールからの出力を取得します。
    *   取得した出力内容を解析し、既知のプロンプト（例: "Do you agree to the license terms? (y/n)"）を検出します。
    *   検出したプロンプトに基づいて、適切な応答を `input` で送信します。
    *   必要に応じて、`get_status` でインストーラーの終了を監視します。

このアプローチにより、AIエージェントは複雑な対話型プロセスを自律的にナビゲートし、完了させることが可能になります。

### タイムアウトとエラーからの回復

シーケンス実行や対話型自動化においては、CLIツールが予期せぬ応答を返したり、応答が途絶えたりする可能性があります。AIエージェントは、このような状況に対応するために、タイムアウト機構やエラーからの回復ロジックを実装することが重要です。

*   **タイムアウト:** `get_output`（`wait`/`timeout`）や`wait_status`、`execute.wait_for`、`input.wait_for_output`を使い、一定時間内に期待する応答が得られない場合にタイムアウトを発生させ、エラーとして処理します。
*   **再試行:** 一時的なエラー（例: ネットワークの問題）の場合、コマンドの再試行を試みます。
*   **代替パス:** 特定のエラーが発生した場合、別のコマンドや手順に切り替える代替パスを定義します。
*   **ユーザーへの通知:** AIエージェントが自動的に回復できない重大なエラーが発生した場合、人間のオペレーターに通知し、介入を促します。

これらの高度な戦略を組み合わせることで、AIエージェントはより堅牢で信頼性の高いCLI自動化ソリューションを構築できます。

## AI連携のベストプラクティス

本アプリケーションは、AIエージェントが対話型CLIツールを操作するための強力なブリッジを提供しますが、その能力を最大限に引き出すためには、AIエージェント側での適切な設計と実装が不可欠です。以下に、AIエージェントが本アプリケーションを効果的に利用するためのベストプラクティスを提案します。

### 1. 状態管理の徹底

CLIツールとの対話は、その性質上、状態を持つプロセスです。AIエージェントは、現在のCLIツールの状態（実行中か、終了したか、特定のプロンプトを待っているかなど）を常に把握し、それに基づいて次のアクションを決定する必要があります。`get_status` アクションを定期的に利用し、CLIツールの状態変化を監視することが重要です。

### 2. 出力解析のロバスト性

`get_output` アクションで取得されるCLIツールの出力は、AIエージェントが次に取るべきアクションを決定するための重要な情報源です。しかし、CLIツールの出力形式は多様であり、バージョンアップによって変化する可能性もあります。AIエージェントは、正規表現、キーワード検索、またはより高度な自然言語処理技術を用いて、出力から必要な情報を正確に抽出し、プロンプトを識別するためのロバストな解析ロジックを実装する必要があります。

*   **プロンプトの識別:** CLIツールがユーザー入力を待っていることを示す特定の文字列（例: `>`、`$`、`:`、`[Y/n]` など）を識別します。
*   **エラーメッセージの検出:** CLIツールからのエラーメッセージや警告（例: `Error:`, `Failed to`, `Warning:` など）を検出し、適切なエラーハンドリングを行います。
*   **情報の抽出:** コマンドの実行結果から、ファイルパス、設定値、ステータス情報など、AIエージェントが後続のタスクで必要とする情報を抽出します。

### 3. タイムアウトとリトライ戦略

CLIツールの応答が遅延したり、予期せぬフリーズが発生したりする可能性があります。AIエージェントは、これらの状況に対応するために、各アクション（特に `execute` や `input` の後）にタイムアウトを設定し、一定時間内に応答がない場合はエラーとして処理するか、リトライを試みるべきです。リトライ回数やリトライ間隔は、タスクの性質とCLIツールの特性に合わせて調整します。

### 4. エラー回復とフォールバック

予期せぬエラーが発生した場合に備え、AIエージェントはエラー回復戦略を事前に定義しておく必要があります。これには、以下のようなアプローチが含まれます。

*   **安全な終了:** エラー発生時にCLIツールを安全に終了させるために `stop` アクションを使用します。
*   **ログ記録:** エラーの詳細と発生時のコンテキストをログに記録し、デバッグや問題分析に役立てます。
*   **代替パス:** 特定のエラーに対して、別のコマンドや手順に切り替えるフォールバックメカニズムを実装します。
*   **人間へのエスカレーション:** AIエージェントが自動的に解決できない問題は、人間のオペレーターに通知し、介入を促します。

### 5. セキュリティの考慮
 
## 返却スキーマ（共通仕様）

- 共通フィールド:
  - `status`: `success` | `error` | `running` | `exited` | `not_running` | `timeout`
  - `message`: 任意の補足文字列（成功/エラー理由など）
  - `error_code`: 任意（エラー時）機械可読なコード（例: `ENOENT`, `JSON_DECODE`, `BROKEN_PIPE`, `UNKNOWN_ACTION`, `BAD_REQUEST`, `INTERNAL`）
- アクション別フィールド（代表）:
  - `execute`: 成功時 `message`。`wait_for:"exited"`指定時は `{status:"success", message, final_status:"exited", return_code}` を同梱
  - `input`: 成功時 `message`。`wait_for_output`指定時は `output`
  - `get_output`: `output`（文字列）。`wait`タイムアウト時は `status:"timeout"`＋`output:""`。`pattern`利用時は `matched`（bool）, `match_index`（一致先頭のオフセット、`include_index`と独立）を返す
  - `dump_output`: `output`、`index`（累積末尾位置）、`start`（返却開始位置）
  - `clear_output`: 成功時 `message`
  - `get_status`: `running`→`pid`、`exited`→`return_code`
  - `wait_status`: `exited`/`timeout`
  - `stop`/`graceful_stop`: 成功時 `message`
- `send_ctrl_event`/`interrupt`: 成功時 `message`。`interrupt`は終了確認後に `final_status` / `return_code` を付与

【シグナル/イベントの範囲（scope）】
- Windowsの`send_ctrl_event`はコンソール制御イベント（Ctrl+C/Break）を対象プロセス（グループ）に送ります。
- POSIXの`send_ctrl_event`はプロセスグループに送ります（`"C"`→`SIGINT`、`"BREAK"`→`SIGTERM`）。
- `stop`/`graceful_stop`は`scope:"process"|"group"`で停止範囲を選択可能（POSIX）。Windowsは常にツリー停止です。

注: 出力は標準出力/標準エラーの結合。サイズ制限は設けていません（ダンプは長大になる可能性があります）。
また、TUIは一時凍結中のため `tui:true` を指定した場合は `status:"error"` と `error_code:"NOT_SUPPORTED"` を返します。

## プロトコル仕様（I/O）

- 本アプリケーションは、標準入力で「1行に1メッセージ」のJSON文字列を受け取り、標準出力で「1行に1メッセージ」のJSONを返します。
- JSON本文に改行を含めたい場合は、JSON文字列内でエスケープ（例: `\n`）。
- 文字エンコーディングはOSの既定（Windows: 多くはShift-JIS/CP932やUTF-8, Linux/macOS: UTF-8）。`set_encoding`で動的に変更可能。

## トラブルシューティング / 運用Tips

- Ctrl+C/Breakが効かない:
  - GUIアプリやサービスプロセスにはコンソール制御イベントが届きません。`graceful_stop`→`stop`の順で停止を試行してください。
  - ツール側がCtrl+Cを独自ハンドリングしている場合があります。`interrupt`のポリシーで`BREAK`や`graceful`/`stop`を後段に用意してください。
- Windowsで文字化けする:
  - `shell:true`＋`cmd.exe`のとき、UTF-8を強制するには `"cmd /c chcp 65001 >NUL & <command>"` 形式を利用。
  - PowerShellでは `-NoProfile -Command "[Console]::OutputEncoding=[Text.Encoding]::UTF8; ..."` を先頭に付与するとUTF-8出力に統一できます。
  - 併せて本アプリを `{"action":"set_encoding","data":{"encoding":"utf-8"}}` でUTF-8に設定すると安定します。
- プロンプト待機の安定化:
  - 改行を出さないCLIは`get_output(wait:true)`だけだとすぐ返る場合があります。`pattern`で具体的なプロンプト文字列（例: `>>> `）を指定し、必要に応じて`since`で差分範囲に限定して検索してください。

## 実行モードの使い分け（通常モード / FSブリッジモード）

### 通常モード（標準入出力）

- 対象: ローカルでマネージャーとAI/スクリプトが同一マシン・同一セッションで動作し、標準入出力で直接JSONをやり取りできる場合。
- 起動: `python interactive_cli_manager.py`
- 利点: レイテンシ最小、実装が単純。
- 典型例: ローカルのLLM/スクリプトが直接このプロセスのSTDIN/STDOUTに書き込み/読み取りできる環境。

### FSブリッジモード（ファイルシステム経由）

- 対象: 本書のような隔離/サンドボックス環境のAIが、同一ワークスペースを共有しつつWindows側のCLIを操作したい場合。ネットワーク不要でプロセス制御が可能。
- 起動: `python interactive_cli_manager.py --fs-bridge fs_bridge`
  - 相対パス指定可（例: `fs_bridge` はカレント配下に作成）。
  - 値省略可: `python interactive_cli_manager.py --fs-bridge` とすると、デフォルトで `./fs_bridge` を使用します。
  - マネージャーは`fs_bridge/in`と`fs_bridge/out`を監視し、inに置かれたJSONファイルを1件ずつ処理し、同名ファイルをoutに出力します。

【プロトコル】
- 入力: `fs_bridge/in/<id>.json` に1件のJSONリクエスト（本マニュアルの各アクションと同スキーマ）。
- 出力: `fs_bridge/out/<id>.json` に1件のJSONレスポンス（同スキーマ）。
- 命名: `<id>`は一意であれば任意（時刻＋UUIDなど）。
- 例（実ファイル内容）:

```
// fs_bridge/in/1700000000000_abc.json
{"action":"execute","data":{"command":["cmd","/c","gemini"],"wait_for":"output","timeout":20}}

// fs_bridge/out/1700000000000_abc.json（マネージャーが生成）
{"status":"success","message":"Command started; output available.","output":"..."}
```

【リファレンス実装】
- 最小クライアント: `fs_send.py`
  - 1リクエストを`fs_bridge/in`へ書き出し、同名レスポンスを`fs_bridge/out`から取得する最小の送信用ユーティリティです（1行1JSON）。
- 参考クライアント: `fs_client.py`
  - 連続フロー（例: 起動→問い合わせ→ログダンプ→停止）をまとめて実行するデモ/検証用スクリプトです。なくても動作には影響しません。

【使いどころ】
- AIがWSL/コンテナ/クラウド側にあり、Windowsホストのプロセスに直接アクセスできないとき。
- ネットワーク経路を用意せず、共有ワークスペース（ファイル）だけで安全に中継したいとき。

【注意点】
- レイテンシ: 監視はポーリング（デフォルト約50ms）であるため、STDIN直結に比べわずかに遅延が増えます。
  - 起動オプション `--fs-interval <秒>` で変更可能（例: `--fs-interval 0.02`）。
- 競合回避: `<id>.json`単位で1リクエスト/1レスポンスを守り、同名ファイルの並行生成は避けてください。
- 競合時の挙動: `in`/`out`に同名ファイルがある場合の動作は未定義です（上書きの可能性あり）。クライアントは`<id>`を時刻＋UUIDなどで一意化してください。`in`ファイルは処理後にマネージャーが削除しますが、異常終了時に残ったファイルは手動でクリーンアップしてください。
- クリーンアップ: outファイルはクライアント側で読み取り後に削除されますが、異常終了時に残ることがあるため、適宜整理してください。
- セキュリティ: 入出力ディレクトリのアクセス権限を適切に管理し、機密情報を含むリクエスト/レスポンスの取り扱いに注意してください。

## TUI対応（将来拡張・一時凍結）

現時点ではTUIモードは提供を一時凍結しています（`execute.data.tui:true`は`NOT_SUPPORTED`を返します）。
将来的にPOSIXのPTY/WindowsのConPTYに基づく実装を再度提供予定です。それまでは以下の方法で代替してください。

- 非対話フラグ/バッチモードの利用（例: `-y`など）
- パイプ/リダイレクトによるワンショット実行（例: `cmd /c echo ... | tool` with `shell:true`）
- `pattern`/`wait`/`timeout`を活用した出力待機

## Gemini CLI連携の勘所（Tips）

- 検証の順序: まず`--version`と`--help`で配線確認→次にワンショット入力（`echo ... | gemini -y`）。
- `shell:true`活用: パイプ/リダイレクトを使う場合は、`{"shell":true, "command":"cmd /c echo ... | gemini -y"}`のように文字列で渡す。
- パス/起動ディレクトリ: FSブリッジでは`--fs-bridge`に絶対パスを渡すと確実。相対パスはCWDに依存。
- 引用（クォート）: JSON内の引用とシェルの引用が衝突しやすい。複雑な文章はPowerShell/`cmd /c`どちらかに統一し、埋め込む引用を最小化する。困ったら`fs_send.py`のようなクライアントを使用。
- タイムアウト: 起動や応答に時間がかかる場合がある。`wait_for:"exited"/"output"`と`timeout`を十分に長めに。
- 文字化け: 必要に応じて`set_encoding`でUTF-8に切り替え。PowerShellなら`[Console]::OutputEncoding=[Text.Encoding]::UTF8;`を先頭に。
- 警告（line buffering）: バイナリ通信で行バッファ指定の警告が出ることがあるが、既定バッファに変更済み（無視可）。

## エラーコード一覧

| error_code       | 意味/原因                                      | 代表的な発生タイミング                          | 推奨対応 |
|------------------|-----------------------------------------------|-----------------------------------------------|---------|
| ENOENT           | 実行ファイル/パスが見つからない                | `execute` で存在しないコマンドを指定           | コマンド/パスを見直す。`PATH`や`env`調整 |
| EXEC_ERROR       | 実行開始時の一般的エラー                        | `execute` 起動時の予期せぬ例外                 | コマンド引数/権限/環境を確認 |
| JSON_DECODE      | 入力JSONの構文エラー                            | 標準入力に不正JSONを送信                        | JSON整形を修正（1行1JSON） |
| BAD_REQUEST      | 必須パラメータ不足・リクエスト不備              | `set_encoding`等で必須キー欠落                  | リクエストのキー/値を補完 |
| UNKNOWN_ACTION   | 未知の`action`                                | action名のタイプミス/未実装API                 | 正しい`action`に修正 |
| BROKEN_PIPE      | 子プロセスの標準入力が閉じられた                | 子が終了/EOF受信後に`input`                     | 再実行/再起動、状態確認後に送る |
| INPUT_ERROR      | 入力処理の一般的エラー                          | `input` 実行時の例外                           | 入力内容や接続状態確認 |
| INTERNAL         | マネージャ内部の予期せぬ例外                    | どのアクションでも起こり得る                   | ログ/ダンプを採取し報告 |
| NOT_SUPPORTED    | 機能未対応（例: 現時点のTUIモード）             | `execute`で`tui:true`を指定                     | 代替手段（非対話フラグ/ワンショット）を利用 |

補足: タイムアウトは`status:"timeout"`で表現し、`error_code`は付与しません（状況に応じてリトライ/フォールバック）。

## CLIレシピ集

### 1) Windows cmd.exe のパイプ/リダイレクト

```json
{
  "action": "execute",
  "data": {"command": "echo HELLO | findstr H", "shell": true,
            "wait_for": "exited", "timeout": 10}
}
```

使いどころ: 簡易フィルタや`dir | findstr`などのワンライナー。文字化け対策が必要なら`chcp 65001`を先頭に。

### 2) PowerShell パイプライン

```json
{
  "action": "execute",
  "data": {"command": ["powershell", "-NoProfile", "-Command",
            "Get-ChildItem | Select-Object -First 1"],
           "wait_for": "exited", "timeout": 20}
}
```

### 3) Git ステータス（PATH補助つき）

```json
{
  "action": "execute",
  "data": {"command": ["git", "status"], "env": {"PATH": "%PATH%"},
            "wait_for": "exited", "timeout": 60}
}
```

使いどころ: PATHにGitが通っていない環境では`env.PATH`で明示。結果は`dump_output`で全文取得可能。

### 4) pip パッケージインストール（Python内蔵）

```json
{
  "action": "execute",
  "data": {"command": ["python", "-m", "pip", "install", "requests"],
            "wait_for": "exited", "timeout": 600}
}
```

使いどころ: 長時間かかる場合は`timeout`を十分長く。進捗は`get_output(peek:true)`で監視。

### 5) 7-Zip 展開（パスに空白あり）

```json
{
  "action": "execute",
  "data": {"command": ["7z", "x", "C:/path with space/archive.7z",
                         "-oC:/path with space/out"],
            "wait_for": "exited", "timeout": 300}
}
```

使いどころ: リスト形式で引数分割すれば、空白を含むパスも安全。

### 6) Python REPL 自動対話（改行なしプロンプト）

1) 起動とプロンプト待機（`>>> `まで）

```json
{"action":"execute","data":{"command":["python"]}}
{"action":"get_output","data":{"pattern": ">>> ", "wait": true, "timeout": 10}}
```

2) 入力と応答待ち

```json
{"action":"input","data":{"text":"print('hi')","wait_for_output": true, "timeout": 5}}
```

3) 終了

```json
{"action":"input","data":{"text":"exit()"}}
```

### 7) SSH ワンライナー実行（鍵認証前提）

```json
{
  "action": "execute",
  "data": {"command": ["ssh", "user@example.com", "ls -la"],
            "wait_for": "exited", "timeout": 60}
}
```

使いどころ: 対話パスワードが必要な構成ではハングし得るため、鍵認証/エージェント前提で利用。出力は`dump_output`で回収。

### 8) Python 仮想環境の作成と利用（Windows / POSIX）

- Windows（cmd.exe）

```json
{"action":"execute","data":{"command":"python -m venv venv && call venv\\Scripts\\activate && pip install -r requirements.txt","shell":true,"wait_for":"exited","timeout":600}}
```

- POSIX（bash）

```json
{"action":"execute","data":{"command":"python3 -m venv venv && . venv/bin/activate && pip install -r requirements.txt","shell":true,"wait_for":"exited","timeout":600}}
```

使いどころ: 同一シェルでの連続実行が必要なため`shell:true`を利用。以降のコマンドで仮想環境を使いたい場合は`env`で`PATH`を仮想環境の`bin`/`Scripts`を先頭に追加する運用も有効。

### 9) Webサーバの起動とログ行待機（パターン待ち）

```json
{"action":"execute","data":{"command":["python","-m","http.server","8080"]}}
{"action":"get_output","data":{"pattern":"Serving HTTP on","wait":true,"timeout":10}}
```

使いどころ: 起動完了メッセージ（例: "Listening on", "Started"）を`pattern`で待つと確実。

### 10) Docker: ビルドと起動→レディログ待機

```json
{"action":"execute","data":{"command":["docker","build","-t","myimg","."],"wait_for":"exited","timeout":1800}}
{"action":"execute","data":{"command":["docker","run","--rm","-p","8080:8080","myimg"]}}
{"action":"get_output","data":{"pattern":"ready","regex":true,"wait":true,"timeout":60}}
```

使いどころ: コンテナログに"ready"が出るまで待機してからテストを実行。

### 11) curlでJSON API呼び出し

```json
{"action":"execute","data":{"command":["curl","-sS","-H","Content-Type: application/json","-d","{\\\"q\\\":\\\"hello\\\"}","https://httpbin.org/post"],"wait_for":"exited","timeout":30}}
```

使いどころ: レスポンスは`dump_output`で全文取得。必要なら`pattern`で`"status":200`等を検出。

### 12) kubectl でPod一覧

```json
{"action":"execute","data":{"command":["kubectl","get","pods","-A"],"wait_for":"exited","timeout":30}}
```

使いどころ: コンテキスト/認証が済んでいる前提。失敗時は`error_code`や`output`を解析。

### 13) HuggingFace CLI ログイン（対話）

```json
{"action":"execute","data":{"command":["huggingface-cli","login"]}}
{"action":"get_output","data":{"pattern":"Token:","wait":true,"timeout":10}}
{"action":"input","data":{"text":"<YOUR_TOKEN>","wait_for_output":true,"timeout":10}}
```

使いどころ: 機密の取扱に注意。トークンは安全な経路で注入し、ログへの露出を避ける（`dump_output`の運用に留意）。

### 14) 学習ジョブの実行とログ追尾

```json
{"action":"execute","data":{"command":["python","train.py","--epochs","10"]}}
{"action":"dump_output"}
{"action":"dump_output","data":{"since":12345}}  // 前回index以降の追尾
```

使いどころ: 定期的に`dump_output`で差分だけ取得して外部にストリーミング。中断は`interrupt`でポリシーに沿って安全に停止。

### 15) SSH ポートフォワーディング（終了はポリシーで）

```json
{"action":"execute","data":{"command":["ssh","-N","-L","127.0.0.1:9000:localhost:9000","user@example.com"]}}
{"action":"get_output","data":{"wait":true,"timeout":2}} // 初期出力待ち（必要に応じて）
{"action":"interrupt","data":{"policy":["C","BREAK","graceful","stop"],"timeout":5}}
```

使いどころ: `-N`はフォアディング専用で長時間ブロック。終了は割り込みポリシーで柔軟に。

備考（今後の追加レシピ予定）

<!--
以下のレシピは今後の拡張候補です。必要になり次第、具体例と使いどころを追記します。

- Git: clone/pull/fetch、サブモジュール更新
- 7-Zip: 圧縮（zip/7z/tar.gz）、正規表現での一括圧縮
- 転送: scp/rsync（差分転送、帯域制限、再開）
- ダウンロード: curl/wgetでのDL＋SHA256ハッシュ検証
- 推論CLI: OpenAI/HuggingFace CLIでの推論呼び出しと結果パース
- Windows固有: chcp 65001やPowerShellのエンコーディング初期化テンプレ
- コンテナ/オーケストレーション: docker compose, kubectl rollout status 等
-->

本アプリケーションを通じてCLIツールを実行することは、システムに対して直接的な操作を行うことを意味します。AIエージェントは、悪意のあるコマンドの実行や、機密情報への不正アクセスを防ぐために、以下のセキュリティ対策を講じる必要があります。

*   **コマンドの検証:** AIエージェントが生成するコマンドは、実行前に検証し、許可されていない操作や危険なコマンドが含まれていないことを確認します。
*   **最小権限の原則:** 本アプリケーションを実行するユーザーアカウントは、必要最小限の権限のみを持つように設定します。
*   **機密情報の取り扱い:** パスワードやAPIキーなどの機密情報は、CLIツールの引数として直接渡すのではなく、環境変数や安全な設定ファイルを通じて管理することを検討します。

これらのベストプラクティスを適用することで、AIエージェントは「対話型CLIマネージャー」を最大限に活用し、複雑なCLI操作を自動化し、より高度なタスクを自律的に実行できるようになります。

## AIエージェントによるアプリケーションプロセスの管理

AIエージェントが「対話型CLIマネージャー」アプリケーションと連携する際、AIはアプリケーションのプロセスを「探す」のではなく、AI自身がそのプロセスを「起動」し、その起動したプロセスとの「通信チャネル」を管理します。これは、AIエージェントがサンドボックス環境内で利用可能なツールを通じて実現されます。

### 1. アプリケーションの起動と通信チャネルの確立

AIエージェントは、`shell_exec` ツールを使用して `interactive_cli_manager.py` スクリプトを起動します。この際、`session_id` を指定することで、そのスクリプトが実行されるシェルセッションを一意に識別し、そのセッションを通じてアプリケーションとの通信チャネルを確立します。

**例:**

```python
# AIエージェントが実行する擬似コード
print(default_api.shell_exec(
    brief="対話型CLIマネージャーを起動します。",
    command="python interactive_cli_manager.py",
    session_id="cli_manager_session", # このセッションIDが通信チャネルとなります
    working_dir="/home/ubuntu" # アプリケーションが配置されているディレクトリ
))
```

上記の `shell_exec` コールにより、`interactive_cli_manager.py` が `cli_manager_session` という名前のシェルセッション内で起動されます。AIエージェントは、以降のすべてのアプリケーション操作（コマンドの実行、入力の送信、出力の取得など）において、この `session_id` を指定することで、起動したアプリケーションインスタンスと通信します。

### 2. 起動したアプリケーションインスタンスへのコマンド送信

アプリケーションが起動し、通信チャネル（`session_id`）が確立された後、AIエージェントは `shell_input` ツールを使用して、JSON形式のコマンドをアプリケーションに送信します。この際も、必ず同じ `session_id` を指定します。

**例：`dir` コマンドの実行**

```python
# AIエージェントが実行する擬似コード
print(default_api.shell_input(
    append_newline=True,
    brief="dirコマンドを実行します。",
    input="{\"action\": \"execute\", \"data\": {\"command\": [\"dir\"]}}",
    session_id="cli_manager_session" # 起動時に指定したセッションIDと同じものを指定
))
```

### 3. アプリケーションからの応答の取得

アプリケーションからの応答（CLIツールの出力やステータスなど）は、同じ `session_id` を持つシェルセッションの標準出力に書き込まれます。AIエージェントは、`shell_view` ツールを使用してこのセッションの出力を監視し、アプリケーションからのJSON応答を読み取ります。

**例：出力の取得**

```python
# AIエージェントが実行する擬似コード
print(default_api.shell_input(
    append_newline=True,
    brief="CLIツールの出力を取得します。",
    input="{\"action\": \"get_output\"}",
    session_id="cli_manager_session"
))

# その後、shell_viewで出力を確認
print(default_api.shell_view(
    brief="セッションの出力を確認します。",
    session_id="cli_manager_session"
))
```

（プロトコル注意）上記の例は可読性のため複数行で表現していますが、実投入時は「1行に1つのJSON文字列」を送ってください。

### まとめ

AIエージェントは、`shell_exec` で「対話型CLIマネージャー」を起動する際に割り当てられる `session_id` を通じて、そのアプリケーションインスタンスと一対一で通信します。したがって、AIが「プロセスを探す」というよりは、AI自身がプロセスを「管理する」という理解が適切です。この `session_id` が、AIとアプリケーション間の専用の通信経路として機能します。

## 常駐型アプリケーションとAIエージェントの連携における注意点と対処方法

AIエージェントが「対話型CLIマネージャー」のような常駐型アプリケーションを操作する際、アプリケーションがAIの応答をブロックし、AIエージェントが停止してしまうという問題が発生する可能性があります。これは、AIエージェントがアプリケーションの終了を待機してしまうために起こります。このセクションでは、この問題の発生メカニズムと、それに対する対処方法を説明します。

### 問題の発生メカニズム

AIエージェントが `shell_exec` ツールを使用して `interactive_cli_manager.py` を起動すると、通常、`shell_exec` は実行したコマンドが終了するまで待機します。しかし、「対話型CLIマネージャー」は、AIエージェントからのリクエストを継続的に処理するために設計された常駐型アプリケーションであるため、自身では終了しません。このため、`shell_exec` が無限に待機状態となり、AIエージェントの次のアクションが実行されず、結果としてAIエージェントが停止したように見えてしまいます。

### 対処方法

この問題を回避し、AIエージェントが常駐型アプリケーションと円滑に連携できるようにするためには、以下のいずれかの方法を適用する必要があります。

#### 1. バックグラウンド実行（推奨）

最も推奨される方法は、`interactive_cli_manager.py` をシェルでバックグラウンド実行することです。これにより、`shell_exec` はアプリケーションの起動後すぐに制御をAIエージェントに返し、AIエージェントはブロックされることなく次のアクションに進むことができます。

**起動方法の変更:**

`shell_exec` の `command` 引数に、バックグラウンド実行を示す `&` を追加します。Windows環境では、`start /b` コマンドを使用することで、同様のバックグラウンド実行を実現できます。

注意: ここでの「バックグラウンド実行（推奨）」は“マネージャー本体”の起動に限ります。対話対象のCLIツールは前景で起動し、本マネージャーのAPI（`wait_for`/`wait_status`/`interrupt`/`stop`）で制御してください。特にWindowsの`start /b`はコンソール/セッションが変わる場合があり、ツールをバックグラウンド起動すると`input`/`get_output`の結び付きが不安定になることがあります。

```python
# AIエージェントが実行する擬似コード (Linux/macOSの場合)
print(default_api.shell_exec(
    brief="対話型CLIマネージャーをバックグラウンドで起動します。",
    command="python interactive_cli_manager.py &", # & を追加
    session_id="cli_manager_session",
    working_dir="/home/ubuntu"
))

# AIエージェントが実行する擬似コード (Windowsの場合)
print(default_api.shell_exec(
    brief="対話型CLIマネージャーをバックグラウンドで起動します。",
    command="start /b python interactive_cli_manager.py", # start /b を追加
    session_id="cli_manager_session",
    working_dir="C:\\Users\\YourUser\\Documents\\cli_manager" # Windowsパスの例
))
```

これにより、`shell_exec` は `interactive_cli_manager.py` のプロセスIDを返しますが、そのプロセスの終了を待つことはありません。AIエージェントは、この後すぐに `shell_input` や `shell_view` を使用してアプリケーションと通信を開始できます。

#### 2. アプリケーションの分離と専用通信チャネルの利用

より高度な解決策として、AIエージェントと常駐型アプリケーション間の通信を、標準入出力とは別の専用チャネル（例：TCPソケット、名前付きパイプ）に分離する方法があります。この場合、AIエージェントはアプリケーションを起動した後、その専用チャネルに接続し、そこを通じてコマンドの送受信を行います。

ただし、この方法は「対話型CLIマネージャー」アプリケーション自体の設計変更が必要となり、より複雑な実装が伴います。現在の `interactive_cli_manager.py` は標準入出力を前提としているため、このアプローチを採用する場合は、アプリケーションコードの改修が必要となります。

### 重要な考慮事項

*   **プロセス管理:** バックグラウンドで起動したアプリケーションは、AIエージェントが明示的に停止しない限り実行され続けます。タスクが完了した際には、`stop` アクションを送信するか、`shell_kill` ツールを使用してプロセスを終了させることを忘れないでください。これにより、リソースの無駄遣いを防ぎ、不要なプロセスが蓄積されるのを避けることができます。

    ```python
    # AIエージェントが実行する擬似コード：アプリケーションの停止
    print(default_api.shell_input(
        append_newline=True,
        brief="対話型CLIマネージャーを停止します。",
        input="{\"action\": \"stop\"}",
        session_id="cli_manager_session"
    ))

    # または、シェルセッションごと終了
    print(default_api.shell_kill(
        brief="対話型CLIマネージャーのシェルセッションを終了します。",
        session_id="cli_manager_session"
    ))
    ```

*   **エラー検出:** バックグラウンド実行の場合、アプリケーションの起動時にエラーが発生しても、`shell_exec` はすぐに成功を返してしまうため、AIエージェントは起動エラーを直接検出できません。アプリケーションが正常に起動したかどうかは、最初の `get_output` や `get_status` アクションの応答で確認する必要があります。

これらの対処方法を理解し適用することで、AIエージェントは常駐型アプリケーションを効果的に利用し、より複雑で継続的なタスクを自動化できるようになります。
