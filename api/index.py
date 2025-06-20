from fastapi import FastAPI, Depends
# from .endpoints import documents, agents
from api.endpoints import documents
from sqlalchemy.orm import Session
from api.db.session import get_db
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 获取版本信息
VERSION = os.environ.get("APP_VERSION", "0.1.0")

app = FastAPI(
    title="Evolve File Processor",
    description="A file processing backend service",
    version=VERSION,
)

# Health check endpoint
@app.get("/")
def read_root():
    return {
        "message": "Welcome to the Evolve Common Service API",
        "version": VERSION,
    }

@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    """
    健康检查端点，验证服务和数据库连接状态
    """
    try:
        # 执行简单查询验证数据库连接
        db.execute("SELECT 1")
        return {
            "status": "healthy",
            "database": "connected",
            "service": "running",
            "version": VERSION,
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": str(e),
            "service": "running",
            "version": VERSION,
        }

# Include routers from endpoints
app.include_router(documents.router, prefix="/documents", tags=["Documents"])
# app.include_router(agents.router, prefix="/api/v1") 