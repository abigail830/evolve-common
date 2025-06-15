#!/usr/bin/env python3
"""
PDF转HTML并保存图片的测试脚本
"""

import sys
import os
import argparse
import logging
from pathlib import Path
from api.services.document_processing_service import DocumentToHTMLConverter

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="测试PDF转HTML并保存图片")
    parser.add_argument("input_file", help="要转换的PDF文件路径")
    parser.add_argument("--output-dir", default="./test_output", help="输出目录")
    
    args = parser.parse_args()
    input_file = args.input_file
    output_dir = args.output_dir
    
    # 确保输入文件存在
    if not os.path.exists(input_file):
        logger.error(f"输入文件不存在: {input_file}")
        return 1
    
    # 确保输出目录存在
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    converter = DocumentToHTMLConverter()
    
    try:
        logger.info(f"开始转换文件: {input_file}")
        html_path, resources_path = converter.convert_file(input_file, output_dir)
        logger.info(f"转换成功！")
        logger.info(f"HTML文件路径: {html_path}")
        logger.info(f"资源目录路径: {resources_path}")
        
        # 检查资源目录内容
        resources_dir = Path(resources_path)
        if resources_dir.exists():
            files = list(resources_dir.glob("*"))
            logger.info(f"资源目录包含 {len(files)} 个文件:")
            for f in files:
                logger.info(f"  - {f.name} ({f.stat().st_size} 字节)")
        else:
            logger.warning(f"资源目录不存在: {resources_path}")
        
        # 尝试打开HTML文件查看结果
        if os.name == 'posix':  # Linux/Mac
            os.system(f"open {html_path}")
        elif os.name == 'nt':  # Windows
            os.system(f"start {html_path}")
        
    except Exception as e:
        logger.error(f"转换过程中出现错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 