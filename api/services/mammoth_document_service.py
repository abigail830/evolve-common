import os
import uuid
import logging
import mammoth
import base64
import re
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from bs4 import BeautifulSoup

from api.core.config import settings

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocxToHTMLConverter:
    """使用 Mammoth 将 DOCX 文档转换为 HTML，并提取图片"""
    
    def __init__(self):
        self.processed_dir = Path(settings.PROCESSED_DIR)
        # 确保处理目录存在
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"初始化DocxToHTMLConverter，处理目录: {self.processed_dir}")
    
    def convert_file(self, file_path: str, output_dir: Optional[str] = None) -> Tuple[str, str]:
        """
        将DOCX文件转换为HTML，并提取图片资源
        
        Args:
            file_path: 输入文件路径
            output_dir: 可选的输出目录
            
        Returns:
            Tuple[str, str]: (HTML文件路径, 资源目录路径)
        """
        input_path = Path(file_path)
        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {file_path}")
        
        # 检查文件格式
        if input_path.suffix.lower() != '.docx':
            raise ValueError(f"Unsupported file format: {input_path.suffix}. Only .docx is supported.")
        
        if output_dir is None:
            output_dir = self.processed_dir
        else:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
        
        # 为当前文档创建唯一的资源子目录
        doc_id = f"{uuid.uuid4().hex}_{input_path.stem}"
        doc_dir = output_dir / doc_id
        resources_dir = doc_dir / "resources"
        resources_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"开始转换文件: {file_path}")
        logger.info(f"输出目录: {doc_dir}")
        logger.info(f"资源目录: {resources_dir}")
        
        # 转换文档为HTML
        with open(input_path, 'rb') as docx_file:
            # 使用Mammoth转换文档
            result = mammoth.convert_to_html(docx_file)
            html_content = result.value
            messages = result.messages
            
            for message in messages:
                if message.type == "warning":
                    logger.warning(f"Mammoth警告: {message.message}")
        
        # 使用BeautifulSoup解析HTML
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 添加基本HTML结构
        if not soup.html:
            html = BeautifulSoup('<!DOCTYPE html><html><head><meta charset="utf-8"></head><body></body></html>', 'html.parser')
            html.body.append(soup)
            soup = html
        
        # 添加样式
        if not soup.head.find('style'):
            style_tag = soup.new_tag('style')
            style_tag.string = """
                body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 20px; }
                img { max-width: 100%; height: auto; }
                .image-container { text-align: center; margin: 15px 0; }
            """
            soup.head.append(style_tag)
        
        # 提取并处理base64编码的图片
        self._extract_base64_images(soup, resources_dir)
        
        # 保存HTML文件
        output_file = doc_dir / f"{input_path.stem}.html"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(str(soup))
        
        logger.info(f"HTML文件保存到: {output_file}")
        return str(output_file), str(resources_dir)
    
    def _extract_base64_images(self, soup: BeautifulSoup, resources_dir: Path):
        """
        从HTML中提取base64编码的图片，并将其保存为文件
        
        Args:
            soup: BeautifulSoup对象
            resources_dir: 资源保存目录
        """
        # 查找所有图片标签
        img_tags = soup.find_all('img')
        logger.info(f"在HTML中找到 {len(img_tags)} 个img标签")
        
        # 用于保存处理过的图片计数
        image_counter = 0
        
        # 处理每个img标签
        for img_tag in img_tags:
            src = img_tag.get('src', '')
            
            # 检查是否为base64编码的图片
            if src.startswith('data:image/'):
                base64_pattern = re.compile(r'^data:image/(\w+);base64,(.+)$')
                match = base64_pattern.match(src)
                
                if match:
                    try:
                        # 提取mime类型和base64内容
                        img_type, base64_data = match.groups()
                        
                        # 确定文件扩展名
                        extension = self._get_extension_from_mime(img_type)
                        
                        # 创建唯一的文件名
                        image_counter += 1
                        img_filename = f"image_{image_counter}{extension}"
                        output_path = resources_dir / img_filename
                        
                        # 解码base64并保存为文件
                        img_data = base64.b64decode(base64_data)
                        with open(output_path, 'wb') as f:
                            f.write(img_data)
                        
                        # 更新img标签的src属性
                        img_tag['src'] = f"resources/{img_filename}"
                        logger.info(f"提取图片 {image_counter}: base64 -> {output_path}")
                    except Exception as e:
                        logger.error(f"处理base64图片时出错: {str(e)}")
            elif src.startswith('word/media/'):
                # 对于Mammoth可能生成的word/media路径引用，进行替换
                logger.warning(f"发现未处理的图片路径引用: {src}，已忽略")
    
    def _get_extension_from_mime(self, mime_subtype: str) -> str:
        """根据MIME子类型获取文件扩展名"""
        mime_map = {
            'png': '.png',
            'jpeg': '.jpg',
            'jpg': '.jpg',
            'gif': '.gif',
            'bmp': '.bmp',
            'tiff': '.tiff',
            'svg+xml': '.svg',
            'webp': '.webp'
        }
        return mime_map.get(mime_subtype.lower(), '.png')  # 默认使用.png
    
    def convert_batch(self, file_paths: List[str], output_dir: Optional[str] = None) -> List[Tuple[str, str]]:
        """
        批量转换多个DOCX文件为HTML
        
        Returns:
            List[Tuple[str, str]]: 每个文件的(HTML文件路径, 资源目录路径)列表
        """
        results = []
        for file_path in file_paths:
            try:
                html_file, resources_dir = self.convert_file(file_path, output_dir)
                results.append((html_file, resources_dir))
                logger.info(f"转换完成: {file_path} -> {html_file} (resources: {resources_dir})")
            except Exception as e:
                logger.error(f"转换 {file_path} 时出错: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())
                continue
        return results

# 实例化供API层调用
docx_to_html_converter = DocxToHTMLConverter() 