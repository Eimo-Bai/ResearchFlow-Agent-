"""
PDF内容解析节点
读取论文PDF并提取文本内容，用于后续分析
"""
import os
import json
from typing import Dict, Any, List
from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context
from coze_coding_dev_sdk import LLMClient
from langchain_core.messages import SystemMessage, HumanMessage
from utils.pdf.pdf_reader import extract_pdf_content

from graphs.state import (
    GlobalState,
    PDFContentParserInput,
    PDFContentParserOutput
)


def pdf_content_parser_node(
    state: PDFContentParserInput,
    config: RunnableConfig,
    runtime: Runtime[Context]
) -> PDFContentParserOutput:
    """
    title: PDF内容解析
    desc: 读取论文PDF并提取文本内容，增强论文摘要信息
    integrations: 无
    """
    ctx = runtime.context
    
    # 为每篇论文尝试读取PDF内容
    enriched_candidates = []
    total_with_pdf = 0
    
    for paper in state.candidates:
        paper_url = paper.get("url", "")
        
        # 尝试读取PDF内容
        if "arxiv.org" in paper_url:
            # arXiv论文：直接读取PDF
            pdf_text = extract_pdf_content(paper_url, max_pages=5)  # 读取前5页
        else:
            # 其他论文：尝试从URL推断PDF链接
            pdf_text = extract_pdf_content(paper_url, max_pages=5)
        
        # 更新论文信息
        enriched_paper = paper.copy()
        
        # 如果成功读取到PDF内容，更新abstract
        if pdf_text and not pdf_text.startswith("Error"):
            # 截取前3000字符作为abstract（避免token超限）
            abstract_text = pdf_text[:3000]
            enriched_paper["abstract"] = abstract_text
            enriched_paper["has_pdf"] = True
            enriched_paper["pdf_content_length"] = len(pdf_text)
            total_with_pdf += 1
        else:
            enriched_paper["has_pdf"] = False
            enriched_paper["pdf_error"] = pdf_text if pdf_text else "No PDF content"
        
        enriched_candidates.append(enriched_paper)
    
    return PDFContentParserOutput(
        candidates=enriched_candidates,
        total_candidates=len(enriched_candidates),
        total_with_pdf=total_with_pdf
    )
