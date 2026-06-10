# Examples

## 查询项目

```bash
python3 scripts/build_ds_webhook_payload.py \
  --webhook-url "https://sql-cn.kuainiujinke.com/webhook/ds-scheduler" \
  --country mx \
  --action list_projects \
  --ds-token "YOUR_DS_TOKEN" \
  --search-val "墨西哥数仓-工作流"
```

## 导出工作流 DAG

```bash
python3 scripts/build_ds_webhook_payload.py \
  --webhook-url "https://sql-cn.kuainiujinke.com/webhook/ds-scheduler" \
  --country mx \
  --action dump_workflow_graph \
  --ds-token "YOUR_DS_TOKEN" \
  --project-code 13068695921632 \
  --workflow-code 174599383687393
```

## 追加 SQL 任务

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

## 追加 SHELL 任务

```bash
python3 scripts/build_ds_webhook_payload.py \
  --webhook-url "https://sql-cn.kuainiujinke.com/webhook/ds-scheduler" \
  --country mx \
  --action append_task \
  --ds-token "YOUR_DS_TOKEN" \
  --project-code 13068695921632 \
  --workflow-code 175767388280714 \
  --task-type SHELL \
  --task-name "dwd_ad_fb_advertiser_get" \
  --template-task-name "dwd_ad_fb_ad_set_get" \
  --script 'python3 $WATTREL_HOME/console.py etl --table=dwd_ad_fb_advertiser_get'
```

