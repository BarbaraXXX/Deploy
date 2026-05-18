# Interview Agent

基于 LangGraph 的模拟技术面试 Agent，通过 MCP Client 接入外部工具能力，支持 Web 部署。

## 快速开始

```bash
# 安装 Python 依赖
uv sync

# 配置环境变量
cp .env.example .env
# 编辑 .env，填入 LLM provider 配置和认证密钥

# 构建前端
cd web && npm install && npm run build && cd ..

# 启动服务（前端 + API 一体）
uv run interview-agent-server
```

访问 http://localhost:8000 ，注册账号后即可开始面试。

### CLI 模式

不需要前端，纯命令行交互（无需登录）：

```bash
uv run interview-agent
```

## 配置说明

所有配置通过 `.env` 文件管理，支持环境变量覆盖。

### LLM 多 Provider 配置

支持同时配置多个 OpenAI 兼容 API（本地模型、DeepSeek、通义千问、智谱等），通过 `LLM_DEFAULT_PROVIDER` 指定默认使用的 provider。

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `LLM_DEFAULT_PROVIDER` | `local` | 默认 provider 名称 |
| `LLM_PROVIDERS` | `{}` | Provider 配置 JSON |

`LLM_PROVIDERS` 格式：

```json
{
  "local": {
    "base_url": "http://localhost:11434/v1",
    "api_key": "",
    "model": "qwen2.5:7b"
  },
  "deepseek": {
    "base_url": "https://api.deepseek.com/v1",
    "api_key": "sk-xxx",
    "model": "deepseek-chat"
  }
}
```

本地模型的 `api_key` 可留空。

### 认证配置

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `AUTH_SECRET_KEY` | `change-me-in-production` | JWT 签名密钥（**生产环境必须更改**） |
| `AUTH_TOKEN_EXPIRE_HOURS` | `24` | Token 过期时间（小时） |

### MCP Server 配置

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `MCP_SERVER_URLS` | 空 | HTTP 传输的 MCP Server URL，逗号分隔 |
| `MCP_STDIO_COMMAND` | 空 | stdio 传输的启动命令 |
| `MCP_STDIO_ARGS` | 空 | stdio 传输的命令参数 |

MCP Server 未配置或不可达时，自动降级为纯 LLM 模式。

## 面试领域

支持 8 个预设领域 + 任意自定义领域：

| 预设领域 | 说明 |
|----------|------|
| `backend` | 后端开发（Python/Java/Go、数据库、微服务、API 设计） |
| `frontend` | 前端开发（JS/TS、React/Vue、浏览器原理、性能优化） |
| `fullstack` | 全栈开发（前后端 + DevOps + 系统设计） |
| `algorithm` | 算法与数据结构（排序/搜索、DP、图论） |
| `embedded` | 嵌入式开发（C/C++、RTOS、驱动、SPI/I2C/UART） |
| `devops` | 运维（CI/CD、Docker/K8s、监控、基础设施即代码） |
| `data` | 数据工程（SQL、ETL、Spark/Flink、数据仓库） |
| `security` | 网络安全（渗透测试、密码学、应急响应） |

在前端页面或 CLI 中输入自定义领域名称（如"游戏开发"、"量化交易"），LLM 会自动适配。

## 项目结构

```
interview-agent/
├── pyproject.toml
├── .env.example
├── web/                        # React + Vite 前端
│   ├── src/
│   │   ├── App.tsx             # 登录页 + 面试设置页 + 对话页
│   │   ├── api.ts              # API 客户端（SSE 流式 + JWT 认证）
│   │   └── index.css           # 设计系统
│   └── dist/                   # 构建产物（由 FastAPI 静态服务）
├── src/interview_agent/
│   ├── __init__.py
│   ├── auth.py                 # JWT 认证（注册/登录/鉴权）
│   ├── config.py               # 多 Provider + 认证配置
│   ├── mcp_client.py           # MCP Client 连接（langchain-mcp-adapters）
│   ├── prompts.py              # 面试系统提示词（预设领域 + 自定义）
│   ├── agent.py                # LangGraph StateGraph 图定义
│   ├── session.py              # 多用户会话管理
│   ├── server.py               # FastAPI + SSE + 静态文件服务
│   └── main.py                 # CLI 交互入口
```

## API

### 认证

| 方法 | 路径 | 认证 | 说明 |
|------|------|------|------|
| POST | `/api/auth/register` | 无 | 注册，返回 JWT |
| POST | `/api/auth/login` | 无 | 登录，返回 JWT |
| GET | `/api/auth/me` | Bearer | 验证 token，返回用户名 |

### 面试

| 方法 | 路径 | 认证 | 说明 |
|------|------|------|------|
| GET | `/api/domains` | 无 | 获取预设领域列表 |
| GET | `/api/providers` | Bearer | 获取可用 LLM provider |
| POST | `/api/sessions` | Bearer | 创建面试会话 |
| POST | `/api/chat/stream` | Bearer | SSE 流式对话 |
| DELETE | `/api/sessions/{id}` | Bearer | 删除会话 |

所有 Bearer 认证的接口需在请求头添加 `Authorization: Bearer <token>`，401 时前端自动跳转登录页。

## 开发模式

前后端分别启动，支持热更新：

```bash
# 终端 1: 后端
uv run uvicorn interview_agent.server:app --reload --port 8000

# 终端 2: 前端（vite dev server 自带 /api 代理到 8000）
cd web && npm run dev
```

访问 http://localhost:5173 。

## 服务器部署

### 前提条件

- Linux x86 服务器，已安装 Docker 和 Docker Compose
- 域名已解析到服务器 IP
- 80 和 443 端口对外开放

### 步骤

**1. 上传项目到服务器**

```bash
# 本地
scp -r interview-agent/ user@your-server:/opt/interview-agent/
```

**2. 配置 .env**

```bash
# 服务器
cd /opt/interview-agent
cp .env.example .env
vim .env
```

必须修改的项：

```env
# 改为你的 LLM 配置
LLM_DEFAULT_PROVIDER=deepseek
LLM_PROVIDERS={"deepseek":{"base_url":"https://api.deepseek.com/v1","api_key":"sk-xxx","model":"deepseek-chat"}}

# 必须修改！用随机长字符串
AUTH_SECRET_KEY=your-random-secret-key-at-least-32-chars

# 域名和证书邮箱
SSL_DOMAIN=interview.your-domain.com
SSL_EMAIL=admin@your-domain.com
```

**3. 一键部署**

```bash
cd deploy
./deploy.sh
```

脚本会自动：
- 首次运行时通过 Let's Encrypt 获取 SSL 证书
- 构建 Docker 镜像（前端 + 后端）
- 启动 Nginx（HTTPS 反代）+ App + Certbot（自动续期）

部署完成后访问 `https://interview.your-domain.com`。

### 常用运维命令

```bash
cd /opt/interview-agent/deploy

# 查看日志
docker compose logs -f app

# 重启
docker compose restart

# 重新构建并启动（更新代码后）
docker compose up -d --build

# 停止
docker compose down
```

### 架构

```
客户端 → Nginx (443/HTTPS) → App (8000)
                                ↓
                          LLM API (外部)
                                ↓
                          MCP Server (可选)
```

- `nginx` — HTTPS 终止、反向代理、静态文件缓存
- `app` — FastAPI 应用（API + 前端静态文件）
- `certbot` — SSL 证书自动续期
- `data/` — 用户数据持久化（users.json），挂载到宿主机
