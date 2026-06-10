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
- `delete_task`
- `dump_workflow_graph`

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
