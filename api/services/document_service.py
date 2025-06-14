import uuid
import aiofiles
from pathlib import Path
from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session

from api.models.document import Document
from api.schemas.document import DocumentCreate


# In a real app, this should be in a config file
STORAGE_PATH = Path("/app/storage/uploads")


async def save_upload_file(file: UploadFile, created_by: str, db: Session) -> Document:
    """
    Saves an uploaded file to the filesystem and creates a corresponding
    database record.
    """
    # Ensure the storage directory exists
    STORAGE_PATH.mkdir(parents=True, exist_ok=True)

    # Sanitize and create a unique filename to prevent overwrites
    original_filename = Path(file.filename).name
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

async def delete_document(document_id: int, db: Session) -> bool:
    """
    删除指定 ID 的文档及其关联的物理文件。
    
    Args:
        document_id: 要删除的文档 ID
        db: 数据库会话
        
    Returns:
        bool: 删除成功返回 True，文档不存在返回 False
    """
    # 查找文档记录
    document = db.query(Document).filter(Document.id == document_id).first()
    
    # 如果文档不存在，返回 False
    if not document:
        return False
    
    # 获取文件路径并检查是否存在
    filepath = Path(document.filepath)
    if filepath.exists():
        try:
            # 删除物理文件
            filepath.unlink()
            
            # 如果文件所在目录为空，也可以选择删除目录
            # 这里我们只删除文件，保留目录结构
        except Exception as e:
            # 如果文件删除失败，记录错误但继续删除数据库记录
            print(f"Warning: Could not delete file {filepath}: {e}")
    
    # 删除数据库记录
    db.delete(document)
    db.commit()
    
    return True 