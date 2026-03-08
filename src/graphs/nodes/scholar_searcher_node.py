"""
A2. 检索 Agent (Scholar Searcher)
根据关键词进行学术论文检索
"""
import re
import hashlib
import logging
from typing import Dict, Any, List
from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context
from coze_coding_dev_sdk import SearchClient

from graphs.state import ScholarSearcherInput, ScholarSearcherOutput

# 设置日志
logger = logging.getLogger(__name__)


def scholar_searcher_node(
    state: ScholarSearcherInput,
    config: RunnableConfig,
    runtime: Runtime[Context]
) -> ScholarSearcherOutput:
    """
    title: 学术检索
    desc: 使用联网搜索检索英文学术论文，放宽过滤条件，提高检索成功率
    integrations: 联网搜索
    """
    ctx = runtime.context
    
    # 构建检索查询词 - 专注于Semantic Scholar、arXiv、OpenAlex等可访问平台
    keywords_str = " ".join(state.keywords[:5])  # 使用前5个关键词
    
    logger.info(f"开始学术检索，关键词: {keywords_str}")
    logger.info(f"最大候选数量: {state.max_candidates}")
    logger.info(f"约束条件: {state.constraints}")
    
    # 优化搜索策略：
    # 1. 使用国内学术搜索平台（更容易访问）
    # 2. 搜索英文文章
    # 3. 使用简化的搜索词
    # 4. 移除site过滤，扩大搜索范围
    
    # 基础查询：关键词 + 学术领域
    search_query = f'{keywords_str}'
    
    # 添加学术关键词，提高结果质量
    search_query += ' "paper" "pdf" "arxiv" OR "pdf" OR "download"'
    
    # 添加年份约束（优先检索2019-2024年的新文章）
    year_range = state.constraints.get("year_range", "2019-2024")
    if year_range:
        # 尝试多个年份组合
        years = ["2024", "2023", "2022", "2021", "2020", "2019"]
        year_query = " OR ".join([f'"{y}"' for y in years])
        search_query += f' ({year_query})'
    
    logger.info(f"搜索查询: {search_query}")
    
    # 调用联网搜索（带重试机制）
    search_client = SearchClient(ctx=ctx)
    
    max_retries = 3
    retry_delay = 2  # 秒
    
    for attempt in range(max_retries):
        try:
            logger.info(f"开始调用联网搜索（尝试 {attempt + 1}/{max_retries}），count={state.max_candidates}...")
            response = search_client.search(
                query=search_query,
                search_type="web",
                count=state.max_candidates,
                need_summary=False,
                time_range=None
            )
            logger.info(f"搜索返回结果数: {len(response.web_items) if response.web_items else 0}")
            break  # 成功则跳出重试循环
        except Exception as e:
            error_msg = str(e)
            logger.error(f"联网搜索失败（尝试 {attempt + 1}/{max_retries}）: {e}")
            
            # 检查是否是连接错误
            is_connection_error = any(keyword in error_msg.lower() for keyword in [
                'connection', 'disposed', 'timeout', 'network', 'dns'
            ])
            
            if is_connection_error and attempt < max_retries - 1:
                logger.warning(f"检测到连接错误，{retry_delay}秒后重试...")
                import time
                time.sleep(retry_delay)
                retry_delay *= 2  # 指数退避
                continue
            else:
                # 非连接错误或重试次数用尽，抛出异常
                logger.error(f"搜索失败，无法继续。查询: {search_query}")
                raise Exception(f"联网搜索失败: {e}")
    
    # 检查搜索结果
    if not response.web_items or len(response.web_items) == 0:
        logger.warning("搜索结果为空，可能的原因：")
        logger.warning("1. 网络问题或搜索平台不可访问")
        logger.warning("2. 搜索词过于具体，没有匹配结果")
        logger.warning("3. 搜索服务限制")
        logger.warning(f"搜索查询: {search_query}")
        return ScholarSearcherOutput(candidates=[], total_candidates=0)
    
    # 解析搜索结果，提取论文信息
    candidates = []
    skipped_count = 0
    
    if response.web_items:
        logger.info(f"开始解析 {len(response.web_items)} 条搜索结果...")
        for idx, item in enumerate(response.web_items):
            # 清理标题：移除 "Title:" 前缀
            raw_title = item.title if item.title else ""
            if raw_title.startswith("Title:"):
                title = raw_title[6:].strip()
            else:
                title = raw_title
            
            # 清理摘要
            raw_abstract = item.snippet if item.snippet else ""
            abstract = raw_abstract.replace("Title:", "").strip()
            
            # 质量过滤：跳过明显的非学术内容（放宽条件）
            # 1. 标题太短（少于3个单词）-> 跳过
            title_words = title.split()
            if len(title_words) < 3:
                logger.info(f"[{idx+1}] 跳过标题过短: {title}")
                skipped_count += 1
                continue
            
            # 2. 标题包含明显的中文博客关键词 -> 跳过（仅检查中文）
            chinese_blog_keywords = [
                "分享", "原创", "最新", "发布", "简介", "教程",
                "博客", "CSDN", "知乎", "掘金", "随笔"
            ]
            # 只检查是否包含中文博客关键词，不检查英文
            if any(keyword in title for keyword in chinese_blog_keywords):
                logger.info(f"[{idx+1}] 跳过中文博客: {title}")
                skipped_count += 1
                continue
            
            # 3. 摘要太短（少于20个字符）-> 跳过（放宽）
            if len(abstract) < 20:
                logger.info(f"[{idx+1}] 跳过摘要过短: {title[:50]}...")
                skipped_count += 1
                continue
            
            # 4. URL明显是中文博客平台 -> 跳过（仅检查中文）
            url = item.url if item.url else ""
            chinese_blog_domains = [
                "csdn.net", "zhihu.com", "juejin.cn", "segmentfault.com"
            ]
            if any(domain in url.lower() for domain in chinese_blog_domains):
                logger.info(f"[{idx+1}] 跳过中文博客URL: {url}")
                skipped_count += 1
                continue
            
            # 提取论文元数据
            paper_info = {
                "title": title,
                "year": extract_year(abstract),
                "venue": extract_venue(abstract),
                "abstract": abstract,
                "paper_id": generate_paper_id(title, item.url),
                "url": url,
                "source": item.site_name if item.site_name else "",
                "is_english": is_english_paper(title, abstract)  # 标记是否为英文文章
            }
            # 过滤：只保留英文论文
            if paper_info["is_english"]:
                candidates.append(paper_info)
                logger.info(f"[{idx+1}] ✓ 添加: {title[:60]}... (年份: {paper_info['year']}, 来源: {paper_info['source']})")
            else:
                logger.info(f"[{idx+1}] ✗ 跳过非英文论文: {title[:60]}...")
                skipped_count += 1
    
    logger.info(f"=" * 80)
    logger.info(f"检索完成！统计信息：")
    logger.info(f"  - 搜索结果总数: {len(response.web_items)}")
    logger.info(f"  - 添加候选论文: {len(candidates)}")
    logger.info(f"  - 跳过结果数: {skipped_count}")
    if len(response.web_items) > 0:
        logger.info(f"  - 添加率: {len(candidates)}/{len(response.web_items)} = {len(candidates)/len(response.web_items)*100:.1f}%")
    else:
        logger.info(f"  - 添加率: 0%")
    logger.info(f"=" * 80)
    
    return ScholarSearcherOutput(
        candidates=candidates,
        total_candidates=len(candidates)
    )


def extract_year(text: str) -> str:
    """从文本中提取年份"""
    if not text:
        return ""
    # 匹配4位数字年份
    year_match = re.search(r'\b(19|20)\d{2}\b', text)
    if year_match:
        return year_match.group()
    return ""


def extract_venue(text: str) -> str:
    """从文本中提取会议/期刊名称（简化版）"""
    if not text:
        return ""
    # 简单启发式：提取大写的缩写或常见的会议名
    venues = ["ICML", "NeurIPS", "ICLR", "AAAI", "IJCAI", "KDD", "WWW", "SIGIR", "CVPR", "ECCV"]
    for venue in venues:
        if venue in text:
            return venue
    return ""


def generate_paper_id(title: str, url: str) -> str:
    """生成论文ID"""
    if not title:
        return ""
    # 简化：使用URL或标题的哈希
    import hashlib
    content = url if url else title
    return hashlib.md5(content.encode()).hexdigest()[:8]


def is_english_paper(title: str, abstract: str) -> bool:
    """判断论文是否为英文（放宽条件）"""
    import re
    
    text = (title + " " + abstract).lower()
    
    # 简单启发式：检查是否包含大量中文字符
    # 如果包含大量中文字符，认为是中文论文
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
    total_chars = len(text)
    
    # 如果中文字符占比超过50%，认为是中文论文（放宽到50%）
    if total_chars > 0 and chinese_chars / total_chars > 0.5:
        return False
    
    # 如果标题是纯中文，认为是中文论文
    title_chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', title))
    title_chars = len(title)
    if title_chars > 0 and title_chinese_chars / title_chars > 0.6:
        return False
    
    # 默认认为是英文（允许混合语言）
    return True
