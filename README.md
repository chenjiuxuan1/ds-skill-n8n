# ds-skill-n8n

一个面向 Codex 的多国家 DolphinScheduler 3.4 调度 skill 与 n8n 中转模板。

## 目标

这个仓库解决两件事：

1. 让 Codex 能把用户的 DS 调度操作意图转换成标准 webhook 请求
2. 让 n8n 接收这些请求后，按国家路由到对应的 `Intelligent-Alarm-Repair-Assistant` 仓库配置，再调用 DS 3.4 API

## 当前支持

- `list_workflows`
- `get_workflow`
- `online_workflow`
- `offline_workflow`
- `trigger_workflow`
- `list_instances`
- `get_instance`

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
    ├── ds_scheduler_router.py
    └── workflow-template.json
```

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

### 2. n8n 侧执行

n8n 可以用 `Execute Command` 节点调用：

```bash
python3 /path/to/ds_scheduler_router.py
```

把 webhook 收到的原始 JSON 作为标准输入传给它。

## 依赖

- Python 3.9+
- n8n
- 目标机器可访问各国 DS 地址
- 目标机器本地存在 6 个国家仓库

## 安全说明

- `ds_token` 必须由调用方提供
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
