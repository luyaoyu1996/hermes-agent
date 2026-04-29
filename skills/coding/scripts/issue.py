#!/usr/bin/env python3
"""查询 CODING 单个事项详情。

Usage:
    python issue.py --project <ProjectName> --code <IssueCode> [--team <team>]
    python issue.py --url <issueUrl> [--team <team>]
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone, timedelta
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


def parse_issue_url(url: str) -> tuple:
    m = re.search(r"/p/([^/]+)/(?:[^/]+/)?issues/(\d+)", url)
    if not m:
        print("Cannot parse ProjectName and IssueCode from URL", file=sys.stderr)
        sys.exit(1)
    project = m.group(1)
    code = int(m.group(2))

    team = None
    host_match = re.search(r"https?://([^.]+)\.coding\.net", url)
    if host_match:
        team = host_match.group(1)

    return project, code, team


def main():
    parser = argparse.ArgumentParser(description="查询 CODING 事项详情")
    parser.add_argument("--project", help="项目名称")
    parser.add_argument("--code", type=int, help="事项编号")
    parser.add_argument("--url", help="事项 URL（自动解析 project 和 code）")
    parser.add_argument("--team", help="团队名（域名前缀）")
    args = parser.parse_args()

    project = args.project
    code = args.code
    team = args.team

    if args.url:
        url_project, url_code, url_team = parse_issue_url(args.url)
        project = project or url_project
        code = code or url_code
        if not team:
            team = url_team

    if not project or not code:
        print("Missing --project and --code, or --url", file=sys.stderr)
        parser.print_help(sys.stderr)
        sys.exit(2)

    token = load_coding_token()
    if not token:
        print("Missing CODING_TOKEN — add it to ~/.hermes/.env", file=sys.stderr)
        sys.exit(1)

    base_url = f"https://{team}.coding.net/open-api" if team else "https://e.coding.net/open-api"

    body = {
        "Action": "DescribeIssue",
        "ProjectName": project,
        "IssueCode": code,
        "ShowImageOutUrl": False,
    }

    data = call_coding_api(base_url, token, body)

    if data.get("Response", {}).get("Error"):
        err = data["Response"]["Error"]
        print(f"API Error [{err.get('Code')}]: {err.get('Message')}", file=sys.stderr)
        sys.exit(1)

    issue = data.get("Response", {}).get("Issue")
    if not issue:
        print("No issue data returned", file=sys.stderr)
        sys.exit(1)

    tz_cn = timezone(timedelta(hours=8))

    print(f"## {issue.get('Name') or issue.get('Title') or '-'}")
    print()
    print(f"- **事项编号**: #{issue.get('Code')}")
    print(f"- **类型**: {issue.get('Type') or issue.get('IssueType') or '-'}")
    print(f"- **状态**: {issue.get('IssueStatusName') or issue.get('IssueStatus') or '-'}")
    print(f"- **优先级**: {issue.get('Priority', '-')}")
    assignee = issue.get("Assignee", {})
    print(f"- **处理人**: {assignee.get('Name', '未分配') if assignee else '未分配'}")
    creator = issue.get("Creator", {})
    print(f"- **创建人**: {creator.get('Name', '-') if creator else '-'}")

    created_at = issue.get("CreatedAt")
    if created_at:
        ts = created_at / 1000 if created_at > 1e12 else created_at
        print(f"- **创建时间**: {datetime.fromtimestamp(ts, tz=tz_cn).strftime('%Y-%m-%d %H:%M:%S')}")

    updated_at = issue.get("UpdatedAt")
    if updated_at:
        ts = updated_at / 1000 if updated_at > 1e12 else updated_at
        print(f"- **更新时间**: {datetime.fromtimestamp(ts, tz=tz_cn).strftime('%Y-%m-%d %H:%M:%S')}")

    description = issue.get("Description")
    if description:
        print()
        print("## 描述")
        print()
        print(description)


if __name__ == "__main__":
    main()
