#!/usr/bin/env python3
"""查询 CODING 事项列表。

Usage:
    python issues.py --project <ProjectName> [--limit 20] [--offset 0] [--type ALL] [--team <team>]
"""

import argparse
import json
import os
import sys
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


def load_coding_token() -> str:
    token = os.environ.get("CODING_TOKEN", "")
    if token:
        return token

    hermes_home = Path(os.environ.get("HERMES_HOME", Path.home() / ".hermes"))
    env_file = hermes_home / ".env"

    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            if line.startswith("CODING_TOKEN="):
                return line.split("=", 1)[1].strip().strip("'\"")

    return ""


def call_coding_api(base_url: str, token: str, body: dict) -> dict:
    data = json.dumps(body).encode("utf-8")
    req = Request(
        base_url,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"token {token}",
        },
        method="POST",
    )
    try:
        with urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except HTTPError as e:
        text = e.read().decode("utf-8", errors="replace") if e.fp else ""
        print(f"CODING API error ({e.code}): {text}", file=sys.stderr)
        sys.exit(1)
    except URLError as e:
        print(f"Network error: {e.reason}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="查询 CODING 事项列表")
    parser.add_argument("--project", required=True, help="项目名称")
    parser.add_argument("--limit", type=int, default=20, help="每页数量（默认 20，最大 50）")
    parser.add_argument("--offset", type=int, default=0, help="分页偏移（默认 0）")
    parser.add_argument("--type", default="ALL", help="事项类型：ALL、REQUIREMENT、BUG、TASK（默认 ALL）")
    parser.add_argument("--team", help="团队名（域名前缀）")
    args = parser.parse_args()

    args.limit = min(args.limit, 50)

    token = load_coding_token()
    if not token:
        print("Missing CODING_TOKEN — add it to ~/.hermes/.env", file=sys.stderr)
        sys.exit(1)

    base_url = f"https://{args.team}.coding.net/open-api" if args.team else "https://e.coding.net/open-api"

    body = {
        "Action": "DescribeIssueList",
        "ProjectName": args.project,
        "IssueType": args.type,
        "Offset": args.offset,
        "Limit": args.limit,
        "Conditions": [],
        "SortKey": "CODE",
        "SortValue": "DESC",
    }

    data = call_coding_api(base_url, token, body)

    if data.get("Response", {}).get("Error"):
        err = data["Response"]["Error"]
        print(f"API Error [{err.get('Code')}]: {err.get('Message')}", file=sys.stderr)
        sys.exit(1)

    issues = data.get("Response", {}).get("IssueList", [])
    total = data.get("Response", {}).get("TotalCount", len(issues))

    print(f"## {args.project} 事项列表（共 {total} 条，显示 {args.offset + 1}-{args.offset + len(issues)}）")
    print()

    if not issues:
        print("暂无事项")
        return

    for issue in issues:
        assignee = issue.get("Assignee", {})
        assignee_name = assignee.get("Name", "未分配") if assignee else "未分配"
        status = issue.get("IssueStatusName") or issue.get("IssueStatus") or "-"
        issue_type = issue.get("Type") or issue.get("IssueType") or "-"

        print(f"- **#{issue.get('Code')}** {issue.get('Name') or issue.get('Title') or '-'}")
        print(f"  状态: {status} | 处理人: {assignee_name} | 类型: {issue_type}")
        print()


if __name__ == "__main__":
    main()
