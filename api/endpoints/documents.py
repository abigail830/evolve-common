from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, Path, Query
from sqlalchemy.orm import Session
from typing import Optional

from api.db.session import get_db
from api import schemas
from api.services import document_service
from api.services.document_processing_service import document_processing_service
from api.services.document_structure_service import document_structure_service
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
    description="Process an existing document using docling to convert to HTML format with preserved images.",
)
def process_document_to_html(
    *,
    document_id: int = Path(..., description="The ID of the document to process."),
    output_format: str = Query("html", description="The desired output format. Currently only 'html' is supported."),
    db: Session = Depends(get_db),
):
    """
    处理指定ID的文档，将其转换为HTML格式并保留图片：
    - 使用document_processing_service统一处理所有文档类型
    - 转换后的文件及其资源将被保存到处理目录中
    
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

    # 2. 使用document_processing_service处理文档
    try:
        # 使用统一的处理服务处理所有文档类型
        html_output_path, resources_path = document_processing_service.convert_file(document.filepath)
        print(f"使用docling处理文档: {document.filepath}")
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

@router.post(
    "/processed/{processed_document_id}/structured",
    status_code=201,
    summary="结构化处理HTML文档",
    description="对已处理的HTML文档进行结构化解析，提取标题、表格、图片和文本，并构建树形结构。",
)
def structure_document(
    *,
    processed_document_id: int = Path(..., description="要结构化处理的已处理文档ID"),
    db: Session = Depends(get_db),
):
    """
    对已处理为HTML格式的文档进行结构化处理：
    1. 获取HTML格式处理文档
    2. 删除已存在的结构化节点（如有）
    3. 解析HTML，按照标题、表格、图片、文本等元素进行拆分
    4. 构建文档树形结构
    5. 将结构信息存储到数据库
    
    - **processed_document_id**: 已处理文档ID
    """
    # 直接获取处理过的文档
    processed_document = document_service.get_processed_document(db, processed_document_id=processed_document_id)
    if not processed_document:
        raise HTTPException(status_code=404, detail=f"未找到ID为{processed_document_id}的处理文档")
        
    if processed_document.format.lower() != "html":
        raise HTTPException(status_code=400, detail=f"ID为{processed_document_id}的文档格式不是HTML")
    
    try:
        # 先删除已存在的结构信息
        deleted_count = document_structure_service.delete_document_structure(
            db=db, processed_document_id=processed_document_id
        )
        
        # 对文档进行结构化处理
        nodes = document_structure_service.process_html_document(
            db=db, processed_document_id=processed_document_id
        )
        
        return {
            "message": f"文档结构化处理成功，删除了{deleted_count}个旧节点，添加了{len(nodes)}个新节点", 
            "processed_document_id": processed_document_id
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except IOError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        error_message = f"文档结构化处理失败: {str(e)}"
        print(f"ERROR - {error_message}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=error_message)

@router.get(
    "/processed/{processed_document_id}/structure",
    status_code=200,
    summary="获取处理文档的结构",
    description="获取特定已处理文档的树形结构，节点按照标题层级组织。",
)
def get_processed_document_structure(
    *,
    processed_document_id: int = Path(..., description="已处理文档ID"),
    db: Session = Depends(get_db),
):
    """
    获取已处理文档的树形结构：
    1. 获取处理过的文档
    2. 检索其结构化节点信息
    3. 返回树形结构数据
    
    - **processed_document_id**: 已处理文档ID
    """
    # 直接获取处理过的文档
    processed_document = document_service.get_processed_document(db, processed_document_id=processed_document_id)
    if not processed_document:
        raise HTTPException(status_code=404, detail=f"未找到ID为{processed_document_id}的处理文档")
    
    try:
        # 获取文档结构
        structure = document_structure_service.get_document_structure(
            db=db, processed_document_id=processed_document_id
        )
        return {
            "processed_document_id": processed_document_id, 
            "original_document_id": processed_document.original_document_id,
            "structure": structure
        }
    except Exception as e:
        error_message = f"获取文档结构失败: {str(e)}"
        print(f"ERROR - {error_message}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=error_message)

@router.get(
    "/nodes/{node_id}/content",
    status_code=200,
    summary="获取节点内容",
    description="获取指定节点及其子节点的内容，特别适用于获取标题下的所有内容。",
)
def get_node_content(
    *,
    node_id: int = Path(..., description="节点ID"),
    db: Session = Depends(get_db),
):
    """
    获取指定节点及其子节点的内容：
    1. 查找指定ID的节点
    2. 如果是标题节点，获取其下所有内容
    3. 返回节点及子节点列表
    
    - **node_id**: 节点ID，通常是标题节点
    """
    try:
        # 获取节点及其子内容
        nodes = document_structure_service.get_header_subtree(db=db, node_id=node_id)
        
        if not nodes:
            raise HTTPException(status_code=404, detail=f"未找到ID为{node_id}的节点或该节点不是标题节点")
            
        return {"node": nodes[0], "children": nodes[1:] if len(nodes) > 1 else []}
    except Exception as e:
        error_message = f"获取节点内容失败: {str(e)}"
        print(f"ERROR - {error_message}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=error_message)

@router.delete(
    "/processed/{processed_document_id}/structure",
    status_code=200,
    summary="删除文档结构信息",
    description="删除指定已处理文档的所有结构化节点信息。",
)
def delete_document_structure(
    *,
    processed_document_id: int = Path(..., description="已处理文档ID"),
    db: Session = Depends(get_db),
):
    """
    删除指定已处理文档的所有结构化节点：
    1. 检查处理过的文档是否存在
    2. 删除所有关联的结构化节点
    
    - **processed_document_id**: 已处理文档ID
    """
    # 检查处理文档是否存在
    processed_document = document_service.get_processed_document(db, processed_document_id=processed_document_id)
    if not processed_document:
        raise HTTPException(status_code=404, detail=f"未找到ID为{processed_document_id}的处理文档")
    
    try:
        # 删除文档结构
        deleted_count = document_structure_service.delete_document_structure(
            db=db, processed_document_id=processed_document_id
        )
        return {"message": f"成功删除文档结构，共删除{deleted_count}个节点", "processed_document_id": processed_document_id}
    except Exception as e:
        error_message = f"删除文档结构失败: {str(e)}"
        print(f"ERROR - {error_message}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=error_message)

@router.get(
    "/processed/{processed_document_id}/toc",
    response_model=schemas.document_node.DocumentToc,
    status_code=200,
    summary="获取文档目录结构",
    description="获取文档的目录结构，仅包含标题节点，形成树形层级结构。",
)
def get_document_toc(
    *,
    processed_document_id: int = Path(..., description="已处理文档ID"),
    db: Session = Depends(get_db),
):
    """
    获取文档的目录结构（仅标题节点）：
    1. 获取处理过的文档
    2. 提取文档中的所有标题节点
    3. 以简化的树形结构返回整个目录
    
    - **processed_document_id**: 已处理文档ID
    """
    # 检查处理文档是否存在
    processed_document = document_service.get_processed_document(db, processed_document_id=processed_document_id)
    if not processed_document:
        raise HTTPException(status_code=404, detail=f"未找到ID为{processed_document_id}的处理文档")
    
    try:
        # 获取简化的目录结构
        toc = document_structure_service.get_document_toc_simplified(
            db=db, processed_document_id=processed_document_id
        )
        return schemas.document_node.DocumentToc(
            processed_document_id=processed_document_id, 
            original_document_id=processed_document.original_document_id,
            toc=toc
        )
    except Exception as e:
        error_message = f"获取目录结构失败: {str(e)}"
        print(f"ERROR - {error_message}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=error_message)


@router.get(
    "/processed/{processed_document_id}/search-headers",
    response_model=schemas.document_node.HeaderSearchResponse,
    status_code=200,
    summary="搜索标题内容",
    description="根据内容模糊搜索标题，并返回匹配的标题节点及其子节点。",
)
def search_headers(
    *,
    processed_document_id: int = Path(..., description="已处理文档ID"),
    query: str = Query(..., description="搜索文本，会进行模糊匹配"),
    db: Session = Depends(get_db),
):
    """
    搜索文档标题内容：
    1. 获取处理过的文档
    2. 根据查询文本模糊匹配标题内容
    3. 对每个匹配的标题，获取其子节点内容
    
    - **processed_document_id**: 已处理文档ID
    - **query**: 搜索文本，将进行模糊匹配
    """
    # 检查处理文档是否存在
    processed_document = document_service.get_processed_document(db, processed_document_id=processed_document_id)
    if not processed_document:
        raise HTTPException(status_code=404, detail=f"未找到ID为{processed_document_id}的处理文档")
    
    try:
        # 搜索标题
        header_nodes = document_structure_service.search_headers_by_content(
            db=db, processed_document_id=processed_document_id, search_text=query
        )
        
        if not header_nodes:
            return schemas.document_node.HeaderSearchResponse(
                message="未找到匹配的标题",
                processed_document_id=processed_document_id,
                query=query,
                results=[]
            )
        
        # 对每个匹配的标题获取其子节点，并转换为简化模型
        results = []
        for header in header_nodes:
            # 创建简化的标题节点
            simplified_header = schemas.document_node.SimpleTocNode(
                id=header.id,
                content=header.content,
                parent_id=header.parent_id,
                node_metadata=header.node_metadata
            )
            
            # 获取子节点
            nodes = document_structure_service.get_header_subtree(db=db, node_id=header.id)
            children = nodes[1:] if len(nodes) > 1 else []
            
            # 添加结果
            results.append(schemas.document_node.HeaderSearchResult(
                header=simplified_header,
                children=children
            ))
            
        return schemas.document_node.HeaderSearchResponse(
            message=f"找到{len(header_nodes)}个匹配的标题",
            processed_document_id=processed_document_id,
            query=query,
            results=results
        )
    except Exception as e:
        error_message = f"搜索标题失败: {str(e)}"
        print(f"ERROR - {error_message}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=error_message)
