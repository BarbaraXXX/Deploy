# interview-vectordb

面经偏好聚合服务。从非结构化面经中提取公司/岗位的面试风格 Profile，供 Agent 注入系统提示词。

## 架构

```
src/interview_vectordb/
  __main__.py     入口              REST + MCP 双模式服务
  cli.py          CLI               import / regen / list / profile 命令
  api.py          REST API          FastAPI，6 个端点
  server.py       MCP Server        FastMCP，4 个工具
  db.py           ProfileDB         JSON 文件存储 + LLM 分层聚合
  schema.py       数据模型          InterviewExperience + InterviewProfile
  config.py       配置               LLMSettings / MCPServerSettings

data/
  experiences/    面经原始文件        {company}_{position}_{uuid}.json
  profiles/       聚合后的 Profile   {company}_{position}.json
```

## 数据模型

### InterviewExperience（输入）
```python
company: str       # 公司名
position: str      # 岗位名
raw_text: str      # 非结构化面经文本，任意格式
```

### InterviewProfile（输出）
```python
company: str              # 公司名
position: str             # 岗位名
difficulty_tendency: str  # 难度倾向 junior/mid/senior
focus_areas: list[str]    # 考查重点领域
interview_style: str      # 面试风格描述
question_types: list[str] # 常见问题类型
key_traits: list[str]     # 区分性特征
source_count: int         # 聚合来源面经数量
```

## 聚合策略

LLM 分层聚合，控制单次 token 消耗：

| 面经数量 | 策略 | LLM 调用次数 |
|---|---|---|
| 1 份 | 直接生成 Profile | 1 |
| 2-5 份 | 逐份提取摘要 → 合并生成 | N+1 |
| 6+ 份 | 逐份摘要 → 分组合并 → 最终聚合 | N + ⌈N/5⌉ + 1 |

## 调试

### 基础操作

```bash
cd interview-vectordb
uv sync

# 导入面经（单个 JSON 文件或目录）
uv run interview-vectordb import /path/to/experiences/

# 生成所有 Profile
uv run interview-vectordb regen

# 查看已有 Profile
uv run interview-vectordb list

# 查看指定 Profile
uv run interview-vectordb profile 字节跳动 后端工程师

# 启动服务
uv run interview-vectordb          # REST (9000) + MCP (9000/mcp)
```

### .env 配置

```bash
LLM_BASE_URL=https://api.deepseek.com
LLM_API_KEY=sk-xxx
LLM_MODEL=deepseek-chat
MCP_SERVER_PORT=9000
```

### REST API

| 端点 | 方法 | 说明 |
|---|---|---|
| `/api/profiles` | GET | 列出所有 Profile（摘要） |
| `/api/profiles/{company}/{position}` | GET | 获取/生成 Profile |
| `/api/profiles/{company}/{position}` | DELETE | 删除 Profile |
| `/api/profiles/{company}/{position}/generate` | POST | 强制重新生成 |
| `/api/experiences/count` | GET | 按公司/岗位统计面经数 |
| `/api/experiences/import` | POST | 批量导入面经 |

### MCP 工具

| 工具 | 说明 |
|---|---|
| `get_profile(company, position)` | 获取 Profile（不存在则自动生成） |
| `list_profiles()` | 列出所有 Profile |
| `delete_profile(company, position)` | 删除 Profile |
| `batch_generate_profiles()` | 批量重新生成 |

### 验证检查

```bash
# 检查导入
uv run python -c "from interview_vectordb.db import ProfileDB; print('OK')"

# 检查 LLM 配置
uv run python -c "from interview_vectordb.config import llm_settings; print(f'{llm_settings.model} @ {llm_settings.base_url}')"

# 检查 REST API
uv run python -c "
from interview_vectordb.api import api_app
routes = [r.path for r in api_app.routes if hasattr(r, 'path')]
print(routes)
"

# 检查已有数据
uv run python -c "
from interview_vectordb.db import ProfileDB
db = ProfileDB()
exps = db._load_all_experiences()
from collections import Counter
keys = Counter((e.company, e.position) for e in exps)
for (c, p), n in keys.items():
    print(f'  {c}/{p}: {n} experiences')
"
```

### 面经文件格式

每份面经一个 JSON 文件，格式：
```json
{
  "company": "字节跳动",
  "position": "后端工程师",
  "raw_text": "字节后端二面，面官上来问了三个系统设计题..."
}
```

文件命名规则：`{company}_{position}_{uuid}.json`（由系统自动生成，导入时无需关心）。

也支持导入包含数组的 JSON 文件：
```json
[
  {"company": "字节", "position": "后端", "raw_text": "..."},
  {"company": "腾讯", "position": "前端", "raw_text": "..."}
]
```
