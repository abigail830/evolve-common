from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class ProcessedDocumentBase(BaseModel):
    format: str
    file_path: str
    resources_path: Optional[str] = None

class ProcessedDocumentCreate(ProcessedDocumentBase):
    original_document_id: int

class ProcessedDocumentInDB(ProcessedDocumentBase):
    id: int
    original_document_id: int
    created_at: datetime

    model_config = {
        "from_attributes": True
    }

class ProcessedDocument(ProcessedDocumentInDB):
    pass 