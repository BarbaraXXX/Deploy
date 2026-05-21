# interview-agent

LangGraph 面试 Agent，支持 JD 注入、面经偏好注入、JWT 认证、SSE 流式输出。

## 架构

```
web/src/                          # React 前端
  App.tsx                           LoginView / SetupView / ChatView
  api.ts                            API 调用 + SSE 流
  index.css                         暗色主题样式

src/interview_agent/
  server.py       FastAPI 入口      路由、认证、SSE、vectordb 代理
  agent.py        LangGraph 图      StateGraph(MessagesState) + MCP 工具
  prompts.py      系统提示词         build_system_prompt(domain, difficulty, jd, profile)
  session.py      会话管理          内存中 InterviewSession，TTL 1h
  auth.py         JWT 认证          bcrypt + JWT，用户数据 data/users.json
  config.py       配置               LLMSettings / MCPSettings / AuthSettings / VectorDBSettings
  jd_parser.py    JD 结构化          LLM 提取 StructuredJD，注入提示词
  mcp_client.py   MCP 客户端         连接外部 MCP Server
  main.py         CLI 入口          交互式命令行面试
```

## 系统提示词注入

`build_system_prompt(domain, difficulty, structured_jd, structured_profile)` 按顺序拼接：

1. **领域描述** — 预设 8 个领域或自定义
2. **难度描述** — junior/mid/senior
3. **JD 信息** — 可选，LLM 从原始 JD 提取的结构化信息
4. **面试偏好** — 可选，从 interview-vectordb 获取的 Profile
5. **面试规则 + 注意事项** — 固定模板

## 调试

### 后端

```bash
cd interview-agent
uv sync

# 启动服务（前端已构建时）
uv run interview-agent-server

# CLI 模式
uv run interview-agent

# 检查导入
uv run python -c "from interview_agent.server import app; print('OK')"

# 检查 LLM 配置
uv run python -c "from interview_agent.config import llm_settings; p=llm_settings.get_provider(); print(f'{p.model} @ {p.base_url}')"
```

### 前端

```bash
cd interview-agent/web
npm install
npm run dev          # Vite 开发服务器 (端口 5173，代理 API 到 8000)
npm run build        # 生产构建到 dist/
```

开发时用 `npm run dev`，修改前端代码实时热更新。生产模式用 `npm run build` 后由 FastAPI 静态文件服务。

### .env 关键配置

```bash
# LLM（必填）
LLM_DEFAULT_PROVIDER=deepseek
LLM_PROVIDERS={"local":{"base_url":"http://10.2.133.86:10087/v1","api_key":"","model":"Qwen_Qwen3.6-27B-Q6_K_M.gguf"},"deepseek":{"base_url":"https://api.deepseek.com/v1","api_key":"sk-xxx","model":"deepseek-chat"}}

# MCP（可选，连接 vectordb）
MCP_SERVER_URLS=http://localhost:9000/mcp

# Profile 代理（可选，连接 vectordb REST API）
VECTORDB_BASE_URL=http://localhost:9000

# 认证（生产必须改）
AUTH_SECRET_KEY=change-me-in-production
```

### 常见问题

| 问题 | 原因 | 解决 |
|---|---|---|
| 前端没显示新功能 | 浏览器缓存 | Cmd+Shift+R 硬刷新 |
| LLM 502 错误 | .env 未加载或 API 不可达 | 检查 `llm_settings.get_provider()` 输出 |
| 面试偏好下拉为空 | vectordb 未启动或未生成 Profile | 先启动 vectordb，运行 `regen` |
| 旧账号无法登录 | 密码格式从 SHA256 迁移到 bcrypt | 删除 data/users.json 中旧格式条目，重新注册 |

## Docker 部署

```bash
cd interview-agent/deploy
# 编辑 .env: LLM_DEFAULT_PROVIDER, LLM_PROVIDERS, AUTH_SECRET_KEY, SSL_DOMAIN
bash deploy.sh
```

Nginx 反代 8000 → 80/443，自动 Let's Encrypt 证书。
