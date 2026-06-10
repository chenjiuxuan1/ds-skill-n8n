#!/usr/bin/env python3
"""Build standardized DS scheduler webhook payloads and curl commands."""

from __future__ import annotations

import argparse
import json
import shlex
from datetime import datetime
from typing import Any, Dict


COUNTRIES = {"cn", "ine", "mx", "ph", "pk", "th"}
ACTIONS = {
    "list_projects",
    "list_workflows",
    "get_workflow",
    "online_workflow",
    "offline_workflow",
    "trigger_workflow",
    "list_instances",
    "get_instance",
    "append_task",
    "append_sql_task",
    "append_shell_task",
    "delete_task",
    "dump_workflow_graph",
}


def _load_json(raw: str | None, default: Any) -> Any:
    if not raw:
        return default
    return json.loads(raw)


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def _normalize_task_type(task_type: str | None, action: str) -> str:
    if action == "append_sql_task":
        return "SQL"
    if action == "append_shell_task":
        return "SHELL"
    if not task_type:
        return ""
    normalized = task_type.strip().upper()
    aliases = {"SQL": "SQL", "SHELL": "SHELL", "SCRIPT": "SHELL", "COMMAND": "SHELL"}
    return aliases.get(normalized, normalized)


def build_payload(args: argparse.Namespace) -> Dict[str, Any]:
    _require(args.country in COUNTRIES, f"Unsupported country: {args.country}")
    _require(args.action in ACTIONS, f"Unsupported action: {args.action}")
    _require(bool(args.ds_token), "ds_token is required")

    task_type = _normalize_task_type(args.task_type, args.action)

    if args.action in {"online_workflow", "offline_workflow", "trigger_workflow", "dump_workflow_graph"}:
        _require(bool(args.workflow_code), f"{args.action} requires --workflow-code")
    if args.action == "get_instance":
        _require(bool(args.instance_id), "get_instance requires --instance-id")
    if args.action == "get_workflow":
        _require(bool(args.workflow_code or args.workflow_name), "get_workflow requires --workflow-code or --workflow-name")
    if args.action in {"append_task", "append_sql_task", "append_shell_task"}:
        _require(bool(args.project_code), f"{args.action} requires --project-code")
        _require(bool(args.workflow_code), f"{args.action} requires --workflow-code")
        _require(bool(args.task_name), f"{args.action} requires --task-name")
        if args.action == "append_task":
            _require(bool(task_type), "append_task requires --task-type")
        _require(bool(task_type in {"SQL", "SHELL"}), f"unsupported task_type: {task_type}")
        if task_type == "SQL":
            _require(bool(args.sql), f"{args.action} requires --sql for SQL task")
        if task_type == "SHELL":
            _require(bool(args.script), f"{args.action} requires --script for SHELL task")
    if args.action == "delete_task":
        _require(bool(args.project_code), "delete_task requires --project-code")
        _require(bool(args.workflow_code), "delete_task requires --workflow-code")
        _require(bool(args.task_name or args.task_code), "delete_task requires --task-name or --task-code")

    payload = {
        "source": "codex-skill",
        "country": args.country,
        "action": args.action,
        "ds_token": args.ds_token,
        "request_id": args.request_id or datetime.now().strftime("%Y%m%d-%H%M%S"),
        "payload": {
            "project_code": args.project_code or "",
            "workflow_code": args.workflow_code or "",
            "workflow_name": args.workflow_name or "",
            "instance_id": args.instance_id or "",
            "start_node_list": args.start_node_list or "",
            "schedule_time": args.schedule_time or "",
            "state_type": args.state_type or "",
            "search_val": args.search_val or "",
            "page_no": args.page_no,
            "page_size": args.page_size,
            "custom_params": _load_json(args.custom_params_json, {}),
        },
    }

    extra = payload["payload"]
    if args.action in {"append_task", "append_sql_task", "append_shell_task"}:
        extra.update(
            {
                "task_type": task_type,
                "task_name": args.task_name or "",
                "task_description": args.task_description or "",
                "template_task_name": args.template_task_name or "",
                "sql": args.sql or "",
                "script": args.script or "",
                "sql_type": args.sql_type if args.sql_type is not None else "",
                "datasource": args.datasource or "",
                "environment_code": args.environment_code or "",
                "tenant_code": args.tenant_code or "",
            "upstream_task_name": args.upstream_task_name or "",
            "upstream_task_code": args.upstream_task_code or "",
            "task_code": args.task_code or "",
        }
        )
        if args.restore_original_state is not None:
            extra["restore_original_state"] = args.restore_original_state
        if args.auto_offline is not None:
            extra["auto_offline"] = args.auto_offline

    if args.action == "delete_task":
        extra.update(
            {
                "task_name": args.task_name or "",
                "task_code": args.task_code or "",
            }
        )
        if args.restore_original_state is not None:
            extra["restore_original_state"] = args.restore_original_state
        if args.auto_offline is not None:
            extra["auto_offline"] = args.auto_offline

    return payload


def build_curl(webhook_url: str, payload: Dict[str, Any]) -> str:
    body = json.dumps(payload, ensure_ascii=False)
    return (
        f"curl -X POST {shlex.quote(webhook_url)} "
        f"-H 'Content-Type: application/json' "
        f"-d {shlex.quote(body)}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Build DS scheduler webhook payload")
    parser.add_argument("--webhook-url", required=True)
    parser.add_argument("--country", required=True)
    parser.add_argument("--action", required=True)
    parser.add_argument("--ds-token", required=True)
    parser.add_argument("--request-id")
    parser.add_argument("--project-code")
    parser.add_argument("--workflow-code")
    parser.add_argument("--workflow-name")
    parser.add_argument("--instance-id")
    parser.add_argument("--start-node-list")
    parser.add_argument("--schedule-time")
    parser.add_argument("--state-type")
    parser.add_argument("--search-val")
    parser.add_argument("--page-no", type=int, default=1)
    parser.add_argument("--page-size", type=int, default=20)
    parser.add_argument("--custom-params-json")
    parser.add_argument("--task-type")
    parser.add_argument("--task-name")
    parser.add_argument("--task-description")
    parser.add_argument("--template-task-name")
    parser.add_argument("--sql")
    parser.add_argument("--script")
    parser.add_argument("--sql-type")
    parser.add_argument("--datasource")
    parser.add_argument("--environment-code")
    parser.add_argument("--tenant-code")
    parser.add_argument("--upstream-task-name")
    parser.add_argument("--upstream-task-code")
    parser.add_argument("--task-code")
    parser.add_argument("--restore-original-state", action="store_const", const=True, default=None)
    parser.add_argument("--auto-offline", action="store_const", const=True, default=None)
    args = parser.parse_args()

    payload = build_payload(args)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    print()
    print("# curl")
    print(build_curl(args.webhook_url, payload))


if __name__ == "__main__":
    main()
