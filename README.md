# RAG 文档问答系统

基于 FastAPI、LangGraph、DeepSeek 和本地向量检索的 RAG Demo。

当前存储结构：
- `FAISS` 负责向量检索
- `SQLite` 负责文档元数据、文档块映射和聊天记录

## 技术栈

- API: FastAPI
- LLM: DeepSeek OpenAI-compatible API
- Embedding: `sentence-transformers` (`all-MiniLM-L6-v2`)
- Vector Store: FAISS
- Metadata Store: SQLite
- Workflow: LangGraph

## 目录结构

```text
app/
  main.py
  api/
    routes.py
  core/
    embeddings.py
    errors.py
    llm.py
  data/
    loader.py
    splitter.py
  graphs/
    graph.py
  services/
    rag_service.py
  storage/
    storage.py
    vector_store.py
static/
tests/
vector_store/
start.ps1
requirements.txt
```

## 环境要求

- Windows PowerShell
- Python 3.12
- 已配置 `.env`

## 安装依赖

```powershell
python -m pip install -r requirements.txt
```

如果你已经创建了项目虚拟环境，使用：

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## 配置

复制 `.env.example` 为 `.env`，至少填写：

```env
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
DEEPSEEK_API_BASE=https://api.deepseek.com
DEEPSEEK_MODEL_NAME=deepseek-chat
EMBEDDING_MODEL=all-MiniLM-L6-v2
VECTOR_STORE_PATH=./vector_store
INDEX_FILE=index.faiss
METADATA_FILE=index.pkl
RETRIEVAL_SCORE_THRESHOLD=1.35
API_PORT=8000
```

## 启动方式

推荐直接使用项目根目录的启动脚本：

```powershell
.\start.ps1
```

这个脚本会：
- 固定使用项目自己的 `.venv`
- 把临时目录切到项目内 `.tmp`
- 清理旧的 `8001` 端口监听
- 在 `127.0.0.1:8001` 启动服务

启动成功后访问：

- 页面：`http://127.0.0.1:8001/`
- 文档：`http://127.0.0.1:8001/docs`
- 健康检查：`http://127.0.0.1:8001/api/v1/health`

## API

### 健康检查

```http
GET /api/v1/health
```

### 上传文档

```http
POST /api/v1/upload
```

支持：
- PDF
- Markdown

### 提问

```http
POST /api/v1/ask
```

请求体示例：

```json
{
  "question": "文档主要内容是什么？"
}
```

## 存储说明

运行时主要文件位于 `vector_store/`：

```text
vector_store/
  app.db
  index.faiss
  index.pkl
  legacy_backup/
```

含义：
- `app.db`: SQLite 元数据数据库
- `index.faiss`: FAISS 索引文件
- `index.pkl`: FAISS 元数据文件
- `legacy_backup/`: 历史 JSON 归档

## 测试

运行全部测试：

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py" -v
```

测试已改为使用项目内 `tests/.tmp/`，避免依赖系统临时目录权限。

## 已知限制

- 当前仍是单机版 Demo，不是多用户正式系统
- 高级能力尚未完成：
  - Query 重写
  - 更正式的 rerank 节点
  - 真正的多轮对话上下文
- 首次加载本地 embedding 模型可能较慢

## 常用维护操作

### 清空当前知识库

删除 `vector_store/` 根目录下的活动文件，保留 `legacy_backup/`。

### 重新上传文档

清库后重新上传需要使用的文档即可。
