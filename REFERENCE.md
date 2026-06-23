# DS Scheduler Reference

## 国家代码

| 国家 | code |
|---|---|
| 中国 | `cn` |
| 印尼 | `ine` |
| 墨西哥 | `mx` |
| 菲律宾 | `ph` |
| 巴基斯坦 | `pk` |
| 泰国 | `th` |

## 当前支持动作

- `list_projects`
- `list_workflows`
- `get_workflow`
- `online_workflow`
- `offline_workflow`
- `trigger_workflow`
- `list_instances`
- `get_instance`
- `retry_instance`
- `append_task`
- `append_sql_task`
- `append_shell_task`
- `disable_task`
- `disable_tasks_except`
- `delete_task`
- `dump_workflow_graph`

## 明确禁止的动作

以下动作不在 skill 支持范围内，并且应被明确拒绝：

- 删除项目
- 删除工作流

也就是说：

- 允许：`delete_task`
- 禁止：`delete_project`
- 禁止：`delete_workflow`

## token 使用规则

- `ds_token` 必须由用户自己提供
- 示例里的 `YOUR_DS_TOKEN` 只是占位符
- 不要把某个固定国家的真实 token 写进 skill、n8n 节点或示例文档
- 同一个动作在不同用户下的可见项目和可执行权限，取决于该用户 token 本身

## 标准 webhook body

```json
{
  "source": "codex-skill",
  "country": "mx",
  "action": "append_task",
  "ds_token": "user-provided-token",
  "request_id": "20260610-001",
  "payload": {
    "project_code": "13068695921632",
    "workflow_code": "174599383687393",
    "task_type": "SQL",
    "task_name": "测试2",
    "template_task_name": "dwd_okr_dashboard_wide_app",
    "sql": "select 2"
  }
}
```

## n8n 标准化后字段

`解析并标准化请求` 节点通常会额外产出：

- `payload_json`
- `payload_b64`
- `valid`
- `errors`

国家执行节点通常实际消费：

- `country`
- `action`
- `ds_token`
- `request_id`
- `payload_b64`

## 实例动作

### `retry_instance`

用于对失败工作流实例执行“失败任务重跑”。

最小 payload：

```json
{
  "project_code": "13068695921632",
  "instance_id": "2614176"
}
```

## 任务追加动作

### `append_task`

必填：
- `project_code`
- `workflow_code`
- `task_type`
- `task_name`
- `template_task_name`

按任务类型补充：
- SQL:
  - `sql`
- SHELL:
  - `script`

可选：
- `sql_type`
- `task_description`
- `datasource`
- `environment_code`
- `tenant_code`
- `upstream_task_name`
- `upstream_task_code`
- `restore_original_state`
- `auto_offline`

### `append_sql_task`

等价于 `append_task + task_type=SQL`

### `append_shell_task`

等价于 `append_task + task_type=SHELL`

### `delete_task`

按任务名或任务 code 删除工作流中的已有节点。

最小 payload：

```json
{
  "project_code": "13068695921632",
  "workflow_code": "175767388280714",
  "task_name": "dwd_ad_fb_campaing_get"
}
```

### `disable_task`

按任务名或任务 code 精确下线工作流中的已有任务节点，但不删除节点。

最小 payload：

```json
{
  "project_code": "13068695921632",
  "workflow_code": "13068714127712",
  "task_name": "ods_app_user"
}
```

可选：

- `task_code`
- `restore_original_state`
- `auto_offline`

说明：

- `disable_task` 适合“批量精确下线任务”
- 推荐逐条发送，避免前缀匹配误伤
- 如果需要保持工作流原有上下线状态，建议同时传：
  - `restore_original_state=true`
  - `auto_offline=true`
- 如果目标是删除节点而不是下线节点，应改用 `delete_task`

### `disable_tasks_except`

用于“保留白名单任务，其余批量下线”。

最小 payload：

```json
{
  "project_code": "13068695921632",
  "workflow_code": "17480254697952",
  "keep_task_names": [
    "ods_msgsvr_ivr_account",
    "ods_msgsvr_ivr_app_account"
  ]
}
```

## 固定操作模板：批量精确下线任务

当用户给出一组任务名，希望“全部下线但不要删除”时，推荐按下面固定模板操作：

1. 先查询这些任务分别位于哪些工作流
2. 确认每个命中的：
   - `project_code`
   - `workflow_code`
   - `task_name`
3. 对每一条命中记录逐条调用 `disable_task`
4. 最后再复查 `flag/version` 或在 DS UI 中确认节点已下线

推荐请求体：

```json
{
  "source": "codex-skill",
  "country": "mx",
  "action": "disable_task",
  "ds_token": "user-provided-token",
  "request_id": "mx-disable-exact-001",
  "payload": {
    "project_code": "13068695921632",
    "workflow_code": "13068714127712",
    "task_name": "ods_app_user",
    "restore_original_state": true,
    "auto_offline": true
  }
}
```

## `sql_type` 兼容

- 查询型：`0 / query / select / read`
- 执行型：`1 / non_query / non-query / update / write / execute`

说明：

- 当前 DS UI 中部分环境会显示为数字值，所以看到 `0` 是正常的
- 如果追加的是 SQL 任务，建议优先传语义化值 `query` 或 `execute`
- gateway 会统一做兼容转换
- 如果追加的是 SHELL 任务，应改用 `task_type=SHELL` 并传 `script`，不使用 `sql_type`

## 返回格式

成功：

```json
{
  "success": true,
  "country": "mx",
  "action": "dump_workflow_graph",
  "request_id": "mx-001",
  "data": {},
  "error": null
}
```

## 安全边界

- `ds_token` 必须由用户提供
- n8n 和远端网关只使用调用者提供的 token
- 允许删除任务节点
- 禁止删除项目
- 禁止删除工作流

失败：

```json
{
  "success": false,
  "country": "mx",
  "action": "append_task",
  "request_id": "mx-002",
  "data": null,
  "error": {
    "code": "INVALID_REQUEST",
    "message": "unsupported action: append_task"
  }
}
```
