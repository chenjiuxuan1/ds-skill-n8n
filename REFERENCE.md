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

## 标准 webhook body

```json
{
  "source": "codex-skill",
  "country": "cn",
  "action": "list_workflows",
  "ds_token": "user-provided-token",
  "request_id": "20260610-001",
  "payload": {
    "project_code": "",
    "workflow_code": "",
    "workflow_name": "",
    "instance_id": "",
    "start_node_list": "",
    "schedule_time": "",
    "state_type": "",
    "search_val": "",
    "page_no": 1,
    "page_size": 20,
    "custom_params": {}
  }
}
```

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
- `disable_task`
- `disable_tasks_except`
- `delete_task`
- `dump_workflow_graph`

## 修改类动作的前置校验

以下动作都属于“整包更新 workflow definition”：

- `append_task`
- `append_sql_task`
- `append_shell_task`
- `delete_task`
- `disable_task`
- `disable_tasks_except`

因此在执行前必须先检查：

1. 工作流中的任务脚本是否仍引用工作流级变量
2. 工作流定义中的 `globalParams / globalParamList / globalParamMap` 是否完整

重点关注的高风险变量：

- `src`
- `db`
- `dt`
- `full`
- `partition`
- `complement`

如果任务脚本还引用了 `${src}`、`${db}`、`${dt}`、`${full}` 等变量，但工作流级参数已经为空：

- 禁止继续执行修改类动作
- 先恢复 `t_ds_workflow_definition_log` 中历史版本的 `global_params`
- 恢复完成后再做下线、删除或新增

典型故障现象：

- 任务日志出现 `--src= --db= --dt= --full=`
- 同步任务报 `get table setting error,no data`

## 动作与字段

### `list_projects`

可选：
- `page_no`
- `page_size`
- `search_val`

### `list_workflows`

可选：
- `project_code`
- `page_no`
- `page_size`
- `search_val`

### `get_workflow`

必填其一：
- `workflow_code`
- `workflow_name`

可选：
- `project_code`

### `online_workflow`

必填：
- `workflow_code`

可选：
- `project_code`

### `offline_workflow`

必填：
- `workflow_code`

可选：
- `project_code`

### `trigger_workflow`

必填：
- `workflow_code`

可选：
- `project_code`
- `start_node_list`
- `schedule_time`
- `custom_params`

### `list_instances`

可选：
- `project_code`
- `state_type`
- `page_no`
- `page_size`
- `search_val`

### `get_instance`

必填：
- `instance_id`

可选：
- `project_code`

### `dump_workflow_graph`

必填：
- `workflow_code`

可选：
- `project_code`

返回重点：
- `workflow_summary`
- `task_definitions`
- `task_relations`
- `locations`

### `append_task`

推荐通用入口。

必填：
- `project_code`
- `workflow_code`
- `task_type`
- `task_name`
- `template_task_name`

按任务类型补充：
- `task_type = SQL`
  - `sql`
- `task_type = SHELL`
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

与 `append_task + task_type=SQL` 等价。

必填：
- `project_code`
- `workflow_code`
- `task_name`
- `sql`

推荐：
- `template_task_name`

可选：
- `sql_type`
- `upstream_task_name`
- `upstream_task_code`
- `restore_original_state`
- `auto_offline`

### `append_shell_task`

与 `append_task + task_type=SHELL` 等价。

必填：
- `project_code`
- `workflow_code`
- `task_name`
- `script`

推荐：
- `template_task_name`

可选：
- `upstream_task_name`
- `upstream_task_code`
- `restore_original_state`
- `auto_offline`

### `disable_task`

用于精确下线单个任务。

必填：
- `project_code`
- `workflow_code`
- `task_name` 或 `task_code`

可选：
- `restore_original_state`
- `auto_offline`

返回重点：
- `task_name`
- `task_code`
- `original_release_state`
- `original_schedule_release_state`
- `restored_original_state`
- `restored_original_schedule_state`

## `sql_type` 兼容规则

当前网关兼容以下写法：

| 输入 | 含义 |
|---|---|
| `0` | 查询型 SQL |
| `query` | 查询型 SQL |
| `select` | 查询型 SQL |
| `read` | 查询型 SQL |
| `1` | 执行型 SQL |
| `non_query` | 执行型 SQL |
| `non-query` | 执行型 SQL |
| `update` | 执行型 SQL |
| `write` | 执行型 SQL |
| `execute` | 执行型 SQL |

如果不显式传：
- 以 `select / with / show / desc / explain` 开头，默认 `0`
- 其他默认 `1`

## 返回格式

成功：

```json
{
  "success": true,
  "country": "mx",
  "action": "append_task",
  "request_id": "mx-add-001",
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
  "request_id": "mx-add-002",
  "data": null,
  "error": {
    "code": "INVALID_REQUEST",
    "message": "task_name is required"
  }
}
```

## 安全边界

- `ds_token` 必须由用户提供
- n8n 和远端网关只使用调用者提供的 token
- 不在 skill 中保存 token
- 不自动放大权限

## 当前不覆盖

- `create_workflow`
- `update_workflow` 的完整 DAG 设计器能力
- 资源中心文件上传
- 非 SQL / SHELL 的自动追加模板（如 PYTHON / SPARK / HTTP）
