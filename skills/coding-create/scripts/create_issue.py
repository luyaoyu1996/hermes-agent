#!/usr/bin/env python3
"""在 CODING 创建事项。

默认：团队 mabangerp，项目 wuliu，类型 REQUIREMENT，优先级 2（普通）

Usage:
    python create_issue.py --name "事项名称" [options]
"""

import argparse
import json
import os
import sys
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

PRIORITY_MAP = {
    "0": 0, "none": 0, "无": 0,
    "1": 1, "low": 1, "低": 1,
    "2": 2, "normal": 2, "普通": 2,
    "3": 3, "high": 3, "高": 3,
    "4": 4, "urgent": 4, "紧急": 4,
}

VALID_TYPES = ("REQUIREMENT", "DEFECT", "TASK", "EPIC")

# wuliu 项目实测值
ISSUE_TYPE_ID = {
    "REQUIREMENT": 7736139,
}

TYPE_LABEL = {
    "REQUIREMENT": "需求",
    "DEFECT": "缺陷",
    "TASK": "任务",
    "EPIC": "史诗",
}

PRIORITY_LABEL = {0: "无", 1: "低", 2: "普通", 3: "高", 4: "紧急"}

TYPE_PATH_MAP = {
    "REQUIREMENT": "requirements",
    "DEFECT": "bug-tracking",
    "TASK": "tasks",
    "EPIC": "epics",
}

WATERMARK = "\n\n---\n*Created by Hermes Agent*"


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


def load_default_assignee_id() -> int | None:
    hermes_home = Path(os.environ.get("HERMES_HOME", Path.home() / ".hermes"))
    env_file = hermes_home / ".env"

    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            if line.startswith("CODING_DEFAULT_ASSIGNEE_ID="):
                try:
                    return int(line.split("=", 1)[1].strip().strip("'\""))
                except ValueError:
                    return None
    return None


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
        print(f"CODING API HTTP 错误 ({e.code}): {text}", file=sys.stderr)
        sys.exit(1)
    except URLError as e:
        print(f"网络错误: {e.reason}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="在 CODING 创建事项")
    parser.add_argument("--name", required=True, help="事项名称")
    parser.add_argument("--desc", default="", help="事项描述（内联）")
    parser.add_argument("--desc-file", help="从文件读取事项描述（优先于 --desc）")
    parser.add_argument("--type", default="REQUIREMENT", help="事项类型：REQUIREMENT（默认）| DEFECT | TASK | EPIC")
    parser.add_argument("--priority", default="2", help="优先级：0-4 或 none/low/normal/high/urgent")
    parser.add_argument("--project", default="wuliu", help="ProjectName（默认：wuliu）")
    parser.add_argument("--team", default="mabangerp", help="团队域名前缀（默认：mabangerp）")
    args = parser.parse_args()

    issue_type = args.type.upper()
    if issue_type not in VALID_TYPES:
        print(f"错误：无效的 --type \"{issue_type}\"，可用值：{' | '.join(VALID_TYPES)}", file=sys.stderr)
        sys.exit(1)

    priority_key = args.priority.lower()
    if priority_key not in PRIORITY_MAP:
        print(f"错误：无效的 --priority \"{args.priority}\"", file=sys.stderr)
        print("可用值：0/none/无  1/low/低  2/normal/普通  3/high/高  4/urgent/紧急", file=sys.stderr)
        sys.exit(1)
    priority = PRIORITY_MAP[priority_key]

    description = ""
    if args.desc_file:
        desc_path = Path(args.desc_file).resolve()
        if not desc_path.exists():
            print(f"错误：找不到描述文件 \"{desc_path}\"", file=sys.stderr)
            sys.exit(1)
        description = desc_path.read_text(encoding="utf-8").strip()
    elif args.desc:
        description = args.desc.strip()

    description += WATERMARK

    token = load_coding_token()
    if not token:
        print("错误：找不到 CODING_TOKEN，请在 ~/.hermes/.env 中配置", file=sys.stderr)
        sys.exit(1)

    base_url = f"https://{args.team}.coding.net/open-api"

    body = {
        "Action": "CreateIssue",
        "ProjectName": args.project,
        "Type": issue_type,
        "Name": args.name,
        "Priority": str(priority),
        "CustomFieldValues": [
            {"Id": 38020331, "Content": "0000"},
        ],
    }

    if description:
        body["Description"] = description

    type_id = ISSUE_TYPE_ID.get(issue_type)
    if type_id:
        body["IssueTypeId"] = type_id

    assignee_id = load_default_assignee_id()
    if assignee_id:
        body["AssigneeId"] = assignee_id

    data = call_coding_api(base_url, token, body)

    if data.get("Response", {}).get("Error"):
        err = data["Response"]["Error"]
        print(f"API 错误 [{err.get('Code')}]: {err.get('Message')}", file=sys.stderr)
        sys.exit(1)

    issue = data.get("Response", {}).get("Issue")
    if not issue:
        print("创建失败：API 未返回事项数据", file=sys.stderr)
        print(json.dumps(data, indent=2, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)

    type_path = TYPE_PATH_MAP.get(issue_type, "issues")

    print("✅ 事项创建成功")
    print()
    print(f"## {issue.get('Title') or args.name}")
    print()
    print(f"- **事项编号**: #{issue.get('Code')}")
    print(f"- **类型**: {TYPE_LABEL.get(issue_type, issue_type)}")
    print(f"- **优先级**: {PRIORITY_LABEL.get(priority, priority)}")
    print(f"- **状态**: {issue.get('IssueStatusName') or issue.get('IssueStatus') or '-'}")
    print(f"- **链接**: https://{args.team}.coding.net/p/{args.project}/{type_path}/issues/{issue.get('Code')}/detail")


if __name__ == "__main__":
    main()
