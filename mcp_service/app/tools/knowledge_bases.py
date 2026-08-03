"""Fixed-response knowledge-base tools used to verify the MCP permission path."""

from __future__ import annotations


def search_finance_knowledge(query: str) -> dict[str, str]:
    """Query the finance knowledge base. The response is fixed during integration testing."""
    return {
        "knowledge_base": "finance",
        "query": query,
        "answer": "财务知识库测试结果：费用报销需提供合规发票、审批记录和费用归属信息。",
    }


def search_business_knowledge(query: str) -> dict[str, str]:
    """Query the business knowledge base. The response is fixed during integration testing."""
    return {
        "knowledge_base": "business",
        "query": query,
        "answer": "业务知识库测试结果：客户需求确认后，应完成方案评审、报价审批和交付排期。",
    }


def search_hr_knowledge(query: str) -> dict[str, str]:
    """Query the HR knowledge base. The response is fixed during integration testing."""
    return {
        "knowledge_base": "hr",
        "query": query,
        "answer": "人事知识库测试结果：请假申请需在系统中提交，并由直属负责人按公司流程审批。",
    }
