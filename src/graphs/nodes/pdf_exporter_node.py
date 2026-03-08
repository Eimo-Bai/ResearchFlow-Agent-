"""
PDF导出节点
将研究总结报告导出为PDF文件，并上传到对象存储提供下载链接
"""
import os
import time
from typing import Dict, Any, List
from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context
from coze_coding_dev_sdk.s3 import S3SyncStorage
from utils.pdf.pdf_generator import generate_research_summary_pdf

from graphs.state import PDFExporterInput, PDFExporterOutput


def pdf_exporter_node(
    state: PDFExporterInput,
    config: RunnableConfig,
    runtime: Runtime[Context]
) -> PDFExporterOutput:
    """
    title: PDF导出
    desc: 将研究总结报告导出为PDF文件，上传到对象存储，提供下载链接
    integrations: reportlab, 对象存储
    """
    ctx = runtime.context
    
    # 构建研究总结数据
    summary_data = {
        'research_problem': state.task,
        'anchors': state.anchors,
        'fusion_hypotheses': state.fusion_hypotheses,
        'final_summary': state.final_summary
    }
    
    # 生成PDF文件路径（本地临时文件）
    timestamp = int(time.time())
    pdf_filename = f"research_summary_{timestamp}.pdf"
    pdf_path = os.path.join("/tmp", pdf_filename)
    
    # 生成PDF到本地
    try:
        print(f"开始生成PDF文件: {pdf_path}")
        generate_research_summary_pdf(summary_data, pdf_path)
        print(f"PDF生成成功: {pdf_path}")
    except Exception as e:
        raise Exception(f"PDF生成失败: {e}")
    
    # 上传到对象存储
    try:
        # 初始化对象存储客户端
        storage = S3SyncStorage(
            endpoint_url=os.getenv("COZE_BUCKET_ENDPOINT_URL"),
            access_key="",
            secret_key="",
            bucket_name=os.getenv("COZE_BUCKET_NAME"),
            region="cn-beijing",
        )
        
        # 上传PDF文件到对象存储
        print(f"开始上传PDF到对象存储...")
        with open(pdf_path, 'rb') as f:
            file_key = storage.stream_upload_file(
                fileobj=f,
                file_name=f"research_summaries/{pdf_filename}",
                content_type="application/pdf",
            )
        
        print(f"PDF上传成功，key: {file_key}")
        
        # 生成下载链接（有效期7天）
        download_url = storage.generate_presigned_url(
            key=file_key,
            expire_time=604800,  # 7天 = 7 * 24 * 60 * 60
        )
        
        print(f"下载链接生成成功: {download_url}")
        
        # 删除本地临时文件
        try:
            os.remove(pdf_path)
            print(f"本地临时文件已删除: {pdf_path}")
        except Exception as e:
            print(f"删除本地文件失败（可忽略）: {e}")
        
        return PDFExporterOutput(
            pdf_url=download_url,
            pdf_path=pdf_path  # 保留本地路径供调试使用
        )
        
    except Exception as e:
        print(f"对象存储上传失败: {e}")
        # 如果上传失败，返回本地路径作为fallback
        return PDFExporterOutput(
            pdf_url=pdf_path,
            pdf_path=pdf_path
        )
