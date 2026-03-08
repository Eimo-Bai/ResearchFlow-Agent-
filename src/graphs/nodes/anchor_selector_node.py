"""
A5. 锚定筛选 Agent (Anchor Selector)
基于可复现性和可融合性筛选锚定论文
"""
import os
import json
from typing import Dict, Any, List
from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context
from coze_coding_dev_sdk import LLMClient
from langchain_core.messages import SystemMessage, HumanMessage

from graphs.state import AnchorSelectorInput, AnchorSelectorOutput


def anchor_selector_node(
    state: AnchorSelectorInput,
    config: RunnableConfig,
    runtime: Runtime[Context]
) -> AnchorSelectorOutput:
    """
    title: 锚定筛选
    desc: 基于可复现性、可融合性、相关性和新颖性评分，筛选锚定论文
    integrations: 大语言模型
    """
    ctx = runtime.context
    
    if not state.paper_cards:
        return AnchorSelectorOutput(
            anchors=[],
            backup=[]
        )
    
    # 加载LLM配置
    cfg_file = os.path.join(os.getenv("COZE_WORKSPACE_PATH"), config['metadata']['llm_cfg'])
    with open(cfg_file, 'r', encoding='utf-8') as fd:
        llm_cfg = json.load(fd)
    
    llm_config = llm_cfg.get("config", {})
    system_prompt = llm_cfg.get("sp", "")
    user_prompt_template = llm_cfg.get("up", "")
    
    # 构建论文JSON
    papers_json = json.dumps(state.paper_cards, ensure_ascii=False, indent=2)
    constraints_json = json.dumps(state.constraints, ensure_ascii=False)
    
    # 构建用户提示词
    user_prompt = user_prompt_template.replace("{{num_anchors}}", str(state.num_anchors))
    user_prompt = user_prompt.replace("{{research_task}}", state.research_task)
    user_prompt = user_prompt.replace("{{constraints}}", constraints_json)
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
        temperature=llm_config.get("temperature", 0.2),
        top_p=llm_config.get("top_p", 0.9),
        max_completion_tokens=llm_config.get("max_completion_tokens", 4000),
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
    
    # 清理表达式：将"0.35*0.85 + 0.35*0.9 = 0.8925"替换为"0.8925"
    import re
    
    # 匹配等号后的数字（计算结果）
    def clean_expressions(match):
        # 匹配形如 "0.35*0.85 + 0.35*0.9 = 0.8925" 或 "0.35*0.85 + 0.35*0.9 + 0.2*1.0 + 0.1*0.9 = 0.8925"
        expr = match.group(1)
        # 查找等号后面的数字
        eq_match = re.search(r'=\s*([0-9]*\.?[0-9]+)', expr)
        if eq_match:
            return f": {eq_match.group(1)},"
        # 如果没有等号，尝试计算表达式
        try:
            # 移除所有空格
            clean_expr = expr.replace(' ', '')
            # 简单计算（仅支持基本运算）
            result = eval(clean_expr)
            return f": {result},"
        except:
            # 如果计算失败，保留原样（会导致后续解析失败）
            return match.group(0)
    
    # 匹配分数字段中的表达式（带冒号的情况）
    json_str = re.sub(r'"(repro_score|merge_score|fit_score|freshness|anchor_score)":\s*([^,}\]]+),', 
                      lambda m: f'"{m.group(1)}": {clean_expressions(m)}' if '=' in m.group(2) else m.group(0),
                      json_str)
    
    # 再次尝试解析
    try:
        parsed_result = json.loads(json_str)
    except json.JSONDecodeError as e:
        # 如果仍然失败，记录清理后的内容以便调试
        raise Exception(f"解析LLM响应失败: {e}\n清理后内容: {json_str}\n原始响应: {response_text}")
    
    # 获取anchors和backup
    anchors = parsed_result.get("anchors", [])
    backup = parsed_result.get("backup", [])
    
    # 容错处理：如果backup是字符串列表，转换为字典列表
    if backup and isinstance(backup, list) and len(backup) > 0:
        if isinstance(backup[0], str):
            # 将字符串列表转换为字典列表
            backup_dict_list = []
            for title in backup:
                backup_dict_list.append({
                    "title": title,
                    "repro_score": 0.0,
                    "merge_score": 0.0,
                    "fit_score": 0.0,
                    "freshness": 0.0,
                    "anchor_score": 0.0,
                    "selection_reason": "候补论文（详细信息待补充）",
                    "mergeable_parts": []
                })
            backup = backup_dict_list
    
    return AnchorSelectorOutput(
        anchors=anchors,
        backup=backup
    )
