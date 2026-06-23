# Examples

先说明两点：

- 所有示例里的 `YOUR_DS_TOKEN` 都必须替换成调用人自己的 DS token
- n8n 只透传这个 token 对应的权限，不会自动放大范围

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

## 查询失败实例

```bash
python3 scripts/build_ds_webhook_payload.py \
  --webhook-url "https://sql-cn.kuainiujinke.com/webhook/ds-scheduler" \
  --country mx \
  --action list_instances \
  --ds-token "YOUR_DS_TOKEN" \
  --project-code 19427088052704 \
  --state-type FAILURE \
  --page-no 1 \
  --page-size 20
```

## 重跑失败实例

```bash
python3 scripts/build_ds_webhook_payload.py \
  --webhook-url "https://sql-cn.kuainiujinke.com/webhook/ds-scheduler" \
  --country mx \
  --action retry_instance \
  --ds-token "YOUR_DS_TOKEN" \
  --project-code 19427088052704 \
  --instance-id 2614176
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

## 删除任务

```bash
python3 scripts/build_ds_webhook_payload.py \
  --webhook-url "https://sql-cn.kuainiujinke.com/webhook/ds-scheduler" \
  --country mx \
  --action delete_task \
  --ds-token "YOUR_DS_TOKEN" \
  --project-code 19427088052704 \
  --workflow-code 174599383687393 \
  --task-name "测试2"
```

## 精确下线单个任务

```bash
python3 scripts/build_ds_webhook_payload.py \
  --webhook-url "https://sql-cn.kuainiujinke.com/webhook/ds-scheduler" \
  --country mx \
  --action disable_task \
  --ds-token "YOUR_DS_TOKEN" \
  --project-code 13068695921632 \
  --workflow-code 13068714127712 \
  --task-name "ods_app_user" \
  --restore-original-state \
  --auto-offline
```

## 批量精确下线任务

当用户给的是一组明确任务名，推荐先查工作流归属，再逐条发送 `disable_task`。

例如：

```bash
python3 scripts/build_ds_webhook_payload.py \
  --webhook-url "https://sql-cn.kuainiujinke.com/webhook/ds-scheduler" \
  --country mx \
  --action disable_task \
  --ds-token "YOUR_DS_TOKEN" \
  --request-id "mx-disable-exact-001" \
  --project-code 13068695921632 \
  --workflow-code 13068714127712 \
  --task-name "ods_app_user" \
  --restore-original-state \
  --auto-offline
```

接着把第二个、第三个任务继续按同样模板逐条发出即可。
