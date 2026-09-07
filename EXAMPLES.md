# Examples

## 0. 定时告警安全调整

先精确查询菲律宾本地告警组：

```bash
python3 scripts/build_ds_webhook_payload.py \
  --webhook-url "https://sql-cn.kuainiujinke.com/webhook/ds-scheduler" \
  --country ph \
  --action list_alert_groups \
  --ds-token "<DS_TOKEN>" \
  --search-val "n8n告警触发器" \
  --page-size 200
```

单项目 dry-run（不写 DolphinScheduler）：

```bash
python3 scripts/build_ds_webhook_payload.py \
  --webhook-url "https://sql-cn.kuainiujinke.com/webhook/ds-scheduler" \
  --country ph \
  --action batch_update_schedule_alerts \
  --ds-token "<DS_TOKEN>" \
  --project-names-json '["DW_DWB"]' \
  --workflow-release-state ONLINE \
  --schedule-release-state ONLINE \
  --warning-type FAILURE \
  --warning-group-name "n8n告警触发器" \
  --dry-run
```

查看 dry-run 后，正式批量必须显式增加 `--execute`。首次只能选一条命中记录，用 `update_schedule` 传 `project_code / schedule_id / warning_type / warning_group_id`，随后 `get_schedule` 回查并用响应中的 `rollback_payload` 恢复；恢复回查通过后才允许扩大范围。

构建器不会把传入 token 回显到 stdout：展示 JSON 使用 `<DS_TOKEN>`，生成的 curl 从环境变量读取。执行生成的 curl 前，在不被日志采集的安全终端中设置：

```bash
read -s DS_TOKEN && export DS_TOKEN
```

恢复时把响应中的完整 `rollback_payload` 作为 JSON 传入；下面只展示结构，值必须来自本次更新响应：

```bash
python3 scripts/build_ds_webhook_payload.py \
  --webhook-url "https://sql-cn.kuainiujinke.com/webhook/ds-scheduler" \
  --country ph \
  --action update_schedule \
  --ds-token "<DS_TOKEN>" \
  --rollback-payload-json '{"country":"ph","project_code":"<PROJECT_CODE>","workflow_code":"<WORKFLOW_CODE>","schedule_id":"<SCHEDULE_ID>","schedule_json":{"startTime":"<ORIGINAL>","endTime":"<ORIGINAL>","crontab":"<ORIGINAL>","timezoneId":"<ORIGINAL>"},"warning_type":"<ORIGINAL>","warning_group_id":"<ORIGINAL>","failure_strategy":"<ORIGINAL>","process_instance_priority":"<ORIGINAL>","worker_group":"<ORIGINAL>","tenant_code":"<ORIGINAL>","environment_code":"<ORIGINAL>","release_state":"<ORIGINAL>","start_params":"<ORIGINAL>"}'
```

不要手工推测 `<ORIGINAL>` 值；应直接复制网关返回的整个 `rollback_payload`。恢复请求成功后仍需调用 `get_schedule` 再次确认。

## 1. 查询中国工作流列表

```bash
python3 scripts/build_ds_webhook_payload.py \
  --webhook-url "https://sql-cn.kuainiujinke.com/webhook/ds-scheduler" \
  --country cn \
  --action list_workflows \
  --ds-token "YOUR_DS_TOKEN" \
  --project-code 158514956085248 \
  --page-no 1 \
  --page-size 20
```

## 2. 查询墨西哥工作流 DAG 结构

```bash
python3 scripts/build_ds_webhook_payload.py \
  --webhook-url "https://sql-cn.kuainiujinke.com/webhook/ds-scheduler" \
  --country mx \
  --action dump_workflow_graph \
  --ds-token "YOUR_DS_TOKEN" \
  --project-code 19427088052704 \
  --workflow-code 174599383687393
```

## 3. 触发中国工作流

```bash
python3 scripts/build_ds_webhook_payload.py \
  --webhook-url "https://sql-cn.kuainiujinke.com/webhook/ds-scheduler" \
  --country cn \
  --action trigger_workflow \
  --ds-token "YOUR_DS_TOKEN" \
  --workflow-code 158515019593728 \
  --custom-params-json '{"dt":"2026-06-10"}'
```

## 3.1 复制工作流为触发式（按需）

```bash
python3 scripts/build_ds_webhook_payload.py \
  --webhook-url "https://sql-cn.kuainiujinke.com/webhook/ds-scheduler" \
  --country ph \
  --action copy_workflow \
  --ds-token "YOUR_DS_TOKEN" \
  --project-code 15843450427744 \
  --workflow-code 15843450427744 \
  --workflow-name "DWD_5M_TRIGGER"
```

说明：

- `workflow-code` 是源工作流 code
- `workflow-name` 是新副本名称，需在项目内唯一
- 默认创建后立即上线（触发式工作流需 ONLINE 才能被 API 触发）；如需先离线可加 `--no-release-workflow`
- 副本不创建任何定时：`trigger_style=true`、`schedule_created=false`

## 4. 在空项目里创建一个空 workflow

```bash
python3 scripts/build_ds_webhook_payload.py \
  --webhook-url "https://sql-cn.kuainiujinke.com/webhook/ds-scheduler" \
  --country mx \
  --action create_workflow \
  --ds-token "YOUR_DS_TOKEN" \
  --project-code 177096834343936 \
  --workflow-name "codex_mx_empty_test_workflow" \
  --description "Created by Codex for DS scheduler skill testing"
```

## 5. 追加 SQL 任务

```bash
python3 scripts/build_ds_webhook_payload.py \
  --webhook-url "https://sql-cn.kuainiujinke.com/webhook/ds-scheduler" \
  --country mx \
  --action append_task \
  --ds-token "YOUR_DS_TOKEN" \
  --project-code 19427088052704 \
  --workflow-code 174599383687393 \
  --task-type SQL \
  --task-name "测试2" \
  --template-task-name "dwd_okr_dashboard_wide_app" \
  --sql "select 2" \
  --sql-type query
```

## 6. 追加 SHELL 任务

```bash
python3 scripts/build_ds_webhook_payload.py \
  --webhook-url "https://sql-cn.kuainiujinke.com/webhook/ds-scheduler" \
  --country mx \
  --action append_task \
  --ds-token "YOUR_DS_TOKEN" \
  --project-code 19427088052704 \
  --workflow-code 174599383687393 \
  --task-type SHELL \
  --task-name "测试shell" \
  --template-task-name "现有SHELL模板任务名" \
  --script "echo hello"
```

## 7. 查询实例详情

```bash
python3 scripts/build_ds_webhook_payload.py \
  --webhook-url "https://sql-cn.kuainiujinke.com/webhook/ds-scheduler" \
  --country pk \
  --action get_instance \
  --ds-token "YOUR_DS_TOKEN" \
  --project-code 158514956085248 \
  --instance-id 1040772
```

## 8. 查询某次实例里的任务明细

```bash
python3 scripts/build_ds_webhook_payload.py \
  --webhook-url "https://sql-cn.kuainiujinke.com/webhook/ds-scheduler" \
  --country mx \
  --action list_task_instances \
  --ds-token "YOUR_DS_TOKEN" \
  --project-code 19427088052704 \
  --instance-id 23511030 \
  --page-no 1 \
  --page-size 100
```

## 9. 拉取任务运行日志

按任务实例 ID 直接拉取：

```bash
python3 scripts/build_ds_webhook_payload.py \
  --webhook-url "https://sql-cn.kuainiujinke.com/webhook/ds-scheduler" \
  --country mx \
  --action get_task_log \
  --ds-token "YOUR_DS_TOKEN" \
  --project-code 19427088052704 \
  --task-instance-id 23458667
```

按“实例 + 任务名”自动定位后拉取：

```bash
python3 scripts/build_ds_webhook_payload.py \
  --webhook-url "https://sql-cn.kuainiujinke.com/webhook/ds-scheduler" \
  --country mx \
  --action get_task_log \
  --ds-token "YOUR_DS_TOKEN" \
  --project-code 19427088052704 \
  --instance-id 23511030 \
  --task-name "ods_repay_asset"
```

## 9.1 停止运行实例

```bash
python3 scripts/build_ds_webhook_payload.py \
  --webhook-url "https://sql-cn.kuainiujinke.com/webhook/ds-scheduler" \
  --country mx \
  --action stop_instance \
  --ds-token "YOUR_DS_TOKEN" \
  --project-code 13068695921632 \
  --instance-id 23511030
```

## 9.2 请求强制失败实例

```bash
python3 scripts/build_ds_webhook_payload.py \
  --webhook-url "https://sql-cn.kuainiujinke.com/webhook/ds-scheduler" \
  --country mx \
  --action force_fail_instance \
  --ds-token "YOUR_DS_TOKEN" \
  --project-code 13068695921632 \
  --instance-id 23511030
```

国家未配置已验证的官方执行类型时会返回 `UNSUPPORTED`。

## 10. 修改已有 SQL 任务内容

```bash
python3 scripts/build_ds_webhook_payload.py \
  --webhook-url "https://sql-cn.kuainiujinke.com/webhook/ds-scheduler" \
  --country mx \
  --action update_sql_task \
  --ds-token "YOUR_DS_TOKEN" \
  --project-code 19427088052704 \
  --workflow-code 174599383687393 \
  --task-name "dwd_okr_dashboard_wide_app" \
  --sql "select 2" \
  --sql-type query
```

## 11. 给任务添加自定义参数

```bash
python3 scripts/build_ds_webhook_payload.py \
  --webhook-url "https://sql-cn.kuainiujinke.com/webhook/ds-scheduler" \
  --country mx \
  --action update_task \
  --ds-token "YOUR_DS_TOKEN" \
  --project-code 19427088052704 \
  --workflow-code 174599383687393 \
  --task-name "dwd_okr_dashboard_wide_app" \
  --task-local-params-json '[{"prop":"biz_date","direct":"IN","type":"VARCHAR","value":"${system.biz.date}"}]'
```

## 12. 给任务填写资源列表

```bash
python3 scripts/build_ds_webhook_payload.py \
  --webhook-url "https://sql-cn.kuainiujinke.com/webhook/ds-scheduler" \
  --country mx \
  --action update_shell_task \
  --ds-token "YOUR_DS_TOKEN" \
  --project-code 19427088052704 \
  --workflow-code 174599383687393 \
  --task-name "load_dim_account_shell" \
  --resource-list-json '[{"id":12345,"name":"ods/load_dim_account.sh","res":"FILE"}]'
```

如需保留原资源再追加新资源，可额外加：

```bash
--merge-resource-list
```

## 13. 修改已有 SHELL 任务脚本

```bash
python3 scripts/build_ds_webhook_payload.py \
  --webhook-url "https://sql-cn.kuainiujinke.com/webhook/ds-scheduler" \
  --country mx \
  --action update_shell_task \
  --ds-token "YOUR_DS_TOKEN" \
  --project-code 19427088052704 \
  --workflow-code 174599383687393 \
  --task-name "load_dim_account_shell" \
  --script "bash /data/apps/ds/load_dim_account.sh ${biz_date}"
```

## 14. 创建定时

```bash
python3 scripts/build_ds_webhook_payload.py \
  --webhook-url "https://sql-cn.kuainiujinke.com/webhook/ds-scheduler" \
  --country cn \
  --action create_schedule \
  --ds-token "YOUR_DS_TOKEN" \
  --project-code 158514956085248 \
  --workflow-code 158515019593728 \
  --crontab "0 0 3 * * ? *" \
  --start-time "2026-06-25 03:00:00" \
  --failure-strategy CONTINUE \
  --process-instance-priority MEDIUM \
  --worker-group default
```

## 15. 上线 / 下线定时

上线：

```bash
python3 scripts/build_ds_webhook_payload.py \
  --webhook-url "https://sql-cn.kuainiujinke.com/webhook/ds-scheduler" \
  --country cn \
  --action online_schedule \
  --ds-token "YOUR_DS_TOKEN" \
  --project-code 158514956085248 \
  --workflow-code 158515019593728
```

下线：

```bash
python3 scripts/build_ds_webhook_payload.py \
  --webhook-url "https://sql-cn.kuainiujinke.com/webhook/ds-scheduler" \
  --country cn \
  --action offline_schedule \
  --ds-token "YOUR_DS_TOKEN" \
  --project-code 158514956085248 \
  --workflow-code 158515019593728
```

## 16. 查看资源中心目录

```bash
python3 scripts/build_ds_webhook_payload.py \
  --webhook-url "https://sql-cn.kuainiujinke.com/webhook/ds-scheduler" \
  --country cn \
  --action list_resources \
  --ds-token "YOUR_DS_TOKEN" \
  --resource-type FILE \
  --current-dir "file:///tmp/dolphinscheduler/storage/default/resources" \
  --search-val "phi" \
  --page-no 1 \
  --page-size 50
```

## 17. 查看资源文件内容

```bash
python3 scripts/build_ds_webhook_payload.py \
  --webhook-url "https://sql-cn.kuainiujinke.com/webhook/ds-scheduler" \
  --country cn \
  --action view_resource_file \
  --ds-token "YOUR_DS_TOKEN" \
  --full-name "file:///tmp/dolphinscheduler/storage/default/resources/phi/score_swap.sql" \
  --skip-line-num 0 \
  --limit 200
```

## 18. 按 SQL 片段反查资源文件

```bash
python3 scripts/build_ds_webhook_payload.py \
  --webhook-url "https://sql-cn.kuainiujinke.com/webhook/ds-scheduler" \
  --country cn \
  --action search_resource_sql \
  --ds-token "YOUR_DS_TOKEN" \
  --current-dir "file:///tmp/dolphinscheduler/storage/default/resources" \
  --sql-query "WITH pkg_raw AS (SELECT CAST(ask_loan_package_loan_uuid AS VARCHAR) ask_loan_uuid" \
  --max-results 10 \
  --max-files 300
```

## 15. 精确下线单个任务

```bash
python3 scripts/build_ds_webhook_payload.py \
  --webhook-url "https://sql-cn.kuainiujinke.com/webhook/ds-scheduler" \
  --country mx \
  --action disable_task \
  --ds-token "YOUR_DS_TOKEN" \
  --project-code 13068695921632 \
  --workflow-code 17480254697952 \
  --task-name "ods_msgsvr_ivr_account"
```

## 16. 下线任务前的安全检查建议

对于同步类工作流，在执行以下动作前：

- `disable_task`
- `disable_tasks_except`
- `delete_task`
- `append_task`

建议先查询工作流详情，确认工作流级参数没有被清空：

```bash
python3 scripts/build_ds_webhook_payload.py \
  --webhook-url "https://sql-cn.kuainiujinke.com/webhook/ds-scheduler" \
  --country mx \
  --action dump_workflow_graph \
  --ds-token "YOUR_DS_TOKEN" \
  --project-code 13068695921632 \
  --workflow-code 20515301105637
```

人工检查重点：

- `raw_workflow_detail.workflowDefinition.globalParams`
- `raw_workflow_detail.workflowDefinition.globalParamList`

如果这里已经是 `[]`，但任务脚本仍然包含：

- `${src}`
- `${db}`
- `${dt}`
- `${full}`

则不要继续修改工作流定义，先恢复历史版本参数。
