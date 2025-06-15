"""
测试文档处理服务的单元测试
"""
import os
import unittest
import tempfile
from pathlib import Path

from api.services.document_processing_service import DocumentToHTMLConverter


class TestDocumentProcessing(unittest.TestCase):
    """测试文档处理服务"""

    def setUp(self):
        """测试前准备工作"""
        self.converter = DocumentToHTMLConverter()
        self.temp_dir = tempfile.mkdtemp()
        # 使用一个简单的测试PDF文件，可以根据实际情况修改路径
        # self.test_pdf_path = Path(__file__).parent / "fixtures" / "sample.pdf"

    def tearDown(self):
        """测试后清理工作"""
        # 可以选择清理临时目录
        # import shutil
        # shutil.rmtree(self.temp_dir)
        pass

    def test_convert_file_with_sample_pdf(self):
        """测试使用样本PDF文件进行转换"""
        # 需要有一个样本PDF文件才能运行此测试
        # 如果没有，可以跳过此测试
        test_pdf_path = Path(__file__).parent / "fixtures" / "sample.pdf"
        if not test_pdf_path.exists():
            self.skipTest(f"样本PDF文件不存在: {test_pdf_path}")

        html_path, resources_path = self.converter.convert_file(
            str(test_pdf_path), self.temp_dir
        )
        
        # 验证转换结果
        self.assertTrue(Path(html_path).exists(), "HTML文件应该存在")
        self.assertTrue(Path(resources_path).exists(), "资源目录应该存在")
        
        # 验证HTML内容包含正确的资源引用
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
            if Path(resources_path).glob("*.png") or Path(resources_path).glob("*.jpg"):
                # 如果有图片资源，应该在HTML中有对应引用
                self.assertTrue(
                    "resources/" in html_content, 
                    "HTML内容应该包含对资源的引用"
                )

    def test_supported_formats(self):
        """测试支持的文件格式检测功能"""
        supported_files = [
            "document.pdf",
            "presentation.pptx",
            "spreadsheet.xlsx",
            "document.docx",
            "webpage.html",
        ]
        
        unsupported_files = [
            "data.csv",
            "script.py",
            "config.json",
        ]
        
        for file in supported_files:
            self.assertTrue(
                self.converter.is_supported_format(file),
                f"应该支持格式: {file}"
            )
            
        for file in unsupported_files:
            self.assertFalse(
                self.converter.is_supported_format(file),
                f"不应该支持格式: {file}"
            )

    def test_convert_file_missing_file(self):
        """测试转换不存在的文件时的错误处理"""
        with self.assertRaises(FileNotFoundError):
            self.converter.convert_file("non_existent_file.pdf")


if __name__ == "__main__":
    unittest.main() 