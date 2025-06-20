"""
文档结构化处理服务
负责HTML文档的解析、树形结构构建和节点存储
"""
from typing import List, Dict, Any, Tuple, Optional
import os
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session

from api.models.document_node import DocumentNode, NodeType
from api.schemas.document_node import DocumentNodeCreate
from api.models.processed_document import ProcessedDocument


class DocumentStructureService:
    """文档结构化服务，负责HTML文档的解析和树形结构构建"""
    
    def process_html_document(self, db: Session, processed_document_id: int) -> List[DocumentNode]:
        """
        处理HTML文档，提取结构并保存到数据库
        
        Args:
            db: 数据库会话
            processed_document_id: 已处理文档ID
            
        Returns:
            List[DocumentNode]: 创建的文档节点列表
        """
        # 1. 获取处理过的HTML文档
        processed_doc = db.query(ProcessedDocument).filter(
            ProcessedDocument.id == processed_document_id
        ).first()
        
        if not processed_doc:
            raise ValueError(f"未找到ID为{processed_document_id}的文档")
        
        if not processed_doc.file_path.endswith('.html'):
            raise ValueError(f"文档格式不是HTML：{processed_doc.file_path}")
            
        # 2. 读取HTML文件内容
        try:
            with open(processed_doc.file_path, 'r', encoding='utf-8') as file:
                html_content = file.read()
        except Exception as e:
            raise IOError(f"读取HTML文件失败: {str(e)}")
            
        # 3. 解析HTML并构建树形结构
        nodes_data = self._parse_html_to_nodes(html_content)
        
        # 4. 存储节点到数据库
        return self._save_nodes_to_db(db, processed_document_id, nodes_data)
    
    def _parse_html_to_nodes(self, html_content: str) -> List[Dict[str, Any]]:
        """
        解析HTML内容，提取节点信息，并按照标题层级构建树结构
        
        Args:
            html_content: HTML文档内容
            
        Returns:
            List[Dict]: 节点数据列表
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        temp_nodes = []  # 临时存储所有节点
        
        # 获取body内容
        body = soup.body or soup
        
        # 第一步：提取所有元素并放入临时列表
        position = 0
        
        # 标题层级栈，用于跟踪当前在处理哪一级标题下的内容
        # 栈中每个元素格式为 [标题级别(1-6), 节点ID]
        header_stack = []
        
        # 扁平方式遍历所有元素
        for element in body.descendants:
            if not hasattr(element, 'name') or element.name is None:
                continue
                
            # 忽略script和style标签
            if element.name in ('script', 'style'):
                continue
                
            # 处理标题元素
            if element.name in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
                header_level = int(element.name[1])  # 提取数字得到标题级别
                
                # 计算父节点 - 查找栈中小于当前标题级别的最近一个标题
                parent_id = None
                while header_stack and header_stack[-1][0] >= header_level:
                    header_stack.pop()  # 移除更高级别或同级的标题
                    
                if header_stack:
                    parent_id = header_stack[-1][1]
                    
                # 创建标题节点
                node_data = {
                    'temp_id': len(temp_nodes),
                    'parent_id': parent_id,
                    'node_type': NodeType.HEADER,
                    'content': element.get_text(strip=True),
                    'node_metadata': {'level': header_level},
                    'position': position,
                    'depth': len(header_stack)  # 深度取决于栈的深度
                }
                temp_nodes.append(node_data)
                position += 1
                
                # 将当前标题压入栈
                header_stack.append([header_level, node_data['temp_id']])
                
            # 处理表格元素
            elif element.name == 'table' and element.parent.name not in ('table', 'td', 'th'):
                # 只处理"整个"表格，忽略嵌套在表格单元格内的表格
                table_html = str(element)
                rows = len(element.find_all('tr', recursive=False))
                cols = 0
                if element.find('tr'):
                    cols = len(element.find('tr').find_all(['td', 'th'], recursive=False))
                    
                # 获取父节点ID - 当前活动的标题
                parent_id = None
                if header_stack:
                    parent_id = header_stack[-1][1]
                    
                node_data = {
                    'temp_id': len(temp_nodes),
                    'parent_id': parent_id,
                    'node_type': NodeType.TABLE,
                    'content': table_html,
                    'node_metadata': {'rows': rows, 'cols': cols},
                    'position': position,
                    'depth': len(header_stack) # 深度取决于栈的深度
                }
                temp_nodes.append(node_data)
                position += 1
                
            # 处理图片元素
            elif element.name == 'img' and element.parent.name not in ('table', 'td', 'th'):
                # 忽略表格内的图片
                img_src = element.get('src', '')
                img_alt = element.get('alt', '')
                
                # 获取父节点ID - 当前活动的标题
                parent_id = None
                if header_stack:
                    parent_id = header_stack[-1][1]
                    
                node_data = {
                    'temp_id': len(temp_nodes),
                    'parent_id': parent_id,
                    'node_type': NodeType.IMAGE,
                    'content': str(element),
                    'node_metadata': {'src': img_src, 'alt': img_alt},
                    'position': position,
                    'depth': len(header_stack)
                }
                temp_nodes.append(node_data)
                position += 1
                
            # 处理文本块元素
            elif (element.name in ('p', 'div', 'ul', 'ol', 'pre', 'blockquote') and
                  element.parent.name not in ('table', 'td', 'th', 'li') and
                  not any(parent.name in ('table', 'td', 'th') for parent in element.parents if hasattr(parent, 'name'))):
                # 忽略表格内的文本块和嵌套在列表项内的块
                
                # 如果元素内包含标题、表格或图片，则跳过，这些会单独处理
                if (element.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'table', 'img'], recursive=True) or
                    not element.get_text(strip=True)):
                    continue
                    
                # 获取父节点ID - 当前活动的标题
                parent_id = None
                if header_stack:
                    parent_id = header_stack[-1][1]
                    
                content_to_store = str(element)
                
                node_data = {
                    'temp_id': len(temp_nodes),
                    'parent_id': parent_id,
                    'node_type': NodeType.TEXT,
                    'content': content_to_store,
                    'node_metadata': {'tag': element.name},
                    'position': position,
                    'depth': len(header_stack)
                }
                temp_nodes.append(node_data)
                position += 1
        
        # 第二步：合并同一标题下的连续文本节点
        merged_nodes = self._merge_consecutive_text_nodes(temp_nodes)
        
        return merged_nodes
    
    def _merge_consecutive_text_nodes(self, nodes: List[Dict]) -> List[Dict]:
        """
        合并拥有相同父节点的连续text节点
        
        Args:
            nodes: 节点列表
            
        Returns:
            List[Dict]: 合并后的节点列表
        """
        if not nodes:
            return []
            
        result = []
        current_parent = None
        text_buffer = []
        text_metadata = {}
        text_position = 0
        text_depth = 0
        
        for node in nodes:
            # 如果是新的parent或非TEXT类型节点，处理之前收集的text
            if (node['parent_id'] != current_parent and text_buffer) or node['node_type'] != NodeType.TEXT:
                # 添加之前收集的文本（如果有）
                if text_buffer:
                    merged_content = '<div class="merged-text">\n' + '\n'.join(text_buffer) + '\n</div>'
                    
                    text_node = {
                        'temp_id': len(result),
                        'parent_id': current_parent,
                        'node_type': NodeType.TEXT,
                        'content': merged_content,
                        'node_metadata': {'merged': True, 'count': len(text_buffer), **text_metadata},
                        'position': text_position,
                        'depth': text_depth
                    }
                    result.append(text_node)
                    text_buffer = []
                    text_metadata = {}
            
            # 处理当前节点
            if node['node_type'] == NodeType.TEXT:
                # 如果是第一个text节点或有新parent
                if not text_buffer or node['parent_id'] != current_parent:
                    current_parent = node['parent_id']
                    text_position = node['position']
                    text_depth = node['depth']
                    if not text_buffer:  # 保存第一个文本节点的元数据
                        text_metadata = node.get('node_metadata', {})
                
                # 将文本内容添加到缓冲区
                text_buffer.append(node['content'])
            else:
                # 非TEXT类型节点直接添加，并更新temp_id
                updated_node = node.copy()
                updated_node['temp_id'] = len(result)
                result.append(updated_node)
        
        # 处理最后剩余的text缓冲区
        if text_buffer:
            merged_content = '<div class="merged-text">\n' + '\n'.join(text_buffer) + '\n</div>'
            text_node = {
                'temp_id': len(result),
                'parent_id': current_parent,
                'node_type': NodeType.TEXT,
                'content': merged_content,
                'node_metadata': {'merged': True, 'count': len(text_buffer), **text_metadata},
                'position': text_position,
                'depth': text_depth
            }
            result.append(text_node)
            
        # 更新所有节点的parent_id引用
        id_mapping = {}
        for old_idx, old_node in enumerate(nodes):
            for new_idx, new_node in enumerate(result):
                # 非TEXT节点通过位置和类型匹配
                if old_node['node_type'] != NodeType.TEXT and new_node['node_type'] == old_node['node_type']:
                    if new_node['position'] == old_node['position']:
                        id_mapping[old_node['temp_id']] = new_node['temp_id']
                        break
        
        # 更新parent_id
        for node in result:
            if node['parent_id'] is not None and node['parent_id'] in id_mapping:
                node['parent_id'] = id_mapping[node['parent_id']]
                    
        return result
    
    def _save_nodes_to_db(self, db: Session, processed_document_id: int, 
                         nodes_data: List[Dict]) -> List[DocumentNode]:
        """
        将节点数据保存到数据库
        
        Args:
            db: 数据库会话
            processed_document_id: 处理文档ID
            nodes_data: 节点数据列表
            
        Returns:
            List[DocumentNode]: 创建的文档节点列表
        """
        # 创建ID映射，将临时ID映射到实际数据库ID
        id_mapping = {}
        db_nodes = []
        
        # 首先创建所有节点，但不设置父子关系
        for node_data in nodes_data:
            temp_id = node_data.pop('temp_id')
            
            # 复制节点数据并添加处理文档ID
            create_data = {**node_data}
            create_data['processed_document_id'] = processed_document_id
            
            # 暂时移除parent_id
            parent_temp_id = create_data.pop('parent_id')
            
            # 创建节点
            db_node = DocumentNode(**create_data)
            db.add(db_node)
            db.flush()  # 获取ID
            
            # 保存ID映射
            id_mapping[temp_id] = db_node.id
            db_nodes.append(db_node)
            
            # 存储原始父ID信息，稍后更新
            db_node._parent_temp_id = parent_temp_id
            
        # 更新父子关系
        for db_node in db_nodes:
            if hasattr(db_node, '_parent_temp_id') and db_node._parent_temp_id is not None:
                db_node.parent_id = id_mapping.get(db_node._parent_temp_id)
                delattr(db_node, '_parent_temp_id')
                
        db.commit()
        return db_nodes
    
    def get_document_structure(self, db: Session, processed_document_id: int) -> List[Dict]:
        """
        获取文档的树形结构
        
        Args:
            db: 数据库会话
            processed_document_id: 处理文档ID
            
        Returns:
            List[Dict]: 树形结构
        """
        # 获取所有节点
        nodes = db.query(DocumentNode).filter(
            DocumentNode.processed_document_id == processed_document_id
        ).order_by(DocumentNode.depth, DocumentNode.position).all()
        
        # 构建树结构
        return self._build_tree_structure(nodes)
    
    def _build_tree_structure(self, nodes: List[DocumentNode]) -> List[Dict]:
        """
        将扁平节点列表构建为树形结构
        
        Args:
            nodes: 节点列表
            
        Returns:
            List[Dict]: 树形结构
        """
        # 创建节点映射
        node_map = {node.id: {"data": node, "children": []} for node in nodes}
        root = []
        
        # 构建树
        for node_id, node_data in node_map.items():
            node = node_data["data"]
            if node.parent_id is None:
                root.append(node_data)
            elif node.parent_id in node_map:
                node_map[node.parent_id]["children"].append(node_data)
        
        return root
    
    def get_header_subtree(self, db: Session, node_id: int) -> List[DocumentNode]:
        """
        获取指定header节点及其所有子节点内容
        
        Args:
            db: 数据库会话
            node_id: 节点ID
            
        Returns:
            List[DocumentNode]: 节点及其子节点
        """
        # 获取目标节点
        target_node = db.query(DocumentNode).filter(DocumentNode.id == node_id).first()
        if not target_node or target_node.node_type != NodeType.HEADER:
            return []
            
        # 获取目标节点的文档ID、深度和位置
        doc_id = target_node.processed_document_id
        target_depth = target_node.depth
        target_pos = target_node.position
        
        # 查找同一文档中的所有后续节点，直到遇到同级或更高级的header
        result = [target_node]
        
        # 获取后续节点
        next_nodes = db.query(DocumentNode).filter(
            DocumentNode.processed_document_id == doc_id,
            DocumentNode.position > target_pos
        ).order_by(DocumentNode.position).all()
        
        # 过滤出属于当前header的节点
        for node in next_nodes:
            # 如果遇到同级或更高级的header，则停止
            if node.node_type == NodeType.HEADER and node.depth <= target_depth:
                break
            result.append(node)
            
        return result
    
    def delete_document_structure(self, db: Session, processed_document_id: int) -> int:
        """
        删除指定处理文档的所有结构化节点
        
        Args:
            db: 数据库会话
            processed_document_id: 处理文档ID
            
        Returns:
            int: 删除的节点数量
        """
        # 查询属于该文档的所有节点
        query = db.query(DocumentNode).filter(
            DocumentNode.processed_document_id == processed_document_id
        )
        
        # 获取节点数量
        count = query.count()
        
        # 删除所有节点
        if count > 0:
            query.delete()
            db.commit()
            
        return count
    
    def get_document_toc(self, db: Session, processed_document_id: int) -> List[Dict]:
        """
        获取文档的目录结构（只包含标题节点）
        
        Args:
            db: 数据库会话
            processed_document_id: 处理文档ID
            
        Returns:
            List[Dict]: 仅包含标题节点的树形结构
        """
        # 获取所有标题节点
        header_nodes = db.query(DocumentNode).filter(
            DocumentNode.processed_document_id == processed_document_id,
            DocumentNode.node_type == NodeType.HEADER
        ).order_by(DocumentNode.position).all()
        
        # 构建树结构
        return self._build_tree_structure(header_nodes)
        
    def search_headers_by_content(self, db: Session, processed_document_id: int, search_text: str) -> List[DocumentNode]:
        """
        通过内容模糊搜索标题节点
        
        Args:
            db: 数据库会话
            processed_document_id: 处理文档ID
            search_text: 搜索文本
            
        Returns:
            List[DocumentNode]: 匹配的标题节点列表
        """
        # 模糊搜索标题节点
        from sqlalchemy import func
        
        search_pattern = f"%{search_text}%"
        header_nodes = db.query(DocumentNode).filter(
            DocumentNode.processed_document_id == processed_document_id,
            DocumentNode.node_type == NodeType.HEADER,
            DocumentNode.content.ilike(search_pattern)  # 不区分大小写的模糊匹配
        ).all()
        
        return header_nodes
    
    def get_document_toc_simplified(self, db: Session, processed_document_id: int) -> List[Dict]:
        """
        获取文档的简化目录结构（只包含标题节点的简化版本）
        
        Args:
            db: 数据库会话
            processed_document_id: 处理文档ID
            
        Returns:
            List[Dict]: 仅包含标题节点简化信息的树形结构
        """
        # 获取所有标题节点
        header_nodes = db.query(DocumentNode).filter(
            DocumentNode.processed_document_id == processed_document_id,
            DocumentNode.node_type == NodeType.HEADER
        ).order_by(DocumentNode.position).all()
        
        # 构建简化的树结构
        return self._build_simplified_tree_structure(header_nodes)
        
    def _build_simplified_tree_structure(self, nodes: List[DocumentNode]) -> List[Dict]:
        """
        构建简化的树形结构，只保留id、content、node_metadata和父子关系
        
        Args:
            nodes: 节点列表
            
        Returns:
            List[Dict]: 简化的树形结构
        """
        if not nodes:
            return []
            
        # 创建简化的节点映射 - 只保留必要字段
        node_map = {}
        for node in nodes:
            node_map[node.id] = {
                "data": {
                    "id": node.id,
                    "content": node.content,
                    "parent_id": node.parent_id,
                    "node_metadata": node.node_metadata
                },
                "children": []
            }
        
        # 构建树结构
        root = []
        for node_id, node_data in node_map.items():
            parent_id = node_data["data"]["parent_id"]
            if parent_id is None:
                root.append(node_data)
            elif parent_id in node_map:
                node_map[parent_id]["children"].append(node_data)
        
        return root


# 实例化服务
document_structure_service = DocumentStructureService() 