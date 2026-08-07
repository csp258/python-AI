"""
LLM answer generator using DeepSeek Chat (via OpenAI-compatible API).

Builds a structured prompt that instructs the model to answer only from the
provided reference material, cite sources, and clearly label inferences.
Supports token-by-token streaming via LangChain's ``astream``.
"""

from typing import AsyncIterator, Tuple, List
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from config import settings

# System prompt: constrains the LLM to behave as a factual, source-citing
# customer-service assistant that never hallucinates.
SYSTEM_PROMPT = """你是一个专业的电商客服助手，专门回答用户关于商品的问题。

请严格遵循以下规则:
1. 仅根据提供的参考资料回答问题，绝对禁止编造信息
2. 如果参考资料不足以回答问题，请明确说明"根据现有资料，我无法回答这个问题"，然后给出你可以提供的相关建议
3. 回答要结构化、清晰，适当使用列表或分段
4. 回答中必须引用具体的参考资料编号，例如【参考资料1】
5. 如果你推断出某些回答，请说明是"推断"而非事实
6. 使用中文回答，语气专业友好"""

# User prompt template: the {context} and {question} placeholders are filled
# at runtime with the retrieved knowledge base chunks and the user's query.
USER_PROMPT_TEMPLATE = """参考资料:
{context}

用户问题: {question}

请根据上述参考资料回答问题，并标注引用来源。"""


def _build_llm():
    """
    Create a DeepSeek Chat LLM instance configured for streaming.
    Temperature 0.3 balances factual accuracy with natural language flow.
    """
    return ChatOpenAI(
        model=settings.deepseek_model,
        api_key=settings.deepseek_api_key,
        base_url=settings.deepseek_base_url,
        temperature=0.3,
        streaming=True,
    )


def build_prompt(context: str, question: str) -> ChatPromptTemplate:
    """
    Build a ChatPromptTemplate with the system and user messages populated.
    Used by the RAG engine for constructing the LLM prompt chain.
    """
    return ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("user", USER_PROMPT_TEMPLATE.format(context=context, question=question)),
    ])


async def generate_stream(
    context: str,
    question: str,
) -> AsyncIterator[Tuple[str, None]]:
    """
    Stream the LLM-generated answer token-by-token using LangChain's async
    streaming. Each yielded tuple contains (token_text, None) following the
    convention expected by ``query_stream`` in the engine module.

    The chain is built as ``prompt | llm`` — LangChain pipes the formatted
    prompt directly into the LLM and streams the output.
    """
    llm = _build_llm()
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("user", USER_PROMPT_TEMPLATE.format(context=context, question=question)),
    ])
    chain = prompt | llm
    async for chunk in chain.astream({}):
        content = chunk.content
        if content:
            yield (content, None)
