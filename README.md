# ResearchFlow Agent 🚀
> 面向研发/科研场景的端到端大模型多 Agent 工作流工具  
> 目标不是“生成摘要”，而是稳定交付：**2–3 篇锚定论文 + 结构化对比表 + 融合创新点 + 最小验证实验清单（MVE）**

---

## 1. 背景（Why）
我长期兼职做论文辅导/科研协作，真实交付要求是：面对不同方向的需求，快速找到**能作为 baseline、能继续拓展**的锚定论文，并给出一条**可执行的实验路线**。  
但现实里存在三个典型痛点：

1) **信息过载**：论文太多，筛选成本高；  
2) **可复现断层**：大量论文缺少可复现实现或线索分散，“看懂了也做不出来”；  
3) **难以收敛成可执行方案**：相关工作读完后仍难落到“下一步做什么”，从选题到实验周期长且质量不稳定。

ResearchFlow Agent 把“论文辅导交付”产品化为一条可复用的多 Agent 工作流，核心关注点是：
- ✅ 可复现（code-first）
- ✅ 可执行（MVE 清单）
- ✅ 可追溯（结构化中间产物 + 质检回退）

---

## 2. 你会得到什么（Deliverables）
给定一个研究任务与约束，系统稳定输出：

### 2.1 锚定论文（Anchors）
- 自动筛选 **2–3 篇** “可跑可改”的锚定论文  
- 每篇附：选择理由（相关性/代表性/可复现性/可扩展性）、复现线索、成本评估、局限与可拓展方向

### 2.2 结构化对比表（Structured Comparison）
- 用统一模板对齐：问题定义、方法框架、数据集、指标、实现/复现线索、关键贡献、局限、复现成本

### 2.3 融合创新点（Innovation Hypotheses）
- 基于锚定论文生成“可落地的融合/改进方向”
- 标注风险点（数据可得性、指标不可比、资源成本、潜在 failure cases）

### 2.4 最小验证实验清单（MVE Checklist）
- 给出 1–3 个最小实验，验证创新点是否有效  
- 明确：baseline、数据集/指标、关键步骤、对照组设计、预期结果与判断标准

---

## 3. 工作流总览（Multi-Agent Workflow）

### 3.1 Mermaid 可视化版
【ResearchFlow Agent 工作流（Multi-Agent Workflow）】

User Input
  ↓
Planner（需求澄清）
- 将方向/约束（数据、指标、是否必须有代码、截止时间、算力等）
  转成检索策略与筛选标准（Retrieval Spec）

  ↓
Retriever（论文检索）
- 拉取候选论文池（Candidate Pool）

  ↓
Code Scout（code-first 复现过滤）
- 查找开源代码/复现线索（repo、脚本、权重、issue 等）
- 标注复现风险与成本（低/中/高）

  ↓
Reader（结构化精读）
- 用统一模板抽取：问题、方法、数据集、指标、贡献、局限、复现成本

  ↓
Selector（打分筛选）
- 按相关性/代表性/可复现性/可扩展性打分
- 选出 2–3 篇锚定论文，并说明选择理由

  ↓
Reviewer（质检门禁 + 回退）
- 检查引用可靠、结论自洽、实验建议可执行
- 不通过：回退到 Retriever/Selector 重新跑一轮

  ↓
Final Deliverables（最终交付）
- 2–3 篇锚定论文 + 结构化对比表 + 融合创新点 + 最小验证实验清单（MVE）


【API 调用示例（Python，仅 1 个示例）】

import requests

url = "https://<YOUR_COZE_DOMAIN>/run"
headers = {
  "Authorization": "Bearer <YOUR_TOKEN>",
  "Content-Type": "application/json"
}

payload = {
  "task": "Find reproducible baselines for cold-start recommendation",
  "description": "Must have runnable code; prefer public datasets; metric=NDCG@10; deadline=2 days",
  "max_candidates": 10,
  "num_anchors": 3,
  "max_loop_count": 1,
  "save_intermediate": False
}

res = requests.post(url, headers=headers, json=payload)
print(res.status_code)
print(res.text)

## 4. Agent 角色说明（Agents）

### 4.1 Planner（计划者）
**目标：**把“模糊需求”转成“可检索、可筛选、可验收”的规格（类似轻量 PRD）
- 输入：研究方向、任务目标、约束（数据/指标/必须有代码/截止时间/算力等）
- 输出：检索策略（query + source + time window）、筛选标准（可复现性优先等）、交付格式

### 4.2 Retriever（巡回者）
**目标：**拉取覆盖面足够且不过载的候选论文池
- 多轮检索：关键词扩展、同义改写、重要会议/期刊范围
- 初筛：明显不相关/质量不达标/无法获取的候选剔除

### 4.3 Code Scout（代码侦察）—— code-first 核心
**目标：**优先锁定“可复现路线”，避免“只会讲不会做”
- 找开源实现/复现线索（repo、复现报告、环境说明、权重链接等）
- 评估可跑通概率：依赖复杂度、脚本完备性、数据可得性、环境新旧
- 输出：代码链接 + 复现风险标注（缺数据/缺权重/环境过旧/仅伪代码等）

### 4.4 Reader（结构化精读）
**目标：**用统一模板把论文“读成结构化信息”，便于对比与落地
模板字段示例：
- Problem / Setup（问题定义、任务设定）
- Method（方法框架与关键模块）
- Dataset / Metrics（数据集与指标）
- Contributions（核心贡献）
- Limitations（局限与 failure cases）
- Repro Cost（复现成本：数据/算力/工程复杂度）
- Extension Ideas（可扩展方向）

### 4.5 Selector（选择器）
**目标：**从候选中选出 2–3 篇“锚定论文”，并解释 why
- 打分维度（可配置权重）：相关性 / 代表性 / 可复现性 / 可扩展性
- 输出：锚定论文列表 + 选择理由 + 备选池（可选）

### 4.6 Reviewer（质检员 / 护栏）
**目标：**把质量做成机制，降低幻觉与不可执行建议
- 引用可靠性检查：标题/作者/会议、是否张冠李戴
- 结论自洽性检查：创新点是否真的由锚定论文推导
- 可执行性检查：数据/指标/资源/步骤是否闭环
- FAIL 触发 rollback：回到 Retriever 或 Selector 重跑，提高交付稳定性

---

## 5. 快速开始（Quick Start）— API 调用示例（可直接复制）

> 替换下面的占位符：  
> - `<YOUR_COZE_DOMAIN>`：你的 Coze 部署域名（例如：gyz344qgv3.coze.site）  
> - `<YOUR_TOKEN>`：你的 API Token（不要提交到仓库）

---

## 5. API 调用示例（可复制）

> 替换占位符：  
> - `<YOUR_COZE_DOMAIN>`：例如 `gyz344qgv3.coze.site`  
> - `<YOUR_TOKEN>`：你的 API Token（不要提交到仓库）

---

### 5.1 获取入参 schema（可选）

**cURL**
```bash
curl --location --request GET 'https://<YOUR_COZE_DOMAIN>/graph_parameter' \
  --header 'Authorization: Bearer <YOUR_TOKEN>'
```

**Python**
```python
import requests

url = "https://<YOUR_COZE_DOMAIN>/graph_parameter"
headers = {"Authorization": "Bearer <YOUR_TOKEN>"}

res = requests.get(url, headers=headers)
print(res.status_code)
print(res.text)
```

---

### 5.2 执行工作流（Run）

**cURL**
```bash
curl --location --request POST 'https://<YOUR_COZE_DOMAIN>/run' \
  --header 'Authorization: Bearer <YOUR_TOKEN>' \
  --header 'Content-Type: application/json' \
  --data '{
    "task": "研究任务题目（必填）",
    "description": "任务描述/约束（选填：数据集/指标/必须有代码/截止时间等）",
    "max_candidates": 10,
    "num_anchors": 3,
    "max_loop_count": 1,
    "save_intermediate": false
  }'
```

**Python**
```python
import requests

url = "https://<YOUR_COZE_DOMAIN>/run"
headers = {
    "Authorization": "Bearer <YOUR_TOKEN>",
    "Content-Type": "application/json"
}

payload = {
    "task": "Find reproducible baselines for cold-start recommendation",
    "description": "Must have runnable code; prefer public datasets; metric=NDCG@10; deadline=2 days",
    "max_candidates": 10,
    "num_anchors": 3,
    "max_loop_count": 1,
    "save_intermediate": False
}

res = requests.post(url, headers=headers, json=payload)
print(res.status_code)
print(res.text)
```

---

## 6. 参数说明（API Parameters）

| 参数 | 类型 | 默认 | 说明 |
|---|---|---:|---|
| task | string | - | 研究任务/题目（必填） |
| description | string | "" | 任务描述/约束：数据集/指标/必须有代码/截止时间/算力等 |
| max_candidates | int | 10 | 最大候选论文数量（建议 10–20） |
| num_anchors | int | 3 | 锚定论文数量（建议 2–5） |
| max_loop_count | int | 1 | 最大回退重跑次数（建议 1–2） |
| save_intermediate | bool | false | 是否保存中间产物（便于 debug/复盘） |

---

## 7. 输出结构（Output Schema）

```json
{
  "anchors": [
    {
      "title": "Paper Title",
      "year": 2024,
      "venue": "NeurIPS/ICLR/ACL/...",
      "why_selected": ["relevance", "reproducibility", "extendability"],
      "links": {
        "paper": "https://arxiv.org/abs/xxxx.xxxxx",
        "code": ["https://github.com/xxx/yyy"]
      },
      "reading_notes": {
        "problem": "...",
        "method": "...",
        "datasets": ["..."],
        "metrics": ["..."],
        "contributions": ["..."],
        "limitations": ["..."],
        "repro_cost": "low/medium/high"
      }
    }
  ],
  "comparison_table": [
    { "paper": "...", "method": "...", "dataset": "...", "metric": "...", "code": "...", "notes": "..." }
  ],
  "innovation_hypotheses": [
    { "idea": "...", "rationale": "...", "risk": "...", "validation": "..." }
  ],
  "mve_checklist": [
    { "exp": "MVE-1", "baseline": "...", "dataset": "...", "metric": "...", "steps": ["..."], "expected": "..." }
  ],
  "warnings": ["data availability risk", "metric mismatch risk"]
}
```
