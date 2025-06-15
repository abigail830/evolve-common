from docling.document_converter import DocumentConverter
from pathlib import Path
from typing import Optional, List, Tuple, Dict
import os
import shutil
import re
import uuid
import logging
import base64
import hashlib
from bs4 import BeautifulSoup
import json

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
        
        # 提取文档中的图片
        logger.info("提取文档中的图片")
        image_map = self._extract_images_from_docling(result.document, resources_dir)
        
        # 使用Docling导出HTML
        logger.info("使用Docling导出HTML内容")
        html_content = result.document.export_to_html()
        
        # 使用BeautifulSoup解析HTML，处理图片引用
        logger.info("处理HTML中的图片引用")
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 处理HTML中的图片引用
        img_tags = soup.find_all('img')
        logger.info(f"在HTML中找到 {len(img_tags)} 个img标签")
        
        # 记录已处理的图片路径
        processed_img_paths = set()
        
        for img_tag in img_tags:
            src = img_tag.get('src', '')
            
            # 处理base64编码的图像
            if src.startswith('data:image/'):
                try:
                    # 解析base64图像
                    img_format = src.split(';')[0].split('/')[1]
                    img_data = src.split(',', 1)[1]
                    
                    # 生成唯一文件名
                    img_hash = hashlib.md5(img_data.encode()).hexdigest()[:12]
                    img_filename = f"embedded_{img_hash}.{img_format}"
                    img_path = resources_dir / img_filename
                    
                    # 保存图像
                    with open(img_path, 'wb') as f:
                        f.write(base64.b64decode(img_data))
                    
                    # 修改img标签的src属性
                    img_tag['src'] = f"resources/{img_filename}"
                    processed_img_paths.add(f"resources/{img_filename}")
                    logger.info(f"处理base64图像: {img_path}")
                    
                except Exception as e:
                    logger.error(f"处理嵌入图像时出错: {str(e)}")
        
        # 过滤出未在HTML中引用的图片
        images_to_insert = [img for img in image_map if img['path'] not in processed_img_paths]
        
        # 如果有未引用的图片，将它们添加到HTML中
        if images_to_insert:
            logger.info(f"有 {len(images_to_insert)} 张图片未在HTML中引用，将添加这些图片")
            self._insert_images_into_html(soup, images_to_insert)
        
        # 获取修改后的HTML内容
        html_content = str(soup)
        
        # 保存HTML文件
        output_file = doc_dir / f"{input_path.stem}.html"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"HTML文件保存到: {output_file}")
        return str(output_file), str(resources_dir)
    
    def _extract_images_from_docling(self, document, resources_dir: Path) -> List[Dict]:
        """
        从Docling文档对象中提取图片
        
        Args:
            document: Docling文档对象
            resources_dir: 资源保存目录
            
        Returns:
            List[Dict]: 图片信息列表
        """
        image_map = []
        
        # 提取文档中的图片
        logger.info("从Docling文档中提取图片")
        
        # 1. 从pictures集合中提取
        if hasattr(document, "pictures"):
            for idx, picture in enumerate(document.pictures):
                try:
                    if hasattr(picture, "image") and picture.image and hasattr(picture.image, "data") and picture.image.data:
                        # 为图像创建唯一文件名
                        image_id = f"picture_{idx+1}"
                        img_filename = f"{image_id}.png"  # 默认使用PNG格式
                        img_path = resources_dir / img_filename
                        
                        # 保存图像数据
                        with open(img_path, 'wb') as f:
                            f.write(picture.image.data)
                        
                        # 记录图片信息
                        image_info = {
                            "id": image_id,
                            "path": f"resources/{img_filename}",
                            "type": "picture",
                            "alt": getattr(picture, "alt_text", f"图片 {idx+1}"),
                            "position": self._get_item_position(picture)
                        }
                        image_map.append(image_info)
                        logger.info(f"从pictures集合中提取图片: {img_path}")
                except Exception as e:
                    logger.error(f"处理picture对象时出错: {str(e)}")
        
        # 2. 从页面中提取图片
        if hasattr(document, "pages"):
            for page_idx, page in enumerate(document.pages):
                if hasattr(page, "items"):
                    for item_idx, item in enumerate(page.items):
                        try:
                            # 检查是否有图像数据
                            if hasattr(item, "image") and item.image:
                                if hasattr(item.image, "data") and item.image.data:
                                    # 为图像创建唯一文件名
                                    image_id = f"image_p{page_idx+1}_i{item_idx+1}"
                                    img_filename = f"{image_id}.png"
                                    img_path = resources_dir / img_filename
                                    
                                    # 保存图像数据
                                    with open(img_path, 'wb') as f:
                                        f.write(item.image.data)
                                    
                                    # 记录图片信息
                                    image_info = {
                                        "id": image_id,
                                        "path": f"resources/{img_filename}",
                                        "type": "page_item",
                                        "page": page_idx + 1,
                                        "item_index": item_idx,
                                        "alt": f"页面图片 {page_idx+1}-{item_idx+1}",
                                        "position": {
                                            "page": page_idx + 1,
                                            "index": item_idx
                                        }
                                    }
                                    
                                    # 如果有位置信息，记录下来
                                    if hasattr(item, "bbox"):
                                        image_info["position"]["bbox"] = {
                                            "x": getattr(item.bbox, "x", 0),
                                            "y": getattr(item.bbox, "y", 0),
                                            "width": getattr(item.bbox, "width", 0),
                                            "height": getattr(item.bbox, "height", 0)
                                        }
                                    
                                    image_map.append(image_info)
                                    logger.info(f"从页面项中提取图片: {img_path}")
                        except Exception as e:
                            logger.error(f"处理页面项时出错: {str(e)}")
        
        logger.info(f"总共从Docling文档中提取了 {len(image_map)} 张图片")
        return image_map
    
    def _get_item_position(self, item) -> Dict:
        """
        获取文档项的位置信息
        
        Args:
            item: Docling文档项
            
        Returns:
            Dict: 位置信息
        """
        position = {}
        
        # 尝试获取页码
        if hasattr(item, "prov") and item.prov:
            for prov in item.prov:
                if hasattr(prov, "page_no"):
                    position["page"] = prov.page_no
                    break
        
        # 尝试获取边界框
        if hasattr(item, "bbox"):
            position["bbox"] = {
                "x": getattr(item.bbox, "x", 0),
                "y": getattr(item.bbox, "y", 0),
                "width": getattr(item.bbox, "width", 0),
                "height": getattr(item.bbox, "height", 0)
            }
        
        return position
    
    def _find_insertion_position(self, img_info, paragraphs):
        """
        根据图片的y坐标找到合适的插入位置
        
        Args:
            img_info: 图片信息
            paragraphs: 段落列表
            
        Returns:
            int: 插入位置索引
        """
        # 如果有y坐标信息，尝试根据y坐标确定位置
        if "bbox" in img_info.get("position", {}):
            y = img_info["position"]["bbox"].get("y", 0)
            
            # 遍历段落，找到第一个y坐标大于图片y坐标的段落
            # 这表示图片应该插入在这个段落之前
            for i, para in enumerate(paragraphs):
                # 尝试从段落的data-y属性获取y坐标
                para_y = None
                if "data-y" in para.attrs:
                    try:
                        para_y = float(para["data-y"])
                    except (ValueError, TypeError):
                        pass
                
                # 如果段落没有y坐标属性，尝试从style属性中提取
                if para_y is None and "style" in para.attrs:
                    style = para["style"]
                    match = re.search(r'top:\s*(\d+(?:\.\d+)?)px', style)
                    if match:
                        try:
                            para_y = float(match.group(1))
                        except (ValueError, TypeError):
                            pass
                
                # 如果找到段落的y坐标，并且大于图片的y坐标，返回这个位置
                if para_y is not None and para_y > y:
                    return i
        
        # 如果无法根据y坐标确定位置，尝试使用item_index
        if "item_index" in img_info:
            item_index = img_info["item_index"]
            # 尝试将item_index映射到段落索引
            # 由于段落通常比item少，使用比例映射
            if len(paragraphs) > 0:
                # 假设item_index是在页面内的索引
                # 计算相对位置（0到1之间的值）
                relative_pos = item_index / 100.0  # 假设页面有100个item
                # 映射到段落索引
                para_index = int(relative_pos * len(paragraphs))
                return min(para_index, len(paragraphs) - 1)
        
        # 如果以上方法都无法确定位置，返回中间位置
        return len(paragraphs) // 2
    
    def _insert_images_into_html(self, soup, image_map):
        """
        将图片插入到HTML中的原始位置
        
        Args:
            soup: BeautifulSoup对象
            image_map: 图片信息列表
        """
        # 过滤掉已经在HTML中的图片
        existing_img_srcs = [img['src'] for img in soup.find_all('img') if 'src' in img.attrs]
        images_to_insert = [img for img in image_map if img['path'] not in existing_img_srcs]
        
        if not images_to_insert:
            logger.info("没有需要插入的图片")
            return
        
        # 按页面和y坐标排序图片
        # 这确保图片按照在原始文档中的顺序插入
        sorted_images = sorted(
            images_to_insert,
            key=lambda img: (
                img.get("position", {}).get("page", 1),
                img.get("position", {}).get("bbox", {}).get("y", 0),
                img.get("item_index", 0)
            )
        )
        
        # 查找可能的页面分隔符
        page_divs = soup.find_all('div', class_=lambda c: c and ('page' in c.lower()))
        
        if page_divs:
            # 如果找到页面分隔符，按页面插入图片
            logger.info(f"找到 {len(page_divs)} 个页面分隔符，按页面插入图片")
            
            # 按页面分组图片
            images_by_page = {}
            for img_info in sorted_images:
                page = img_info.get("position", {}).get("page", 1)
                if page not in images_by_page:
                    images_by_page[page] = []
                images_by_page[page].append(img_info)
            
            # 处理每个页面
            for page_num, page_images in images_by_page.items():
                # 找到对应的页面容器
                page_idx = min(page_num - 1, len(page_divs) - 1)
                if page_idx >= 0 and page_idx < len(page_divs):
                    page_div = page_divs[page_idx]
                    
                    # 在页面内查找段落和其他元素
                    elements = page_div.find_all(['p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'table'])
                    
                    if elements:
                        # 按y坐标排序图片（从上到下）
                        page_images.sort(
                            key=lambda img: img.get("position", {}).get("bbox", {}).get("y", 0)
                        )
                        
                        # 为每个图片找到合适的插入位置
                        for img_info in page_images:
                            # 根据图片的y坐标找到合适的插入位置
                            insert_pos = self._find_insertion_position(img_info, elements)
                            
                            # 创建图片元素
                            img_tag = soup.new_tag('img')
                            img_tag['src'] = img_info['path']
                            img_tag['alt'] = img_info.get('alt', 'Document Image')
                            img_tag['data-image-id'] = img_info['id']
                            if "bbox" in img_info.get("position", {}):
                                img_tag['data-original-x'] = str(img_info["position"]["bbox"].get("x", 0))
                                img_tag['data-original-y'] = str(img_info["position"]["bbox"].get("y", 0))
                                img_tag['data-original-width'] = str(img_info["position"]["bbox"].get("width", 0))
                                img_tag['data-original-height'] = str(img_info["position"]["bbox"].get("height", 0))
                            
                            # 创建容器
                            container = soup.new_tag('div')
                            container['class'] = 'image-container'
                            container['style'] = 'text-align: center; margin: 10px 0;'
                            container.append(img_tag)
                            
                            # 插入到合适位置
                            if insert_pos < len(elements):
                                elements[insert_pos].insert_before(container)
                                logger.info(f"在页面 {page_num} 的元素 {insert_pos + 1}/{len(elements)} 前插入图片: {img_info['path']}")
                            else:
                                # 如果插入位置超出范围，添加到页面末尾
                                page_div.append(container)
                                logger.info(f"在页面 {page_num} 末尾添加图片: {img_info['path']}")
                    else:
                        # 如果没有元素，直接添加到页面
                        for img_info in page_images:
                            # 创建图片元素
                            img_tag = soup.new_tag('img')
                            img_tag['src'] = img_info['path']
                            img_tag['alt'] = img_info.get('alt', 'Document Image')
                            img_tag['data-image-id'] = img_info['id']
                            
                            # 创建容器
                            container = soup.new_tag('div')
                            container['class'] = 'image-container'
                            container['style'] = 'text-align: center; margin: 10px 0;'
                            container.append(img_tag)
                            
                            # 添加到页面
                            page_div.append(container)
                            logger.info(f"在页面 {page_num} 中添加图片: {img_info['path']}")
        else:
            # 如果没有找到页面分隔符，尝试在段落之间插入图片
            logger.info("未找到页面分隔符，尝试在文档流中插入图片")
            
            # 获取所有文本和结构元素
            elements = soup.find_all(['p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'table', 'ul', 'ol'])
            
            if elements:
                # 为每个图片找到合适的插入位置
                for img_info in sorted_images:
                    # 根据图片的位置信息找到合适的插入位置
                    insert_pos = self._find_insertion_position(img_info, elements)
                    
                    # 创建图片元素
                    img_tag = soup.new_tag('img')
                    img_tag['src'] = img_info['path']
                    img_tag['alt'] = img_info.get('alt', 'Document Image')
                    img_tag['data-image-id'] = img_info['id']
                    
                    # 创建容器
                    container = soup.new_tag('div')
                    container['class'] = 'image-container'
                    container['style'] = 'text-align: center; margin: 10px 0;'
                    container.append(img_tag)
                    
                    # 插入到合适位置
                    if insert_pos < len(elements):
                        elements[insert_pos].insert_before(container)
                        logger.info(f"在元素 {insert_pos + 1}/{len(elements)} 前插入图片: {img_info['path']}")
                    else:
                        # 如果插入位置超出范围，添加到最后一个元素后
                        elements[-1].insert_after(container)
                        logger.info(f"在最后一个元素后插入图片: {img_info['path']}")
            else:
                # 如果没有找到任何元素，添加到body
                logger.warning("未找到任何元素，将图片添加到body")
                self._append_images_to_body(soup, sorted_images)
    
    def _append_images_to_body(self, soup, image_map):
        """
        将图片添加到HTML的body末尾
        
        Args:
            soup: BeautifulSoup对象
            image_map: 图片信息列表
        """
        # 查找body元素
        body = soup.find('body')
        if not body:
            # 如果没有body标签，创建一个
            body = soup.new_tag('body')
            if soup.html:
                soup.html.append(body)
            else:
                html = soup.new_tag('html')
                html.append(body)
                soup.append(html)
        
        # 过滤掉已经在HTML中的图片
        existing_img_srcs = [img['src'] for img in soup.find_all('img') if 'src' in img.attrs]
        images_to_append = [img for img in image_map if img['path'] not in existing_img_srcs]
        
        if not images_to_append:
            logger.info("没有需要添加的图片")
            return
        
        # 创建图片容器
        container = soup.new_tag('div')
        container['class'] = 'document-images'
        container['style'] = 'margin-top: 30px;'
        
        # 添加图片
        for img_info in images_to_append:
            # 创建图片元素
            img_tag = soup.new_tag('img')
            img_tag['src'] = img_info['path']
            img_tag['alt'] = img_info.get('alt', 'Document Image')
            img_tag['data-image-id'] = img_info['id']
            img_tag['style'] = 'max-width: 100%; margin: 10px 0;'
            
            # 创建图片容器
            img_container = soup.new_tag('div')
            img_container['style'] = 'text-align: center; margin: 15px 0;'
            img_container.append(img_tag)
            
            # 添加图片说明
            if 'alt' in img_info:
                caption = soup.new_tag('div')
                caption.string = img_info['alt']
                caption['style'] = 'font-style: italic; color: #666;'
                img_container.append(caption)
            
            # 添加到容器
            container.append(img_container)
        
        # 添加到body
        body.append(container)
        logger.info(f"在HTML body末尾添加了 {len(images_to_append)} 张图片")

    def convert_batch(self, file_paths: List[str], output_dir: Optional[str] = None) -> List[Tuple[str, str]]:
        """
        批量转换多个文件为 HTML
        
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