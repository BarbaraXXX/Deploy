# Interview Tester

面试 Agent 自动化测试工具。通过模拟 AI 候选人与面试 Agent 对话，记录完整面试过程，并从多个维度评估面试 Agent 的表现。

## 架构

```
┌──────────────┐     ┌──────────────────┐
│  测试 Agent   │────▶│  面试 Agent       │
│  (Candidate)  │◀────│  (Interviewer)   │
│  模拟候选人    │     │  LangGraph Agent  │
└──────┬───────┘     └──────────────────┘
       │                      │
       ▼                      ▼
┌──────────────┐     ┌──────────────────┐
│  评估 Agent   │     │  面试记录 (JSON)  │
│  (Evaluator)  │     │  data/sessions/  │
│  多维度评分    │     │                  │
└──────────────┘     └──────────────────┘
```

**工作流程**：
1. 测试 Agent 启动面试 Agent，以"你好，我准备好面试了"开场
2. 面试 Agent 提问 → 测试 Agent 模拟候选人回答 → 面试 Agent 追问 → 循环
3. 检测到面试结束信号后，评估 Agent 对整场面试进行多维度评估
4. 结果保存为 JSON 文件

## 项目结构

```
interview-tester/
├── src/interview_tester/
│   ├── main.py          # CLI 入口，交互式运行测试
│   ├── server.py        # FastAPI Web 服务，SSE 流式输出
│   ├── candidate.py     # 候选人 Agent，模拟不同水平的候选人
│   ├── evaluator.py     # 评估 Agent，多维度评分
│   ├── recorder.py      # 会话记录器，保存 JSON
│   ├── schemas.py       # 数据模型（TestConfig, QAPair, Evaluation, TestSession）
│   └── config.py        # 配置管理，读取 .env
├── web/
│   └── index.html       # Web 前端 SPA（单文件，无构建步骤）
├── data/sessions/       # 测试会话 JSON 输出目录
├── pyproject.toml       # 项目依赖和入口
└── .env.example         # 环境变量示例
```

## 快速开始

### 前置条件

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) 包管理器
- 有效的 LLM API Key（配置在 `../interview-agent/.env`）

### 安装

```bash
cd interview-tester
uv sync
```

### 运行

**CLI 模式**：

```bash
uv run interview-tester --domain backend --difficulty mid --candidate-level mid --max-rounds 50
```

**Web 模式**：

```bash
uv run interview-tester-server
```

浏览器打开 http://localhost:8765

## 使用方式

### CLI

```bash
# 后端开发，中级难度，中级候选人，最多 50 轮
uv run interview-tester --domain backend --difficulty mid --candidate-level mid --max-rounds 50

# 算法，高级难度，高级候选人
uv run interview-tester --domain algorithm --difficulty senior --candidate-level senior

# 可用领域: backend, frontend, fullstack, algorithm, embedded, devops, data, security
# 可用难度: junior, mid, senior
```

CLI 会在终端实时输出每轮对话，测试完成后打印评估结果和 JSON 文件路径。

### Web

1. 打开 http://localhost:8765
2. 选择领域、难度、候选人水平
3. 点击"开始测试"，实时观看面试对话
4. 面试结束后查看评估结果
5. 可在"查看历史记录"中回看过往测试

## 测试输出

每次测试生成一个 JSON 文件，保存在 `data/sessions/` 目录：

```json
{
  "session_id": "test_20240101_120000_1234",
  "config": {
    "domain": "backend",
    "difficulty": "mid",
    "candidate_level": "mid",
    "max_rounds": 50
  },
  "started_at": "2024-01-01T12:00:00+00:00",
  "ended_at": "2024-01-01T12:15:00+00:00",
  "qa_pairs": [
    {
      "round": 1,
      "question": "请介绍一下你的后端开发经验...",
      "answer": "我有大约3-5年的后端开发经验...",
      "question_timestamp": "2024-01-01T12:00:05+00:00",
      "answer_timestamp": "2024-01-01T12:00:15+00:00"
    }
  ],
  "total_rounds": 8,
  "status": "completed",
  "evaluation": {
    "style_naturalness": 7,
    "difficulty_appropriateness": 8,
    "follow_up_quality": 6,
    "topic_coverage": 7,
    "overall_score": 7,
    "strengths": ["追问深入", "话题覆盖广"],
    "weaknesses": ["部分追问缺乏逻辑递进"],
    "summary": "面试 Agent 整体表现良好...",
    "improvement_suggestions": ["增加场景化提问", "优化追问逻辑"]
  }
}
```

## 评估维度

| 维度 | 字段 | 说明 |
|------|------|------|
| 对话自然度 | `style_naturalness` | 面试官的提问和回应是否自然流畅，避免机械感 |
| 难度适当性 | `difficulty_appropriateness` | 问题难度是否匹配设定难度和候选人水平 |
| 追问质量 | `follow_up_quality` | 面试官根据候选人回答进行追问的质量和深度 |
| 话题覆盖 | `topic_coverage` | 面试涉及的知识面广度，是否覆盖该领域核心话题 |
| 总体评分 | `overall_score` | 对面试官整体表现的综合评价（1-10 分） |

## 配置

### 环境变量

LLM 配置共享 `../interview-agent/.env`，无需重复配置。

本项目专属变量（`interview-tester/.env`）：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `TEST_CANDIDATE_TEMPERATURE` | 0.7 | 候选人 LLM 温度，越高回答越有创造性 |
| `TEST_EVALUATOR_TEMPERATURE` | 0.3 | 评估 LLM 温度，越低评估越一致 |

### .env.example

```bash
# 候选人 LLM 温度（越高越有创造性）
TEST_CANDIDATE_TEMPERATURE=0.7
# 评估 LLM 温度（越低越一致）
TEST_EVALUATOR_TEMPERATURE=0.3
```

## 开发

### 添加新领域

在 `candidate.py` 的 `get_candidate_system_prompt` 中无需修改，领域描述由面试 Agent 侧处理。如需自定义候选人行为，可修改对应的 prompt 模板。

### 修改评估维度

1. 在 `schemas.py` 的 `Evaluation` 模型中添加新字段
2. 在 `evaluator.py` 的 `_EVALUATOR_PROMPT` 中添加评估维度描述和 JSON 格式
3. 在 Web 前端 `web/index.html` 的评分卡片区域添加对应展示

### 依赖关系

```
interview-tester
├── interview-agent (path dependency, 可编辑安装)
│   └── 提供: build_interview_agent(), llm_settings
├── langchain-openai >= 0.3.0
├── pydantic >= 2.0.0
├── pydantic-settings >= 2.0.0
├── python-dotenv >= 1.0.0
├── fastapi >= 0.115.0
├── uvicorn >= 0.30.0
└── sse-starlette >= 2.0.0
```
