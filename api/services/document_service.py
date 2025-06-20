import uuid
import aiofiles
from pathlib import Path
from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session
import os
from sqlalchemy import desc

from api.models.document import Document
from api.models.processed_document import ProcessedDocument
from api.schemas.document import DocumentCreate
from api.schemas.processed_document import ProcessedDocumentCreate


# Use a project-relative path for storage
STORAGE_PATH = Path("storage/uploads")


def get_document(db: Session, document_id: int) -> Document | None:
    """
    Retrieves a document by its ID.
    """
    return db.query(Document).filter(Document.id == document_id).first()


async def save_upload_file(file: UploadFile, created_by: str, db: Session) -> Document:
    """
    Saves an uploaded file to the filesystem and creates a corresponding
    database record.
    """
    # Ensure the storage directory exists
    STORAGE_PATH.mkdir(parents=True, exist_ok=True)

    # Sanitize and create a unique filename to prevent overwrites
    original_filename = Path(file.filename).name
    # Use os.path.join for better cross-platform compatibility
    unique_filename = f"{uuid.uuid4()}_{original_filename}"
    filepath = STORAGE_PATH / unique_filename

    # Save the file asynchronously
    try:
        # Get file size while reading
        file_size = 0
        async with aiofiles.open(filepath, "wb") as f:
            while content := await file.read(1024 * 1024):  # Read in 1MB chunks
                file_size += len(content)
                await f.write(content)

        if file_size == 0:
            raise HTTPException(status_code=400, detail="Cannot upload empty file.")

    except Exception as e:
        # Clean up failed upload
        if filepath.exists():
            filepath.unlink()
        raise HTTPException(status_code=500, detail=f"Could not save file: {e}")

    # Create the database record
    db_document_in = DocumentCreate(
        filename=original_filename,
        filepath=str(filepath),
        filesize=file_size,
        created_by=created_by,
    )
    
    db_document = Document(**db_document_in.dict())
    db.add(db_document)
    db.commit()
    db.refresh(db_document)

    return db_document 


def create_processed_document(db: Session, *, processed_document_in: ProcessedDocumentCreate) -> ProcessedDocument:
    """
    Creates a database record for a processed document.
    """
    db_processed_document = ProcessedDocument(**processed_document_in.dict())
    db.add(db_processed_document)
    db.commit()
    db.refresh(db_processed_document)
    return db_processed_document


async def delete_document(document_id: int, db: Session) -> bool:
    """
    删除指定 ID 的文档及其所有关联的处理文档和物理文件。
    
    Args:
        document_id: 要删除的文档 ID
        db: 数据库会话
        
    Returns:
        bool: 删除成功返回 True，文档不存在返回 False
    """
    # 查找文档记录
    document = get_document(db, document_id=document_id)
    
    # 如果文档不存在，返回 False
    if not document:
        return False
    
    # 1. 首先删除所有关联的处理文档
    processed_documents = get_processed_documents_by_original_id(db, original_document_id=document_id)
    for processed_doc in processed_documents:
        # 使用已有的delete_processed_document函数删除每个处理文档
        await delete_processed_document(db, processed_document_id=processed_doc.id)
    
    # 2. 删除原始文档的物理文件
    filepath = Path(document.filepath)
    if filepath.exists():
        try:
            # 删除物理文件
            filepath.unlink()
            
            # 如果文件目录为空，尝试删除目录
            try:
                parent_dir = filepath.parent
                if parent_dir.exists() and not any(parent_dir.iterdir()):
                    parent_dir.rmdir()
            except Exception as e:
                print(f"Warning: Could not delete empty directory {parent_dir}: {e}")
        except Exception as e:
            # 如果文件删除失败，记录错误但继续删除数据库记录
            print(f"Warning: Could not delete file {filepath}: {e}")
    
    # 3. 删除数据库记录
    db.delete(document)
    db.commit()
    
    return True


def get_processed_document(db: Session, processed_document_id: int) -> ProcessedDocument | None:
    """
    获取指定ID的处理过的文档。
    
    Args:
        db: 数据库会话
        processed_document_id: 处理过的文档ID
    
    Returns:
        ProcessedDocument: 处理过的文档对象，如果不存在则返回None
    """
    return db.query(ProcessedDocument).filter(ProcessedDocument.id == processed_document_id).first()


def get_processed_documents_by_original_id(db: Session, original_document_id: int) -> list[ProcessedDocument]:
    """
    获取原始文档关联的所有处理过的文档。
    
    Args:
        db: 数据库会话
        original_document_id: 原始文档ID
    
    Returns:
        list[ProcessedDocument]: 处理过的文档列表
    """
    return db.query(ProcessedDocument).filter(ProcessedDocument.original_document_id == original_document_id).all()


async def delete_processed_document(db: Session, processed_document_id: int) -> bool:
    """
    删除指定ID的处理过的文档及其关联的物理文件和资源目录。
    
    Args:
        db: 数据库会话
        processed_document_id: 处理过的文档ID
    
    Returns:
        bool: 删除成功返回True，文档不存在返回False
    """
    # 查找处理过的文档记录
    processed_document = get_processed_document(db, processed_document_id)
    
    # 如果处理过的文档不存在，返回False
    if not processed_document:
        return False
    
    # 获取文件路径并检查是否存在
    filepath = Path(processed_document.file_path)
    if filepath.exists():
        try:
            # 删除物理文件
            filepath.unlink()
        except Exception as e:
            # 如果文件删除失败，记录错误但继续删除数据库记录
            print(f"Warning: Could not delete file {filepath}: {e}")
    
    # 删除资源目录
    if processed_document.resources_path:
        resources_path = Path(processed_document.resources_path)
        if resources_path.exists():
            try:
                # 删除资源目录下的所有文件
                for file in resources_path.glob('*'):
                    try:
                        if file.is_file():
                            file.unlink()
                        elif file.is_dir():
                            import shutil
                            shutil.rmtree(file)
                    except Exception as e:
                        print(f"Warning: Could not delete resource file {file}: {e}")
                
                # 删除资源目录本身
                resources_path.rmdir()
                
                # 尝试删除父目录（如果为空）
                parent_dir = filepath.parent
                if parent_dir.exists() and not any(parent_dir.iterdir()):
                    parent_dir.rmdir()
            except Exception as e:
                print(f"Warning: Could not delete resources directory {resources_path}: {e}")
    
    # 删除数据库记录
    db.delete(processed_document)
    db.commit()
    
    return True 


def get_latest_processed_document_by_format(db: Session, original_document_id: int, format: str = "html") -> ProcessedDocument | None:
    """
    获取指定原始文档的最新处理文档，按指定格式过滤。
    
    Args:
        db: 数据库会话
        original_document_id: 原始文档ID
        format: 文档格式，默认为"html"
    
    Returns:
        ProcessedDocument: 处理过的文档对象，如果不存在则返回None
    """
    return db.query(ProcessedDocument).filter(
        ProcessedDocument.original_document_id == original_document_id,
        ProcessedDocument.format == format
    ).order_by(desc(ProcessedDocument.created_at)).first() 