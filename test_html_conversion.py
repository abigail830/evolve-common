#!/usr/bin/env python3
"""
HTML转换和图片提取测试脚本
"""

import sys
import os
from pathlib import Path
import argparse
import base64
import logging
from api.services.document_processing_service import DocumentToHTMLConverter

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_test_html_with_images(output_path):
    """创建一个包含base64编码图片的HTML测试文件"""
    # 创建一个简单的1x1像素的透明PNG
    transparent_pixel = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
    
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>测试HTML文件</title>
</head>
<body>
    <h1>HTML转换测试</h1>
    <p>这是一个测试段落，包含一个base64编码的图片：</p>
    <img src="data:image/png;base64,{transparent_pixel}" alt="测试图片1">
    <p>另一个测试段落，带有另一个图片：</p>
    <img src="data:image/png;base64,{transparent_pixel}" alt="测试图片2">
</body>
</html>
"""
    
    # 保存HTML文件
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    logger.info(f"测试HTML文件已创建: {output_path}")
    return output_path

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="测试HTML转换和图片提取")
    parser.add_argument("--input-file", help="要转换的PDF/HTML文件路径")
    parser.add_argument("--create-test-html", action="store_true", help="创建测试HTML文件")
    parser.add_argument("--output-dir", default="./test_output", help="输出目录")
    
    args = parser.parse_args()
    input_file = args.input_file
    output_dir = args.output_dir
    
    # 确保输出目录存在
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # 如果请求创建测试HTML文件
    if args.create_test_html:
        test_html_path = os.path.join(output_dir, "test_with_images.html")
        input_file = create_test_html_with_images(test_html_path)
    
    if not input_file:
        logger.error("请提供输入文件路径或使用--create-test-html选项")
        return 1
    
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