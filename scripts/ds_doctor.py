#!/usr/bin/env python3
"""Preflight for the ds-scheduler skill: prove the token works *before* doing work.

The failure this exists for: a first-time caller sends an action, gets back a
bare ``DS_API_ERROR 401``, and reasonably concludes the gateway, the routing or
the request format is broken. It almost never is. DS stores tokens per instance,
so the usual cause is a token that was minted on another country's DS, or one
that has since been rotated while a stale copy sat in a local file.

This script checks, in order:

1. a token is actually resolvable for the requested country;
2. the token is free of the copy-paste damage that also produces 401
   (surrounding whitespace, a trailing newline, an obviously wrong length);
3. the country is one the skill supports;
4. the live webhook actually accepts the token, via a minimal read.

Every check reports what to do next. The token is never printed.

Usage:
    python3 scripts/ds_doctor.py --country pk
    python3 scripts/ds_doctor.py --country pk --ds-token "$DS_TOKEN"
    python3 scripts/ds_doctor.py --country mx --token-config config/ds-tokens.local.json
    python3 scripts/ds_doctor.py --country pk --json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

DEFAULT_WEBHOOK = "https://sql-cn.kuainiujinke.com/webhook/ds-scheduler"

COUNTRIES = {"cn", "ine", "mx", "ph", "pk", "th"}

# Where a per-country token conventionally lives on a workstation. Documented in
# SKILL.md; kept here so the doctor and the docs cannot drift apart.
SECRETS_DIR = Path.home() / ".config" / "codex-secrets"

# DS tokens are 32 hex characters today. Anything else is not rejected outright
# (DS could change the format), just flagged as worth a second look.
EXPECTED_TOKEN_LENGTH = 32

TOKEN_GUIDANCE = (
    "令牌无效，或该令牌不属于 {country} 实例。\n"
    "    DS 令牌存在各国实例自己的库里、互不相通：在 {country} 以外的国家创建的令牌，\n"
    "    {country} 的 DS 并不认识它。请依次确认：\n"
    "      1. 令牌是在 {country} 的 DolphinScheduler「安全中心 → 令牌管理 → 新建」创建的；\n"
    "      2. 复制时没有多余空格或换行（用 printf 而不是 echo 写入文件）；\n"
    "      3. 令牌没有被轮换、停用或删除——旧的本地副本最容易造成这个 401。"
)

ACCESS_GUIDANCE = (
    "网关访问控制拦截了本次请求。这不是令牌失效，而是权限或配额问题。\n"
    "    访问策略由值班平台「DS网关使用统计 → 用户权限与管控」生成，并下发到各国机器的\n"
    "    /root/ds-scheduler-gateway/config/access_policy.json。未登记的令牌默认只读\n"
    "    （enforceUnknown=true），所以写/控制/删除类动作会被拒。请联系值班同学把你的\n"
    "    令牌登记进策略，而不是重新创建令牌。"
)

UNREACHABLE_GUIDANCE = (
    "无法通过 n8n 中转到目标国家。请确认本机网络能访问上述 webhook 域名，\n"
    "    并确认对应国家的跳板机与 DolphinScheduler 处于可用状态。"
)


def token_file_for(country: str) -> Path:
    return SECRETS_DIR / f"{country}-dolphinscheduler-token"


def load_token_from_config(config_path: str, country: str) -> str:
    """Same semantics as build_ds_webhook_payload.py: ``{"tokens": {"pk": ...}}``."""
    path = Path(config_path).expanduser()
    if not path.is_file():
        raise SystemExit(f"token config not found: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    tokens = data.get("tokens", data) if isinstance(data, dict) else {}
    token = tokens.get(country) if isinstance(tokens, dict) else ""
    if isinstance(token, str) and token.startswith("${") and token.endswith("}"):
        token = os.environ.get(token[2:-1], "")
    return str(token or "").strip()


def resolve_token(
    country: str,
    ds_token: Optional[str] = None,
    token_config: Optional[str] = None,
    token_file: Optional[str] = None,
) -> Tuple[str, str]:
    """Return ``(raw_token, source)`` in priority order; ``("", "")`` when nothing is set.

    The token is returned **unstripped** on purpose: surrounding whitespace and
    trailing newlines are a real cause of 401, and :func:`inspect_token` can only
    report them if it sees the value exactly as it was stored.
    """
    if ds_token and ds_token.strip():
        return ds_token, "--ds-token"
    if token_config:
        return load_token_from_config(token_config, country), "--token-config"
    if token_file:
        path = Path(token_file).expanduser()
        if not path.is_file():
            raise SystemExit(f"token file not found: {path}")
        return path.read_text(encoding="utf-8"), str(path)
    env = os.environ.get(f"DS_TOKEN_{country.upper()}", "")
    if env.strip():
        return env, f"$DS_TOKEN_{country.upper()}"
    default = token_file_for(country)
    if default.is_file():
        return default.read_text(encoding="utf-8"), str(default)
    return "", ""


def inspect_token(raw: str) -> List[str]:
    """Return human-readable problems with the token *as stored*, not as sent."""
    problems: List[str] = []
    if not raw:
        problems.append("令牌为空")
        return problems
    if raw != raw.strip():
        problems.append("令牌首尾有空白字符（复制粘贴常见），发送前会被去掉，请清理来源")
    if any(ch in raw for ch in ("\n", "\r", "\t")):
        problems.append("令牌里含换行或制表符，几乎一定是复制粘贴带进来的")
    if " " in raw:
        problems.append("令牌里含空格")
    if len(raw.strip()) != EXPECTED_TOKEN_LENGTH:
        problems.append(
            f"令牌长度为 {len(raw.strip())}，而 DS 目前发放的是 {EXPECTED_TOKEN_LENGTH} 位"
            "——请确认没有截断或粘连"
        )
    return problems


def mask(token: str) -> str:
    if not token:
        return "(未设置)"
    return f"{token[:4]}…{token[-2:]}" if len(token) > 8 else "…"


def probe(webhook_url: str, country: str, token: str, timeout: int = 60) -> Dict[str, Any]:
    """Minimal read against the live webhook.

    ``list_projects`` is the cheapest action that proves the whole chain:
    n8n -> jump host -> gateway -> DS auth.
    """
    body = json.dumps(
        {
            "source": "codex-skill",
            "country": country,
            "action": "list_projects",
            "ds_token": token,
            "request_id": "ds-doctor",
            "payload": {"page_size": 1, "page_no": 1},
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        webhook_url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8", "replace"))
    except urllib.error.HTTPError as exc:
        return {"success": False, "error": {"code": f"HTTP_{exc.code}", "message": exc.reason}}
    except Exception as exc:  # noqa: BLE001 - reported, not raised
        return {"success": False, "error": {"code": "WEBHOOK_UNREACHABLE", "message": repr(exc)}}


def _error_code(response: Dict[str, Any]) -> str:
    error = response.get("error") or {}
    return str(error.get("code") or "")


def _error_message(response: Dict[str, Any]) -> Any:
    error = response.get("error") or {}
    return error.get("message")


def _ds_status(response: Dict[str, Any]) -> Optional[int]:
    """Read DS's HTTP status whether the gateway translated it or not."""
    message = _error_message(response)
    if isinstance(message, dict):
        status = message.get("status")
        if isinstance(status, int):
            return status
    return None


def diagnose(country: str, response: Dict[str, Any]) -> Tuple[bool, str, List[str]]:
    """Turn a webhook response into ``(ok, headline, next_steps)``.

    Understands both the translated error codes and the older bare
    ``DS_API_ERROR`` shape, so the doctor is useful before every host has
    picked up the newer gateway code.
    """
    if response.get("success"):
        return True, f"令牌有效，{country} 链路完全打通（可读取到项目）", [
            f"可以通过 n8n 正常操作 {country} 的 DolphinScheduler 了",
        ]

    code = _error_code(response)
    status = _ds_status(response)

    if code == "TOKEN_INVALID_OR_WRONG_INSTANCE" or status == 401:
        return False, f"令牌未通过 {country} 的身份校验（DS 401）", [TOKEN_GUIDANCE.format(country=country)]

    if code == "DS_PERMISSION_DENIED" or status == 403:
        return False, f"令牌有效，但账号在 {country} 权限不足（DS 403）", [
            "确认该账号是目标项目的成员，且项目角色允许该动作",
            "若是写/控制/删除类动作被拦，检查网关访问控制是否把该令牌当作只读",
        ]

    if code.startswith("ACCESS_"):
        return False, f"网关访问控制拦截（{code}）", [ACCESS_GUIDANCE]

    if code in {"DS_UNREACHABLE", "DS_UNAVAILABLE", "WEBHOOK_UNREACHABLE"} or (
        status is not None and status >= 500
    ):
        return False, f"链路不可达（{code or status}）", [UNREACHABLE_GUIDANCE]

    message = _error_message(response)
    detail = message if not isinstance(message, dict) else json.dumps(message, ensure_ascii=False)
    return False, f"未识别的失败（{code or 'no code'}）", [f"原始返回：{str(detail)[:400]}"]


def run(args: argparse.Namespace) -> int:
    country = (args.country or "").strip().lower()
    if country not in COUNTRIES:
        print(f"❌ 不支持的国家：{country!r}（可用：{', '.join(sorted(COUNTRIES))}）")
        return 2

    raw_token, source = resolve_token(country, args.ds_token, args.token_config, args.token_file)
    token = raw_token.strip()
    checks: List[Dict[str, Any]] = []

    if not token:
        checks.append(
            {
                "name": "解析令牌",
                "ok": False,
                "detail": f"没有找到 {country} 的令牌",
                "next": [
                    f"任选一种方式提供：--ds-token / --token-config / {token_file_for(country)}",
                    "首次使用请到该国家的 DolphinScheduler「安全中心 → 令牌管理 → 新建」创建",
                    "写入文件时用 printf 而不是 echo，避免带上换行：",
                    f"  printf '%s' '<TOKEN>' > {token_file_for(country)}",
                    f"  chmod 600 {token_file_for(country)}",
                ],
            }
        )
    else:
        problems = inspect_token(raw_token)
        checks.append(
            {
                "name": "解析令牌",
                "ok": True,
                "detail": f"来源 {source}，{mask(token)}，{len(token)} 位",
                "next": [],
            }
        )
        checks.append(
            {
                "name": "令牌格式",
                "ok": not problems,
                "detail": "；".join(problems) if problems else "格式正常",
                "next": ["清理令牌来源（去掉空白/换行）后重跑本脚本"] if problems else [],
            }
        )

        if not args.offline:
            response = probe(args.webhook_url, country, token, args.timeout)
            ok, headline, steps = diagnose(country, response)
            checks.append({"name": "线上探测", "ok": ok, "detail": headline, "next": steps})
        else:
            checks.append({"name": "线上探测", "ok": True, "detail": "已按 --offline 跳过", "next": []})

    if args.json:
        print(json.dumps({"country": country, "checks": checks}, ensure_ascii=False, indent=2))
    else:
        print(f"ds-scheduler doctor · {country}\n")
        for check in checks:
            print(f"  {'✅' if check['ok'] else '❌'} {check['name']}: {check['detail']}")
            for step in check["next"]:
                for line in step.splitlines():
                    print(f"      {line}")
        print()
        if all(check["ok"] for check in checks):
            print("✅ 全部通过，可以正常使用")
        else:
            print("❌ 存在问题，请按上面的提示处理后重跑")

    return 0 if all(check["ok"] for check in checks) else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--country", required=True, help="cn / ine / mx / ph / pk / th")
    parser.add_argument("--webhook-url", default=DEFAULT_WEBHOOK)
    parser.add_argument("--ds-token", help="token directly (prefer the file or config)")
    parser.add_argument("--token-config", help="JSON file with per-country tokens")
    parser.add_argument("--token-file", help="file holding just this country's token")
    parser.add_argument("--timeout", type=int, default=60)
    parser.add_argument("--offline", action="store_true", help="skip the live probe")
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    return run(parser.parse_args())


if __name__ == "__main__":
    sys.exit(main())
