from sqlalchemy import Column, Integer, String, DateTime, func, ForeignKey
from sqlalchemy.orm import relationship
from api.db.base import Base

class ProcessedDocument(Base):
    __tablename__ = "processed_documents"

    id = Column(Integer, primary_key=True, index=True)
    original_document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    file_path = Column(String, nullable=False, unique=True)
    resources_path = Column(String, nullable=True)  # 存储资源文件夹的路径
    format = Column(String, nullable=False, default="html")  # e.g., html, markdown
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    original_document = relationship("Document", back_populates="processed_documents") 