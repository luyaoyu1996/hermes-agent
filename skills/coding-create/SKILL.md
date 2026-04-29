---
name: coding-create
description: 在 CODING 项目中创建事项（需求/缺陷/任务），支持指定类型、优先级和描述。
version: 1.0.0
author: luyaoyu
license: MIT
dependencies: []
metadata:
  hermes:
    tags: [CODING, Issues, Create, Project Management]
    requires:
      env: [CODING_TOKEN]
    primaryEnv: CODING_TOKEN

---

# CODING 事项创建

在马帮ERP物流-海外仓产品线（ProjectName: `wuliu`）创建事项。

## 前置条件

`~/.hermes/.env` 中需配置 `CODING_TOKEN`（与 `coding` 查询 skill 共用同一个 token，需有事项写权限）。

## 默认行为

| 参数 | 默认值 | 说明 |
|------|--------|------|
| 团队 | `mabangerp` | mabangerp.coding.net |
| 项目 | `wuliu` | 马帮ERP物流-海外仓产品线 |
| 类型 | `REQUIREMENT` | 未声明缺陷时一律建需求 |
| 优先级 | `2`（普通） | 可由 Agent 根据上下文判断 |

## 优先级参考

| 值 | 别名 | 适用场景 |
|----|------|---------|
| 4 | urgent / 紧急 | 线上故障、核心功能不可用 |
| 3 | high / 高 | 影响主流程、有 DDL 的需求 |
| 2 | normal / 普通 | 常规需求或非阻塞缺陷（**默认**） |
| 1 | low / 低 | 优化类、无明确时间要求 |
| 0 | none / 无 | 无优先级 |

## 用法

```bash
# 最简用法（类型默认 REQUIREMENT，优先级默认普通）
python {baseDir}/scripts/create_issue.py --name "事项名称"

# 创建需求，带描述
python {baseDir}/scripts/create_issue.py \
  --name "新增批量导出功能" \
  --desc "支持 Excel 和 CSV 两种格式，入口在订单列表页右上角"

# 创建缺陷，紧急
python {baseDir}/scripts/create_issue.py \
  --name "订单同步接口超时" \
  --type DEFECT \
  --priority urgent

# 从文件读取描述（适合长文本）
python {baseDir}/scripts/create_issue.py \
  --name "重构海外仓入库流程" \
  --desc-file /tmp/issue_desc.txt

# 指定其他项目
python {baseDir}/scripts/create_issue.py \
  --name "..." \
  --project <ProjectName>
```

## 输出示例

```
✅ 事项创建成功

## 新增批量导出功能

- **事项编号**: #1024
- **类型**: 需求
- **优先级**: 普通
- **状态**: 未开始
- **链接**: https://mabangerp.coding.net/p/wuliu/requirements/issues/1024/detail
```

## 注意

- 创建事项**不可撤销**，执行前请确认名称和类型正确
- CODING_TOKEN 需有对应项目的事项写权限，否则返回 `UnauthorizedOperation`
