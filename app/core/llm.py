import os
from typing import Optional

from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

SYSTEM_PROMPT = """你是一个严格基于文档内容回答问题的助手。

要求：
1. 仅使用提供的文档内容回答问题。
2. 如果文档中没有足够信息，请直接回答“`不知道。已上传文档中没有足够信息回答这个问题。`”。
3. 不要编造、补充或使用外部知识。
4. 回答尽量简洁、准确，必要时使用列表。
5. 优先引用文档中的明确事实，不要输出与文档无关的推测。
"""


def get_llm(temperature: float = 0.3) -> ChatOpenAI:
    return ChatOpenAI(
        model=os.getenv("DEEPSEEK_MODEL_NAME", "deepseek-chat"),
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url=os.getenv("DEEPSEEK_API_BASE"),
        temperature=temperature,
    )


def generate_answer(context: str, question: str, llm: Optional[ChatOpenAI] = None) -> str:
    if llm is None:
        llm = get_llm()

    if not context or not context.strip():
        return "不知道。已上传文档中没有足够信息回答这个问题。"

    prompt = f"""基于以下文档内容回答问题：

文档内容：
{context}

问题：{question}

回答："""

    response = llm.invoke([
        ("system", SYSTEM_PROMPT),
        ("human", prompt)
    ])

    return response.content.strip()
