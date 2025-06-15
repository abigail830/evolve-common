#!/usr/bin/env python
"""
文档转换测试脚本

用法:
    python test_document_conversion.py <文档路径>
"""

import os
import sys
from pathlib import Path
from api.services.document_processing_service import test_document_conversion

def main():
    if len(sys.argv) < 2:
        print("请提供要转换的文档路径")
        print("用法: python test_document_conversion.py <文档路径>")
        return 1
    
    file_path = sys.argv[1]
    if not os.path.exists(file_path):
        print(f"错误: 文件 '{file_path}' 不存在")
        return 1
    
    print(f"开始转换文档: {file_path}")
    html_file, resources_dir = test_document_conversion(file_path)
    
    if html_file and resources_dir:
        print("\n转换成功! 您可以在浏览器中打开HTML文件查看结果")
        return 0
    else:
        print("\n转换失败，请检查错误信息")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 