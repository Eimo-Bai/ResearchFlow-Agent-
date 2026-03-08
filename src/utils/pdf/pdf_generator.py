"""
PDF生成工具
将Markdown格式的研究总结报告转换为PDF
"""
import os
import re
from typing import Dict, List, Any
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# 注册中文字体
def register_chinese_font():
    """注册中文字体"""
    try:
        # 尝试注册常见的中文字体
        font_paths = [
            '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc',
            '/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf',
            '/System/Library/Fonts/PingFang.ttc',
            'C:/Windows/Fonts/msyh.ttc',
            'C:/Windows/Fonts/simhei.ttf',
        ]
        
        for font_path in font_paths:
            if os.path.exists(font_path):
                pdfmetrics.registerFont(TTFont('ChineseFont', font_path))
                return 'ChineseFont'
        
        # 如果找不到中文字体，使用默认字体（可能不支持中文）
        return 'Helvetica'
    except Exception as e:
        print(f"注册中文字体失败: {e}")
        return 'Helvetica'

CHINESE_FONT = register_chinese_font()


def generate_pdf_from_markdown(markdown_content: str, output_path: str) -> str:
    """
    将Markdown内容转换为PDF
    
    Args:
        markdown_content: Markdown格式的文本内容
        output_path: PDF输出路径
        
    Returns:
        PDF文件的绝对路径
    """
    # 确保输出目录存在
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # 创建PDF文档
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    
    # 创建样式
    styles = getSampleStyleSheet()
    
    # 自定义样式
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontName=CHINESE_FONT,
        fontSize=20,
        spaceAfter=20,
        textColor=colors.HexColor('#1f77b4'),
        alignment=1  # 居中
    )
    
    heading2_style = ParagraphStyle(
        'CustomHeading2',
        parent=styles['Heading2'],
        fontName=CHINESE_FONT,
        fontSize=16,
        spaceAfter=12,
        spaceBefore=12,
        textColor=colors.HexColor('#2c3e50')
    )
    
    heading3_style = ParagraphStyle(
        'CustomHeading3',
        parent=styles['Heading3'],
        fontName=CHINESE_FONT,
        fontSize=14,
        spaceAfter=10,
        spaceBefore=10,
        textColor=colors.HexColor('#34495e')
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontName=CHINESE_FONT,
        fontSize=11,
        spaceAfter=8,
        leading=16,
        wordWrap='CJK'
    )
    
    # 解析Markdown并构建PDF元素
    elements = []
    
    # 按行分割Markdown内容
    lines = markdown_content.split('\n')
    current_section = None
    bullet_list = []
    table_data = []
    in_table = False
    
    for line in lines:
        line = line.strip()
        
        # 跳过空行
        if not line:
            if bullet_list:
                # 输出列表
                for item in bullet_list:
                    elements.append(Paragraph(f"• {item}", normal_style))
                bullet_list = []
            continue
        
        # 处理一级标题（##）
        if line.startswith('## ') and not line.startswith('###'):
            if bullet_list:
                for item in bullet_list:
                    elements.append(Paragraph(f"• {item}", normal_style))
                bullet_list = []
            elements.append(Paragraph(line[3:], title_style))
            continue
        
        # 处理二级标题（###）
        if line.startswith('###'):
            if bullet_list:
                for item in bullet_list:
                    elements.append(Paragraph(f"• {item}", normal_style))
                bullet_list = []
            elements.append(Paragraph(line[4:], heading2_style))
            continue
        
        # 处理三级标题（####）
        if line.startswith('####'):
            if bullet_list:
                for item in bullet_list:
                    elements.append(Paragraph(f"• {item}", normal_style))
                bullet_list = []
            elements.append(Paragraph(line[5:], heading3_style))
            continue
        
        # 处理列表项（- 或数字.）
        if line.startswith('- ') or re.match(r'^\d+\.', line):
            if bullet_list:
                bullet_list.append(line[2:] if line.startswith('- ') else line.split('.', 1)[1].strip())
            else:
                bullet_list = [line[2:] if line.startswith('- ') else line.split('.', 1)[1].strip()]
            continue
        
        # 处理表格
        if line.startswith('|'):
            if not in_table:
                in_table = True
            
            # 解析表格行
            cells = [cell.strip() for cell in line.split('|')[1:-1]]
            if cells and cells[0]:  # 跳过分隔行
                table_data.append(cells)
            continue
        else:
            if in_table:
                # 表格结束，输出表格
                if table_data and len(table_data) > 1:
                    # 创建表格
                    table = Table(table_data)
                    table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), CHINESE_FONT),
                        ('FONTSIZE', (0, 0), (-1, 0), 12),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                        ('FONTNAME', (0, 1), (-1, -1), CHINESE_FONT),
                        ('FONTSIZE', (0, 1), (-1, -1), 10),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black),
                        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
                    ]))
                    elements.append(table)
                    elements.append(Spacer(1, 0.5*cm))
                table_data = []
                in_table = False
        
        # 处理普通段落
        if bullet_list:
            for item in bullet_list:
                elements.append(Paragraph(f"• {item}", normal_style))
            bullet_list = []
        
        elements.append(Paragraph(line, normal_style))
    
    # 输出剩余的列表项
    if bullet_list:
        for item in bullet_list:
            elements.append(Paragraph(f"• {item}", normal_style))
    
    # 生成PDF
    doc.build(elements)
    
    return output_path


def generate_research_summary_pdf(summary_data: Dict[str, Any], output_path: str) -> str:
    """
    根据研究总结数据生成PDF
    
    Args:
        summary_data: 研究总结数据（包含anchors、fusion_hypotheses等）
        output_path: PDF输出路径
        
    Returns:
        PDF文件的绝对路径
    """
    markdown_content = build_markdown_summary(summary_data)
    return generate_pdf_from_markdown(markdown_content, output_path)


def build_markdown_summary(summary_data: Dict[str, Any]) -> str:
    """
    根据研究总结数据构建Markdown文本
    
    Args:
        summary_data: 研究总结数据
        
    Returns:
        Markdown格式的文本
    """
    lines = []
    
    # 研究问题
    research_problem = summary_data.get('research_problem', '未指定')
    lines.append("## 研究问题")
    lines.append(research_problem)
    lines.append("")
    
    # 锚定论文
    anchors = summary_data.get('anchors', [])
    if anchors:
        lines.append("## 锚定论文")
        for i, anchor in enumerate(anchors, 1):
            title = anchor.get('title', '未命名')
            url = anchor.get('url', '')
            selection_reason = anchor.get('selection_reason', '无')
            lines.append(f"### {i}. {title}")
            if url:
                lines.append(f"- **论文链接**: {url}")
            lines.append(f"- **方法**: {selection_reason[:100]}...")
            lines.append(f"- **选择理由**: {selection_reason}")
            lines.append("")
    
    # 对比表
    if anchors:
        lines.append("## 对比表")
        # 构建表格数据
        table_lines = ["| 论文 | 数据集 | 指标 | 核心贡献 | 复现成本 | 可改进点 |"]
        table_lines.append("|------|--------|------|----------|----------|----------|")
        for anchor in anchors:
            title = anchor.get('title', '')[:30] + '...' if len(anchor.get('title', '')) > 30 else anchor.get('title', '')
            venue = anchor.get('venue', '未指定')
            # 简化处理，使用占位符
            table_lines.append(f"| {title} | 公开数据集 | 推荐精度/召回率/NDCG | 模型优化与增强 | 低/中/高 | 可进一步优化 |")
        lines.extend(table_lines)
        lines.append("")
    
    # 融合创新方案
    fusion_hypotheses = summary_data.get('fusion_hypotheses', [])
    if fusion_hypotheses:
        lines.append("## 融合创新方案")
        for i, fusion in enumerate(fusion_hypotheses, 1):
            target = fusion.get('fusion_target', '未指定')
            method = fusion.get('fusion_method', '未指定')
            risks = fusion.get('risks_and_solutions', [])
            
            lines.append(f"### 方案{i}: {target}")
            lines.append(f"- **改哪里**: {method[:100]}...")
            lines.append(f"- **为什么有效**: 见详细说明")
            lines.append(f"- **风险**:")
            for risk_item in risks:
                risk = risk_item.get('risk', '未指定')
                solution = risk_item.get('solution', '未指定')
                lines.append(f"  - {risk}")
                lines.append(f"    解决方案: {solution}")
            lines.append("")
    
    # 最小验证实验
    lines.append("## 最小验证实验（MVE）")
    lines.append("- **基线**: 原始模型")
    lines.append("- **数据集**: 公开数据集")
    lines.append("- **指标**: 推荐准确率、召回率、NDCG")
    lines.append("- **对照组**: 原始模型、融合模型")
    lines.append("- **预期结果**: 指标提升3%-5%")
    lines.append("- **失败条件**: 指标无提升或下降超过1%")
    lines.append("")
    
    # 风险与回退策略
    lines.append("## 风险与回退策略")
    lines.append("- **无代码**: 基于开源代码手动实现核心模块")
    lines.append("- **结论冲突**: 拆分模块逐一验证，保留有效组件")
    lines.append("- **数据不可得**: 替换为同类型公开数据集")
    lines.append("- **其他风险**: 根据具体情况调整策略")
    
    return '\n'.join(lines)
