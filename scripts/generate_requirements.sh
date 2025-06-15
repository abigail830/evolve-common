#!/bin/bash

# 确保脚本在错误时退出
set -e

echo "生成 requirements.txt 文件..."

# 检查是否在虚拟环境中
if [ -z "$VIRTUAL_ENV" ]; then
    echo "错误: 请先激活虚拟环境 (source .venv/bin/activate)"
    exit 1
fi

# 检查 uv 是否已安装
if ! command -v uv &> /dev/null; then
    echo "错误: uv 未安装。请先安装 uv: 'brew install uv'"
    exit 1
fi

# 使用 uv pip list 生成 requirements.txt
echo "导出 requirements.txt..."
uv pip list --format=freeze > requirements.txt

# 从 pyproject.toml 提取直接依赖生成 requirements-minimal.txt
echo "生成 requirements-minimal.txt..."
grep -A 1000 "^\[tool.poetry.dependencies\]" pyproject.toml | grep -B 1000 "^\[tool.poetry.group" | grep "^[a-zA-Z]" | sed 's/ = .*$//' > requirements-minimal.txt

echo "完成! requirements.txt 和 requirements-minimal.txt 已更新。" 