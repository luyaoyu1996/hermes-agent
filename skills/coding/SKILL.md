---
name: coding
description: Query CODING project issues via CODING Open API. Supports fetching issue details and listing issues by project.
version: 1.0.0
author: luyaoyu
license: MIT
dependencies: []
metadata:
  hermes:
    tags: [CODING, Issues, Project Management]
    requires:
      env: [CODING_TOKEN]
    primaryEnv: CODING_TOKEN

---

# CODING 事项查询

通过 CODING Open API 查询事项详情或事项列表。

## 前置条件

`~/.hermes/.env` 中需配置 `CODING_TOKEN`（CODING 个人令牌，需有事项读权限）。

## 使用方式

查询事项详情（通过 URL）：

```bash
python {baseDir}/scripts/issue.py --url "https://mabangerp.coding.net/p/wuliu/requirements/issues/105402/detail"
```

查询事项详情（通过项目名 + 编号）：

```bash
python {baseDir}/scripts/issue.py --project wuliu --code 105402
```

查询事项列表：

```bash
python {baseDir}/scripts/issues.py --project wuliu
python {baseDir}/scripts/issues.py --project wuliu --limit 20 --offset 0
python {baseDir}/scripts/issues.py --project wuliu --type REQUIREMENT
```

## 参数说明

### issue.py（事项详情）

| 参数 | 说明 |
|------|------|
| `--project <name>` | 项目名称 |
| `--code <number>` | 事项编号 |
| `--url <url>` | 事项 URL（自动解析 project 和 code） |
| `--team <name>` | 团队名，默认从 URL 解析或使用 `e.coding.net` |

### issues.py（事项列表）

| 参数 | 说明 |
|------|------|
| `--project <name>` | 项目名称（必填） |
| `--limit <n>` | 每页数量，默认 20，最大 50 |
| `--offset <n>` | 分页偏移，默认 0 |
| `--type <type>` | 事项类型：`ALL`（默认）、`REQUIREMENT`、`BUG`、`TASK` |
| `--team <name>` | 团队名，若域名为 `{team}.coding.net` 时使用 |

## 说明

- 从事项 URL 解析：支持 `/p/{Project}/issues/{Code}/` 和 `/p/{Project}/requirements/issues/{Code}/` 等格式
- API 限流约 30 次/秒
