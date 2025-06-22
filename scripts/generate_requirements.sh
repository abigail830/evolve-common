#!/bin/bash

# 确保脚本在错误时退出
set -e

echo "生成轻量级依赖列表..."

# 确保在项目根目录运行
if [ ! -f "pyproject.toml" ]; then
    echo "错误：请在项目根目录运行此脚本"
    exit 1
fi

# 使用 poetry 生成锁文件
echo "更新 poetry.lock..."
poetry lock

# 创建临时环境并安装基础依赖
echo "创建临时虚拟环境..."
python -m venv .venv.temp
source .venv.temp/bin/activate

# 安装基本依赖和核心依赖，但避免安装大型ML库
pip install --upgrade pip wheel
echo "安装核心依赖..."

# 先安装基础依赖
pip install fastapi uvicorn[standard] python-dotenv pydantic pydantic-settings sqlalchemy alembic psycopg2-binary python-multipart aiofiles

# 安装docling-core和其他必要的轻量级依赖
pip install docling-core beautifulsoup4 lxml pillow python-docx python-pptx pymupdf openpyxl rtree marko requests tqdm

# 单独安装docling，但不安装其ML依赖
pip install --no-deps docling

# 生成requirements.txt
echo "生成requirements.txt..."
pip freeze > requirements.txt

# 清理
echo "清理临时环境..."
deactivate
rm -rf .venv.temp

echo "完成！requirements.txt已生成"
echo "以下是需要额外验证的包（可能是大型依赖）:"
grep -E 'torch|transformers|numpy|scipy|unstructured|easyocr' requirements.txt || echo "没有发现大型ML依赖！" 