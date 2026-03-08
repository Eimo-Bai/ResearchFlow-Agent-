"""
A7. 审稿人/反思 Agent (Critic)
检查融合方案的新颖性和可验证性
"""
import os
import json
from typing import Dict, Any, List
from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context
from coze_coding_dev_sdk import LLMClient
from langchain_core.messages import SystemMessage, HumanMessage

from graphs.state import CriticInput, CriticOutput


def critic_node(
    state: CriticInput,
    config: RunnableConfig,
    runtime: Runtime[Context]
) -> CriticOutput:
    """
    title: 审稿反思
    desc: 检查融合方案的新颖性和可验证性，决定是否需要补检索
    integrations: 大语言模型
    """
    ctx = runtime.context
    
    if not state.fusion_hypotheses:
        return CriticOutput(
            need_supplementary_search=False,
            supplementary_queries=[],
            novelty_check={"analysis": "无融合方案"},
            verification_check={"analysis": "无融合方案"},
            loop_count=state.loop_count
        )
    
    # 检查循环次数限制
    if state.loop_count >= state.max_loop_count:
        return CriticOutput(
            need_supplementary_search=False,
            supplementary_queries=[],
            novelty_check={
                "analysis": "已达到最大循环次数，强制终止",
                "suggestions": ["建议直接使用当前方案"]
            },
            verification_check={
                "analysis": "已达到最大循环次数，强制终止",
                "suggestions": ["建议快速验证可行性"]
            },
            loop_count=state.loop_count
        )
    
    # 加载LLM配置
    cfg_file = os.path.join(os.getenv("COZE_WORKSPACE_PATH"), config['metadata']['llm_cfg'])
    with open(cfg_file, 'r', encoding='utf-8') as fd:
        llm_cfg = json.load(fd)
    
    llm_config = llm_cfg.get("config", {})
    system_prompt = llm_cfg.get("sp", "")
    user_prompt_template = llm_cfg.get("up", "")
    
    # 构建输入JSON
    hypotheses_json = json.dumps(state.fusion_hypotheses, ensure_ascii=False, indent=2)
    keywords_str = ", ".join(state.keywords)
    
    # 构建用户提示词
    user_prompt = user_prompt_template.replace("{{research_task}}", state.research_task)
    user_prompt = user_prompt.replace("{{keywords}}", keywords_str)
    user_prompt = user_prompt.replace("{{loop_count}}", str(state.loop_count))
    user_prompt = user_prompt.replace("{{max_loop_count}}", str(state.max_loop_count))
    user_prompt = user_prompt.replace("{{hypotheses_json}}", hypotheses_json)
    
    # 调用LLM
    llm_client = LLMClient(ctx=ctx)
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
    ]
    
    response = llm_client.invoke(
        messages=messages,
        model=llm_config.get("model", "doubao-seed-1-8-251228"),
        temperature=llm_config.get("temperature", 0.3),
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
    except json.JSONDecodeError as e:
        raise Exception(f"解析LLM响应失败: {e}\n原始响应: {response_text}")
    
    # 更新循环计数
    new_loop_count = state.loop_count
    if parsed_result.get("need_supplementary_search", False):
        new_loop_count = state.loop_count + 1
    
    return CriticOutput(
        need_supplementary_search=parsed_result.get("need_supplementary_search", False),
        supplementary_queries=parsed_result.get("supplementary_queries", []),
        novelty_check=parsed_result.get("novelty_check", {}),
        verification_check=parsed_result.get("verification_check", {}),
        loop_count=new_loop_count
    )
