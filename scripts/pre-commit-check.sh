#!/bin/bash
# 预提交检查脚本 - 检查requirements.txt是否包含大型ML依赖

echo "检查requirements.txt是否包含大型ML依赖..."

# 检查requirements.txt是否存在
if [ ! -f "requirements.txt" ]; then
    echo "警告: requirements.txt文件不存在!"
    exit 1
fi

# 检查是否包含大型ML依赖
if grep -E 'torch|transformers|numpy|scipy|unstructured|easyocr|docling-ibm-models' requirements.txt; then
    echo "⚠️ 错误: requirements.txt包含大型ML库依赖!"
    echo "请运行 'make clean-requirements' 生成轻量级依赖列表"
    exit 1
fi

echo "✅ requirements.txt检查通过，未包含大型ML依赖"
exit 0 