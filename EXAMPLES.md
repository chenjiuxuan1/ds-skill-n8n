# Examples

## 1. 触发中国工作流

```bash
python3 scripts/build_ds_webhook_payload.py \
  --webhook-url "https://your-n8n/webhook/ds-scheduler" \
  --country cn \
  --action trigger_workflow \
  --ds-token "YOUR_DS_TOKEN" \
  --workflow-code 158515019593728 \
  --custom-params-json '{"dt":"2026-06-05"}'
```

## 2. 查询菲律宾工作流详情

```bash
python3 scripts/build_ds_webhook_payload.py \
  --webhook-url "https://your-n8n/webhook/ds-scheduler" \
  --country ph \
  --action get_workflow \
  --ds-token "YOUR_DS_TOKEN" \
  --workflow-code 16916179865056
```

## 3. 下线泰国工作流

```bash
python3 scripts/build_ds_webhook_payload.py \
  --webhook-url "https://your-n8n/webhook/ds-scheduler" \
  --country th \
  --action offline_workflow \
  --ds-token "YOUR_DS_TOKEN" \
  --workflow-code 16894765522823
```

## 4. 查询巴基斯坦实例详情

```bash
python3 scripts/build_ds_webhook_payload.py \
  --webhook-url "https://your-n8n/webhook/ds-scheduler" \
  --country pk \
  --action get_instance \
  --ds-token "YOUR_DS_TOKEN" \
  --instance-id 1040772
```
