# interactive-cli-manager
対話型CLIをAIエージェントから操作するための小さなブリッジ。STDIN/STDOUTとFSブリッジ（in/outのJSON）に対応（Windows/Unix）。

対話型CLIをAIエージェントから操作するための小さなブリッジです。  
- ✅ **標準入出力モード** と **FSブリッジ（in/out JSON）** の二刀流
- ✅ Windows/Unix 両対応、プロンプト検知・割り込み送出対応
- ✅ AIが扱いやすい **JSON API**（execute / input / get_output / stop など）

## Install / Requirements
- Python 3.10+（Windows/Unix）
- 文字化け時は `{"action":"set_encoding","data":{"encoding":"cp932"}}` か `utf-8` に切替

## Quick Start (FSブリッジ)
```bash
python interactive_cli_manager.py --fs-bridge
# 送信例（Pythonのバージョン表示）
python fs_send.py "{\"action\":\"execute\",\"data\":{\"command\":[\"python\",\"-V\"],\"wait_for\":\"exited\",\"timeout\":10}}"
```


免責事項（Disclaimer）

日本語
本ソフトウェアは 現状のまま（AS IS） 提供され、いかなる明示または黙示の保証も行いません。本ソフトウェアの使用・誤用・不具合・セキュリティ事故等により発生した 損害・損失・トラブル について、作者は一切の責任を負いません。
本ツールは 任意コマンドの実行 を前提とするため、管理者権限での実行は避け、VM/コンテナ等の隔離環境 で使用してください。fs_bridge の共有ディレクトリには 秘密情報を置かない でください。
本プロジェクトは Google / OpenAI / xterm.js ほかいかなる企業・団体とも無関係 です。製品名・商標は各所有者に帰属します。

English
This software is provided “AS IS”, without warranty of any kind, express or implied. The author shall not be liable for any damages or issues arising from the use or misuse of this software, including but not limited to security incidents or data loss.
Because this tool can execute arbitrary commands, avoid running it with administrative privileges and prefer isolated environments (VM/containers). Do not place secrets in the fs_bridge directories.
This project is not affiliated with Google, OpenAI, or any other company. All product names and trademarks are the property of their respective owners.
