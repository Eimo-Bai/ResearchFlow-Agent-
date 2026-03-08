"""
学术研究创新工作流 - 状态定义
包含全局状态、图输入输出、节点输入输出
"""
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field


# ==================== 全局状态 ====================
class GlobalState(BaseModel):
    """工作流全局状态"""
    # 用户输入
    task: str = Field(..., description="研究任务题目")
    description: str = Field(..., description="任务描述/要求")
    
    # 可配置参数（默认值调整为更快输出）
    max_candidates: int = Field(default=10, description="最大候选论文数量")
    num_anchors: int = Field(default=3, description="锚定论文数量")
    max_loop_count: int = Field(default=1, description="最大循环次数")
    save_intermediate: bool = Field(default=False, description="是否保存中间结果")
    
    # 循环计数
    loop_count: int = Field(default=0, description="当前循环次数")
    
    # 统计字段
    total_candidates: int = Field(default=0, description="检索到的候选论文总数")
    total_papers_with_code: int = Field(default=0, description="有代码的论文数量")
    total_with_pdf: int = Field(default=0, description="成功读取PDF的论文数")
    
    # A1 输出：结构化需求
    research_task: str = Field(default="", description="结构化研究任务")
    constraints: Dict[str, Any] = Field(default={}, description="约束条件")
    keywords: List[str] = Field(default=[], description="关键词列表")
    exclusion: List[str] = Field(default=[], description="排除内容")
    
    # A2 输出：候选论文池
    candidates: List[Dict[str, Any]] = Field(default=[], description="候选论文列表")
    
    # A3 输出：带代码标记的论文
    papers_with_code: List[Dict[str, Any]] = Field(default=[], description="有代码的论文列表")
    
    # A4 输出：论文摘要卡片
    paper_cards: List[Dict[str, Any]] = Field(default=[], description="论文摘要卡片")
    
    # A5 输出：锚定论文和候补论文
    anchors: List[Dict[str, Any]] = Field(default=[], description="锚定论文列表")
    backup: List[Dict[str, Any]] = Field(default=[], description="候补论文列表")
    
    # A6 输出：融合创新方案
    fusion_hypotheses: List[Dict[str, Any]] = Field(default=[], description="融合创新方案")
    
    # A7 输出：审稿结果
    need_supplementary_search: bool = Field(default=False, description="是否需要补检索")
    supplementary_queries: List[str] = Field(default=[], description="补检索查询词")
    novelty_check: Dict[str, Any] = Field(default={}, description="新颖性检查结果")
    verification_check: Dict[str, Any] = Field(default={}, description="可验证性检查结果")
    
    # 结果总结
    final_summary: str = Field(default="", description="最终研究总结")


# ==================== 图输入输出 ====================
class GraphInput(BaseModel):
    """工作流输入"""
    task: str = Field(..., description="研究任务题目")
    description: str = Field(..., description="任务描述/要求")
    max_candidates: int = Field(default=10, description="最大候选论文数量（建议10-20）")
    num_anchors: int = Field(default=3, description="锚定论文数量（建议2-5）")
    max_loop_count: int = Field(default=1, description="最大循环次数（建议1-2）")
    save_intermediate: bool = Field(default=False, description="是否保存中间结果")


class GraphOutput(BaseModel):
    """工作流输出"""
    # 锚定论文详细信息
    anchors: List[Dict[str, Any]] = Field(..., description="锚定论文列表（含标题、简介、评分、可融合部件）")
    # 融合创新方案
    fusion_hypotheses: List[Dict[str, Any]] = Field(..., description="融合创新方案（含融合方式、创新点、可执行改动清单）")
    # 审稿结果
    novelty_check: Dict[str, Any] = Field(..., description="新颖性检查结果")
    verification_check: Dict[str, Any] = Field(..., description="可验证性检查结果")
    # 统计信息
    total_candidates: int = Field(..., description="检索到的候选论文总数")
    total_papers_with_code: int = Field(..., description="有代码的论文数量")
    total_with_pdf: int = Field(..., description="成功读取PDF的论文数")
    loop_count: int = Field(..., description="实际循环次数")
    # 研究总结
    final_summary: str = Field(default="", description="研究总结：锚定论文简介和融合方案概述")
    # PDF报告
    pdf_url: str = Field(default="", description="PDF研究报告的URL")


# ==================== A1: 需求解析 Agent ====================
class IntentBuilderInput(BaseModel):
    """A1 节点输入"""
    task: str = Field(..., description="研究任务题目")
    description: str = Field(..., description="任务描述/要求")


class IntentBuilderOutput(BaseModel):
    """A1 节点输出"""
    research_task: str = Field(..., description="结构化研究任务")
    constraints: Dict[str, Any] = Field(..., description="约束条件（年份范围、必须开源、可复现性、数据偏好）")
    keywords: List[str] = Field(..., description="关键词列表（10-20个）")
    exclusion: List[str] = Field(..., description="排除内容列表")


# ==================== A2: 检索 Agent ====================
class ScholarSearcherInput(BaseModel):
    """A2 节点输入"""
    keywords: List[str] = Field(..., description="关键词列表")
    constraints: Dict[str, Any] = Field(..., description="约束条件")
    max_candidates: int = Field(..., description="最大候选论文数量")


class ScholarSearcherOutput(BaseModel):
    """A2 节点输出"""
    candidates: List[Dict[str, Any]] = Field(..., description="候选论文列表")
    total_candidates: int = Field(..., description="实际检索到的论文数量")


# ==================== A2.5: PDF内容解析 Agent ====================
class PDFContentParserInput(BaseModel):
    """PDF内容解析节点输入"""
    candidates: List[Dict[str, Any]] = Field(..., description="候选论文列表")


class PDFContentParserOutput(BaseModel):
    """PDF内容解析节点输出"""
    candidates: List[Dict[str, Any]] = Field(..., description="增强后的候选论文列表（含PDF内容）")
    total_candidates: int = Field(..., description="论文总数")
    total_with_pdf: int = Field(..., description="成功读取PDF的论文数")


# ==================== A3: 代码发现 Agent ====================
class CodeHunterInput(BaseModel):
    """A3 节点输入"""
    candidates: List[Dict[str, Any]] = Field(..., description="候选论文列表")


class CodeHunterOutput(BaseModel):
    """A3 节点输出"""
    papers_with_code: List[Dict[str, Any]] = Field(..., description="有代码的论文列表")
    total_papers_with_code: int = Field(..., description="有代码的论文数量")


# ==================== A4: 快速总结 Agent ====================
class PaperSummarizerInput(BaseModel):
    """A4 节点输入"""
    papers_with_code: List[Dict[str, Any]] = Field(..., description="有代码的论文列表")


class PaperSummarizerOutput(BaseModel):
    """A4 节点输出"""
    paper_cards: List[Dict[str, Any]] = Field(..., description="论文摘要卡片列表")
    total_summarized: int = Field(..., description="已总结的论文数量")


# ==================== A5: 锚定筛选 Agent ====================
class AnchorSelectorInput(BaseModel):
    """A5 节点输入"""
    paper_cards: List[Dict[str, Any]] = Field(..., description="论文摘要卡片")
    research_task: str = Field(..., description="研究任务")
    constraints: Dict[str, Any] = Field(..., description="约束条件")
    num_anchors: int = Field(..., description="需要的锚定论文数量")


class AnchorSelectorOutput(BaseModel):
    """A5 节点输出"""
    anchors: List[Dict[str, Any]] = Field(..., description="锚定论文列表（含评分）")
    backup: List[Dict[str, Any]] = Field(..., description="候补论文列表")


# ==================== A6: 融合创新 Agent ====================
class FusionArchitectInput(BaseModel):
    """A6 节点输入"""
    anchors: List[Dict[str, Any]] = Field(..., description="锚定论文列表")
    research_task: str = Field(..., description="研究任务")


class FusionArchitectOutput(BaseModel):
    """A6 节点输出"""
    fusion_hypotheses: List[Dict[str, Any]] = Field(..., description="融合创新方案列表")
    total_hypotheses: int = Field(..., description="生成的方案数量")


# ==================== A7: 审稿人/反思 Agent ====================
class CriticInput(BaseModel):
    """A7 节点输入"""
    fusion_hypotheses: List[Dict[str, Any]] = Field(..., description="融合创新方案")
    research_task: str = Field(..., description="研究任务")
    keywords: List[str] = Field(..., description="关键词列表")
    loop_count: int = Field(..., description="当前循环次数")
    max_loop_count: int = Field(..., description="最大循环次数")


class CriticOutput(BaseModel):
    """A7 节点输出"""
    need_supplementary_search: bool = Field(..., description="是否需要补检索")
    supplementary_queries: List[str] = Field(..., description="补检索查询词（如需要）")
    novelty_check: Dict[str, Any] = Field(..., description="新颖性检查结果")
    verification_check: Dict[str, Any] = Field(..., description="可验证性检查结果")
    loop_count: int = Field(..., description="更新后的循环次数")


# ==================== 循环条件判断 ====================
class ShouldContinueSearchInput(BaseModel):
    """循环条件判断输入"""
    need_supplementary_search: bool = Field(..., description="是否需要补检索")
    loop_count: int = Field(..., description="当前循环次数")
    max_loop_count: int = Field(..., description="最大循环次数")


# ==================== 子图调用节点 ====================
class SearchLoopInput(BaseModel):
    """检索循环子图调用节点输入"""
    keywords: List[str] = Field(..., description="关键词列表")
    constraints: Dict[str, Any] = Field(..., description="约束条件")
    max_candidates: int = Field(..., description="最大候选论文数量")
    num_anchors: int = Field(..., description="锚定论文数量")
    research_task: str = Field(..., description="研究任务")
    loop_count: int = Field(default=0, description="当前循环次数")
    max_loop_count: int = Field(default=3, description="最大循环次数")


class SearchLoopOutput(BaseModel):
    """检索循环子图调用节点输出"""
    candidates: List[Dict[str, Any]] = Field(default=[], description="候选论文列表")
    papers_with_code: List[Dict[str, Any]] = Field(default=[], description="有代码的论文列表")
    paper_cards: List[Dict[str, Any]] = Field(default=[], description="论文摘要卡片")
    anchors: List[Dict[str, Any]] = Field(default=[], description="锚定论文列表")
    backup: List[Dict[str, Any]] = Field(default=[], description="候补论文列表")
    fusion_hypotheses: List[Dict[str, Any]] = Field(default=[], description="融合创新方案")
    novelty_check: Dict[str, Any] = Field(default={}, description="新颖性检查结果")
    verification_check: Dict[str, Any] = Field(default={}, description="可验证性检查结果")
    need_supplementary_search: bool = Field(default=False, description="是否需要补检索")
    supplementary_queries: List[str] = Field(default=[], description="补检索查询词")
    loop_count: int = Field(default=0, description="更新后的循环次数")
    total_candidates: int = Field(default=0, description="检索到的候选论文总数")
    total_papers_with_code: int = Field(default=0, description="有代码的论文数量")
    total_with_pdf: int = Field(default=0, description="成功读取PDF的论文数")


# ==================== 保存中间结果 ====================
class SaveResultsInput(BaseModel):
    """保存结果节点输入"""
    research_task: str = Field(..., description="研究任务")
    candidates: List[Dict[str, Any]] = Field(default=[], description="候选论文")
    papers_with_code: List[Dict[str, Any]] = Field(default=[], description="有代码的论文")
    paper_cards: List[Dict[str, Any]] = Field(default=[], description="论文摘要")
    anchors: List[Dict[str, Any]] = Field(default=[], description="锚定论文")
    fusion_hypotheses: List[Dict[str, Any]] = Field(default=[], description="融合方案")
    novelty_check: Dict[str, Any] = Field(default={}, description="新颖性检查")
    verification_check: Dict[str, Any] = Field(default={}, description="可验证性检查")
    loop_count: int = Field(default=0, description="循环次数")


class SaveResultsOutput(BaseModel):
    """保存结果节点输出"""
    saved: bool = Field(..., description="是否保存成功")
    file_path: str = Field(default="", description="保存的文件路径")


# ==================== 结果总结节点 ====================
class ResultSummaryInput(BaseModel):
    """结果总结节点输入"""
    anchors: List[Dict[str, Any]] = Field(default=[], description="锚定论文列表")
    fusion_hypotheses: List[Dict[str, Any]] = Field(default=[], description="融合创新方案")
    novelty_check: Dict[str, Any] = Field(default={}, description="新颖性检查结果")
    verification_check: Dict[str, Any] = Field(default={}, description="可验证性检查结果")
    research_task: str = Field(default="", description="研究任务")


class ResultSummaryOutput(BaseModel):
    """结果总结节点输出"""
    final_summary: str = Field(..., description="研究总结：锚定论文简介和融合方案概述")


# ==================== 锚定论文PDF解析节点 ====================
class AnchorPDFParserInput(BaseModel):
    """锚定论文PDF解析节点输入"""
    anchors: List[Dict[str, Any]] = Field(..., description="锚定论文列表")


class AnchorPDFParserOutput(BaseModel):
    """锚定论文PDF解析节点输出"""
    enriched_anchors: List[Dict[str, Any]] = Field(..., description="增强后的锚定论文列表（含PDF内容）")
    total_anchors: int = Field(..., description="锚定论文数量")
    total_with_pdf: int = Field(..., description="成功读取PDF的论文数")


# ==================== PDF导出节点 ====================
class PDFExporterInput(BaseModel):
    """PDF导出节点输入"""
    anchors: List[Dict[str, Any]] = Field(..., description="锚定论文列表")
    fusion_hypotheses: List[Dict[str, Any]] = Field(..., description="融合创新方案")
    final_summary: str = Field(..., description="研究总结文本")
    task: str = Field(..., description="研究任务题目")


class PDFExporterOutput(BaseModel):
    """PDF导出节点输出"""
    pdf_url: str = Field(..., description="PDF文件的URL")
    pdf_path: str = Field(..., description="PDF文件路径")
