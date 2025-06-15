from pydantic import BaseModel
from datetime import datetime
from .processed_document import ProcessedDocument


# Shared properties
class DocumentBase(BaseModel):
    filename: str
    filesize: int
    created_by: str | None = None


# Properties to receive on item creation
class DocumentCreate(DocumentBase):
    filepath: str


# Properties to return to client
class Document(DocumentBase):
    id: int
    filepath: str
    created_at: datetime
    processed_documents: list[ProcessedDocument] = []

    class Config:
        orm_mode = True 