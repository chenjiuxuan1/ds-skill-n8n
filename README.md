# ds-skill-n8n

一个面向 Codex 的多国家 DolphinScheduler 3.4 调度 skill 与 n8n 中转模板。

## 目标

这个仓库解决两件事：

1. 让 Codex 能把用户的 DS 调度操作意图转换成标准 webhook 请求
2. 让 n8n 接收这些请求后，按国家路由到对应跳板机，再调用跳板机上的 `ds-scheduler-gateway` 执行 DS 3.4 API

## 当前支持

- `list_projects`
- `list_workflows`
- `get_workflow`
- `online_workflow`
- `offline_workflow`
- `trigger_workflow`
- `list_instances`
- `get_instance`
- `retry_instance`
- `dump_workflow_graph`
- `append_task`
- `append_sql_task`
- `append_shell_task`
- `delete_task`

## 仓库结构

```text
.
├── SKILL.md
├── REFERENCE.md
├── EXAMPLES.md
├── scripts/
│   └── build_ds_webhook_payload.py
└── n8n/
    ├── README.md
    └── workflow-template.json
```

## 正式链路

```text
User
  -> Codex skill
  -> n8n webhook
  -> 解析并标准化请求
  -> If(valid)
  -> 按国家分流
  -> Execute Command
  -> SSH 到各国跳板机
  -> /root/ds-scheduler-gateway/scripts/ds_scheduler_entry.py
  -> DolphinScheduler 3.4 API
  -> 内容解析
  -> Respond to Webhook
```

## 权限与 token 规则

- `ds_token` 必须由最终使用者自己提供
- `ds_token` 决定这次请求能操作哪些项目、工作流、实例
- skill 和 n8n 都不应该默认内置共享 token
- 当用户没有提供 token 时，Codex 应先提示用户补充自己的 token，再执行正式请求

## 快速开始

### 1. 生成 webhook 请求

```bash
python3 scripts/build_ds_webhook_payload.py \
  --webhook-url "https://your-n8n/webhook/ds-scheduler" \
  --country cn \
  --action trigger_workflow \
  --ds-token "YOUR_DS_TOKEN" \
  --workflow-code 158515019593728 \
  --custom-params-json '{"dt":"2026-06-05"}'
```

其中：

- `YOUR_DS_TOKEN` 需要替换成调用人的真实 DS token
- `country` 需要和目标环境一致
- 这个请求只是发给 n8n，中间不会自动提权

### 2. n8n 侧执行

n8n 推荐按国家分别配置 `Execute Command` 节点，直接 SSH 到跳板机执行：

```bash
ssh -p 36000 root@10.20.47.14 "cd /root/ds-scheduler-gateway && python3 scripts/ds_scheduler_entry.py --country cn --action '{{$json.action}}' --ds-token '{{$json.ds_token}}' --request-id '{{$json.request_id}}' --payload-b64 '{{$json.payload_b64}}'"
```

其他国家只替换两部分：

- SSH 地址
- `--country`

## 依赖

- Python 3.9+
- n8n
- 各国家跳板机上已部署 `/root/ds-scheduler-gateway`
- n8n 可通过 `Execute Command` 节点访问对应跳板机
- 跳板机到目标 DS 环境网络可达

## 安全说明

- `ds_token` 必须由调用方提供，而且应当是调用方自己的 token
- 本仓库不负责扩大 DS 权限
- 建议 n8n 侧额外校验：
  - 共享密钥
  - 国家白名单
  - 动作白名单

## 备注

这是一版可运行骨架。

第二版可以继续补：
- `create_workflow`
- `update_workflow`
- 完整 workflow definition 导入
- 资源文件上传
- 审计与幂等控制
