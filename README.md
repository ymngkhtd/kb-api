# Knowledge Base API (kb-api)

P.A.R.A. 个人知识库的本地 RESTful API 服务，支持笔记 CRUD、全文搜索、语义搜索和智能分类。

## 项目结构

```
kb-api/
├── app/
│   ├── main.py                  # FastAPI 入口 + 中间件
│   ├── config.py                # 全局配置（环境变量加载）
│   ├── auth/
│   │   ├── jwt.py               # JWT 生成/验证/刷新
│   │   ├── dependencies.py      # FastAPI 认证依赖注入
│   │   └── user_manager.py      # 用户加载 + bcrypt 验证
│   ├── routers/
│   │   ├── auth_router.py       # /auth/*  登录、刷新、用户信息
│   │   ├── notes_router.py      # /notes/* 笔记 CRUD
│   │   ├── search_router.py     # /search/* 全文 + 语义搜索
│   │   └── classify_router.py   # /classify/* P.A.R.A. 分类
│   ├── services/
│   │   ├── file_service.py      # 文件操作 + 路径沙箱 + Git 集成
│   │   ├── search_service.py    # 全文搜索（文本/正则）
│   │   ├── semantic_service.py  # 语义搜索（ChromaDB 向量存储）
│   │   └── para_classifier.py   # P.A.R.A. 规则引擎分类
│   ├── embedding/
│   │   ├── __init__.py          # Provider 工厂（懒加载单例）
│   │   ├── base.py              # EmbeddingProvider 抽象基类
│   │   ├── local_provider.py    # sentence-transformers 本地模型
│   │   └── openai_provider.py   # OpenAI 兼容 API
│   ├── models/                  # Pydantic 数据模型
│   ├── schemas/                 # 请求/响应 Schema
│   └── utils/
│       └── path_utils.py        # 路径安全校验
├── config/
│   └── users.yaml               # 用户配置（含白名单）
├── skill/
│   ├── SKILL.md                 # Agent OpenAPI Skill 定义
│   └── references/
│       └── para-rules.md        # P.A.R.A. 分类规则参考
├── scripts/
│   └── hash_password.py         # 密码哈希生成工具
├── data/chroma/                 # ChromaDB 向量存储（运行时生成）
├── logs/                        # 审计日志（运行时生成）
├── run.py                       # 启动入口
├── requirements.txt
├── .env.example
└── .gitignore
```

## 快速开始

### 1. 安装依赖

```bash
cd kb-api
pip install -r requirements.txt
```

### 2. 配置

```bash
# 复制环境变量模板
cp .env.example .env
# 按需编辑 .env
```

### 3. 生成用户密码

```bash
# 交互式输入
python scripts/hash_password.py

# 或直接传参
python scripts/hash_password.py "your-password"
```

将生成的哈希填入 `config/users.yaml` 中对应用户的 `password_hash` 字段。

### 4. 启动服务

```bash
python run.py
```

服务启动后访问 http://127.0.0.1:8000/docs 查看 Swagger UI。

## 核心功能

### 认证 (JWT)

| 端点 | 方法 | 说明 |
|------|------|------|
| `/auth/login` | POST | 用户名密码登录，返回 access_token + refresh_token |
| `/auth/refresh` | POST | 刷新 access_token |
| `/auth/me` | GET | 查看当前用户信息 |
| `/auth/reload-users` | POST | 热加载 users.yaml（仅 admin） |

### 笔记 CRUD

| 端点 | 方法 | 说明 |
|------|------|------|
| `/notes` | GET | 列出目录内容（支持 `?path=&recursive=`） |
| `/notes/{path}` | GET | 读取文件内容或列出目录（自动检测） |
| `/notes/{path}` | POST | 创建文件或目录 |
| `/notes/{path}` | PUT | 更新文件内容 |
| `/notes/{path}` | DELETE | 删除文件（默认归档到 90_Archives） |

### 搜索

| 端点 | 方法 | 说明 |
|------|------|------|
| `/search` | POST | 全文搜索（支持正则） |
| `/search/semantic` | POST | 语义搜索（需先构建索引） |
| `/search/index` | POST | 构建/重建向量索引（仅 admin） |

### 智能分类

| 端点 | 方法 | 说明 |
|------|------|------|
| `/classify/suggest` | POST | 分析内容，返回 P.A.R.A. 分类建议 |
| `/classify/move` | POST | 移动文件到目标路径 |

## 安全架构

### 多层防护

```
请求 → [127.0.0.1 本地绑定]
     → [JWT Bearer Token 验证]
     → [用户权限检查] → permissions 列表
     → [路径沙箱] → allowed_paths 白名单
                  → ../ 穿越防护
                  → 符号链接跳出检测
     → [系统目录排除] → .git, kb-api, __pycache__ 等
     → [审计日志] → logs/audit.log
```

### 用户配置 (`config/users.yaml`)

白名单路径为**知识库相对路径**：

```yaml
users:
  - username: "admin"
    password_hash: "$2b$12$..."
    role: "admin"
    allowed_paths:
      - ""            # 空字符串 = 完整访问权限
    permissions:
      - "read"
      - "write"
      - "delete"
      - "search"
      - "classify"

  - username: "agent-reader"
    password_hash: "$2b$12$..."
    role: "agent"
    allowed_paths:
      - "30_Resources"           # 仅访问 30_Resources 及子目录
      - "20_Areas/22_Finance"    # 仅访问 Finance 区域
    permissions:
      - "read"
      - "search"
```

### 权限说明

| 权限 | 允许的操作 |
|------|-----------|
| `read` | GET 笔记/目录 |
| `write` | POST/PUT 创建和更新 |
| `delete` | DELETE 删除/归档 |
| `search` | 全文搜索和语义搜索 |
| `classify` | P.A.R.A. 分类建议 |

## 语义搜索

支持两种 Embedding Provider：

### 本地模型（默认）

使用 `sentence-transformers`，无需外部 API。推荐模型：

| 模型 | 语言 | 维度 | 说明 |
|------|------|------|------|
| `paraphrase-multilingual-MiniLM-L12-v2` | 多语言 | 384 | **默认**，速度快 |
| `BAAI/bge-small-zh-v1.5` | 中文优化 | 512 | 中文场景更佳 |
| `BAAI/bge-m3` | 多语言 | 1024 | 精度最高 |

```env
KB_EMBEDDING_PROVIDER=local
KB_EMBEDDING_MODEL=paraphrase-multilingual-MiniLM-L12-v2
```

### OpenAI 兼容 API（可选）

支持 OpenAI、vLLM、Ollama、LiteLLM 等：

```env
KB_EMBEDDING_PROVIDER=openai
KB_EMBEDDING_MODEL=text-embedding-3-small
KB_OPENAI_API_KEY=sk-xxx
KB_OPENAI_BASE_URL=http://localhost:11434/v1  # Ollama 示例
```

### 使用流程

```bash
# 1. 首次使用需构建索引（需管理员权限）
curl -X POST http://127.0.0.1:8000/search/index \
  -H "Authorization: Bearer $TOKEN"

# 2. 语义搜索
curl -X POST http://127.0.0.1:8000/search/semantic \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "交易系统如何构建", "top_k": 10}'
```

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `KB_KB_ROOT` | 父目录 | 知识库根目录绝对路径 |
| `KB_JWT_SECRET` | — | JWT 签名密钥(**必须修改**) |
| `KB_JWT_ALGORITHM` | HS256 | JWT 算法 |
| `KB_JWT_ACCESS_EXPIRE_MINUTES` | 60 | Access Token 有效期（分钟） |
| `KB_JWT_REFRESH_EXPIRE_DAYS` | 7 | Refresh Token 有效期（天） |
| `KB_HOST` | 127.0.0.1 | 监听地址 |
| `KB_PORT` | 8000 | 监听端口 |
| `KB_EMBEDDING_PROVIDER` | local | `local` 或 `openai` |
| `KB_EMBEDDING_MODEL` | paraphrase-multilingual-MiniLM-L12-v2 | 模型名 |
| `KB_GIT_AUTO_COMMIT` | false | 写操作后自动 git commit |
| `KB_LOG_LEVEL` | INFO | 日志级别 |

## Git 集成

开启 `KB_GIT_AUTO_COMMIT=true` 后，所有写操作（创建、更新、删除、移动）会自动执行：

```bash
git add -A
git commit -m "[kb-api:username] Create/Update/Delete path"
```

与你现有的 Obsidian Git 插件同步方案兼容。

## Agent Skill

`skill/` 目录包含 OpenAPI Skill 定义文件，可直接用于 Claude 等 AI Agent：

- [skill/SKILL.md](skill/SKILL.md) — API 调用快速参考
- [skill/references/para-rules.md](skill/references/para-rules.md) — P.A.R.A. 分类详细规则

使用方式：将 `skill/` 目录复制到 `~/.claude/skills/knowledge-base-api/` 即可。
