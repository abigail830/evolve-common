#!/usr/bin/env python3
"""
测试Docling转换功能的脚本
"""

from api.services.document_processing_service import DocumentToHTMLConverter
import os
import sys
from pathlib import Path
import argparse
import shutil

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="测试Docling PDF转HTML功能")
    parser.add_argument("input_file", help="要转换的PDF文件路径")
    parser.add_argument("--output-dir", help="输出目录", default="./test_output")
    
    args = parser.parse_args()
    input_file = args.input_file
    output_dir = args.output_dir
    
    # 确保输出目录存在
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    converter = DocumentToHTMLConverter()
    
    try:
        print(f"开始转换文件: {input_file}")
        html_path, resources_path = converter.convert_file(input_file, output_dir)
        print(f"转换成功！")
        print(f"HTML文件路径: {html_path}")
        print(f"资源目录路径: {resources_path}")
        
        # 尝试打开HTML文件查看结果
        if os.name == 'posix':  # Linux/Mac
            os.system(f"open {html_path}")
        elif os.name == 'nt':  # Windows
            os.system(f"start {html_path}")
        
    except Exception as e:
        print(f"转换过程中出现错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 