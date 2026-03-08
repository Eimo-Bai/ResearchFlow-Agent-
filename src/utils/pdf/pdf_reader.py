"""
PDF读取和解析工具
用于从URL或本地路径读取PDF文件并提取文本内容
"""
import os
import requests
import tempfile
from typing import Optional
from pypdf import PdfReader
from utils.file.file import FileOps


class PDFReader:
    """PDF读取器类"""
    
    def __init__(self):
        self.temp_dir = "/tmp/pdf_cache"
        os.makedirs(self.temp_dir, exist_ok=True)
    
    def read_pdf_from_url(self, url: str, max_pages: int = 10) -> str:
        """
        从URL读取PDF文件并提取文本
        
        Args:
            url: PDF文件的URL
            max_pages: 最多读取的页数（默认10页）
        
        Returns:
            提取的文本内容
        """
        try:
            # 下载PDF文件
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            # 保存到临时文件
            with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.pdf', dir=self.temp_dir) as f:
                f.write(response.content)
                temp_path = f.name
            
            # 读取PDF内容
            text = self.read_pdf_from_file(temp_path, max_pages)
            
            # 删除临时文件
            try:
                os.unlink(temp_path)
            except:
                pass
            
            return text
            
        except Exception as e:
            return f"Error reading PDF from URL: {str(e)}"
    
    def read_pdf_from_file(self, file_path: str, max_pages: int = 10) -> str:
        """
        从本地文件读取PDF并提取文本
        
        Args:
            file_path: PDF文件路径
            max_pages: 最多读取的页数（默认10页）
        
        Returns:
            提取的文本内容
        """
        try:
            reader = PdfReader(file_path)
            num_pages = len(reader.pages)
            
            # 限制读取的页数
            pages_to_read = min(num_pages, max_pages)
            
            text_parts = []
            for i in range(pages_to_read):
                page = reader.pages[i]
                text_parts.append(page.extract_text())
            
            return "\n\n".join(text_parts)
            
        except Exception as e:
            return f"Error reading PDF file: {str(e)}"
    
    def extract_arxiv_pdf_url(self, arxiv_url: str) -> Optional[str]:
        """
        从arXiv URL提取PDF下载链接
        
        Args:
            arxiv_url: arXiv论文URL（如 https://arxiv.org/abs/2301.12345）
        
        Returns:
            PDF下载URL
        """
        # 将abs替换为pdf
        pdf_url = arxiv_url.replace("/abs/", "/pdf/")
        
        # 添加.pdf后缀（如果还没有）
        if not pdf_url.endswith(".pdf"):
            pdf_url += ".pdf"
        
        return pdf_url
    
    def read_arxiv_paper(self, arxiv_url: str, max_pages: int = 10) -> str:
        """
        读取arXiv论文的PDF内容
        
        Args:
            arxiv_url: arXiv论文URL
            max_pages: 最多读取的页数
        
        Returns:
            提取的文本内容
        """
        try:
            # 提取PDF URL
            pdf_url = self.extract_arxiv_pdf_url(arxiv_url)
            
            # 读取PDF
            return self.read_pdf_from_url(pdf_url, max_pages)
            
        except Exception as e:
            return f"Error reading arXiv paper: {str(e)}"


# 全局实例
pdf_reader = PDFReader()


def extract_pdf_content(url: str, max_pages: int = 10) -> str:
    """
    从URL提取PDF内容的便捷函数
    
    Args:
        url: PDF文件URL
        max_pages: 最多读取的页数
    
    Returns:
        提取的文本内容
    """
    # 检查是否是arXiv URL
    if "arxiv.org" in url:
        return pdf_reader.read_arxiv_paper(url, max_pages)
    else:
        return pdf_reader.read_pdf_from_url(url, max_pages)
