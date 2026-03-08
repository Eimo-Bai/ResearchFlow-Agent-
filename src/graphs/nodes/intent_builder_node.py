"""
A1. 需求解析 Agent (Intent Builder)
解析用户输入的研究需求，提取结构化信息
"""
import os
import json
from typing import Dict, Any
from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context
from coze_coding_dev_sdk import LLMClient
from langchain_core.messages import SystemMessage, HumanMessage

from graphs.state import IntentBuilderInput, IntentBuilderOutput


def intent_builder_node(
    state: IntentBuilderInput,
    config: RunnableConfig,
    runtime: Runtime[Context]
) -> IntentBuilderOutput:
    """
    title: 需求解析
    desc: 解析研究题目和描述，提取结构化需求（任务、约束、关键词、排除项）
    integrations: 大语言模型
    """
    ctx = runtime.context
    
    # 加载LLM配置
    cfg_file = os.path.join(os.getenv("COZE_WORKSPACE_PATH"), config['metadata']['llm_cfg'])
    with open(cfg_file, 'r', encoding='utf-8') as fd:
        llm_cfg = json.load(fd)
    
    llm_config = llm_cfg.get("config", {})
    system_prompt = llm_cfg.get("sp", "")
    user_prompt_template = llm_cfg.get("up", "")
    
    # 构建用户提示词
    user_prompt = user_prompt_template.replace("{{task}}", state.task)
    user_prompt = user_prompt.replace("{{description}}", state.description)
    
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
        max_completion_tokens=llm_config.get("max_completion_tokens", 2000),
        thinking=llm_config.get("thinking", "disabled")
    )
    
    # 解析LLM响应
    response_text = response.content
    if isinstance(response_text, list):
        # 处理多模态响应
        text_parts = []
        for item in response_text:
            if isinstance(item, dict) and item.get("type") == "text":
                text_parts.append(item.get("text", ""))
        response_text = " ".join(text_parts)
    
    # 提取JSON（处理可能的markdown代码块）
    json_str = response_text.strip()
    if "```json" in json_str:
        json_str = json_str.split("```json")[1].split("```")[0].strip()
    elif "```" in json_str:
        json_str = json_str.split("```")[1].split("```")[0].strip()
    
    try:
        parsed_result = json.loads(json_str)
    except json.JSONDecodeError as e:
        raise Exception(f"解析LLM响应失败: {e}\n原始响应: {response_text}")
    
    # 构建输出
    return IntentBuilderOutput(
        research_task=parsed_result.get("research_task", ""),
        constraints=parsed_result.get("constraints", {}),
        keywords=parsed_result.get("keywords", []),
        exclusion=parsed_result.get("exclusion", [])
    )
