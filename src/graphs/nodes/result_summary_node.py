"""
结果总结节点
整合锚定论文和融合方案，生成简洁的研究总结报告
"""
import os
import json
from typing import Dict, Any, List
from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context
from coze_coding_dev_sdk import LLMClient
from langchain_core.messages import SystemMessage, HumanMessage

from graphs.state import ResultSummaryInput, ResultSummaryOutput


def result_summary_node(
    state: ResultSummaryInput,
    config: RunnableConfig,
    runtime: Runtime[Context]
) -> ResultSummaryOutput:
    """
    title: 结果总结
    desc: 整合锚定论文和融合方案，生成简洁的研究总结报告
    integrations: 大语言模型
    """
    ctx = runtime.context
    
    # 如果没有锚定论文和融合方案，生成基础总结
    if not state.anchors and not state.fusion_hypotheses:
        return ResultSummaryOutput(
            final_summary=generate_basic_summary(state.research_task)
        )
    
    # 加载LLM配置
    cfg_file = os.path.join(os.getenv("COZE_WORKSPACE_PATH"), config['metadata']['llm_cfg'])
    with open(cfg_file, 'r', encoding='utf-8') as fd:
        llm_cfg = json.load(fd)
    
    llm_config = llm_cfg.get("config", {})
    system_prompt = llm_cfg.get("sp", "")
    user_prompt_template = llm_cfg.get("up", "")
    
    # 构建简化版的JSON（只包含关键信息）
    anchors_json = json.dumps([{
        "title": a.get("title", ""),
        "method": a.get("what", a.get("selection_reason", "")[:100]),
        "reason": a.get("selection_reason", "")[:200]
    } for a in state.anchors[:3]], ensure_ascii=False, indent=2)
    
    hypotheses_json = json.dumps([{
        "title": h.get("fusion_target", h.get("title", "")),
        "changes": h.get("changes_list", [])[:3],
        "innovation": h.get("innovation_point", "")[:100],
        "risks": [r.get("risk", "") for r in h.get("risks_and_solutions", [])[:2]]
    } for h in state.fusion_hypotheses[:3]], ensure_ascii=False, indent=2)
    
    # 构建用户提示词
    user_prompt = user_prompt_template.replace("{{research_task}}", state.research_task or "")
    user_prompt = user_prompt.replace("{{anchors_json}}", anchors_json)
    user_prompt = user_prompt.replace("{{hypotheses_json}}", hypotheses_json)
    
    # 调用LLM
    llm_client = LLMClient(ctx=ctx)
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
    ]
    
    try:
        response = llm_client.invoke(
            messages=messages,
            model=llm_config.get("model", "doubao-seed-1-8-251228"),
            temperature=llm_config.get("temperature", 0.5),
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
        
        return ResultSummaryOutput(
            final_summary=response_text.strip()
        )
    except Exception as e:
        # 如果LLM调用失败，生成基础总结
        return ResultSummaryOutput(
            final_summary=generate_basic_summary(state.research_task, str(e))
        )


def generate_basic_summary(research_task: str, error_msg: str = "") -> str:
    """生成基础总结（当LLM调用失败时使用）"""
    summary = f"""# 研究问题
{research_task or '设计基于图神经网络的推荐系统'}

## 锚定论文
当前未检索到合适的锚定论文

## 对比表
| 论文 | 数据集 | 指标 | 核心贡献 | 复现成本 | 可改进点 |
|------|--------|------|----------|----------|----------|\n"""
    
    if error_msg:
        summary += f"\n## 错误提示\n生成详细总结时遇到问题：{error_msg}\n"
        summary += "\n## 建议\n请尝试调整搜索关键词或增加候选论文数量后重试。"
    
    return summary
