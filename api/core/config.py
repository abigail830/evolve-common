import os
from pathlib import Path
from pydantic import BaseModel

class Settings(BaseModel):
    """应用配置"""
    # 项目名称
    PROJECT_NAME: str = "Evolve Common API"
    
    # API版本
    API_V1_STR: str = "/api/v1"
    
    # 数据库URL
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./test.db")
    
    # 处理文件的存储目录
    PROCESSED_DIR: str = os.getenv("PROCESSED_DIR", "./storage/processed")
    
    # 上传文件的存储目录
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "./storage/uploads")
    
    # 确保目录存在
    def setup_directories(self):
        """确保必要的目录存在"""
        Path(self.PROCESSED_DIR).mkdir(parents=True, exist_ok=True)
        Path(self.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)

    model_config = {
        "env_file": ".env",
        "case_sensitive": True
    }

# 创建全局设置实例
settings = Settings()

# 确保目录存在
settings.setup_directories() 