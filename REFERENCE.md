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
- `append_task`
- `append_sql_task`
- `append_shell_task`
- `dump_workflow_graph`

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

## `sql_type` 兼容

- 查询型：`0 / query / select / read`
- 执行型：`1 / non_query / non-query / update / write / execute`

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

