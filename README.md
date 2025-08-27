# interactive-cli-manager
対話型CLIをAIエージェントから操作するための小さなブリッジ。STDIN/STDOUTとFSブリッジ（in/outのJSON）に対応（Windows/Unix）。

対話型CLIをAIエージェントから操作するための小さなブリッジです。  
- ✅ **標準入出力モード** と **FSブリッジ（in/out JSON）** の二刀流
- ✅ Windows/Unix 両対応、プロンプト検知・割り込み送出対応
- ✅ AIが扱いやすい **JSON API**（execute / input / get_output / stop など）

任意コマンド実行を扱います。隔離環境（コンテナ/VM）推奨

## Quick Start (FSブリッジ)
```bash
python interactive_cli_manager.py --fs-bridge fs_bridge
# 送信例（Pythonのバージョン表示）
python fs_send.py "{\"action\":\"execute\",\"data\":{\"command\":[\"python\",\"-V\"],\"wait_for\":\"exited\",\"timeout\":10}}"
