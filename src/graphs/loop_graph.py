"""
学术研究创新工作流 - 检索循环子图
实现A2-A7的循环逻辑：检索 -> 代码发现 -> 论文总结 -> 锚定筛选 -> 融合创新 -> 审稿反思 -> (循环或结束)
"""
from langgraph.graph import StateGraph, END
from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context
from typing import Dict, Any, TYPE_CHECKING

from graphs.state import (
    GlobalState,
    ShouldContinueSearchInput,
    SearchLoopInput,
    SearchLoopOutput
)

from graphs.nodes.scholar_searcher_node import scholar_searcher_node
from graphs.nodes.code_hunter_node import code_hunter_node
from graphs.nodes.paper_summarizer_node import paper_summarizer_node
from graphs.nodes.anchor_selector_node import anchor_selector_node
from graphs.nodes.fusion_architect_node import fusion_architect_node
from graphs.nodes.critic_node import critic_node


# ==================== 条件判断函数 ====================
def should_continue_search(state: ShouldContinueSearchInput) -> str:
    """
    title: 是否继续补检索
    desc: 根据审稿结果和循环次数，决定是否需要补检索或结束流程
    """
    # 检查是否需要补检索
    if not state.need_supplementary_search:
        return "结束循环"
    
    # 检查循环次数限制
    if state.loop_count >= state.max_loop_count:
        return "结束循环"
    
    # 继续补检索（增加循环计数）
    return "继续检索"


# ==================== 子图编排 ====================
def create_loop_graph():  # type: ignore
    """创建检索循环子图"""
    
    # 创建状态图，使用GlobalState
    builder = StateGraph(GlobalState)
    
    # 添加节点
    builder.add_node("scholar_searcher", scholar_searcher_node)
    
    builder.add_node("code_hunter", code_hunter_node)
    
    builder.add_node(
        "paper_summarizer",
        paper_summarizer_node,
        metadata={"type": "agent", "llm_cfg": "config/paper_summarizer_cfg.json"}
    )
    
    builder.add_node(
        "anchor_selector",
        anchor_selector_node,
        metadata={"type": "agent", "llm_cfg": "config/anchor_selector_cfg.json"}
    )
    
    builder.add_node(
        "fusion_architect",
        fusion_architect_node,
        metadata={"type": "agent", "llm_cfg": "config/fusion_architect_cfg.json"}
    )
    
    builder.add_node(
        "critic",
        critic_node,
        metadata={"type": "agent", "llm_cfg": "config/critic_cfg.json"}
    )
    
    # 设置入口点
    builder.set_entry_point("scholar_searcher")
    
    # 添加线性边（子图内部流程）
    builder.add_edge("scholar_searcher", "code_hunter")
    builder.add_edge("code_hunter", "paper_summarizer")
    builder.add_edge("paper_summarizer", "anchor_selector")
    builder.add_edge("anchor_selector", "fusion_architect")
    builder.add_edge("fusion_architect", "critic")
    
    # 添加条件边（循环逻辑）
    builder.add_conditional_edges(
        source="critic",
        path=should_continue_search,
        path_map={
            "继续检索": "scholar_searcher",
            "结束循环": END
        }
    )
    
    # 编译子图
    return builder.compile()


# 创建全局子图实例
search_loop_graph = create_loop_graph()


# ==================== 子图调用函数 ====================
def call_search_loop(
    state: SearchLoopInput,
    config: RunnableConfig,
    runtime: Runtime[Context]
) -> SearchLoopOutput:
    """
    title: 检索循环
    desc: 调用检索循环子图，执行学术论文检索、代码发现、融合创新的完整流程
    """
    ctx = runtime.context
    
    # 构建GlobalState
    global_state = GlobalState(
        task="",
        description="",
        keywords=state.keywords,
        constraints=state.constraints,
        max_candidates=state.max_candidates,
        num_anchors=state.num_anchors,
        research_task=state.research_task,
        loop_count=state.loop_count,
        max_loop_count=state.max_loop_count
    )
    
    # 调用子图
    result = search_loop_graph.invoke(global_state, config)
    
    # 检查结果类型并转换为字典
    if isinstance(result, dict):
        result_dict = result
    elif hasattr(result, "model_dump"):  # type: ignore
        result_dict = result.model_dump()  # type: ignore
    else:
        result_dict = {}
    
    # 安全获取函数
    def safe_get(key: str, default: Any = None) -> Any:
        if isinstance(result_dict, dict):
            return result_dict.get(key, default)
        return default
    
    # 构建输出
    return SearchLoopOutput(
        candidates=safe_get("candidates", []),
        papers_with_code=safe_get("papers_with_code", []),
        paper_cards=safe_get("paper_cards", []),
        anchors=safe_get("anchors", []),
        backup=safe_get("backup", []),
        fusion_hypotheses=safe_get("fusion_hypotheses", []),
        novelty_check=safe_get("novelty_check", {}),
        verification_check=safe_get("verification_check", {}),
        need_supplementary_search=safe_get("need_supplementary_search", False),
        supplementary_queries=safe_get("supplementary_queries", []),
        loop_count=safe_get("loop_count", 0),
        total_candidates=len(safe_get("candidates", [])),
        total_papers_with_code=len([p for p in safe_get("papers_with_code", []) if isinstance(p, dict) and p.get("has_code", False)]),
        total_with_pdf=0  # PDF解析在主图的anchor_pdf_parser节点中执行，这里暂时为0
    )
