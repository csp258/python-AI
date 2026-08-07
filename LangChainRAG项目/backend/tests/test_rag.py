"""Unit tests for the RAG module components.

Tests pure functions (intent classification, FAQ cache, retriever helpers)
that have no external dependencies.
"""
import sys
import os

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from langchain_core.documents import Document as LCDocument

from rag.intent import classify_intent
from rag.faq_cache import try_faq, _keyword_match
from rag.retriever import _deduplicate, format_context


class TestClassifyIntent:
    def test_return_refund_intent(self):
        assert classify_intent("我想退货") == "售后维权"

    def test_return_refund_intent_2(self):
        assert classify_intent("怎么退款呢") == "售后维权"

    def test_logistics_intent(self):
        assert classify_intent("快递什么时候到") == "物流配送"

    def test_logistics_intent_2(self):
        assert classify_intent("几天到货") == "物流配送"

    def test_payment_intent(self):
        assert classify_intent("可以用花呗分期吗") == "支付与价格"

    def test_product_intent(self):
        assert classify_intent("这个配置怎么样") == "商品咨询"

    def test_member_intent(self):
        assert classify_intent("会员等级怎么提升") == "会员与账户"

    def test_generic_fallback(self):
        assert classify_intent("你好") == "通用咨询"

    def test_generic_fallback_2(self):
        assert classify_intent("今天天气不错") == "通用咨询"

    def test_empty_question(self):
        assert classify_intent("") == "通用咨询"


class TestKeywordMatch:
    def test_exact_keyword_match(self):
        result = _keyword_match("我要退货")
        assert result is not None
        assert "7天内无理由退换" in result

    def test_keyword_in_middle_of_string(self):
        result = _keyword_match("请问怎么退款")
        assert result is not None
        assert "原路返回" in result

    def test_no_match(self):
        result = _keyword_match("今天天气如何")
        assert result is None

    def test_empty_question(self):
        result = _keyword_match("")
        assert result is None


class TestTryFAQ:
    def test_returns_answer_and_sources(self):
        result = try_faq("物流查询")
        assert result is not None
        answer, sources = result
        assert "顺丰快递" in answer
        assert len(sources) == 1
        assert sources[0]["filename"] == "FAQ知识库"

    def test_returns_none_on_no_match(self):
        result = try_faq("量子计算原理")
        assert result is None


class TestDeduplicate:
    def test_removes_duplicate_docs(self):
        docs = [
            LCDocument(page_content="Same content here", metadata={}),
            LCDocument(page_content="Same content here", metadata={}),
            LCDocument(page_content="Unique content", metadata={}),
        ]
        result = _deduplicate(docs)
        assert len(result) == 2

    def test_empty_list(self):
        assert _deduplicate([]) == []

    def test_no_duplicates(self):
        docs = [
            LCDocument(page_content="A", metadata={}),
            LCDocument(page_content="B", metadata={}),
        ]
        result = _deduplicate(docs)
        assert len(result) == 2


class TestFormatContext:
    def test_formats_context_and_sources(self):
        docs = [
            LCDocument(page_content="参考内容1", metadata={"source": "doc1.pdf"}),
            LCDocument(page_content="参考内容2", metadata={"source": "doc2.txt"}),
        ]
        scores = [0.85, 0.72]

        ctx, sources = format_context(docs, scores)
        assert "参考资料1" in ctx
        assert "参考资料2" in ctx
        assert "doc1.pdf" in ctx
        assert "doc2.txt" in ctx
        assert len(sources) == 2
        assert sources[0]["filename"] == "doc1.pdf"
        assert sources[0]["score"] == 0.85

    def test_empty_docs(self):
        ctx, sources = format_context([], [])
        assert ctx == ""
        assert sources == []

    def test_doc_without_source_metadata(self):
        docs = [LCDocument(page_content="no source", metadata={})]
        scores = [0.5]
        ctx, sources = format_context(docs, scores)
        assert "未知文档" in ctx
        assert sources[0]["filename"] == "未知文档"


class TestLoader:
    def test_unsupported_extension_raises_error(self):
        from rag.loader import load_document
        import pytest
        with pytest.raises(ValueError, match="Unsupported"):
            load_document("/fake/path.xyz", ".xyz")
