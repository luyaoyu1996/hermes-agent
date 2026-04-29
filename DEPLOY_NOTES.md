# Hermes Agent 部署与开发笔记

## 项目概况

- 仓库：https://github.com/luyaoyu1996/hermes-agent（fork 自 NousResearch/hermes-agent）
- 版本：v0.9.0
- 技术栈：Python 3.11 + Node.js
- 服务器：腾讯云 OpenCloudOS 9.4（2C4G），IP 见服务器配置

## 服务器部署方式

采用**直接安装**（非 Docker），因为 2C4G 机器跑 Docker build 太慢。

### 安装路径

- 代码：`/opt/hermes-agent`
- 虚拟环境：`/opt/hermes-agent/venv`
- 配置目录：`~/.hermes/`
- 日志：`/var/log/hermes-gateway.log`

### 关键配置文件

**~/.hermes/.env**
```bash
DASHSCOPE_API_KEY=sk-sp-03cfbb3b4809421c8468792efcd44519
DASHSCOPE_BASE_URL=https://coding.dashscope.aliyuncs.com/v1
WECOM_BOT_ID=aibhVLKyKLZlq8lwZCDJYINPK-R2aLDjRwZ
WECOM_SECRET=dGTYyC7DHLz3brXa9r2Ksy1eCI9EgE7tqlkwOKzOOdN
WECOM_DM_POLICY=open
GATEWAY_ALLOW_ALL_USERS=true
TERMINAL_TIMEOUT=60
```

**~/.hermes/config.yaml**
```yaml
model:
  provider: custom
  model: doubao-seed-2.0-pro
  base_url: https://ark.cn-beijing.volces.com/api/coding/v3
  api_key: d97a4345-e9f7-4336-8914-fa52ddb7be98

terminal:
  backend: local
```

### Dockerfile 修改（备忘）

本地 Dockerfile 加了国内镜像源（npm 淘宝 + pip 清华），虽然最终没用 Docker 部署，但保留了修改以备后续使用。

## 企业微信接入

- 模式：WeCom AI Bot（WebSocket，无需公网端口）
- 启动命令：`hermes gateway`
- 后台运行：`nohup hermes gateway > /var/log/hermes-gateway.log 2>&1 &`
- 支持：私聊、群聊、图片/文件/语音、Markdown 渲染、自动重连
- 图片问题修复：已修改 [gateway/platforms/base.py](gateway/platforms/base.py)，取消 markdown 图片 URL 白名单限制；企业微信会尝试把回复中的 `![...](https://...)` 作为原生图片发送，失败时自动回退为文本链接

## 开发工作流

```
本地 PyCharm 改代码（D:\AI PROJECT\hermes-agent）
    ↓ Commit + Push
GitHub (luyaoyu1996/hermes-agent)
    ↓ 服务器执行
cd /opt/hermes-agent && git pull origin main
    ↓ 重启
kill %1 && nohup hermes gateway > /var/log/hermes-gateway.log 2>&1 &
```

## Git 管理详解

### 仓库关系

```
NousResearch/hermes-agent (upstream 上游原仓库)
    ↓ fork
luyaoyu1996/hermes-agent (origin 你的 fork，GitHub 上)
    ↓ clone                    ↓ clone
本地 D:\AI PROJECT\hermes-agent    腾讯云 /opt/hermes-agent
```

### Remote 配置

本地和服务器上都需要配置两个 remote：

```bash
# 查看当前 remote
git remote -v

# 应该看到：
# origin    https://github.com/luyaoyu1996/hermes-agent.git (fetch/push)
# upstream  https://github.com/NousResearch/hermes-agent.git (fetch/push)

# 如果没有 upstream，添加：
git remote add upstream https://github.com/NousResearch/hermes-agent.git
```

### 日常开发流程（本地 PyCharm）

```bash
# 1. 开发前先拉最新代码
git pull origin main

# 2. 在 PyCharm 里改代码

# 3. 提交（PyCharm GUI 或命令行）
git add <修改的文件>
git commit -m "feat: 描述你的改动"

# 4. 推送到你的 fork
git push origin main
```

PyCharm 等效操作：
| 命令行 | PyCharm |
|--------|---------|
| git pull | 工具栏蓝色 ↓ 箭头（Update Project） |
| git add + commit | Alt+0 打开 Commit 面板，勾选文件，写 message |
| git push | Commit and Push 按钮，或 Ctrl+Shift+K |
| git fetch upstream | Git → Fetch → 选 upstream |
| git merge upstream/main | Git → Merge → 选 upstream/main |

### 服务器更新部署

```bash
# SSH 登录服务器后
cd /opt/hermes-agent
git pull origin main

# 如果改了 Python 依赖（pyproject.toml / requirements.txt）
source venv/bin/activate
uv pip install -e ".[all]"

# 重启 gateway
# 先找到并杀掉旧进程
ps aux | grep "hermes gateway" | grep -v grep | awk '{print $2}' | xargs kill 2>/dev/null
nohup hermes gateway > /var/log/hermes-gateway.log 2>&1 &
```

### 同步上游更新（NousResearch 发布新版本时）

```bash
# 本地执行
git fetch upstream
git merge upstream/main

# 如果有冲突，在 PyCharm 里解决冲突后
git push origin main

# 然后去服务器拉取
ssh root@你的服务器IP
cd /opt/hermes-agent
git pull origin main
```

### 分支策略建议

- `main`：稳定版本，服务器部署用这个分支
- 功能开发建议新建分支：`git checkout -b feat/my-new-skill`
- 开发完成后合并回 main：PyCharm → Git → Merge → 选你的分支
- 合并后推送并在服务器更新

### .gitignore 注意事项

以下文件不应提交到 Git：
- `.env`（包含 API key 等敏感信息）
- `venv/`（虚拟环境）
- `node_modules/`（Node 依赖）
- `__pycache__/`
- `*.pyc`
- `.hermes/`（运行时配置）

## Skills 开发

- 仓库内 skills 路径：`skills/`，走 git 流程管理
- 运行时 skills 路径：`~/.hermes/skills/`（可直接在服务器创建，不走 git）
- 推荐走 git 流程，便于版本管理和回滚

## 从 OpenClaw 迁移

- 服务器上原有 OpenClaw 部署，配置在 `~/.openclaw/`
- 自动迁移失败（卡死），手动搬了 API key 和企业微信配置
- OpenClaw 的飞书配置未迁移（如需要可后续处理）

## 常用命令

```bash
# 启动交互式 CLI
hermes

# 启动 gateway（企业微信等消息平台）
hermes gateway

# 诊断
hermes doctor

# 切换模型
hermes model

# 查看配置
hermes config
```
