# interactive-cli-manager
対話型CLIをAIエージェントから操作するための小さなブリッジ。STDIN/STDOUTとFSブリッジ（in/outのJSON）に対応（Windows/Unix）。

対話型CLIをAIエージェントから操作するための小さなブリッジです。  
- ✅ **標準入出力モード** と **FSブリッジ（in/out JSON）** の二刀流
- ✅ Windows/Unix 両対応、プロンプト検知・割り込み送出対応
- ✅ AIが扱いやすい **JSON API**（execute / input / get_output / stop など）

## Install / Requirements
- Python 3.10+（Windows/Unix）
- 文字化け時は `{"action":"set_encoding","data":{"encoding":"cp932"}}` か `utf-8` に切替

## Safety Notes
任意コマンドを扱うため **VM/コンテナ等の隔離環境推奨**。`fs_bridge/in`（入力）/`fs_bridge/out`（出力）は公開しないこと。

## Quick Start (FSブリッジ)
```bash
python interactive_cli_manager.py --fs-bridge fs_bridge
# 送信例（Pythonのバージョン表示）
python fs_send.py "{\"action\":\"execute\",\"data\":{\"command\":[\"python\",\"-V\"],\"wait_for\":\"exited\",\"timeout\":10}}"
