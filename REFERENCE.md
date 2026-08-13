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
    "process_instance_id": "",
    "task_instance_id": "",
    "task_name": "",
    "task_code": "",
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
- `resolve_project`
- `list_alert_groups`
- `list_workflows`
- `create_workflow`
- `list_schedules`
- `get_schedule`
- `create_schedule`
- `update_schedule`
- `batch_update_schedule_alerts`
- `online_schedule`
- `offline_schedule`
- `schedule_blast_radius`
- `get_workflow`
- `online_workflow`
- `offline_workflow`
- `trigger_workflow`
- `list_instances`
- `get_instance`
- `list_task_instances`
- `get_task_log`
- `retry_instance`
- `stop_instance`
- `force_fail_instance`
- `check_failed_instances`
- `append_task`
- `append_sql_task`
- `append_shell_task`
- `update_task`
- `update_sql_task`
- `update_shell_task`
- `disable_task`
- `disable_tasks_except`
- `delete_task`
- `dump_workflow_graph`
- `list_datasources`
- `get_datasource`
- `extract_task_runtime_config`
- `list_resources`
- `view_resource_file`
- `search_resource_sql`
- `find_resource_usage`
- `search_country_git_sql`

### `resolve_project`

必填其一：
- `project_code`
- `project_name`

按名称解析时只接受唯一精确匹配；无匹配返回 `PROJECT_NOT_FOUND`，名称
歧义返回 `AMBIGUOUS_PROJECT`。

### `stop_instance`

必填：
- `project_code`
- `instance_id`

只调用 DolphinScheduler 官方 `executeType=STOP`。操作前读取实例状态，
已停止时幂等成功，完成态实例返回 `INVALID_INSTANCE_STATE`。

### `force_fail_instance`

必填：
- `project_code`
- `instance_id`

仅使用国家配置中已验证的官方 API 映射。未配置或官方不支持时返回
`UNSUPPORTED`；不会修改 DS 元数据库，也不会降级成停止。

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

### `list_schedules`

必填：
- `project_code`

可选：
- `workflow_code`
- `schedule_id`
- `page_no`
- `page_size`
- `search_val`

### `get_schedule`

必填：
- `project_code`

必填其一：
- `schedule_id`
- `workflow_code`
- `workflow_name`

### `create_schedule`

必填：
- `project_code`
- `workflow_code`

至少提供其一：
- `schedule_json`
- `crontab`

常用可选：
- `start_time`
- `end_time`
- `timezone_id`
- `warning_type`
- `warning_group_id`
- `failure_strategy`
- `process_instance_priority`
- `worker_group`
- `tenant_code`
- `environment_code`
- `custom_params`

### `update_schedule`

必填：
- `project_code`

必填其一：
- `schedule_id`
- `workflow_code`

至少提供一类变更：
- 定时字段：`schedule_json` 或 `crontab`
- 告警字段：`warning_type` 或 `warning_group_id`

只提供告警字段时，网关会读取原始定时并完整保留 `schedule`、起止时间、时区、失败策略、优先级、worker group、tenant、environment、start params 和 `releaseState`。更新后会回查；验证失败时自动按原快照恢复。

`warning_type` 仅允许：`NONE / SUCCESS / FAILURE / ALL`。

### `list_alert_groups`

可选：
- `search_val`
- `page_no`
- `page_size`

传 `search_val` 时按 `group_name` 精确匹配。无匹配返回 `ALERT_GROUP_NOT_FOUND`，同名多条返回 `AMBIGUOUS_ALERT_GROUP`，禁止自动选择。

### `batch_update_schedule_alerts`

必填：
- `project_names`：唯一、非空项目名数组
- `warning_type`
- `warning_group_name`

状态条件固定为：
- `workflow_release_state=ONLINE`
- `schedule_release_state=ONLINE`

可选：
- `dry_run`：默认 `true`
- `retry_attempts`：默认 2，范围 1–5
- `retry_delay_ms`：默认 250，范围 0–10000
- `rate_limit_ms`：默认 100，范围 0–10000

服务端实时解析本国项目 code 和本国告警组 ID；任何项目或告警组缺失/歧义都会使该国家在零写入状态结束。结果状态包括：
- `DRY_RUN_MATCHED`
- `UPDATED`
- `SKIPPED_ALREADY_MATCHED`
- `SKIPPED_NOT_ONLINE`
- `FAILED_UNCHANGED`
- `FAILED_ROLLED_BACK`
- `VERIFICATION_FAILED_ROLLED_BACK`
- `FAILED_ROLLBACK_FAILED`

汇总字段：`total / matched / updated / skipped / failed / verification_failed / rolled_back / rollback_failed`。每个可修改项返回不含 token 的 `rollback_payload`。

### rollback payload

`rollback_payload` 由网关从更新前快照生成，字段为：

`country / project_code / workflow_code / schedule_id / schedule_json / warning_type / warning_group_id / failure_strategy / process_instance_priority / worker_group / tenant_code / environment_code / release_state / start_params`。

可用 `build_ds_webhook_payload.py --action update_schedule --rollback-payload-json '<完整 JSON>'` 构建恢复请求。构建器拒绝未知字段、国家不一致或包含额外敏感字段的 payload。

构建器默认不在 stdout 回显真实 token。打印的 JSON 使用 `<DS_TOKEN>`；打印的 curl 使用 `${DS_TOKEN:?set DS_TOKEN}`，执行前应从安全输入或密钥管理器注入环境变量，禁止把 token 写入命令历史或日志。

### `online_schedule`

必填：
- `project_code`

必填其一：
- `schedule_id`
- `workflow_code`

### `offline_schedule`

必填：
- `project_code`

必填其一：
- `schedule_id`
- `workflow_code`

### `schedule_blast_radius`

必填：
- `project_code`
- `workflow_code`

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

### `list_task_instances`

必填：
- `project_code`

必填其一：
- `process_instance_id`
- `instance_id`

可选：
- `page_no`
- `page_size`
- `state_type`
- `search_val`

### `get_task_log`

必填：
- `project_code`

推荐直接提供：
- `task_instance_id`

也支持通过以下组合自动定位：
- `process_instance_id` 或 `instance_id`
- `task_name` 或 `task_code`

返回重点：
- `task_instance_id`
- `process_instance_id`
- `task_name`
- `task_code`
- `state`
- `host`
- `log_path`
- `log_endpoint_used`
- `log`

### `retry_instance`

必填：
- `project_code`
- `instance_id`

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

### `list_datasources`

可选：
- `page_no`
- `page_size`
- `search_val`

### `get_datasource`

必填其一：
- `datasource`
- `datasource_id`

### `extract_task_runtime_config`

必填：
- `project_code`
- `workflow_code`

必填其一：
- `task_name`
- `task_code`

### `list_resources`

用于查看资源中心某个目录下的文件 / 文件夹列表。

可选：
- `resource_type`
  - 默认 `FILE`
  - 也支持 `UDF`
- `full_name`
- `resource_full_name`
- `current_dir`
- `resource_dir`
- `search_val`
- `page_no`
- `page_size`

默认行为：
- 如果没有传目录，网关会先调用 DS 的 `resources/base-dir`，然后从资源根目录开始列

### `view_resource_file`

用于读取资源中心单个文件内容。

必填其一：
- `full_name`
- `resource_full_name`
- `file_name`
- `resource_name`

可选：
- `resource_type`
  - 默认 `FILE`
- `current_dir`
- `resource_dir`
- `skip_line_num`
- `limit`

说明：
- 如果只传 `file_name` / `resource_name`，网关会先在当前目录里按名称解析出 `full_name`

### `search_resource_sql`

用于在资源中心文本文件里按 SQL 片段反查命中文件。

必填其一：
- `sql_query`
- `sql`

可选：
- `resource_type`
  - 默认 `FILE`
- `current_dir`
- `resource_dir`
- `file_name`
- `search_val`
- `max_results`
- `max_files`
- `content_limit`

说明：
- 这个动作会遍历资源树中的文本文件，并读取内容做标准化匹配
- 适合“我知道一段 SQL，想反查它在哪个资源文件里”

### `create_workflow`

用于在指定项目下创建一个空的 workflow definition。

必填：
- `project_code`
- `workflow_name`

可选：
- `description`
- `tenant_code`
- `execution_type`
- `global_params`
- `timeout`

默认行为：
- 创建空 workflow，不自动创建任务
- `taskDefinitionJson = []`
- `taskRelationJson = []`
- `locations = []`
- `execution_type` 默认 `PARALLEL`
- `global_params` 默认 `[]`
- `timeout` 默认 `0`

返回重点：
- `workflow_name`
- `workflow_code`
- `project_code`
- `execution_type`
- `timeout`
- `create_result`

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
- `task_description`
- `upstream_task_name`
- `upstream_task_code`
- `restore_original_state`
- `auto_offline`

### `update_task`

必填：
- `project_code`
- `workflow_code`

必填其一：
- `task_name`
- `task_code`

常用可选：
- `task_description`
- `sql`
- `script`
- `sql_type`
- `datasource`
- `datasource_id`
- `local_params`
- `task_local_params`
- `replace_local_params`
- `resource_list`
- `resources`
- `replace_resource_list`
- `pre_statements`
- `post_statements`
- `task_params_patch`
- `environment_code`
- `tenant_code`
- `restore_original_state`
- `auto_offline`

SQL 任务附加可选：
- `title`
- `receivers`
- `receivers_cc`
- `show_type`
- `conn_params`

### `update_sql_task`

与 `update_task` 相同，但默认用于 SQL 任务。

至少提供其一：
- `sql`
- `task_params_patch`

必填：
- `project_code`
- `workflow_code`
- `task_name` 或 `task_code`

可选：
- `task_description`
- `sql_type`
- `datasource`
- `datasource_id`
- `local_params`
- `task_local_params`
- `replace_local_params`
- `resource_list`
- `resources`
- `replace_resource_list`
- `pre_statements`
- `post_statements`
- `task_params_patch`
- `environment_code`
- `tenant_code`
- `restore_original_state`
- `auto_offline`
- SQL 任务告警相关字段：
  - `title`
  - `receivers`
  - `receivers_cc`
  - `show_type`
  - `conn_params`

### `update_shell_task`

与 `update_task` 相同，但默认用于 SHELL 任务。

至少提供其一：
- `script`
- `task_params_patch.rawScript`

必填：
- `project_code`
- `workflow_code`
- `task_name` 或 `task_code`

可选：
- `task_description`
- `local_params`
- `task_local_params`
- `replace_local_params`
- `resource_list`
- `resources`
- `replace_resource_list`
- `task_params_patch`
- `environment_code`
- `tenant_code`
- `restore_original_state`
- `auto_offline`

### 自定义参数与资源字段说明

- `local_params` / `task_local_params`
  - 写入 `taskParams.localParams`
  - 既支持标准 DS 数组，也支持 `{ "biz_date": "${system.biz.date}" }` 这种对象简写
- `resource_list` / `resources`
  - 写入 `taskParams.resourceList`
  - 支持数组，元素可以是资源对象、资源 id，或资源名字符串
- `replace_local_params`
  - `true` 时整体替换原自定义参数
  - 默认 `false`，按 `prop` 合并
- `replace_resource_list`
  - 只在显式传了 `resource_list` / `resources` 时生效
  - 默认 `true`，按传入值整体替换原资源列表
  - 如需保留原资源并追加新资源，传 `false`
  - 如果用命令行 builder 生成请求，可加 `--merge-resource-list`

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
| `query` | 查询型 SQL |
| `select` | 查询型 SQL |
| `read` | 查询型 SQL |
| `查询` | 查询型 SQL |
| `non_query` | 执行型 SQL |
| `non-query` | 执行型 SQL |
| `非查询` | 执行型 SQL |
| `update` | 执行型 SQL |
| `write` | 执行型 SQL |
| `execute` | 执行型 SQL |
| `0` | 查询型 SQL，兼容旧写法 |
| `1` | 执行型 SQL，兼容旧写法 |

如果不显式传：
- 以 `select / with / show / desc / explain` 开头，默认按 `query` 处理
- 其他默认按 `non_query` 处理

说明：
- 面向 skill / webhook 的推荐写法是 `query` 或 `non_query`
- gateway 写回 DS taskParams 时会自动转换成 DS 兼容值
- SQL 任务如果传 `datasource` 名称，gateway 会优先解析成 datasource id 再写回，避免 DS 前端编辑页回填异常

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

- `update_workflow` 的完整 DAG 设计器能力
- 资源中心文件上传
- 非 SQL / SHELL 的自动追加模板（如 PYTHON / SPARK / HTTP）
