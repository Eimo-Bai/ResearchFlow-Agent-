"""
A6. 融合创新 Agent (Fusion Architect)
基于锚定论文设计融合创新方案
"""
import os
import json
from typing import Dict, Any, List
from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context
from coze_coding_dev_sdk import LLMClient
from langchain_core.messages import SystemMessage, HumanMessage

from graphs.state import FusionArchitectInput, FusionArchitectOutput


def fusion_architect_node(
    state: FusionArchitectInput,
    config: RunnableConfig,
    runtime: Runtime[Context]
) -> FusionArchitectOutput:
    """
    title: 融合创新
    desc: 基于锚定论文设计融合创新方案，包含融合目标、方式、创新点、改动清单、风险对策、验证实验
    integrations: 大语言模型
    """
    ctx = runtime.context
    
    if not state.anchors:
        return FusionArchitectOutput(
            fusion_hypotheses=[],
            total_hypotheses=0
        )
    
    # 加载LLM配置
    cfg_file = os.path.join(os.getenv("COZE_WORKSPACE_PATH"), config['metadata']['llm_cfg'])
    with open(cfg_file, 'r', encoding='utf-8') as fd:
        llm_cfg = json.load(fd)
    
    llm_config = llm_cfg.get("config", {})
    system_prompt = llm_cfg.get("sp", "")
    user_prompt_template = llm_cfg.get("up", "")
    
    # 构建锚定论文JSON
    anchors_json = json.dumps(state.anchors, ensure_ascii=False, indent=2)
    
    # 构建用户提示词
    user_prompt = user_prompt_template.replace("{{research_task}}", state.research_task)
    user_prompt = user_prompt.replace("{{anchors_json}}", anchors_json)
    
    # 调用LLM
    llm_client = LLMClient(ctx=ctx)
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
    ]
    
    response = llm_client.invoke(
        messages=messages,
        model=llm_config.get("model", "doubao-seed-1-8-251228"),
        temperature=llm_config.get("temperature", 0.7),
        top_p=llm_config.get("top_p", 0.9),
        max_completion_tokens=llm_config.get("max_completion_tokens", 5000),
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
            fusion_hypotheses = parsed_result
        else:
            fusion_hypotheses = [parsed_result]
    except json.JSONDecodeError as e:
        raise Exception(f"解析LLM响应失败: {e}\n原始响应: {response_text}")
    
    return FusionArchitectOutput(
        fusion_hypotheses=fusion_hypotheses,
        total_hypotheses=len(fusion_hypotheses)
    )
