from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, Path, Query
from sqlalchemy.orm import Session
from typing import Optional

from api.db.session import get_db
from api import schemas
from api.services import document_service
from api.models.document import Document

router = APIRouter()


@router.post(
    "/",
    response_model=schemas.document.Document,
    status_code=201,
    summary="Upload a document",
    description="Upload a file and create a document record in the database.",
)
async def upload_document(
    *,
    db: Session = Depends(get_db),
    file: UploadFile = File(..., description="The document file to upload."),
    created_by: str = Form("default_user", description="Identifier of the user uploading the file.")
):
    """
    Uploads a document. The file is saved to a storage volume and its metadata
    is recorded in the database.

    - **file**: The file to be uploaded.
    - **created_by**: The identifier for the user or system performing the upload.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided.")
        
    document = await document_service.save_upload_file(
        file=file, created_by=created_by, db=db
    )
    return document

@router.get(
    "/",
    response_model=list[schemas.document.Document],
    status_code=200,
    summary="List all documents",
    description="Retrieve all document records from the database with optional pagination and sorting.",
)
def list_documents(
    skip: int = Query(0, description="Number of records to skip (for pagination)"),
    limit: int = Query(100, description="Maximum number of records to return"),
    sort_by: Optional[str] = Query("created_at", description="Field to sort by (id, filename, filesize, created_at)"),
    sort_desc: bool = Query(True, description="Sort in descending order"),
    db: Session = Depends(get_db),
):
    """
    Retrieve all documents from the database with pagination and sorting options.
    
    - **skip**: Number of records to skip (for pagination)
    - **limit**: Maximum number of records to return
    - **sort_by**: Field to sort by (id, filename, filesize, created_at)
    - **sort_desc**: Sort in descending order if true, ascending if false
    """
    # 构建查询
    query = db.query(Document)
    
    # 排序
    if sort_by:
        # 确保排序字段存在
        if not hasattr(Document, sort_by):
            sort_by = "created_at"  # 默认排序字段
        
        # 获取排序字段
        sort_field = getattr(Document, sort_by)
        
        # 应用排序方向
        if sort_desc:
            query = query.order_by(sort_field.desc())
        else:
            query = query.order_by(sort_field)
    
    # 应用分页
    documents = query.offset(skip).limit(limit).all()
    
    return documents

@router.delete(
    "/{document_id}",
    status_code=204,
    summary="Delete a document",
    description="Delete a document record from the database and its associated file from storage.",
)
async def delete_document(
    document_id: int = Path(..., description="The ID of the document to delete"),
    db: Session = Depends(get_db),
):
    """
    Delete a document by its ID.
    
    This endpoint will:
    1. Find the document record in the database
    2. Delete the associated file from storage
    3. Remove the document record from the database
    
    - **document_id**: The ID of the document to delete
    """
    # 调用服务层的删除方法
    success = await document_service.delete_document(document_id=document_id, db=db)
    
    if not success:
        raise HTTPException(status_code=404, detail=f"Document with ID {document_id} not found")
    
    # 204 No Content 响应不需要返回内容
    return None 