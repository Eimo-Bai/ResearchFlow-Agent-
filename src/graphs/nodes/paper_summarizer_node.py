"""
A4. 快速总结 Agent (Paper Summarizer)
对有代码的论文生成结构化摘要
"""
import os
import json
import logging
from typing import Dict, Any, List
from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context
from coze_coding_dev_sdk import LLMClient
from langchain_core.messages import SystemMessage, HumanMessage

from graphs.state import PaperSummarizerInput, PaperSummarizerOutput

# 设置日志
logger = logging.getLogger(__name__)


def paper_summarizer_node(
    state: PaperSummarizerInput,
    config: RunnableConfig,
    runtime: Runtime[Context]
) -> PaperSummarizerOutput:
    """
    title: 论文总结
    desc: 对有代码的论文生成结构化摘要，突出可融合的模块化部件
    integrations: 大语言模型
    """
    ctx = runtime.context
    
    # 筛选有代码的论文
    papers_with_code = [p for p in state.papers_with_code if p.get("has_code", False)]
    
    # 如果没有有代码的论文，使用所有候选论文（放宽要求）
    if not papers_with_code and state.papers_with_code:
        logger.info("未找到有代码的论文，使用所有候选论文进行总结")
        papers_with_code = state.papers_with_code[:10]  # 限制前10篇
    
    if not papers_with_code:
        return PaperSummarizerOutput(
            paper_cards=[],
            total_summarized=0
        )
    
    # 限制一次总结的论文数量（避免token超限）
    max_batch = 10
    paper_cards = []
    
    for i in range(0, len(papers_with_code), max_batch):
        batch = papers_with_code[i:i + max_batch]
        batch_cards = summarize_batch(batch, config, ctx)
        paper_cards.extend(batch_cards)
    
    return PaperSummarizerOutput(
        paper_cards=paper_cards,
        total_summarized=len(paper_cards)
    )


def summarize_batch(
    papers: List[Dict[str, Any]],
    config: RunnableConfig,
    ctx: Context
) -> List[Dict[str, Any]]:
    """批量总结论文"""
    # 加载LLM配置
    cfg_file = os.path.join(os.getenv("COZE_WORKSPACE_PATH"), config['metadata']['llm_cfg'])
    with open(cfg_file, 'r', encoding='utf-8') as fd:
        llm_cfg = json.load(fd)
    
    llm_config = llm_cfg.get("config", {})
    system_prompt = llm_cfg.get("sp", "")
    user_prompt_template = llm_cfg.get("up", "")
    
    # 构建论文JSON
    papers_json = json.dumps(papers, ensure_ascii=False, indent=2)
    
    # 构建用户提示词
    user_prompt = user_prompt_template.replace("{{num_papers}}", str(len(papers)))
    user_prompt = user_prompt.replace("{{papers_json}}", papers_json)
    
    # 调用LLM
    llm_client = LLMClient(ctx=ctx)
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
    ]
    
    response = llm_client.invoke(
        messages=messages,
        model=llm_config.get("model", "doubao-seed-1-8-251228"),
        temperature=llm_config.get("temperature", 0.4),
        top_p=llm_config.get("top_p", 0.9),
        max_completion_tokens=llm_config.get("max_completion_tokens", 3000),
        thinking=llm_config.get("thinking", "disabled")
    )
    
    # 解析响应
    response_text = response.content
    if isinstance(response_text, list):
        text_parts = []
        for item in response_text:
            if isinstance(item, dict) and item.get("type") == "text":
                text_parts.append(item.get("text", ""))
        response_text = " ".join(text_parts)
    
    # 提取JSON
    json_str = response_text.strip()
    if "```json" in json_str:
        json_str = json_str.split("```json")[1].split("```")[0].strip()
    elif "```" in json_str:
        json_str = json_str.split("```")[1].split("```")[0].strip()
    
    try:
        parsed_result = json.loads(json_str)
        if isinstance(parsed_result, list):
            return parsed_result
        else:
            return [parsed_result]
    except json.JSONDecodeError as e:
        raise Exception(f"解析LLM响应失败: {e}\n原始响应: {response_text}")
