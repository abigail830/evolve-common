#!/bin/bash

# 确保脚本在错误时退出
set -e

echo "生成轻量级依赖列表..."

# 确保在项目根目录运行
if [ ! -f "pyproject.toml" ]; then
    echo "错误：请在项目根目录运行此脚本"
    exit 1
fi

# 直接创建干净的requirements.txt文件
cat > requirements.txt << 'EOL'
# FastAPI和Web服务器依赖
fastapi==0.111.1
uvicorn==0.29.0
python-multipart==0.0.7
aiofiles==0.8.0
pydantic==2.11.5
pydantic-settings==2.9.1
starlette==0.37.2
python-dotenv==1.1.0

# 数据库相关依赖
sqlalchemy==2.0.41
alembic==1.16.1
psycopg2-binary==2.9.10

# 基础依赖库
anyio==4.9.0
cffi==1.17.1
click==8.2.1
cryptography==45.0.4
h11==0.16.0
idna==3.10
sniffio==1.3.1
typing_extensions==4.14.0

# 文档处理依赖（轻量级）
beautifulsoup4==4.13.4
lxml==5.4.0
pillow==11.2.1
python-docx==1.1.2
python-pptx==1.0.2
pymupdf==1.26.1
openpyxl==3.1.5
rtree==1.4.0
marko==2.1.3
requests==2.32.4
tqdm==4.67.1

# 注意：不要在这里包含docling，它将在Dockerfile中单独安装，使用--no-deps参数
# docling==2.36.1
# docling-core==2.34.2
EOL

echo "✅ 完成！requirements.txt已生成"
echo "此文件不包含大型ML依赖，docling将在构建时使用--no-deps参数单独安装" 