# 项目计划书总结
## Response:
2026/4/23 18:38:14

🚀 项目计划书（可直接交给 Claude code 执行）
========================

> 基于 LangGraph 的 RAG 文档问答系统（可扩展为多Agent分析平台）  
> 目标：**Claude code 独立开发 + 可部署 + 可扩展**

* * *

🧠 1. 项目目标（必须实现）
================

### 🎯 核心能力

*   文档上传（PDF）
*   文档向量化存储
*   问答（基于文档）
*   引用来源（避免幻觉）
*   API接口调用
*   可部署（云端）

* * *

🧱 2. 系统架构（必须按此实现）
==================

```
Client（前端/手机）
        ↓
FastAPI（API层）
        ↓
LangGraph（工作流）
        ↓
┌───────────────┐
│ Query Node    │
│ Retrieve Node │
│ Generate Node │
└───────────────┘
        ↓
Vector DB（FAISS / Chroma）
        ↓
Embedding + LLM
```

* * *

⚙️ 3. 模块拆解（必须严格分层）
==================

3.1 数据层（离线）
-----------

### 功能

*   PDF解析
*   文本切块
*   向量化
*   存储

### 输出

```
vector_store/
```

* * *

3.2 检索层
-------

### 功能

*   相似度搜索
*   Top-K文档返回

### 输入

```
question
```

### 输出

```
documents[]
```

* * *

3.3 生成层（LLM）
------------

### 功能

*   拼接上下文
*   生成回答
*   返回引用

* * *

3.4 工作流层（LangGraph）
-------------------

### 必须实现节点

| Node | 功能 |
| --- | --- |
| query | 输入处理 |
| retrieve | 检索 |
| generate | 生成 |

* * *

3.5 API层（FastAPI）
-----------------

### 必须接口

```
POST /upload
POST /ask
GET  /health
```

* * *

🧩 4. 核心数据结构
============

```
class GraphState(TypedDict):
    question: str
    documents: list
    answer: str
```

* * *

🔄 5. 工作流逻辑（必须实现）
=================

```
START
 ↓
query
 ↓
retrieve
 ↓
generate
 ↓
END
```

* * *

🧪 6. 核心流程
==========

6.1 离线阶段
--------

```
PDF → 切块 → embedding → 向量库
```

* * *

6.2 在线阶段
--------

```
问题 → 检索 → 拼接 → LLM → 返回
```

* * *

📦 7. 技术选型（固定）
==============

| 模块 | 技术 |
| --- | --- |
| API | FastAPI |
| LLM | OpenAI API |
| Embedding | OpenAI Embedding |
| 向量库 | FAISS / Chroma |
| 工作流 | LangGraph |

* * *

📁 8. 项目结构（必须生成）
================

```
app/
 ├── main.py
 ├── api/
 │    ├── routes.py
 ├── services/
 │    ├── rag_service.py
 ├── graphs/
 │    ├── graph.py
 ├── core/
 │    ├── embeddings.py
 │    ├── llm.py
 ├── data/
 │    ├── loader.py
 │    ├── splitter.py
 ├── storage/
 │    ├── vector_store.py
```

* * *

🚀 9. 执行任务（必须完成）
=====================

✅ Phase 1（基础版）
--------------

*   PDF上传
*   向量化
*   问答接口

* * *

✅ Phase 2（增强版）
--------------

*   返回引用
*   多文档支持
*   错误处理

* * *

✅ Phase 3（进阶）
-------------

*   Query重写
*   文档评分节点
*   多轮对话

* * *

🧨 10. 关键约束（必须遵守）
=================

*   所有回答必须基于 documents
*   无文档 → 返回“不知道”
*   必须支持扩展节点
*   所有模块解耦

* * *

🧠 11. 扩展方向（预留）
===============

*   多Agent（分析/决策）
*   金融数据接入（FMP）
*   定时分析任务
*   云部署（Docker + Worker）

* * *

📌 12. 一句话任务定义
=======================

> 构建一个基于 LangGraph 的 RAG 文档问答系统，支持 PDF 向量检索与基于上下文的 LLM 回答，提供 API 接口并具备可扩展的工作流结构。
> 
> ChatGPT-LangGraph 项目推荐

* * *

✅ 交付标准
======

*   可运行 API
*   可上传 PDF
*   可提问并得到答案
*   返回引用文本
*   无幻觉回答
