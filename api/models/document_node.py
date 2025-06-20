import enum
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, JSON, Enum, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from api.db.base import Base


class NodeType(enum.Enum):
    HEADER = "header"
    TABLE = "table"
    IMAGE = "image"
    TEXT = "text"


class DocumentNode(Base):
    __tablename__ = "document_nodes"

    id = Column(Integer, primary_key=True, index=True)
    processed_document_id = Column(Integer, ForeignKey("processed_documents.id", ondelete="CASCADE"), nullable=False)
    parent_id = Column(Integer, ForeignKey("document_nodes.id", ondelete="CASCADE"), nullable=True)
    
    node_type = Column(Enum(NodeType), nullable=False)
    content = Column(Text, nullable=True)
    node_metadata = Column(JSON, nullable=True)
    position = Column(Integer, nullable=False)
    depth = Column(Integer, nullable=False, default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 关系
    processed_document = relationship("ProcessedDocument", back_populates="nodes")
    parent = relationship("DocumentNode", remote_side=[id], backref="children")
    
    # 索引以优化查询性能
    __table_args__ = (
        Index('idx_document_node_processed_doc_position', 'processed_document_id', 'position'),
        Index('idx_document_node_processed_doc_type', 'processed_document_id', 'node_type'),
        Index('idx_document_node_parent_id', 'parent_id'),
    ) 