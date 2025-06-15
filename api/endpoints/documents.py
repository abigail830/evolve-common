from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, Path, Query
from sqlalchemy.orm import Session
from typing import Optional

from api.db.session import get_db
from api import schemas
from api.services import document_service
from api.services.document_processing_service import document_processing_service
from api.services.mammoth_document_service import docx_to_html_converter
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

@router.post(
    "/{document_id}/process",
    response_model=schemas.processed_document.ProcessedDocument,
    status_code=201,
    summary="Process a document and convert to HTML",
    description="Process an existing document using mammoth for DOCX files or docling for other formats to convert to HTML format with preserved images.",
)
def process_document_to_html(
    *,
    document_id: int = Path(..., description="The ID of the document to process."),
    output_format: str = Query("html", description="The desired output format. Currently only 'html' is supported."),
    db: Session = Depends(get_db),
):
    """
    处理指定ID的文档，根据文件类型选择合适的处理方法将其转换为HTML格式：
    - 对于DOCX文档：使用Mammoth转换为HTML并提取图片
    - 对于其他格式：使用原有的docling转换服务
    
    转换后的文件及其资源将被保存到处理目录中。

    - **document_id**: 要处理的文档ID.
    - **output_format**: 输出格式，目前只支持"html".
    """
    # 1. 从数据库获取文档
    document = document_service.get_document(db, document_id=document_id)
    if not document:
        raise HTTPException(status_code=404, detail=f"Document with ID {document_id} not found")
    
    # 检查请求的输出格式
    if output_format.lower() != "html":
        raise HTTPException(status_code=400, detail="Currently only HTML output format is supported")

    # 2. 根据文档格式选择合适的处理服务处理文档
    try:
        if document.filepath.lower().endswith('.docx'):
            # 对于DOCX文档使用Mammoth服务
            html_output_path, resources_path = docx_to_html_converter.convert_file(document.filepath)
            print(f"使用Mammoth转换DOCX文档: {document.filepath}")
        else:
            # 对于其他格式使用原有的处理服务
            html_output_path, resources_path = document_processing_service.convert_file(document.filepath)
            print(f"使用原始服务转换非DOCX文档: {document.filepath}")
            
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # 捕获可能的错误，提供详细信息以便调试
        error_message = f"Failed to process document: {str(e)}"
        print(f"ERROR - {error_message}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=error_message)

    # 3. 为处理后的文档创建数据库记录
    processed_doc_in = schemas.processed_document.ProcessedDocumentCreate(
        original_document_id=document_id,
        file_path=html_output_path,
        resources_path=resources_path,
        format=output_format.lower(),
    )

    db_processed_document = document_service.create_processed_document(
        db=db, processed_document_in=processed_doc_in
    )

    return db_processed_document


@router.get(
    "/{document_id}/processed",
    response_model=list[schemas.processed_document.ProcessedDocument],
    status_code=200,
    summary="List all processed documents for a document",
    description="Retrieve all processed document records related to the specified original document.",
)
def list_processed_documents(
    document_id: int = Path(..., description="The ID of the original document."),
    db: Session = Depends(get_db),
):
    """
    列出指定原始文档关联的所有处理过的文档。
    
    - **document_id**: 原始文档ID
    """
    # 首先检查原始文档是否存在
    document = document_service.get_document(db, document_id=document_id)
    if not document:
        raise HTTPException(status_code=404, detail=f"Document with ID {document_id} not found")
    
    # 获取所有关联的处理过的文档
    processed_documents = document_service.get_processed_documents_by_original_id(db, original_document_id=document_id)
    
    return processed_documents


@router.delete(
    "/processed/{processed_document_id}",
    status_code=204,
    summary="Delete a processed document",
    description="Delete a processed document record from the database and its associated file from storage.",
)
async def delete_processed_document(
    processed_document_id: int = Path(..., description="The ID of the processed document to delete"),
    db: Session = Depends(get_db),
):
    """
    删除指定ID的处理过的文档。
    
    此端点将：
    1. 根据ID查找处理过的文档记录
    2. 删除关联的物理文件
    3. 从数据库中删除文档记录
    
    - **processed_document_id**: 要删除的处理过文档的ID
    """
    # 调用服务层的删除方法
    success = await document_service.delete_processed_document(db=db, processed_document_id=processed_document_id)
    
    if not success:
        raise HTTPException(status_code=404, detail=f"Processed document with ID {processed_document_id} not found")
    
    # 204 No Content 响应不需要返回内容
    return None
