from datetime import datetime
from typing import Optional, Dict, List, Any, Union
from pydantic import BaseModel, Field
from enum import Enum


class NodeTypeEnum(str, Enum):
    HEADER = "header"
    TABLE = "table"
    IMAGE = "image"
    TEXT = "text"


class DocumentNodeBase(BaseModel):
    processed_document_id: int
    parent_id: Optional[int] = None
    node_type: NodeTypeEnum
    content: Optional[str] = None
    node_metadata: Optional[Dict[str, Any]] = None
    position: int
    depth: int = 0


class DocumentNodeCreate(DocumentNodeBase):
    pass


class DocumentNode(DocumentNodeBase):
    id: int

    class Config:
        from_attributes = True


class DocumentNodeWithChildren(BaseModel):
    """包含节点及其直接子节点的响应模型"""
    node: DocumentNode
    children: List[DocumentNode]


# 递归类型需要先声明
class TreeNode(BaseModel):
    """树形结构的节点表示"""
    data: DocumentNode
    children: List["TreeNode"] = []


# 更新引用，解决循环引用
TreeNode.model_rebuild()


class DocumentStructure(BaseModel):
    """整个文档的树形结构响应模型"""
    id: int
    structure: List[TreeNode]


# 简化的标题节点模型，用于TOC响应
class SimpleTocNode(BaseModel):
    """简化的标题节点模型，只包含必要字段"""
    id: int
    content: str
    parent_id: Optional[int] = None
    node_metadata: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


# 递归类型需要先声明
class TocTreeNode(BaseModel):
    """简化的树形结构节点表示，用于TOC"""
    data: SimpleTocNode
    children: List["TocTreeNode"] = []


# 更新引用，解决循环引用
TocTreeNode.model_rebuild()


class DocumentToc(BaseModel):
    """文档目录结构响应模型"""
    processed_document_id: int
    original_document_id: int
    toc: List[TocTreeNode]


# 简化的标题搜索响应模型
class HeaderSearchResult(BaseModel):
    """标题搜索结果模型"""
    header: SimpleTocNode
    children: List[DocumentNode]


class HeaderSearchResponse(BaseModel):
    """标题搜索响应模型"""
    message: str
    processed_document_id: int
    query: str
    results: List[HeaderSearchResult] 