# n8n DS Scheduler

这一版建议让 n8n 暴露一个专用 webhook，然后由 n8n 调本目录下的 Python 路由脚本。

## 推荐 n8n 结构

1. `Webhook`
2. `Code` 或 `Set`
   - 透传原始 JSON
3. `Execute Command`
   - 调用 `python3 ds_scheduler_router.py`
4. `Respond to Webhook`

## Webhook 输入

请求体遵循 skill 的标准协议，见上级目录 `REFERENCE.md`。

## Execute Command 示例

假设把 `ds_scheduler_router.py` 放在服务器：

```bash
python3 /opt/ds-scheduler/ds_scheduler_router.py
```

并把 webhook body 原样写入标准输入。

## 认证建议

- 不要暴露匿名高权限入口
- 建议至少校验：
  - `country`
  - `action`
  - `ds_token`
- 如果需要，再额外加：
  - `shared_secret`
  - IP allowlist
  - 过期时间 / nonce

## 第一版动作

- `list_workflows`
- `get_workflow`
- `online_workflow`
- `offline_workflow`
- `trigger_workflow`
- `list_instances`
- `get_instance`

## 注意

- `ds_token` 来自调用者，不由脚本持久化
- 国家默认配置来自各国 `Intelligent-Alarm-Repair-Assistant` 仓库
- 如果要支持 `create_workflow / update_workflow`，建议作为第二版扩展
