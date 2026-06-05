---
name: ds-scheduler
description: Route multi-country DolphinScheduler 3.4 workflow operations through an n8n webhook using standardized country-aware payloads, curl commands, and operator guidance. Use when users want to query, trigger, online, offline, or inspect DS workflows or instances for cn, ine, mx, ph, pk, or th.
---

# DS Scheduler

用于把 Codex 侧的调度操作请求，转换成标准化的 n8n webhook 请求。

## 何时使用

适用：
- 用户要操作 `CN / INE / MX / PH / PK / TH` 的 DS 调度
- 用户要做 `查询 / 上线 / 下线 / 触发 / 实例查询`
- 用户希望由 Codex 生成标准请求体、`curl` 命令和调用说明

不适用：
- 用户要直接从 Codex 调用 DS 内网 API
- 用户要第二版能力：完整新建/更新 workflow definition

## 第一版动作

- `list_workflows`
- `get_workflow`
- `online_workflow`
- `offline_workflow`
- `trigger_workflow`
- `list_instances`
- `get_instance`

## 必要输入

最少要确认：
- `country`：`cn / ine / mx / ph / pk / th`
- `action`
- `ds_token`

按动作补充：
- `workflow_code`
- `instance_id`
- `project_code`（可选，允许覆盖国家默认项目）
- `custom_params`
- `page_no / page_size / search_val / state_type`

## 工作流

1. 识别国家和动作
2. 校验动作所需字段
3. 生成标准 webhook payload
4. 生成可执行 `curl`
5. 说明哪些字段来自用户、哪些字段会由 n8n 补全

## 输出要求

默认输出：
- 识别结果：国家、动作
- 标准 JSON payload
- 可执行 `curl`
- 参数说明

如果 webhook 当前不可直接访问：
- 仍然输出 payload 和 `curl`
- 明确提示“需要在可达 n8n 的环境执行”

## 标准 webhook 契约

见 [REFERENCE.md](REFERENCE.md)

## 常见示例

见 [EXAMPLES.md](EXAMPLES.md)

## 辅助脚本

使用 [scripts/build_ds_webhook_payload.py](scripts/build_ds_webhook_payload.py) 生成标准 payload 与 `curl`。

## n8n 落地

n8n 侧路由模板与说明见：
- [n8n/README.md](n8n/README.md)
- [n8n/ds_scheduler_router.py](n8n/ds_scheduler_router.py)
