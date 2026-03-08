"""
学术研究创新工作流 - 主图编排
基于7个Agent节点实现学术论文检索、代码发现、融合创新的完整流程
主图结构：A1意图构建 -> 检索循环子图(A2-A7) -> 结果总结 -> 输出
"""
from langgraph.graph import StateGraph, END
from typing import Dict, Any

from graphs.state import (
    GlobalState,
    GraphInput,
    GraphOutput
)

from graphs.nodes.intent_builder_node import intent_builder_node
from graphs.nodes.result_summary_node import result_summary_node
from graphs.nodes.anchor_pdf_parser_node import anchor_pdf_parser_node
from graphs.nodes.pdf_exporter_node import pdf_exporter_node
from graphs.loop_graph import search_loop_graph, call_search_loop, SearchLoopInput, SearchLoopOutput


# ==================== 图编排 ====================
def create_graph() -> StateGraph:
    """创建学术研究创新工作流主图"""
    
    # 创建状态图，指定入参和出参
    builder = StateGraph(
        GlobalState,
        input_schema=GraphInput,
        output_schema=GraphOutput
    )
    
    # 添加节点
    builder.add_node(
        "intent_builder",
        intent_builder_node,
        metadata={"type": "agent", "llm_cfg": "config/intent_builder_cfg.json"}
    )
    
    builder.add_node(
        "search_loop",
        call_search_loop,
        metadata={"type": "loopcond"}
    )
    
    builder.add_node("anchor_pdf_parser", anchor_pdf_parser_node)
    
    builder.add_node(
        "result_summary",
        result_summary_node,
        metadata={"type": "agent", "llm_cfg": "config/result_summary_cfg.json"}
    )
    
    builder.add_node("pdf_exporter", pdf_exporter_node)
    
    # 设置入口点
    builder.set_entry_point("intent_builder")
    
    # 添加边（线性流程）
    builder.add_edge("intent_builder", "search_loop")
    builder.add_edge("search_loop", "anchor_pdf_parser")
    builder.add_edge("anchor_pdf_parser", "result_summary")
    builder.add_edge("result_summary", "pdf_exporter")
    builder.add_edge("pdf_exporter", END)
    
    # 编译图
    return builder.compile()


# 创建全局图实例
main_graph = create_graph()
