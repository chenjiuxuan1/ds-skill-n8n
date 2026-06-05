# DS Scheduler Reference

## 国家代码

| 国家 | code | 本地仓库 |
|---|---|---|
| 中国 | `cn` | `/Users/jiangchuanchen/Desktop/CN-Intelligent-Alarm-Repair-Assistant` |
| 印尼 | `ine` | `/Users/jiangchuanchen/Desktop/INE-Intelligent-Alarm-Repair-Assistant` |
| 墨西哥 | `mx` | `/Users/jiangchuanchen/Desktop/MX-Intelligent-Alarm-Repair-Assistant` |
| 菲律宾 | `ph` | `/Users/jiangchuanchen/Desktop/PH-Intelligent-Alarm-Repair-Assistant` |
| 巴基斯坦 | `pk` | `/Users/jiangchuanchen/Desktop/PK-Intelligent-Alarm-Repair-Assistant` |
| 泰国 | `th` | `/Users/jiangchuanchen/Desktop/TH-Intelligent-Alarm-Repair-Assistant` |

## 标准请求体

```json
{
  "source": "codex-skill",
  "country": "cn",
  "action": "trigger_workflow",
  "ds_token": "user-provided-token",
  "request_id": "20260605-001",
  "payload": {
    "project_code": "158514956085248",
    "workflow_code": "158515019593728",
    "instance_id": "",
    "workflow_name": "",
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

## 动作与参数

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

## 返回格式

成功：

```json
{
  "success": true,
  "country": "cn",
  "action": "trigger_workflow",
  "request_id": "20260605-001",
  "data": {},
  "error": null
}
```

失败：

```json
{
  "success": false,
  "country": "cn",
  "action": "offline_workflow",
  "request_id": "20260605-002",
  "data": null,
  "error": {
    "code": "DS_API_ERROR",
    "message": "workflow not found"
  }
}
```

## 安全边界

- `ds_token` 必须由用户提供
- n8n 不扩大 token 权限，只用它访问 DS
- 国家默认配置仅补足：
  - `base_url`
  - `project_code`
  - `environment_code`
  - `tenant_code`

## 第一版不做

- `create_workflow`
- `update_workflow`
- workflow JSON 结构生成
- 资源文件自动上传
- 跨国家批量写操作
