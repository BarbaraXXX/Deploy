# InterviewLG

模拟技术面试系统，基于 LangGraph Agent + 面经偏好分析 + Web 前端。

## 项目结构

```
interviewLG/
├── interview-agent/        # 面试 Agent（LangGraph + FastAPI + React）
├── interview-vectordb/     # 面经偏好服务（Profile 聚合 + MCP Server + REST API）
└── data/                   # 运行时数据（不上传 git）
    ├── experiences/        # 面经原始文件
    └── profiles/           # 聚合后的 Profile
```

## 架构

```
┌─────────────┐     ┌──────────────────┐     ┌──────────────────┐
│   浏览器     │────▶│  interview-agent │────▶│ interview-vectordb│
│  React SPA  │◀────│  FastAPI :8000   │◀────│  FastAPI :9000    │
│             │     │                  │     │  + MCP :9000/mcp  │
│             │     │  LangGraph Agent │     │  ProfileDB (JSON) │
│             │     │  JWT Auth        │     │  LLM 聚合(DeepSeek)│
└─────────────┘     └──────────────────┘     └──────────────────┘
```

**数据流**：
1. 前端选择领域/难度/JD/偏好 → Agent 创建会话
2. Agent 调用 vectordb 获取 Profile → 注入系统提示词
3. JD 经 LLM 结构化 → 注入系统提示词
4. 面试全程由 LangGraph Agent 驱动，SSE 流式输出

## 快速调试

### 前置条件

- Python 3.11+, uv, Node.js 18+
- DeepSeek API Key（或其他 OpenAI 兼容 API）

### 1. 配置 .env

```bash
# interview-agent/.env
cp interview-agent/.env.example interview-agent/.env
# 编辑 LLM_PROVIDERS 填入 API Key

# interview-vectordb/.env
cp interview-vectordb/.env.example interview-vectordb/.env
# 编辑 LLM_API_KEY 填入 API Key
```

### 2. 启动 vectordb（先启动）

```bash
cd interview-vectordb
uv sync
uv run interview-vectordb         # 启动 REST+MCP 服务 (端口 9000)
```

### 3. 导入面经 & 生成 Profile

```bash
cd interview-vectordb
uv run interview-vectordb import /path/to/experiences/   # 导入面经
uv run interview-vectordb regen                          # 生成 Profile
uv run interview-vectordb list                           # 查看 Profile
```

### 4. 启动 Agent

```bash
cd interview-agent
uv sync
cd web && npm install && npm run build && cd ..   # 构建前端
uv run interview-agent-server                     # 启动服务 (端口 8000)
```

### 5. 访问

浏览器打开 http://localhost:8000

### 6. 连接 Profile

在 `interview-agent/.env` 中设置：
```
VECTORDB_BASE_URL=http://localhost:9000
```

前端 SetupView 的"面试偏好"下拉框会自动加载已有 Profile。

## Docker 部署

```bash
cd interview-agent/deploy
# 编辑 .env 和 deploy.sh 中的域名/邮箱
bash deploy.sh
```

## CLI 模式（无前端）

```bash
cd interview-agent
uv run interview-agent    # 交互式 CLI 面试
```
