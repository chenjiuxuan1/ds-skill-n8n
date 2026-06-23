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
  - `retry_instance`
  - `dump_workflow_graph`
  - `append_task`
  - `append_sql_task`
  - `append_shell_task`
  - `disable_task`
  - `disable_tasks_except`
  - `delete_task`

## 当前架构

`Codex -> n8n Webhook -> 请求标准化 -> If(valid) -> 按国家分流 -> 各国 Execute Command(SSH 跳板机) -> /root/ds-scheduler-gateway/scripts/ds_scheduler_entry.py -> DS API -> 内容解析 -> Respond to Webhook`

## 使用前提

- 用户必须明确提供自己的 `ds_token`
- `ds_token` 代表的是用户本人在对应 DS 环境里的项目范围和操作权限
- 如果用户没有给 token，先提醒用户补充，再发正式请求
- 不要在 skill、n8n、示例代码里内置固定 token
- `country` 必须是 `cn / ine / mx / ph / pk / th` 之一
- 删除能力只允许到任务节点，不允许到项目或工作流层级

## 默认执行约束

- 这个 skill 不直接访问 DS API
- 这个 skill 负责构造或发送标准 webhook 请求
- 真正执行发生在 n8n 的国家节点里
- 各国家节点统一走跳板机上的 `/root/ds-scheduler-gateway`
- 如果用户只说“帮我查/帮我改”，但没有给 token，先提示：
  - “请提供你自己的 DS token，我会按你的权限范围操作”

## 关键点

- `ds_token` 必须由用户提供，且应使用用户自己的 token
- n8n 只做中转，不扩大权限，不保存公共高权限 token
- 各国节点统一执行 `/root/ds-scheduler-gateway/scripts/ds_scheduler_entry.py`
- `append_task` 是通用追加入口
- `append_sql_task` / `append_shell_task` 是特化入口
- `disable_task` 用于精确下线单个任务节点，但不删除节点
- `disable_tasks_except` 用于“白名单保留，其余批量禁用”
- `delete_task` 用于按 `task_name` 或 `task_code` 删除已有任务
- `retry_instance` 用于对失败实例执行失败任务重跑

## 固定模板：批量精确下线任务

当用户要“把一批指定任务下线，但不要删掉任务节点”时，统一使用 `disable_task`，不要误用 `delete_task`。

推荐固定流程：

1. 先按任务名定位任务所在工作流
2. 拿到每条命中的 `project_code / workflow_code / task_name`
3. 对每条任务逐条发送 `disable_task`
4. 如果用户要求“保持原工作流上下线状态”，在 payload 中显式传：
   - `restore_original_state=true`
   - `auto_offline=true`

适用场景：
- 批量关闭 ODS 白名单外任务
- 只下线节点，不删除 DAG
- 精确命中，不做前缀模糊批量误伤

不适用：
- 真正要删除节点时，这时才用 `delete_task`

## 强制安全边界

- 允许：删除任务节点 `delete_task`
- 禁止：删除项目
- 禁止：删除工作流
- 如果用户提出“删除项目”或“删除工作流”，直接拒绝，不构造 webhook
- 如果外部原始请求试图传入 `delete_project`、`delete_workflow` 或等价动作，n8n 应直接拦截

## 参考

- 协议与字段：[REFERENCE.md](REFERENCE.md)
- 示例：[EXAMPLES.md](EXAMPLES.md)
- n8n 节点说明：[n8n/README.md](n8n/README.md)
- 请求构造脚本：[scripts/build_ds_webhook_payload.py](scripts/build_ds_webhook_payload.py)
