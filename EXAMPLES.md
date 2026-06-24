# Examples

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

## 4. 追加 SQL 任务

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

## 5. 追加 SHELL 任务

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

## 6. 查询实例详情

```bash
python3 scripts/build_ds_webhook_payload.py \
  --webhook-url "https://sql-cn.kuainiujinke.com/webhook/ds-scheduler" \
  --country pk \
  --action get_instance \
  --ds-token "YOUR_DS_TOKEN" \
  --project-code 158514956085248 \
  --instance-id 1040772
```

## 7. 下线任务前的安全检查建议

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
