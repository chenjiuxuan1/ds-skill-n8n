# n8n DS Scheduler

## 环境切换动作

请求 normalizer 已加入 `update_workflow_environment` 与 `batch_update_workflow_environment`，用于批量切换
DS 环境（`environmentCode`）。这两个动作走的是「逐字回写线上工作流定义、只改 environmentCode」的路径，
因此不受结构修改类动作的 `globalParams` 门禁影响。

- `environment_code` 必填，normalizer 会先 `trim` 再校验非空。
- `dry_run` 默认 `true`；只有布尔值 `false` 才进入正式切换。
- `batch_update_workflow_environment` 的 `workflow_codes` 必须是唯一非空字符串数组；标量会被包成单元素数组。
- `include_schedule` / `require_global_params` 只有显式布尔值才会透传，缺省时由网关使用各自的默认值。
- `rate_limit_ms` 必须在 0–10000 之间（默认 100）。
- 网关侧 `batch_update_workflow_environment` 会先做零写入预检，任一工作流读取不可信则整批中止。
- 审计节点 `构造审计写入SQL` 已把这两个动作登记为 medium 风险。

## 定时告警动作

请求 normalizer 已加入 `list_alert_groups` 与 `batch_update_schedule_alerts`，并允许 `update_schedule` 在不传 cron 的情况下只更新告警字段。

- `batch_update_schedule_alerts` 默认 `dry_run=true`；只有布尔值 `false` 才会进入正式更新。
- `project_names` 必须是唯一、非空字符串数组。
- `warning_type` 仅允许 `NONE / SUCCESS / FAILURE / ALL`。
- `workflow_release_state` 与 `schedule_release_state` 必须都是 `ONLINE`。
- `retry_attempts / retry_delay_ms / rate_limit_ms` 有边界校验。
- `release_state` 与 `start_params` 会被保留，因此网关返回的 rollback payload 可原样再次作为 `update_schedule.payload`。
- normalizer 不会把 `ds_token` 复制进业务 `payload` 或 rollback 数据；token 仅保留在当前请求路由字段中。

导入或发布工作流前，确认 `workflow-template.json` 和 `ds-scheduler-router.latest.json` 的“解析并标准化请求”代码与 `request_normalizer.js` 完全一致。

修改 normalizer 后运行 `python3 scripts/sync_schedule_alert_router.py` 同步两个制品；脚本还会把批量告警修改登记为最新 Router 的风险审计动作，但审计只持久化 `ds_token_present` 布尔值，不持久化 token 明文。

这版 skill 对应的是当前已经打通的中转结构：

```text
Codex
  -> n8n Webhook
  -> 解析并标准化请求
  -> If(valid)
  -> 按国家分流
  -> 各国 Execute Command
  -> 内容解析
  -> Respond to Webhook
```

## 推荐节点

1. `Webhook`
2. `Code in JavaScript`
   - 节点名示例：`解析并标准化请求`
   - 把 `payload` 规范化成：
     - `payload_json`
     - `payload_b64`
     - `valid`
     - `errors`
3. `If`
   - `{{$json.valid}} == true`
4. `Switch`
   - `{{$json.country}}`
   - 分到 `cn / ine / mx / ph / pk / th`
5. 各国家 `Execute Command`
6. `Code in JavaScript`
   - 节点名示例：`内容解析`
   - 解析远端命令 stdout 中的 JSON
7. `Respond to Webhook`

## 各国家执行命令模式

每个国家节点都执行同一套网关，只是 SSH 目标不同。

示例结构：

```bash
ssh -p 36000 root@10.20.47.14 "cd /root/ds-scheduler-gateway && python3 scripts/ds_scheduler_entry.py --country cn --action '{{$json.action}}' --ds-token '{{$json.ds_token}}' --request-id '{{$json.request_id}}' --payload-b64 '{{$json.payload_b64}}'"
```

说明：
- `country` 固定写当前国家
- 其他参数直接透传上游解析节点结果
- 远端仓库路径固定为 `/root/ds-scheduler-gateway`

代码更新节点请不要写成：

```bash
git pull origin main
```

因为这个仓库里的 `origin` 可能仍指向旧的 `scaffold`。

统一推荐改成：

```bash
git pull gateway-github main
```

如需走内网仓，则使用：

```bash
git pull internal main
```

## 远端网关职责

远端 `ds-scheduler-gateway` 负责：
- 校验国家配置
- 解码 `payload_b64`
- 根据 `action` 调对应 handler
- 调 Dolphinscheduler API
- 返回统一 JSON

## 当前支持动作

共 **48** 个，按落地位置分两类。

### 一、网关动作（46 个，由各国节点的 `else` 分支转给 `scripts/ds_scheduler_entry.py`）

只读查询（22）：

`resolve_project`、`list_projects`、`list_workflows`、`get_workflow`、`dump_workflow_graph`、
`list_schedules`、`get_schedule`、`schedule_blast_radius`、`list_alert_groups`、`get_alert_instance`、
`list_instances`、`get_instance`、`list_task_instances`、`get_task_log`、`check_failed_instances`、
`list_datasources`、`get_datasource`、`extract_task_runtime_config`、`list_resources`、
`view_resource_file`、`search_resource_sql`、`search_country_git_sql`

写入（13）：

`create_workflow`、`copy_workflow`、`append_task`、`append_sql_task`、`append_shell_task`、
`update_task`、`update_sql_task`、`update_shell_task`、`create_schedule`、`update_schedule`、
`batch_update_schedule_alerts`、`update_workflow_environment`、`batch_update_workflow_environment`

删除白名单（3）：

`delete_task`、`disable_task`、`disable_tasks_except`

> 分级口径取自 `gateway/access.py`：读 22 + 写 13 + 删除 3 + 控制 8 = 46；
> 另有 2 个跳板机本地动作，合计 48。这四个分级常量必须与值班平台的
> `src/ds-scheduler-access.mjs` 保持一致。

控制（8）：

`online_workflow`、`offline_workflow`、`trigger_workflow`、`retry_instance`、`stop_instance`、
`force_fail_instance`、`online_schedule`、`offline_schedule`

### 二、跳板机本地动作（2 个，不经过网关）

- `find_resource_usage` — 各国节点的远端 shell 直接执行（复用只读 DS 候选助手做 MySQL 连接发现，再查一次元数据）
- `get_auto_repair_log` — 远端 shell 直接读 `/data` 下的日志文件（`tail -n 200`）

这两个动作**在 normalizer 白名单里，却不在网关注册表里**，因为在 `else` 分支之前就被远端
shell 用 `[ "$ACTION" = ... ]` 拦截了。`tests/test_action_alignment.py` 会校验六个国家节点
都确实实现了这两个拦截，并保留把其余动作转发给网关的 `else` 分支。

### 三、无自动化入口的代码更新链路

`ds-scheduler-router` 与 `各国-DS失败自动重跑统一入口` 里都有 `X更新DS网关代码` /
`X代码拉取` 这一类 SSH 节点，做的是：

```bash
cd /root/ds-scheduler-gateway
git remote add gateway-github https://github.com/chenjiuxuan1/ds-scheduler-gateway.git
git fetch --prune gateway-github main
git reset --hard FETCH_HEAD
```

**这两条链路都是「孤立」的**：它们没有任何入边，webhook 触发不到，n8n 公共 API 也没有
执行工作流的接口。所以网关代码更新只能在 n8n 界面里手工执行（右键 `中国代码拉取` →
`Execute step`，会顺着连边依次跑完六国）。

---

最新可导入工作流为 `ds-scheduler-router.latest.json`。它严格基于用户提供的
`ds-scheduler-router (2).json` 增量修改，保留 24 个节点、19 组连接、六国
分流、代码拉取和审计链路，只在“解析并标准化请求”节点增加实例动作契约。

## 解析节点职责

`内容解析` 节点需要把 `Execute Command` 的结果：
- `code`
- `stdout`
- `stderr`

转换成最终 webhook 返回：

```json
{
  "success": true,
  "country": "mx",
  "action": "list_workflows",
  "request_id": "mx-test-001",
  "data": {},
  "error": null
}
```

如果 stdout 不是合法 JSON，则返回统一错误结构。

## 任务实例与任务日志链路

新增推荐排障链路如下：

1. `list_instances`
   - 先定位失败或目标运行实例
2. `get_instance`
   - 看实例基础状态
3. `list_task_instances`
   - 拉出该实例下所有任务实例
4. `get_task_log`
   - 根据 `task_instance_id` 或 `instance_id + task_name` 拉详细日志

这样 Codex 通过同一条 n8n webhook，就能继续往下追到具体任务日志，不需要再手工进 DS 页面点日志。

## 推荐正式 webhook

如果当前环境已经发布，可使用：

```text
https://sql-cn.kuainiujinke.com/webhook/ds-scheduler
```

如果是测试态，则使用 n8n 提供的 test webhook URL。
