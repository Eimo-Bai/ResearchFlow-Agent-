"""
A3. 代码发现 Agent (Code Hunter)
检查论文是否有开源代码，提取GitHub链接
"""
import re
import logging
from typing import Dict, Any, List
from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context
from coze_coding_dev_sdk import SearchClient

from graphs.state import CodeHunterInput, CodeHunterOutput

# 设置日志
logger = logging.getLogger(__name__)


def code_hunter_node(
    state: CodeHunterInput,
    config: RunnableConfig,
    runtime: Runtime[Context]
) -> CodeHunterOutput:
    """
    title: 代码发现
    desc: 检查论文是否有开源代码，提取GitHub链接
    integrations: 联网搜索
    """
    ctx = runtime.context
    
    papers_with_code = []
    
    logger.info(f"开始代码发现，候选论文数量: {len(state.candidates)}")
    
    for idx, paper in enumerate(state.candidates):
        title = paper.get("title", "")
        url = paper.get("url", "")
        abstract = paper.get("abstract", "")
        
        logger.info(f"处理论文 {idx+1}/{len(state.candidates)}: {title}")
        
        # 从摘要中提取GitHub链接
        has_code, repo_urls = extract_github_links(abstract)
        evidence = "摘要中的GitHub链接"
        
        # 如果摘要中没有，尝试从URL中提取
        if not has_code:
            has_code, repo_urls = extract_github_links(url)
            evidence = "URL中的GitHub链接"
        
        # 如果还是没有，尝试通过搜索补充
        if not has_code and title:
            logger.info(f"尝试搜索论文代码: {title}")
            has_code, repo_urls = search_github_repo(title, ctx)
            if has_code:
                evidence = "搜索找到的GitHub仓库"
            else:
                evidence = "无代码"
        
        paper_info = {
            "title": title,
            "year": paper.get("year", ""),
            "venue": paper.get("venue", ""),
            "abstract": abstract,
            "paper_id": paper.get("paper_id", ""),
            "url": url,
            "source": paper.get("source", ""),
            "has_code": has_code,
            "repo_urls": repo_urls,
            "code_evidence": evidence
        }
        
        papers_with_code.append(paper_info)
        logger.info(f"论文 '{title}' 代码状态: {has_code}, 证据: {evidence}")
    
    total_with_code = sum(1 for p in papers_with_code if p["has_code"])
    logger.info(f"代码发现完成，找到 {total_with_code}/{len(papers_with_code)} 篇有代码的论文")
    
    return CodeHunterOutput(
        papers_with_code=papers_with_code,
        total_papers_with_code=total_with_code
    )


def extract_github_links(text: str) -> tuple:
    """从文本中提取GitHub链接"""
    if not text:
        return False, []
    
    # 匹配GitHub URL模式
    github_pattern = r'https?://github\.com/[A-Za-z0-9_-]+/[A-Za-z0-9_.-]+/?'
    matches = re.findall(github_pattern, text)
    
    if matches:
        return True, list(set(matches))  # 去重
    return False, []


def search_github_repo(paper_title: str, ctx: Context) -> tuple:
    """通过搜索查找GitHub仓库"""
    if not paper_title:
        return False, []
    
    search_client = SearchClient(ctx=ctx)
    
    # 清理标题
    clean_title = paper_title.replace("Title:", "").strip()
    
    # 策略1：优先搜索PapersWithCode（最准确）
    try:
        # 使用更通用的搜索词
        search_query = f'{clean_title} site:paperswithcode.com'
        logger.info(f"PapersWithCode搜索: {search_query}")
        response = search_client.search(
            query=search_query,
            search_type="web",
            count=3,
            need_summary=False
        )
        
        if response.web_items:
            for item in response.web_items:
                # 从URL和snippet中提取GitHub链接
                url = item.url if item.url else ""
                snippet = item.snippet if item.snippet else ""
                full_text = (url + " " + snippet).lower()
                has_code, repo_urls = extract_github_links(full_text)
                if has_code:
                    logger.info(f"PapersWithCode找到代码: {repo_urls}")
                    return has_code, repo_urls
    except Exception as e:
        logger.error(f"PapersWithCode搜索失败: {e}")
    
    # 策略2：从arXiv URL推断GitHub（很多arXiv论文在GitHub上有代码）
    try:
        # 简化搜索词：使用论文标题中的主要关键词
        keywords = extract_keywords(clean_title)
        if keywords:
            # 搜索关键词 + github
            search_query = f'{" ".join(keywords[:4])} github'
            logger.info(f"GitHub关键词搜索: {search_query}")
            response = search_client.search(
                query=search_query,
                search_type="web",
                count=5,
                need_summary=False
            )
            
            if response.web_items:
                for item in response.web_items:
                    url = item.url if item.url else ""
                    # 检查是否是GitHub仓库页面
                    if url and "github.com" in url and "/blob/" not in url and "/commit/" not in url and "/issues/" not in url:
                        has_code, repo_urls = extract_github_links(url)
                        if has_code:
                            logger.info(f"GitHub搜索找到代码: {repo_urls}")
                            return has_code, repo_urls
    except Exception as e:
        logger.error(f"GitHub搜索失败: {e}")
    
    # 策略3：论文标题包含"Graph Neural Network"，大概率有开源实现
    # 这种情况下，直接标记为可能有代码，但不返回具体URL
    try:
        title_lower = clean_title.lower()
        if any(keyword in title_lower for keyword in [
            "graph neural network", "gnn", "graph convolution", "recommendation system"
        ]):
            # 搜索更通用的关键词
            keywords = extract_keywords(clean_title)
            if len(keywords) >= 3:
                search_query = f'{" ".join(keywords[:3])} implementation code'
                logger.info(f"通用代码搜索: {search_query}")
                response = search_client.search(
                    query=search_query,
                    search_type="web",
                    count=3,
                    need_summary=False
                )
                
                if response.web_items:
                    for item in response.web_items:
                        url = item.url if item.url else ""
                        # 检查是否是GitHub或代码托管平台
                        if url and ("github.com" in url or "gitlab.com" in url):
                            has_code, repo_urls = extract_github_links(url)
                            if has_code:
                                logger.info(f"通用搜索找到代码: {repo_urls}")
                                return has_code, repo_urls
    except Exception as e:
        logger.error(f"通用代码搜索失败: {e}")
    
    logger.info(f"未找到论文代码: {clean_title}")
    return False, []


def extract_keywords(title: str) -> List[str]:
    """从论文标题中提取关键词"""
    # 简单的关键词提取策略：移除常见的停用词
    stop_words = {"a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by", "is", "are", "was", "were", "be"}
    words = title.lower().split()
    keywords = [w for w in words if len(w) > 2 and w not in stop_words]
    return keywords[:5]  # 返回前5个关键词


def determine_code_evidence(has_code: bool, repo_urls: List[str], paper: Dict[str, Any]) -> str:
    """确定代码证据来源"""
    if not has_code:
        return "无代码"
    
    if repo_urls:
        return f"GitHub: {', '.join(repo_urls)}"
    
    # 检查是否在Papers with Code中
    if "paperswithcode" in paper.get("url", "").lower():
        return "PapersWithCode"
    
    return "其他来源"
