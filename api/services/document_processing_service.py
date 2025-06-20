from docling.document_converter import DocumentConverter
from pathlib import Path
from typing import Optional, Tuple
import os
import uuid
import logging
from docling_core.types.doc import ImageRefMode

from api.core.config import settings

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocumentToHTMLConverter:
    """使用 Docling 将文档（PPT、PDF、DOC 等）转换为 HTML"""
    def __init__(self):
        self.converter = DocumentConverter()
        self.supported_formats = [
            '.pdf', '.docx', '.doc', '.pptx', '.ppt',
            '.html', '.htm', '.png', '.jpg', '.jpeg'
        ]
        # 使用环境变量PROCESSED_DIR或默认值
        self.processed_dir = Path(os.getenv("PROCESSED_DIR", "./storage/processed"))
        # 确保处理目录存在
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"初始化DocumentToHTMLConverter，处理目录: {self.processed_dir}")

    def convert_file(self, file_path: str, output_dir: Optional[str] = None) -> Tuple[str, str]:
        """
        将单个文件转换为 HTML，并保留图片资源
        
        Args:
            file_path: 输入文件路径
            output_dir: 可选的输出目录
            
        Returns:
            Tuple[str, str]: (HTML文件路径, 资源目录路径)
        """
        input_path = Path(file_path)
        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {file_path}")
        
        if output_dir is None:
            output_dir = self.processed_dir
        else:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
        
        # 为当前文档创建唯一的资源子目录（使用UUID避免重名）
        doc_id = f"{uuid.uuid4().hex}_{input_path.stem}"
        doc_dir = output_dir / doc_id
        resources_dir = doc_dir / "resources"
        resources_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"开始转换文件: {file_path}")
        logger.info(f"输出目录: {doc_dir}")
        logger.info(f"资源目录: {resources_dir}")
        
        # 使用Docling转换文档
        logger.info(f"使用Docling转换文档: {file_path}")
        result = self.converter.convert(input_path)
        
        # 记录文档中的图片数量
        logger.info(f"文档中包含 {len(result.document.pictures)} 张图片")
        
        # 使用Docling的save_as_html方法保存HTML，并指定图片模式和资源目录
        output_file = doc_dir / f"{input_path.stem}.html"
        logger.info(f"使用Docling的save_as_html方法保存HTML，图片模式为REFERENCED")
        result.document.save_as_html(
            filename=output_file,
            artifacts_dir=resources_dir,
            image_mode=ImageRefMode.REFERENCED
        )
        
        logger.info(f"HTML文件保存到: {output_file}")
        return str(output_file), str(resources_dir)

    def is_supported_format(self, file_path: str) -> bool:
        """判断文件格式是否支持"""
        file_extension = Path(file_path).suffix.lower()
        return file_extension in self.supported_formats

# 实例化供 API 层调用
document_processing_service = DocumentToHTMLConverter()

# 测试函数
def test_document_conversion(file_path: str):
    """
    测试文档转换功能
    
    Args:
        file_path: 要转换的文档路径
    """
    try:
        converter = DocumentToHTMLConverter()
        html_file, resources_dir = converter.convert_file(file_path)
        
        print(f"文档转换成功!")
        print(f"HTML文件: {html_file}")
        print(f"资源目录: {resources_dir}")
        
        # 检查HTML文件是否存在
        if os.path.exists(html_file):
            print(f"HTML文件大小: {os.path.getsize(html_file)} 字节")
            
            # 统计资源目录中的图片数量
            resources_path = Path(resources_dir)
            if resources_path.exists():
                image_files = list(resources_path.glob('*.*'))
                print(f"提取的图片数量: {len(image_files)}")
                for img_file in image_files[:5]:  # 只显示前5个
                    print(f"  - {img_file.name} ({os.path.getsize(img_file)} 字节)")
                if len(image_files) > 5:
                    print(f"  ... 以及其他 {len(image_files) - 5} 个文件")
        
        return html_file, resources_dir
    except Exception as e:
        print(f"测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return None, None

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        test_document_conversion(sys.argv[1])
    else:
        print("请提供要转换的文档路径")
        print("用法: python -m api.services.document_processing_service <文档路径>") 