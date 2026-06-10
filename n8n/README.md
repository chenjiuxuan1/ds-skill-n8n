# n8n DS Scheduler

当前推荐链路：

```text
Webhook
  -> 解析并标准化请求
  -> If(valid)
    -> false -> 构造请求错误响应
    -> true  -> 按国家分流
             -> 各国 Execute Command
             -> 内容解析
             -> Respond to Webhook
```

## 节点代码来源

直接使用本目录文件：

- `request_normalizer.js`
- `error_response.js`
- `parse_command_output.js`

## `解析并标准化请求`

使用 `request_normalizer.js`

作用：
- 校验国家
- 校验动作
- 校验必填参数
- 明确要求调用人自行提供 `ds_token`
- 产出：
  - `payload_json`
  - `payload_b64`
  - `valid`
  - `errors`

## `构造请求错误响应`

使用 `error_response.js`

## `内容解析`

使用 `parse_command_output.js`

作用：
- 读取 `Execute Command` 的 `stdout`
- 尝试解析成 JSON
- 如果 `stdout` 为空或不是合法 JSON，构造成统一错误响应

## token 规则

- `ds_token` 必须来自当前调用用户
- n8n 不应内置共享高权限 token
- 国家节点只透传 `{{$json.ds_token}}` 到跳板机命令
- 谁的 token 发起请求，就按谁的 DS 权限执行

## 各国家命令模板

示例：

```bash
ssh -p 36000 root@10.20.47.14 "cd /root/ds-scheduler-gateway && python3 scripts/ds_scheduler_entry.py --country cn --action '{{$json.action}}' --ds-token '{{$json.ds_token}}' --request-id '{{$json.request_id}}' --payload-b64 '{{$json.payload_b64}}'"
```

每个国家只替换：
- SSH 地址
- `--country`

建议正式环境中为 6 个国家分别放置 6 个 Execute Command 节点，避免在一个节点里拼复杂条件命令。

## 支持动作

- `list_projects`
- `list_workflows`
- `get_workflow`
- `online_workflow`
- `offline_workflow`
- `trigger_workflow`
- `list_instances`
- `get_instance`
- `retry_instance`
- `append_task`
- `append_sql_task`
- `append_shell_task`
- `delete_task`
- `dump_workflow_graph`

## 注意

如果某个动作在 n8n 中返回 `200` 但 body 为空，优先检查：
- `解析并标准化请求` 是否包含该动作白名单
- 对应国家 `Execute Command` 是否真正返回了 `stdout`
- `内容解析` 是否仍在使用旧代码
- `Respond to Webhook` 的 `Response Body` 是否为 `{{ $json }}`

如果某个用户说“别人能查到、我查不到”，优先检查：
- 他传入的 `ds_token` 是否属于他本人
- 该 token 是否具备目标项目权限
- 是否误用了其他国家的 token
