## 项目概述
- **名称**: 学术研究创新工作流
- **功能**: 基于Semantic Scholar、arXiv、OpenAlex等平台检索英文文章，进行代码发现、锚定筛选、融合创新的完整科研辅助流程，帮助用户从研究需求到创新方案设计的全流程自动化

### 节点清单
| 节点名 | 文件位置 | 类型 | 功能描述 | 分支逻辑 | 配置文件 |
|-------|---------|------|---------|---------|---------|
| intent_builder | `nodes/intent_builder_node.py` | agent | 需求解析：解析研究题目和描述，提取结构化需求（强制英文关键词） | - | `config/intent_builder_cfg.json` |
| search_loop | `loop_graph.py` | loopcond | 检索循环：调用子图执行学术论文检索、代码发现、融合创新的完整流程 | - | - |
| scholar_searcher | `nodes/scholar_searcher_node.py` | task | 学术检索：使用联网搜索检索英文学术论文，放宽过滤条件，提高检索成功率 | - | - |
| code_hunter | `nodes/code_hunter_node.py` | task | 代码发现：通过PapersWithCode和GitHub搜索查找论文的开源代码 | - | - |
| paper_summarizer | `nodes/paper_summarizer_node.py` | agent | 论文总结：对有代码的论文生成结构化摘要 | - | `config/paper_summarizer_cfg.json` |
| anchor_selector | `nodes/anchor_selector_node.py` | agent | 锚定筛选：基于可复现性和可融合性筛选锚定论文 | - | `config/anchor_selector_cfg.json` |
| fusion_architect | `nodes/fusion_architect_node.py` | agent | 融合创新：基于锚定论文设计融合创新方案 | - | `config/fusion_architect_cfg.json` |
| critic | `nodes/critic_node.py` | agent | 审稿反思：检查融合方案的新颖性和可验证性 | "继续检索"→scholar_searcher, "结束循环"→END | `config/critic_cfg.json` |
| anchor_pdf_parser | `nodes/anchor_pdf_parser_node.py` | task | 锚定论文PDF解析：解析选定锚定论文的PDF内容，增强论文摘要 | - | - |
| result_summary | `nodes/result_summary_node.py` | agent | 结果总结：整合锚定论文和融合方案，生成结构化总结报告 | - | `config/result_summary_cfg.json` |
| pdf_exporter | `nodes/pdf_exporter_node.py` | task | PDF导出：将研究总结报告导出为PDF文件，上传到对象存储，提供下载链接 | - | - |

**类型说明**: task(task节点) / agent(大模型) / condition(条件分支) / loopcond(条件循环)

## 子图清单
| 子图名 | 文件位置 | 功能描述 | 被调用节点 |
|-------|---------|------|---------|-----------|
| search_loop_graph | `graphs/loop_graph.py` | 检索循环子图：包含A2-A7的循环逻辑，实现学术论文检索→代码发现→论文总结→锚定筛选→融合创新→审稿反思的循环流程 | search_loop |

## 工作流架构
```
用户输入
  ↓
intent_builder (A1: 需求解析 - 强制英文关键词)
  ↓
search_loop (调用子图)
  ├─ scholar_searcher (A2: 学术检索 - 使用联网搜索检索英文学术论文，放宽过滤条件)
  ├─ code_hunter (A3: 代码发现 - PapersWithCode + GitHub搜索)
  ├─ paper_summarizer (A4: 论文总结)
  ├─ anchor_selector (A5: 锚定筛选)
  ├─ fusion_architect (A6: 融合创新)
  └─ critic (A7: 审稿反思)
       ↓
  (条件判断: 是否需要补检索)
       ↓
  └─ 是 → 回到scholar_searcher (循环)
  └─ 否 → anchor_pdf_parser (解析选定锚定论文的PDF)
       ↓
  result_summary (结果总结 - 使用增强的锚定论文信息)
       ↓
  pdf_exporter (PDF导出 - 生成PDF研究报告)
  ↓
输出结果（含锚定论文详细简介、融合方案详细说明、PDF报告URL）
```

## 集成使用
- 节点`intent_builder`使用集成：大语言模型（豆包）
- 节点`scholar_searcher`使用集成：联网搜索（Web Search）- **优化检索策略，放宽过滤条件，提高检索成功率**
- 节点`code_hunter`使用集成：联网搜索（Web Search）
- 节点`paper_summarizer`使用集成：大语言模型（豆包）
- 节点`anchor_selector`使用集成：大语言模型（豆包）
- 节点`fusion_architect`使用集成：大语言模型（豆包）
- 节点`critic`使用集成：大语言模型（豆包）
- 节点`result_summary`使用集成：大语言模型（豆包）
- 节点`pdf_exporter`使用集成：reportlab（PDF生成库）、对象存储（S3兼容存储）

## 关键特性
1. **优化检索策略**：移除site过滤，扩大搜索范围，使用英文关键词检索学术论文
2. **放宽过滤条件**：降低质量过滤的严格程度，提高检索成功率
3. **详细日志输出**：在关键步骤输出详细日志，便于调试和问题定位
4. **英文文章过滤**：自动识别并过滤中文论文，只保留英文文章（中文字符占比超过50%才过滤）
5. **强制英文搜索**：无论用户输入是中文还是英文，系统会自动翻译关键词，使用英文进行学术检索
6. **锚定论文PDF解析**：只对选定的锚定论文（3-5篇）进行PDF内容解析，大幅提升检索循环性能
7. **PapersWithCode集成**：优先使用PapersWithCode搜索论文代码，提高代码发现准确率
8. **GitHub代码搜索**：如果PapersWithCode没有找到，则直接搜索GitHub
9. **可配置参数**：
   - `max_candidates`: 最大候选论文数量（默认10）
   - `num_anchors`: 锚定论文数量（默认3）
   - `max_loop_count`: 最大循环次数（默认1）
   - `save_intermediate`: 是否保存中间结果（默认false）

5. **锚定论文评分公式**：
   ```
   AnchorScore = 0.35 * ReproScore + 0.35 * MergeScore + 0.2 * FitScore + 0.1 * Freshness
   ```

6. **融合方案输出要素**：
   - 融合目标（换应用/换模型/换训练目标）
   - 融合方式（A的部件+B的部件）
   - 创新点表述（novelty claim）
   - **可以融合的点在哪里**（重点说明）
   - 可执行改动清单
   - 风险与对策
   - 最小验证实验

7. **结构化输出**：
   - 锚定论文：标题、简介、可融合部件、评分
   - 融合方案：融合方式、创新点、融合点说明、改动清单
   - 审稿结果：新颖性、可验证性分析
   - 最终总结：结构化的markdown报告

8. **循环逻辑**：
   - 主图是DAG（无环），循环通过子图实现
   - 子图内部使用条件边实现循环
   - 当`need_supplementary_search=true`且未达最大循环次数时，继续循环
   - 循环次数自动递增

## 输入输出示例

**输入**：
```json
{
  "task": "设计一个用于电商推荐的图神经网络模型",
  "description": "要求解决冷启动问题，使用注意力机制，需要开源代码可复现",
  "max_candidates": 50,
  "num_anchors": 3,
  "max_loop_count": 3,
  "save_intermediate": true
}
```

**输出**：
```json
{
  "anchors": [
    {
      "title": "LightGCN: Simplifying and Powering Graph Convolution Network for Recommendation",
      "what": "A simple yet effective GCN-based recommendation model",
      "how": "Uses graph convolution layers for recommendation",
      "anchor_score": 0.88,
      "mergeable_parts": ["graph encoder", "bilinear decoder", "loss function"],
      "selection_reason": "High reproducibility and modular design"
    }
  ],
  "fusion_hypotheses": [
    {
      "fusion_target": "换模型：将LightGCN的聚合器替换为注意力机制",
      "fusion_method": "LightGCN的graph encoder + Attention Mechanism",
      "innovation_point": "Introduce attention mechanism into graph convolution layers to address cold start problem",
      "fusion_points": "Replace neighbor aggregation in LightGCN with attention-based aggregation",
      "changes_list": [
        "Modify graph encoder to include attention weights",
        "Update loss function to incorporate attention regularization",
        "Adjust training procedure"
      ],
      "risks_and_solutions": [
        {"risk": "Attention computation overhead", "solution": "Use sparse attention or caching"}
      ],
      "min_validation_experiment": "Test on cold-start users with attention-based aggregation",
      "feasibility": "high"
    }
  ],
  "novelty_check": {
    "has_potential_duplicates": false,
    "analysis": "The combination of LightGCN and attention mechanism for cold start is novel"
  },
  "verification_check": {
    "all_verifiable": true,
    "analysis": "All experiments can be reproduced with public datasets"
  },
  "total_candidates": 50,
  "total_papers_with_code": 15,
  "total_with_pdf": 40,
  "loop_count": 1,
  "final_summary": "# 研究总结\n\n## 研究任务\n设计基于注意力机制的图神经网络电商推荐模型，解决冷启动问题\n\n## 锚定论文\n### 论文1: LightGCN: Simplifying and Powering Graph Convolution Network for Recommendation\n- **简介**: 一个简洁而有效的基于GCN的推荐模型\n- **可融合部件**: graph encoder, bilinear decoder, loss function\n- **评分**: 0.88\n\n## 融合创新方案\n### 方案1: 换模型：将LightGCN的聚合器替换为注意力机制\n- **融合方式**: LightGCN的graph encoder + Attention Mechanism\n- **创新点**: 将注意力机制引入图卷积层以解决冷启动问题\n- **可以融合的点**: 将LightGCN中的邻居聚合替换为基于注意力的聚合\n- **可执行改动**:\n  1. 修改graph encoder以包含注意力权重\n  2. 更新loss函数以包含注意力正则化\n  3. 调整训练流程\n- **可行性**: 高\n\n## 审稿结果\n- **新颖性**: LightGCN与注意力机制结合解决冷启动问题是新颖的\n- **可验证性**: 所有实验都可以使用公开数据集复现\n- **建议**: 建议在多个数据集上进行消融实验\n\n## 结论\n该融合方案具有较高的创新性和可行性，建议进一步开展实验验证。",
  "pdf_url": "https://coze-coding-project.tos.coze.site/coze_storage_xxx/research_summary_xxx_xxx.pdf?sign=..."
}
}
```

## 文件结构
```
├── config/
│   ├── intent_builder_cfg.json      # A1节点配置
│   ├── paper_summarizer_cfg.json    # A4节点配置
│   ├── anchor_selector_cfg.json     # A5节点配置
│   ├── fusion_architect_cfg.json    # A6节点配置
│   ├── critic_cfg.json              # A7节点配置
│   └── result_summary_cfg.json      # 结果总结节点配置
├── src/
│   └── graphs/
│       ├── state.py                 # 状态定义
│       ├── graph.py                 # 主图编排
│       ├── loop_graph.py            # 循环子图编排
│       ├── nodes/
│       │   ├── intent_builder_node.py
│       │   ├── scholar_searcher_node.py  # 学术检索（Semantic Scholar/arXiv/OpenAlex）
│       │   ├── pdf_content_parser_node.py  # PDF内容解析（新增）
│       │   ├── code_hunter_node.py        # 代码发现（PapersWithCode + GitHub）
│       │   ├── paper_summarizer_node.py
│       │   ├── anchor_selector_node.py
│       │   ├── anchor_pdf_parser_node.py  # 锚定论文PDF解析
│       │   ├── fusion_architect_node.py
│       │   ├── critic_node.py
│       │   ├── result_summary_node.py
│       │   └── pdf_exporter_node.py       # PDF导出节点（新增）
│       └── utils/
│           └── pdf/
│               ├── pdf_reader.py          # PDF读取工具
│               ├── __init__.py
│               └── pdf_generator.py       # PDF生成工具（新增）
└── AGENTS.md                        # 本文档

## 修改记录
- **2024-01**: 修改学术检索策略，使用Semantic Scholar、arXiv、OpenAlex等可访问平台检索英文文章（2020-2024）
- **2024-01**: 移除SCI期刊识别逻辑，不限制期刊/会议类型
- **2024-01**: 添加PDF内容解析节点，自动读取论文PDF并提取文本内容
- **2024-01**: 集成PapersWithCode搜索，优先查找论文的官方代码实现
- **2024-01**: 添加结果总结节点，生成结构化的研究总结报告
- **2024-01**: 优化GraphOutput结构，重点输出锚定论文简介和融合方案详细说明
- **2024-01**: **性能优化**：将PDF解析从循环中移除，只对选定的锚定论文（3-5篇）进行PDF解析
- **2024-01**: **中英文优化**：修改intent_builder配置，强制输出英文关键词，无论用户输入是中文还是英文
- **2024-01**: **检索优化**：移除site过滤，扩大搜索范围；放宽质量过滤条件，提高检索成功率
- **2024-01**: **参数优化**：调整默认参数（max_candidates=10, num_anchors=3, max_loop_count=1）
- **2024-01**: **输出优化**：简化结果总结格式，从9个章节减少到6个核心章节（研究问题、锚定论文、对比表、融合方案、MVE、风险与回退策略）
- **2024-01**: **PDF导出**：添加PDF导出节点，使用reportlab库将研究总结报告导出为PDF文件，包含完整的格式化内容
- **2024-01**: **PDF上传**：集成对象存储服务，将生成的PDF上传到云存储，生成可下载的签名URL（有效期7天），用户可直接点击链接下载
- **2024-01**: **锚定论文链接**：在PDF报告的锚定论文部分增加论文链接显示

```
