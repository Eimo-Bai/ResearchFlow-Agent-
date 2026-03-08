"""
锚定论文PDF解析节点
解析选定锚定论文的PDF内容，用于增强论文摘要和后续分析
"""
import os
from typing import Dict, Any, List
from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context
from utils.pdf.pdf_reader import extract_pdf_content

from graphs.state import AnchorPDFParserInput, AnchorPDFParserOutput


def anchor_pdf_parser_node(
    state: AnchorPDFParserInput,
    config: RunnableConfig,
    runtime: Runtime[Context]
) -> AnchorPDFParserOutput:
    """
    title: 锚定论文PDF解析
    desc: 解析选定锚定论文的PDF内容，提取论文详细信息以增强摘要和分析
    integrations: 无
    """
    ctx = runtime.context
    
    # 为每篇锚定论文尝试读取PDF内容
    enriched_anchors = []
    total_with_pdf = 0
    
    for paper in state.anchors:
        paper_url = paper.get("url", "")
        paper_title = paper.get("title", "")
        
        # 尝试读取PDF内容
        pdf_text = ""
        
        if "arxiv.org" in paper_url:
            # arXiv论文：直接读取PDF
            pdf_text = extract_pdf_content(paper_url, max_pages=10)  # 锚定论文读取10页
        elif paper_url.endswith(".pdf"):
            # 直接是PDF链接
            pdf_text = extract_pdf_content(paper_url, max_pages=10)
        else:
            # 其他论文：尝试从URL推断PDF链接
            # 简单策略：在URL后加上.pdf
            pdf_url = paper_url.rstrip("/") + ".pdf"
            pdf_text = extract_pdf_content(pdf_url, max_pages=10)
        
        # 更新论文信息
        enriched_paper = paper.copy()
        
        # 如果成功读取到PDF内容，增强论文信息
        if pdf_text and not pdf_text.startswith("Error"):
            # 截取前5000字符作为详细信息（避免token超限）
            detailed_info = pdf_text[:5000]
            
            # 更新或创建详细描述字段
            enriched_paper["detailed_description"] = detailed_info
            enriched_paper["has_pdf"] = True
            enriched_paper["pdf_content_length"] = len(pdf_text)
            
            # 如果原文摘要较短，用PDF内容增强
            original_abstract = enriched_paper.get("abstract", "")
            if len(original_abstract) < 500 and len(detailed_info) > len(original_abstract):
                # 保留原文摘要前200字符，然后添加PDF提取的内容
                enriched_paper["abstract"] = original_abstract[:200] + "\n\n[PDF Content Excerpt]\n" + detailed_info
            
            total_with_pdf += 1
        else:
            enriched_paper["has_pdf"] = False
            enriched_paper["pdf_error"] = pdf_text if pdf_text else "No PDF content available"
        
        enriched_anchors.append(enriched_paper)
    
    return AnchorPDFParserOutput(
        enriched_anchors=enriched_anchors,
        total_anchors=len(enriched_anchors),
        total_with_pdf=total_with_pdf
    )
