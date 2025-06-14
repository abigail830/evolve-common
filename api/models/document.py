from sqlalchemy import Column, Integer, String, DateTime, func
from api.db.base import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    filepath = Column(String, nullable=False, unique=True)
    filesize = Column(Integer, nullable=False)
    created_by = Column(String, nullable=True)  # Simple user tracking
    created_at = Column(DateTime(timezone=True), server_default=func.now()) 