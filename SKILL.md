---
name: ds-scheduler
description: Use the n8n-based DolphinScheduler gateway to inspect and operate multi-country DS 3.4 workflows and instances for cn, ine, mx, ph, pk, and th. Use when the user wants Codex to build or send standardized n8n webhook requests for listing projects/workflows, reading workflow or instance details, online/offline, trigger, dumping workflow DAG structure, or appending SQL/SHELL tasks through the country jump-host gateway.
---

# DS Scheduler

把 Codex 侧的调度请求，转换成标准化的 n8n webhook 调用，并通过各国跳板机上的 `ds-scheduler-gateway` 执行实际 DS API 操作。

## 何时使用

适用：
- 用户要通过 n8n 中转访问 DolphinScheduler 3.4
- 用户要操作 `cn / ine / mx / ph / pk / th`
- 用户要做：
  - `list_projects`
  - `list_workflows`
  - `get_workflow`
  - `online_workflow`
  - `offline_workflow`
  - `trigger_workflow`
  - `list_instances`
  - `get_instance`
  - `dump_workflow_graph`
  - `append_task`
  - `append_sql_task`
  - `append_shell_task`

## 当前架构

`Codex -> n8n Webhook -> 请求标准化 -> If(valid) -> 按国家分流 -> 各国 Execute Command -> 内容解析 -> Respond to Webhook`

## 关键点

- `ds_token` 必须由用户提供
- n8n 只做中转，不扩大权限
- 各国节点统一执行 `/root/ds-scheduler-gateway/scripts/ds_scheduler_entry.py`
- `append_task` 是通用追加入口
- `append_sql_task` / `append_shell_task` 是特化入口

## 参考

- 协议与字段：[REFERENCE.md](REFERENCE.md)
- 示例：[EXAMPLES.md](EXAMPLES.md)
- n8n 节点说明：[n8n/README.md](n8n/README.md)
- 请求构造脚本：[scripts/build_ds_webhook_payload.py](scripts/build_ds_webhook_payload.py)

